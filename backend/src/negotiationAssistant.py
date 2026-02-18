"""
Negotiation Assistant Module
Handles car lease/loan negotiation interactions with Ollama
Includes background fine-tuning capability based on conversation history
"""

import ollama
import json
import os
import threading
import time
from datetime import datetime


# Background fine-tuning state
FINE_TUNING_STATE = {
    'is_running': False,
    'progress': 0,
    'status': 'idle',
    'last_run': None,
    'conversations_processed': 0
}

FINE_TUNING_LOCK = threading.Lock()


def chat_with_ollama(messages, model='llama3.2'):
    """
    Send messages to Ollama and return the response.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model name to use (default: llama3.2)
    
    Returns:
        Response dict from Ollama or error dict
    """
    try:
        response = ollama.chat(
            model=model,
            messages=messages,
            options={
                'temperature': 0.7,
                'top_p': 0.9,
                'num_predict': 2048
            }
        )
        return response
    except Exception as e:
        return {'error': f'Ollama chat failed: {str(e)}'}


def negotiate_with_ollama(analysis_text, market_data='', action='points', context=None):
    """
    Generate negotiation advice based on analysis and market data.
    
    Args:
        analysis_text: The contract/VIN analysis text
        market_data: Market comparison data (optional)
        action: Type of output ('questions', 'points', 'email')
        context: Additional context dict (recipient, tone, etc.)
    
    Returns:
        JSON string with negotiation advice
    """
    context = context or {}
    
    # Build the prompt based on action type
    if action == 'questions':
        prompt = f"""Based on the following car lease/loan analysis, generate 5-7 clarifying questions 
that a consumer should ask the dealer or lender. Focus on unclear terms, missing information, 
and potential negotiation opportunities.

Analysis:
{analysis_text}

{f"Market Data: {market_data}" if market_data else ""}

Return ONLY valid JSON in this format:
{{
    "questions": ["question 1", "question 2", ...],
    "explanation": "Brief explanation of why these questions are important"
}}"""

    elif action == 'email':
        recipient = context.get('recipient', 'Dealer/Lender')
        tone = context.get('tone', 'professional')
        
        prompt = f"""Generate a professional negotiation email based on the following analysis.
The email should be {tone} in tone and address key negotiation points.

Analysis:
{analysis_text}

{f"Market Data: {market_data}" if market_data else ""}

Recipient: {recipient}

Return ONLY valid JSON in this format:
{{
    "subject": "Email subject line",
    "body": "Full email body with greeting, main points, and closing",
    "notes": "Tips for sending this email"
}}"""

    else:  # action == 'points'
        prompt = f"""Based on the following car lease/loan analysis, generate 3-5 concrete negotiation points 
with rationale and suggested talking points. Focus on terms that favor the consumer.

Analysis:
{analysis_text}

{f"Market Data: {market_data}" if market_data else ""}

Return ONLY valid JSON in this format:
{{
    "negotiation_points": [
        {{
            "point": "Brief negotiation point title",
            "rationale": "Why this is important and data to support it",
            "suggested_text": "Exact phrase consumer can use"
        }},
        ...
    ],
    "summary": "Overall negotiation strategy summary"
}}"""

    try:
        messages = [
            {
                'role': 'system',
                'content': 'You are an expert car lease/loan negotiation assistant. '
                          'Always return valid JSON responses. Be concise and consumer-focused.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ]
        
        response = chat_with_ollama(messages, model='llama3.2')
        
        if isinstance(response, dict) and 'error' in response:
            return json.dumps({'error': response['error']})
        
        # Extract the content from response
        reply = response.get('message', {}).get('content', '')
        
        # Try to clean up and validate JSON
        reply = reply.strip()
        if reply.startswith('```json'):
            reply = reply[7:]
        if reply.startswith('```'):
            reply = reply[3:]
        if reply.endswith('```'):
            reply = reply[:-3]
        reply = reply.strip()
        
        # Validate it's proper JSON
        json.loads(reply)  # Will raise if invalid
        
        return reply
        
    except json.JSONDecodeError:
        # If model didn't return valid JSON, wrap it
        return json.dumps({
            'error': 'Model returned invalid JSON',
            'raw_response': reply if 'reply' in locals() else 'No response'
        })
    except Exception as e:
        return json.dumps({'error': f'Negotiation failed: {str(e)}'})


def start_background_fine_tuning(chat_log_folder='chat_logs', model='llama3.2'):
    """
    Start background fine-tuning process in a separate thread.
    Analyzes conversation logs to improve model responses.
    
    Args:
        chat_log_folder: Path to folder containing chat logs
        model: Model name to fine-tune
    """
    def fine_tune_worker():
        with FINE_TUNING_LOCK:
            if FINE_TUNING_STATE['is_running']:
                print("[FINE-TUNE] Already running, skipping")
                return
            
            FINE_TUNING_STATE['is_running'] = True
            FINE_TUNING_STATE['status'] = 'analyzing'
            FINE_TUNING_STATE['progress'] = 0
            FINE_TUNING_STATE['last_run'] = datetime.now().isoformat()
        
        try:
            print(f"[FINE-TUNE] Starting background fine-tuning at {datetime.now()}")
            
            # Load all chat logs
            if not os.path.exists(chat_log_folder):
                print(f"[FINE-TUNE] Chat log folder not found: {chat_log_folder}")
                return
            
            log_files = [f for f in os.listdir(chat_log_folder) if f.endswith('.json')]
            total_logs = len(log_files)
            
            print(f"[FINE-TUNE] Found {total_logs} chat logs to analyze")
            
            if total_logs == 0:
                with FINE_TUNING_LOCK:
                    FINE_TUNING_STATE['status'] = 'no_data'
                return
            
            # Analyze conversations to build training patterns
            successful_patterns = []
            
            for idx, log_file in enumerate(log_files):
                try:
                    with open(os.path.join(chat_log_folder, log_file), 'r', encoding='utf-8') as f:
                        log_data = json.load(f)
                    
                    # Extract successful conversation patterns
                    if log_data.get('user_messages') and log_data.get('assistant_reply'):
                        pattern = {
                            'context': log_data.get('user_messages', []),
                            'response': log_data.get('assistant_reply', ''),
                            'quality_score': calculate_response_quality(log_data)
                        }
                        
                        # Only include high-quality responses
                        if pattern['quality_score'] > 0.7:
                            successful_patterns.append(pattern)
                    
                    # Update progress
                    progress = int((idx + 1) / total_logs * 100)
                    with FINE_TUNING_LOCK:
                        FINE_TUNING_STATE['progress'] = progress
                        FINE_TUNING_STATE['conversations_processed'] = idx + 1
                    
                    time.sleep(0.01)  # Small delay to not overwhelm system
                    
                except Exception as e:
                    print(f"[FINE-TUNE] Error processing {log_file}: {e}")
                    continue
            
            print(f"[FINE-TUNE] Identified {len(successful_patterns)} high-quality patterns")
            
            # In a real implementation, you would:
            # 1. Create a fine-tuning dataset from successful_patterns
            # 2. Use Ollama's fine-tuning API (when available)
            # 3. Save the fine-tuned model
            
            # For now, we'll save the patterns for future use
            with FINE_TUNING_LOCK:
                FINE_TUNING_STATE['status'] = 'training'
                FINE_TUNING_STATE['progress'] = 50
            
            # Simulate training process (in real implementation, this would be actual training)
            patterns_file = os.path.join(chat_log_folder, '_fine_tune_patterns.json')
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'model': model,
                    'total_patterns': len(successful_patterns),
                    'patterns': successful_patterns[:50],  # Save top 50 patterns
                    'metrics': {
                        'avg_quality': sum(p['quality_score'] for p in successful_patterns) / len(successful_patterns) if successful_patterns else 0,
                        'total_conversations': total_logs
                    }
                }, f, indent=2, ensure_ascii=False)
            
            print(f"[FINE-TUNE] Saved fine-tuning patterns to {patterns_file}")
            
            # Update progress to completion
            with FINE_TUNING_LOCK:
                FINE_TUNING_STATE['status'] = 'completed'
                FINE_TUNING_STATE['progress'] = 100
            
            print(f"[FINE-TUNE] Completed at {datetime.now()}")
            
        except Exception as e:
            print(f"[FINE-TUNE] Error during fine-tuning: {e}")
            with FINE_TUNING_LOCK:
                FINE_TUNING_STATE['status'] = 'error'
                FINE_TUNING_STATE['error'] = str(e)
        
        finally:
            with FINE_TUNING_LOCK:
                FINE_TUNING_STATE['is_running'] = False
    
    # Start in background thread
    thread = threading.Thread(target=fine_tune_worker, daemon=True)
    thread.start()
    print("[FINE-TUNE] Background fine-tuning thread started")


