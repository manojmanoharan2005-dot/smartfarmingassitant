from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from utils.auth import login_required
from utils.db import save_crop_recommendation, delete_crop, get_user_crops
from ml_models.model_integration import crop_predictor
from datetime import datetime

crop_bp = Blueprint('crop', __name__)


# Helper function for crop categorization
def get_crop_category(crop_name):
    crop_name = crop_name.lower().strip()
    
    categories = {
        'Fruits': ['apple', 'banana', 'grapes', 'mango', 'muskmelon', 'orange', 'papaya', 'pomegranate', 'watermelon', 'coconut'],
        'Pulses & Vegetables': ['pigeonpeas', 'kidneybeans', 'mothbeans', 'mungbean', 'blackgram', 'lentil', 'chickpea'], 
        'Grains & Cereals': ['rice', 'wheat', 'maize'],
        'Commercial Crops': ['cotton', 'jute', 'coffee', 'tea']
    }
    
    # Check for direct match
    for category, crops in categories.items():
        if crop_name in crops:
            return category
            
    # Default category
    return 'Other Crops'

@crop_bp.route('/crop/suggestion', methods=['GET', 'POST'])
@login_required
def crop_suggestion():
    # GET request - show empty form
    if request.method == 'GET':
        return render_template('crop_suggestion.html', 
                             user_name=session.get('user_name', 'Farmer'),
                             current_date=datetime.now().strftime('%B %d, %Y'))
    
    # POST request - process form and show results
    if request.method == 'POST':
        try:
            # Get and validate form data
            nitrogen = float(request.form['nitrogen'])
            phosphorous = float(request.form['phosphorous'])
            potassium = float(request.form['potassium'])
            temperature = float(request.form['temperature'])
            humidity = float(request.form['humidity'])
            ph = float(request.form['ph'])
            rainfall = float(request.form['rainfall'])
            
            # Validate ranges (optional but recommended)
            if not (0 <= nitrogen <= 200):
                flash('Nitrogen level should be between 0-200 mg/kg', 'error')
                return redirect(url_for('crop.crop_suggestion'))
                
            if not (0 <= humidity <= 100):
                flash('Humidity should be between 0-100%', 'error')
                return redirect(url_for('crop.crop_suggestion'))
                
            if not (3 <= ph <= 10):
                flash('pH should be between 3-10', 'error')
                return redirect(url_for('crop.crop_suggestion'))
            
            # Get ML model predictions
            print("🔍 Getting crop predictions...")
            prediction_result = crop_predictor.predict_crop_recommendation(
                nitrogen, phosphorous, potassium, temperature, humidity, ph, rainfall
            )
            
            crop_recommendations = []
            if prediction_result and prediction_result.get('top_recommendations'):
                # Use real ML predictions
                crop_recommendations = prediction_result['top_recommendations']
                print(f"✅ Got {len(crop_recommendations)} crop recommendations")
                
                # Add success message with count
                flash(f'🌾 Success! Generated {len(crop_recommendations)} crop recommendations based on your soil analysis!', 'success')
                
            else:
                # Fallback to enhanced mock data based on input conditions
                print("⚠️ Using fallback recommendations")
                crop_recommendations = generate_fallback_recommendations(
                    nitrogen, phosphorous, potassium, temperature, humidity, ph, rainfall
                )
                flash('⚠️ Using basic recommendations. Install ML packages for AI predictions.', 'warning')
            
            # Categorize recommendations
            categorized_recommendations = {}
            for crop in crop_recommendations:
                category = get_crop_category(crop['name'])
                if category not in categorized_recommendations:
                    categorized_recommendations[category] = []
                categorized_recommendations[category].append(crop)
            
            # Sort categories to ensure consistent order (Fruits, Vegetables, Grains, etc.)
            # Define preferred order
            preferred_order = ['Grains & Cereals', 'Pulses & Vegetables', 'Fruits', 'Commercial Crops', 'Other Crops']
            sorted_categorized = {k: categorized_recommendations[k] for k in preferred_order if k in categorized_recommendations}
            # Add any remaining categories not in preferred order
            for k, v in categorized_recommendations.items():
                if k not in sorted_categorized:
                    sorted_categorized[k] = v
            
            categorized_recommendations = sorted_categorized
            
            # Store input data to preserve form values
            input_data = {
                'nitrogen': nitrogen,
                'phosphorous': phosphorous,
                'potassium': potassium,
                'temperature': temperature,
                'humidity': humidity,
                'ph': ph,
                'rainfall': rainfall
            }
            
            # Return template with results
            return render_template('crop_suggestion.html',
                                 recommendations=crop_recommendations,
                                 categorized_recommendations=categorized_recommendations,
                                 input_data=input_data,
                                 user_name=session.get('user_name', 'Farmer'),
                                 current_date=datetime.now().strftime('%B %d, %Y'))
        
        except ValueError as e:
            flash('❌ Please enter valid numerical values for all fields.', 'error')
            print(f"Validation error: {e}")
        except Exception as e:
            flash(f'❌ An error occurred: {str(e)}', 'error')
            print(f"Unexpected error: {e}")
        
        # Redirect back to form on error
        return redirect(url_for('crop.crop_suggestion'))

