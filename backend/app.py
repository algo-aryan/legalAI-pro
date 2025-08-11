# backend/app.py - Flask API Server

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import tempfile
import uuid
from werkzeug.utils import secure_filename
import json
from datetime import datetime

# Import our chatbots
from general_legal_bot import legal_bot
from contract_bot import ContractAnalyzer
# Remove: from app import contract_analyzers
from globals import contract_analyzers


# inside your existing app.py
from legal_bert_service import bp as contract_bp
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
UPLOAD_FOLDER = 'uploads'
VECTORSTORE_FOLDER = 'vectorstore'
ALLOWED_EXTENSIONS = {'pdf'}

app.register_blueprint(contract_bp, url_prefix="/api")


# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VECTORSTORE_FOLDER, exist_ok=True)

# Global variables to store contract analyzer instances

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Static file serving (for frontend)
@app.route('/')
def serve_frontend():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'LegalAI Pro API is running'})

@app.route('/api/chat/general', methods=['POST'])
def general_chat():
    """General legal assistant chat endpoint"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get response from general legal bot
        response = legal_bot(message)
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        print(f"Error in general chat: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your request'}), 500

@app.route('/api/contract/upload', methods=['POST'])
def upload_contract():
    """Upload and analyze contract endpoint"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, f"{session_id}_{filename}")
        file.save(filepath)
        
        # Initialize contract analyzer for this session
        contract_analyzer = ContractAnalyzer()
        contract_analyzer.load_document(filepath)
        
        # Store analyzer instance
        contract_analyzers[session_id] = contract_analyzer
        
        # Generate initial analysis
        analysis_result = contract_analyzer.analyze_contract()
        
        return jsonify({
            'session_id': session_id,
            'filename': filename,
            'analysis': analysis_result,
            'message': 'Contract uploaded and analyzed successfully'
        })
    
    except Exception as e:
        print(f"Error in contract upload: {str(e)}")
        return jsonify({'error': f'An error occurred while uploading the contract: {str(e)}'}), 500

@app.route('/api/contract/chat', methods=['POST'])
def contract_chat():
    """Contract-specific chat endpoint"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        message = data.get('message', '').strip()
        
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get contract analyzer for this session
        contract_analyzer = contract_analyzers.get(session_id)
        if not contract_analyzer:
            return jsonify({'error': 'Contract session not found. Please upload a contract first.'}), 404
        
        # Get response from contract bot
        response = contract_analyzer.ask_question(message)
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        print(f"Error in contract chat: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your request'}), 500

@app.route('/api/contract/analyze', methods=['POST'])
def analyze_contract():
    """Re-analyze contract for detailed insights"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        
        # Get contract analyzer for this session
        contract_analyzer = contract_analyzers.get(session_id)
        if not contract_analyzer:
            return jsonify({'error': 'Contract session not found'}), 404
        
        # Generate detailed analysis
        analysis = contract_analyzer.analyze_contract()
        
        return jsonify({
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        print(f"Error in contract analysis: {str(e)}")
        return jsonify({'error': 'An error occurred while analyzing the contract'}), 500

@app.route('/api/case/predict', methods=['POST'])
def predict_case():
    """Case outcome prediction endpoint"""
    try:
        data = request.get_json()
        case_type = data.get('case_type')
        case_description = data.get('case_description')
        jurisdiction = data.get('jurisdiction')
        case_value = data.get('case_value', '')
        parties_involved = data.get('parties_involved', '')
        
        # Validate required fields
        if not all([case_type, case_description, jurisdiction]):
            return jsonify({'error': 'Case type, description, and jurisdiction are required'}), 400
        
        # Create prediction prompt
        prediction_prompt = f"""
        Analyze this legal case and provide a prediction:
        
        Case Type: {case_type}
        Description: {case_description}
        Jurisdiction: {jurisdiction}
        Case Value: {case_value}
        Parties: {parties_involved}
        
        Provide:
        1. Predicted outcome probability (as percentage)
        2. Key factors affecting the case
        3. Strategic recommendations
        4. Estimated timeline
        5. Potential settlement range (if applicable)
        
        Format as JSON with clear sections.
        """
        
        # Use general legal bot for prediction
        response = legal_bot(prediction_prompt)
        
        # Mock structured response (you can enhance this with actual ML model)
        prediction_data = {
            'confidence': 78,  # This should come from your ML model
            'outcome': response[:200] + "..." if len(response) > 200 else response,
            'factors': [
                'Strong evidence documentation',
                'Clear liability establishment', 
                'Favorable jurisdiction precedents'
            ],
            'recommendations': [
                'Consider mediation before litigation',
                'Strengthen evidence collection',
                'Prepare for settlement negotiations'
            ],
            'timeline': '6-12 months',
            'full_analysis': response
        }
        
        return jsonify({
            'prediction': prediction_data,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        print(f"Error in case prediction: {str(e)}")
        return jsonify({'error': 'An error occurred while predicting case outcome'}), 500

# Cleanup endpoint to manage memory
@app.route('/api/cleanup', methods=['POST'])
def cleanup_session():
    """Clean up contract analyzer session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if session_id and session_id in contract_analyzers:
            del contract_analyzers[session_id]
            
            # Optional: Delete uploaded file
            for filename in os.listdir(UPLOAD_FOLDER):
                if filename.startswith(session_id):
                    os.remove(os.path.join(UPLOAD_FOLDER, filename))
        
        return jsonify({'message': 'Session cleaned up successfully'})
    
    except Exception as e:
        print(f"Error in cleanup: {str(e)}")
        return jsonify({'error': 'An error occurred during cleanup'}), 500

if __name__ == '__main__':
    print("Starting LegalAI Pro Backend Server...")
    print("Frontend will be available at: http://localhost:5000")
    print("API endpoints available at: http://localhost:5000/api/")
    app.run(debug=True, host='0.0.0.0', port=5000)