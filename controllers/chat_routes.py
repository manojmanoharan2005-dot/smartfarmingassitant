from flask import Blueprint, request, jsonify, session
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# Configure Gemini API from environment variable
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please add your API key to .env")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model - use gemma-3-4b-it
model = genai.GenerativeModel('gemma-3-4b-it')

# System context for the chatbot
SYSTEM_CONTEXT = """You are a helpful Smart Farming AI Assistant. You help farmers with information about:

1. **Crop Recommendations**: The platform uses ML to suggest best crops based on soil parameters (N, P, K, pH, temperature, humidity, rainfall). Users can access this via 'Crop Suggestion' in the sidebar.

2. **Disease Detection**: Users can upload plant leaf images to identify diseases. The AI analyzes images and provides disease names, symptoms, and treatment recommendations. Works best with clear, well-lit leaf photos.

3. **Fertilizer Recommendations**: Users select crop type and enter soil NPK values to get personalized fertilizer advice. Soil testing is available at local agriculture offices (₹50-200) or through DIY kits.

4. **Market Price**: Provides real-time crop prices across India (displayed in both per quintal and per kg rates), nearby mandi locations, and price trends to help farmers make selling decisions.

5. **Expense Calculator**: Tracks farming expenses by category (seeds, fertilizer, labor, etc.), calculates revenue and profit, shows pie charts, includes loan/EMI calculator, and exports to PDF. Users can compare with crop benchmarks.

6. **Weather Information**: Shows current conditions, temperature, humidity, rainfall predictions, and 7-day forecasts to help plan farming activities.

7. **Government Schemes**: Information about PM-KISAN (₹6000/year), crop insurance, soil health cards, agricultural loans, subsidies, and other farming benefits.

8. **Farmer's Manual**: Complete farming guide with soil testing methods, parameter ranges, and agricultural best practices.

**Navigation**: 
- Sidebar features: Crop Suggestion, Fertilizer Advice, Market Price
- Tools dropdown (top right): Expense Calculator, Farmer's Manual, Govt Schemes, Weather

**Soil Testing Guide**:
- NPK testing: Agriculture office (₹50-200), private labs (₹200-500), or DIY kits (₹300-1000)
- pH testing: Digital meter (₹200-500), test strips (₹50-100), or vinegar/baking soda test (free)
- Parameters: N, P, K (kg/ha), pH (3.5-9.5), temperature (8-45°C), humidity (14-100%), rainfall (20-3000mm)

Be friendly, conversational, and provide step-by-step guidance. Use emojis occasionally. Keep responses concise but informative. If users ask about features not available, politely explain what the platform currently offers."""

@chat_bp.route('/message', methods=['POST'])
def chat_message():
    """Handle chatbot messages using Gemini API"""
    try:
        # Check if user is logged in
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': 'Please login to use the chatbot'
            }), 401
        
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Message cannot be empty'
            }), 400
        
        # Simple direct approach - no chat history for now
        print(f"User message: {user_message}")
        
        # Create a new model instance for each request
        chat_model = genai.GenerativeModel('gemma-3-4b-it')
        
        # Generate response with system context
        prompt = f"{SYSTEM_CONTEXT}\n\nUser Question: {user_message}\n\nProvide a helpful, concise answer:"
        
        response = chat_model.generate_content(prompt)
        
        print(f"Bot response: {response.text}")
        
        return jsonify({
            'success': True,
            'response': response.text,
            'timestamp': None
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"Chatbot error details: {error_msg}")
        print(f"Error type: {type(e).__name__}")
        
        # Return more detailed error for debugging
        return jsonify({
            'success': False,
            'error': f'API Error: {error_msg}',
            'details': f'Check if API key is valid. Error type: {type(e).__name__}'
        }), 500

@chat_bp.route('/test', methods=['GET'])
def test_api():
    """Test endpoint to verify Gemini API is configured"""
    try:
        if GEMINI_API_KEY == 'YOUR_GEMINI_API_KEY_HERE':
            return jsonify({
                'success': False,
                'message': 'Please configure your Gemini API key in chat_routes.py or as GEMINI_API_KEY environment variable'
            }), 500
        
        # Simple test
        model = genai.GenerativeModel('gemma-3-4b-it')
        response = model.generate_content("Say 'Hello, Smart Farming!' in one sentence.")
        
        return jsonify({
            'success': True,
            'message': 'Gemini API is configured correctly!',
            'test_response': response.text
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Gemini API test failed',
            'error': str(e)
        }), 500