def generate_fallback_recommendations(nitrogen, phosphorous, potassium, temperature, humidity, ph, rainfall):
    """Generate smart fallback recommendations based on input parameters"""
    
    # Rule-based crop scoring
    crops_scores = []
    
    # Rice scoring
    rice_score = 0.0
    if 80 <= nitrogen <= 120: rice_score += 0.2
    if 35 <= phosphorous <= 60: rice_score += 0.15
    if 35 <= potassium <= 45: rice_score += 0.15
    if 20 <= temperature <= 30: rice_score += 0.2
    if 80 <= humidity <= 95: rice_score += 0.15
    if 5.5 <= ph <= 7.0: rice_score += 0.1
    if 150 <= rainfall <= 300: rice_score += 0.05
    
    crops_scores.append(('Rice', rice_score))
    
    # Wheat scoring
    wheat_score = 0.0
    if 70 <= nitrogen <= 100: wheat_score += 0.2
    if 40 <= phosphorous <= 60: wheat_score += 0.15
    if 35 <= potassium <= 50: wheat_score += 0.15
    if 15 <= temperature <= 25: wheat_score += 0.2
    if 55 <= humidity <= 75: wheat_score += 0.15
    if 6.0 <= ph <= 7.5: wheat_score += 0.1
    if 75 <= rainfall <= 180: wheat_score += 0.05
    
    crops_scores.append(('Wheat', wheat_score))
    
    # Maize scoring
    maize_score = 0.0
    if 70 <= nitrogen <= 100: maize_score += 0.2
    if 40 <= phosphorous <= 60: maize_score += 0.15
    if 15 <= potassium <= 25: maize_score += 0.15
    if 18 <= temperature <= 27: maize_score += 0.2
    if 55 <= humidity <= 75: maize_score += 0.15
    if 5.5 <= ph <= 7.0: maize_score += 0.1
    if 60 <= rainfall <= 110: maize_score += 0.05
    
    crops_scores.append(('Maize', maize_score))
    
    # Cotton scoring
    cotton_score = 0.0
    if 100 <= nitrogen <= 150: cotton_score += 0.2
    if 35 <= phosphorous <= 60: cotton_score += 0.15
    if 15 <= potassium <= 30: cotton_score += 0.15
    if 21 <= temperature <= 30: cotton_score += 0.2
    if 70 <= humidity <= 85: cotton_score += 0.15
    if 5.8 <= ph <= 8.0: cotton_score += 0.1
    if 50 <= rainfall <= 100: cotton_score += 0.05
    
    crops_scores.append(('Cotton', cotton_score))
    
    # Jute scoring
    jute_score = 0.0
    if 60 <= nitrogen <= 100: jute_score += 0.2
    if 35 <= phosphorous <= 60: jute_score += 0.15
    if 35 <= potassium <= 50: jute_score += 0.15
    if 24 <= temperature <= 37: jute_score += 0.2
    if 80 <= humidity <= 95: jute_score += 0.15
    if 6.0 <= ph <= 7.5: jute_score += 0.1
    if 120 <= rainfall <= 200: jute_score += 0.05
    
    crops_scores.append(('Jute', jute_score))
    
    # Banana scoring
    banana_score = 0.0
    if 80 <= nitrogen <= 120: banana_score += 0.2
    if 70 <= phosphorous <= 100: banana_score += 0.15
    if 45 <= potassium <= 60: banana_score += 0.15
    if 26 <= temperature <= 32: banana_score += 0.2
    if 75 <= humidity <= 90: banana_score += 0.15
    if 6.5 <= ph <= 7.5: banana_score += 0.1
    if 75 <= rainfall <= 150: banana_score += 0.05
    
    crops_scores.append(('Banana', banana_score))
    
    # Sort by score and create recommendations
    crops_scores.sort(key=lambda x: x[1], reverse=True)
    
    recommendations = []
    for crop_name, score in crops_scores:
        # Normalize score to percentage
        confidence = min(max(score * 100, 30), 95)  # Keep between 30-95%
        
        # Determine priority
        if confidence >= 70:
            priority = 'High'
        elif confidence >= 50:
            priority = 'Medium'
        else:
            priority = 'Low'
            
        recommendations.append({
            'name': crop_name,
            'probability': confidence / 100,
            'confidence_percentage': confidence,
            'priority': priority
        })
    
    return recommendations

@crop_bp.route('/crop/start/<crop_name>/<float:probability>')
@login_required
def start_growing(crop_name, probability):
    user_id = session['user_id']
    
    try:
        # Create crop data
        crop_data = {
            'crop_name': crop_name,
            'probability': probability,
            'user_id': user_id,
            'created_at': datetime.now()
        }
        
        # Create timeline data
        timeline_data = {
            'sowing_date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'monitoring'
        }
        
        # Save crop recommendation (if database functions are available)
        try:
            result = save_crop_recommendation(user_id, crop_data, timeline_data)
            flash(f'🌱 Started monitoring {crop_name} with {probability*100:.1f}% suitability!', 'success')
        except:
            # Fallback if database save fails
            flash(f'🌱 {crop_name} selected for growing! (Database save pending)', 'info')
        
    except Exception as e:
        flash(f'❌ Error starting crop: {str(e)}', 'error')
        print(f"Error in start_growing: {e}")
    
    return redirect(url_for('dashboard.dashboard'))

@crop_bp.route('/crop/delete/<crop_id>')
@login_required
def delete_crop_route(crop_id):
    try:
        result = delete_crop(crop_id)
        
        if result and hasattr(result, 'deleted_count') and result.deleted_count > 0:
            flash('Crop deleted successfully!', 'success')
        else:
            flash('Error deleting crop!', 'error')
    except Exception as e:
        flash(f'Error deleting crop: {str(e)}', 'error')
    
    return redirect(url_for('dashboard.dashboard'))

@crop_bp.route('/api/crop/predict', methods=['POST'])
@login_required
def api_predict_crop():
    """API endpoint for crop prediction"""
    try:
        data = request.get_json()
        
        prediction_result = crop_predictor.predict_crop_recommendation(
            data['nitrogen'], data['phosphorus'], data['potassium'],
            data['temperature'], data['humidity'], data['ph'], data['rainfall']
        )
        
        if prediction_result:
            return jsonify({
                'success': True,
                'data': prediction_result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Model prediction failed'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
