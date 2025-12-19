from flask import Blueprint, request, jsonify, session
import google.generativeai as genai
import os

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# Configure Gemini API
# You can set this as an environment variable or directly here
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'YOUR_GEMINI_API_KEY_HERE')
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model
model = genai.GenerativeModel('gemini-2.5-flash')

# System context for the chatbot
SYSTEM_CONTEXT = """You are a helpful Smart Farming AI Assistant. You help farmers with information about:

1. **Crop Recommendations**: The platform uses ML to suggest best crops based on soil parameters (N, P, K, pH, temperature, humidity, rainfall). Users can access this via 'Crop Suggestion' in the sidebar.

2. **Disease Detection**: Users can upload plant leaf images to identify diseases. The AI analyzes images and provides disease names, symptoms, and treatment recommendations. Works best with clear, well-lit leaf photos.

3. **Fertilizer Recommendations**: Users select crop type and enter soil NPK values to get personalized fertilizer advice. Soil testing is available at local agriculture offices (₹50-200) or through DIY kits.

4. **Market Watch**: Provides real-time crop prices across India (displayed in both per quintal and per kg rates), nearby mandi locations, and price trends to help farmers make selling decisions.

5. **Expense Calculator**: Tracks farming expenses by category (seeds, fertilizer, labor, etc.), calculates revenue and profit, shows pie charts, includes loan/EMI calculator, and exports to PDF. Users can compare with crop benchmarks.

6. **Weather Information**: Shows current conditions, temperature, humidity, rainfall predictions, and 7-day forecasts to help plan farming activities.

7. **Government Schemes**: Information about PM-KISAN (₹6000/year), crop insurance, soil health cards, agricultural loans, subsidies, and other farming benefits.

8. **Farmer's Manual**: Complete farming guide with soil testing methods, parameter ranges, and agricultural best practices.

**Navigation**: 
- Sidebar features: Crop Suggestion, Fertilizer Advice, Market Watch
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
        
        # Get chat history from request (optional)
        chat_history = data.get('history', [])
        
        # Build conversation context
        conversation = []
        if chat_history:
            for msg in chat_history[-5:]:  # Last 5 messages for context
                conversation.append({
                    'role': 'user' if msg.get('sender') == 'user' else 'model',
                    'parts': [msg.get('text', '')]
                })
        
        # Start chat with context
        chat = model.start_chat(history=conversation)
        
        # Send message with system context prepended for first message
        if not conversation:
            full_message = f"{SYSTEM_CONTEXT}\n\nUser: {user_message}"
        else:
            full_message = user_message
        
        response = chat.send_message(full_message)
        
        return jsonify({
            'success': True,
            'response': response.text,
            'timestamp': None  # Frontend will add timestamp
        })
        
    except Exception as e:
        print(f"Chatbot error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Sorry, I encountered an error. Please try again.',
            'details': str(e)
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
        model = genai.GenerativeModel('gemini-pro')
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
