from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import json
from datetime import datetime
import uuid
import ollama

# Import from separate modules
from slaExtractor import extract_text_from_file, process_with_ollama
from vinAnalyzer import analyze_vin
from negotiationAssistant import negotiate_with_ollama, chat_with_ollama

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
CHAT_LOG_FOLDER = 'chat_logs'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(CHAT_LOG_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return jsonify({
        'message': 'File Upload and Processing API',
        'endpoints': {
            '/upload': 'POST - Upload and process file',
            '/files': 'GET - List all processed files',
            '/files/<id>': 'GET - Get specific processed file data'
        }
    })


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save the uploaded file
        file.save(filepath)
        
        # Extract text from file
        text_content = extract_text_from_file(filepath)
        
        # Process with Ollama
        ollama_result = process_with_ollama(text_content, filename)
        
        # Save processed data
        processed_data = {
            'id': timestamp,
            'original_filename': filename,
            'uploaded_filename': unique_filename,
            'upload_time': datetime.now().isoformat(),
            'file_path': filepath,
            'extracted_text': text_content[:500],  # First 500 chars
            'ollama_analysis': ollama_result,
            'file_size': os.path.getsize(filepath)
        }
        
        # Save to JSON file
        processed_file = os.path.join(PROCESSED_FOLDER, f"{timestamp}.json")
        with open(processed_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'message': 'File uploaded and processed successfully',
            'data': processed_data
        }), 200
    
    return jsonify({'error': 'File type not allowed'}), 400