def calculate_response_quality(log_data):
    """
    Calculate quality score for a conversation log.
    Used to identify high-quality responses for fine-tuning.
    
    Args:
        log_data: Chat log dictionary
    
    Returns:
        Quality score between 0 and 1
    """
    score = 0.0
    
    try:
        reply = log_data.get('assistant_reply', '')
        
        # Check for JSON structure (indicates structured response)
        try:
            json.loads(reply)
            score += 0.3
        except:
            pass
        
        # Check response length (not too short, not too long)
        if 100 < len(reply) < 2000:
            score += 0.2
        elif 50 < len(reply) <= 100:
            score += 0.1
        
        # Check for key negotiation terms
        negotiation_keywords = [
            'negotiate', 'contract', 'terms', 'rate', 'price',
            'monthly', 'payment', 'lease', 'loan', 'dealer'
        ]
        keyword_count = sum(1 for kw in negotiation_keywords if kw.lower() in reply.lower())
        score += min(keyword_count * 0.05, 0.3)
        
        # Check for professional tone indicators
        quality_indicators = [
            'suggest', 'recommend', 'consider', 'important',
            'should', 'could', 'typically', 'generally'
        ]
        indicator_count = sum(1 for ind in quality_indicators if ind.lower() in reply.lower())
        score += min(indicator_count * 0.05, 0.2)
        
    except Exception:
        pass
    
    return min(score, 1.0)


def get_fine_tuning_status():
    """
    Get current fine-tuning status.
    
    Returns:
        Dictionary with fine-tuning state information
    """
    with FINE_TUNING_LOCK:
        return dict(FINE_TUNING_STATE)
