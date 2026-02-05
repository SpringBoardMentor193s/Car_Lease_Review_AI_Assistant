"""
Negotiation Assistant Module
Handles chat and negotiation functionalities using Ollama
"""

import json
import ollama


def negotiate_with_ollama(analysis_text: str, market_data: str, action: str, context: dict):
    """Use Ollama to generate negotiation questions, points, or email drafts.
    action: 'questions' | 'points' | 'email'
    Returns raw model content (expected JSON string).
    """
    # Build instruction
    system_prompt = (
        "You are a helpful negotiation assistant for customers reviewing service contracts and SLAs. "
        "When given the contract analysis and optional market data, produce concise, actionable outputs. "
        "You must respond ONLY with valid JSON matching the requested schema. No additional text or commentary."
    )

    # Define schema depending on action
    if action == 'questions':
        schema = (
            '{"questions": ["short question strings"], "explanation": "one-line explanation"}'
        )
        user_prompt = (
            "Produce a list of focused questions the buyer should ask the dealer or vendor regarding the contract/SLA. "
            "Include any follow-ups and a one-line explanation. Return ONLY valid JSON matching this schema: " + schema
        )
    elif action == 'points':
        schema = (
            '{"negotiation_points": [{"point":"short title","rationale":"why it matters","suggested_text":"text to propose"}], "summary":"short summary"}'
        )
        user_prompt = (
            "Analyze the contract/SLA and produce negotiation talking points prioritized for the customer. "
            "For each point provide a short rationale and suggested wording the customer can use. Return ONLY valid JSON matching this schema: " + schema
        )
    else:
        # email
        schema = ('{"subject":"...","body":"...","notes":"optional"}')
        user_prompt = (
            "Generate a polite, clear negotiation email to the dealer asking for desired changes based on the contract analysis and market data. "
            "Return ONLY valid JSON matching this schema: " + schema
        )

    # Combine inputs
    user_message = "Contract Analysis:\n" + (analysis_text or "(none)") + "\n\nMarket Data:\n" + (market_data or "(none)") + "\n\nContext:\n" + json.dumps(context or {}) + "\n\n" + user_prompt

    try:
        response = ollama.chat(
            model='llama3.2',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ],
            format='json'
        )

        return response['message']['content']
    except Exception as e:
        return json.dumps({'error': 'Ollama call failed', 'message': str(e)})


def chat_with_ollama(messages, model='llama3.2'):
    """Send a messages array to Ollama and return the assistant content."""
    try:
        print(f"[DEBUG] Sending {len(messages)} messages to Ollama model: {model}")
        for i, msg in enumerate(messages):
            print(f"[DEBUG] Message {i}: role={msg.get('role')}, content={msg.get('content', '')[:50]}...")
        
        response = ollama.chat(
            model=model,
            messages=messages
        )
        print(f"[DEBUG] Ollama chat response received: {type(response)}")
        return response
    except Exception as e:
        print(f"[ERROR] Ollama chat exception: {str(e)}")
        return {'error': str(e)}