@app.route('/files', methods=['GET'])
def list_files():
    """List all processed files"""
    try:
        processed_files = []
        for filename in os.listdir(PROCESSED_FOLDER):
            if filename.endswith('.json'):
                filepath = os.path.join(PROCESSED_FOLDER, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    processed_files.append({
                        'id': data['id'],
                        'filename': data['original_filename'],
                        'upload_time': data['upload_time'],
                        'file_size': data['file_size']
                    })
        
        # Sort by upload time, newest first
        processed_files.sort(key=lambda x: x['upload_time'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': processed_files
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/files/<file_id>', methods=['GET'])
def get_file(file_id):
    """Get specific processed file data"""
    try:
        filepath = os.path.join(PROCESSED_FOLDER, f"{file_id}.json")
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify({
                'success': True,
                'data': data
            }), 200
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Check if Ollama is available"""
    try:
        ollama.list()
        return jsonify({
            'status': 'healthy',
            'ollama': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'ollama': 'disconnected',
            'error': str(e)
        }), 500


@app.route('/presets', methods=['GET'])
def list_presets():
    """Return available conversation presets and short descriptions."""
    presets = {
        'car_negotiation': 'Negotiation assistant preseeded for car lease/loan contract review and negotiation.'
    }
    return jsonify({'success': True, 'presets': presets}), 200


@app.route('/analyze-vin', methods=['POST'])
def analyze_vin_route():
    """API endpoint to analyze VINs. Accepts JSON { vin: '...' } or form data."""
    vin = None
    if request.is_json:
        body = request.get_json()
        vin = body.get('vin')
    else:
        vin = request.form.get('vin') or request.args.get('vin')

    if not vin:
        return jsonify({'error': 'No VIN provided'}), 400

    result = analyze_vin(vin.strip())
    return jsonify({'success': True, 'vin': vin, 'analysis': result}), 200


@app.route('/negotiation', methods=['POST'])
def negotiation_route():
    """Endpoint to generate negotiation questions/points/email.
    Expected JSON: { analysis: <string or object>, market_data: <string>, action: 'questions'|'points'|'email', context: { recipient, tone, ... } }
    """
    if not request.is_json:
        return jsonify({'error': 'Expected JSON body'}), 400

    body = request.get_json()
    analysis = body.get('analysis')
    market_data = body.get('market_data', '')
    action = body.get('action', 'points')
    context = body.get('context', {})

    # Normalize analysis to text
    if isinstance(analysis, dict):
        analysis_text = json.dumps(analysis)
    else:
        analysis_text = str(analysis or '')

    result = negotiate_with_ollama(analysis_text, market_data, action, context)

    # Try to parse model response as JSON and return it; otherwise return raw
    try:
        parsed = json.loads(result)
        return jsonify({'success': True, 'result': parsed}), 200
    except Exception:
        return jsonify({'success': True, 'raw': result}), 200


@app.route('/chat', methods=['POST'])
def chat_route():
    """Proxy chat messages to Ollama. Expect JSON: { messages: [{role, content}], model?: 'llama3.2' }
    Returns { success: True, reply: <string>, raw: <ollama response> } or error.
    """
    if not request.is_json:
        return jsonify({'error': 'Expected JSON body'}), 400

    body = request.get_json()
    messages = body.get('messages')
    # preserve original user-sent messages for logging
    original_messages = list(messages) if isinstance(messages, list) else []
    model = body.get('model', 'llama3.2')
    preset = body.get('preset')

    if not messages or not isinstance(messages, list):
        return jsonify({'error': 'Missing or invalid messages array'}), 400

    # If a preset is requested, insert the preset system prompt first
    if preset == 'car_negotiation':
        # Project-specific system prompt for negotiation assistant
        CAR_NEGOTIATION_PROMPT = (
            "Project: Car Lease/Loan Contract Review and Negotiation AI Assistant. "
            "You assist consumers in understanding, reviewing, and negotiating car lease or loan contracts. "
            "Focus on extracting SLA terms (interest rates, mileage limits, penalties, early termination), providing fair market benchmarks, and suggesting negotiation strategies and messages. "
            "Be concise, action-oriented, and provide JSON outputs when requested (questions, negotiation points, email drafts). Prioritize consumer-friendly language and cite assumptions."
        )
        # Prepend system message
        messages = [{'role': 'system', 'content': CAR_NEGOTIATION_PROMPT}] + messages

    try:
        resp = chat_with_ollama(messages, model=model)
        print(f"[DEBUG] Ollama response type: {type(resp)}")
        print(f"[DEBUG] Ollama response: {resp}")
    except Exception as e:
        print(f"[ERROR] chat_with_ollama failed: {str(e)}")
        return jsonify({'success': False, 'error': f'Ollama request failed: {str(e)}'}), 500

    # If resp is an error dict
    if isinstance(resp, dict) and resp.get('error'):
        print(f"[ERROR] Ollama returned error: {resp.get('error')}")
        return jsonify({'success': False, 'error': resp.get('error')}), 500

    try:
        # Expecting structure: {'message': {'content': '...'}}
        reply = resp['message']['content']
        print(f"[DEBUG] Extracted reply: {reply[:100]}...")

        # Save chat log (original messages + assistant reply)
        try:
            log_entry = {
                'id': uuid.uuid4().hex,
                'timestamp': datetime.now().isoformat(),
                'model': model,
                'preset': preset,
                'user_messages': original_messages,
                'system_messages': [m for m in messages if m.get('role') == 'system'],
                'assistant_reply': reply,
                'raw_response': resp
            }
            log_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{log_entry['id']}.json"
            log_path = os.path.join(CHAT_LOG_FOLDER, log_name)
            try:
                with open(log_path, 'w', encoding='utf-8') as f:
                    json.dump(log_entry, f, indent=2, ensure_ascii=False)
            except TypeError:
                # Fallback if raw response contains non-serializable parts
                log_entry['raw_response'] = str(resp)
                with open(log_path, 'w', encoding='utf-8') as f:
                    json.dump(log_entry, f, indent=2, ensure_ascii=False)
        except Exception:
            # Log save should not break the API response
            pass

        return jsonify({'success': True, 'reply': reply, 'raw': resp}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to parse model response: {str(e)}', 'raw': resp}), 500





if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
