from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.auth import login_required
from datetime import datetime
import sys
import os

# Add path for ML model
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml_models'))

# Optional DB helper - safe import
try:
    from utils.db import save_fertilizer_recommendation, delete_fertilizer_recommendation
except Exception:
    save_fertilizer_recommendation = None
    delete_fertilizer_recommendation = None

# Import ML predictor
try:
    from predict import FertilizerPredictor
    ml_predictor = FertilizerPredictor()
    print("✓ ML Fertilizer Predictor loaded successfully")
except Exception as e:
    print(f"✗ Warning: Could not load ML predictor: {e}")
    ml_predictor = None

fertilizer_bp = Blueprint('fertilizer', __name__, url_prefix='/fertilizer')

def generate_fertilizer_recommendations(crop_type, n, p, k, temperature, humidity, soil_moisture):
    """Enhanced rule-based fertilizer recommender with better logic"""
    recommendations = []

    # Determine nutrient deficiencies (lower values indicate need)
    n_deficit = max(0, 100 - n)  # Higher deficit = more need
    p_deficit = max(0, 60 - p)
    k_deficit = max(0, 50 - k)
    
    # Soil condition factors
    dry_soil = soil_moisture < 40
    wet_soil = soil_moisture > 70
    high_temp = temperature > 30
    low_temp = temperature < 15

    # Fertilizer database with detailed properties
    candidates = [
        {
            'name': 'Urea (46-0-0)',
            'dosage': '50-100 kg/acre',
            'usage': 'Apply in split doses: 50% at sowing, 25% at tillering, 25% at flowering',
            'note': 'Best nitrogen source for rapid vegetative growth',
            'n_content': 46, 'p_content': 0, 'k_content': 0
        },
        {
            'name': 'DAP (18-46-0)',
            'dosage': '75-125 kg/acre',
            'usage': 'Apply at time of sowing or transplanting for root development',
            'note': 'Excellent phosphorus source, also provides nitrogen',
            'n_content': 18, 'p_content': 46, 'k_content': 0
        },
        {
            'name': 'MOP (0-0-60)',
            'dosage': '50-75 kg/acre',
            'usage': 'Apply during flowering and fruit formation stage',
            'note': 'High potassium for fruit quality and disease resistance',
            'n_content': 0, 'p_content': 0, 'k_content': 60
        },
        {
            'name': 'NPK 19-19-19',
            'dosage': '100-150 kg/acre',
            'usage': 'Apply as basal dose or during active growth phase',
            'note': 'Balanced fertilizer for overall plant nutrition',
            'n_content': 19, 'p_content': 19, 'k_content': 19
        },
        {
            'name': 'NPK 20-20-0-13',
            'dosage': '125-175 kg/acre',
            'usage': 'Apply when both N and P are needed with sulfur benefit',
            'note': 'Contains sulfur (13%) for protein synthesis',
            'n_content': 20, 'p_content': 20, 'k_content': 0
        },
        {
            'name': 'Single Super Phosphate',
            'dosage': '100-200 kg/acre',
            'usage': 'Mix with soil before planting for root development',
            'note': 'Provides phosphorus and sulfur for early growth',
            'n_content': 0, 'p_content': 16, 'k_content': 0
        },
        {
            'name': 'Organic Compost',
            'dosage': '2-5 tons/acre',
            'usage': 'Apply 2-3 weeks before sowing and mix well with soil',
            'note': 'Improves soil structure, water retention, and microbial activity',
            'n_content': 2, 'p_content': 1, 'k_content': 1
        }
    ]

    # Calculate scores for each fertilizer
    for fertilizer in candidates:
        score = 0.0
        
        # Score based on nutrient matching (0-70 points)
        if n_deficit > 0 and fertilizer['n_content'] > 0:
            score += min(30, (n_deficit / 100) * fertilizer['n_content'])
        if p_deficit > 0 and fertilizer['p_content'] > 0:
            score += min(25, (p_deficit / 60) * fertilizer['p_content'])
        if k_deficit > 0 and fertilizer['k_content'] > 0:
            score += min(15, (k_deficit / 50) * fertilizer['k_content'])
        
        # Balanced fertilizers get bonus when multiple deficits exist
        deficits = (n_deficit > 20) + (p_deficit > 15) + (k_deficit > 15)
        if deficits >= 2 and 'NPK' in fertilizer['name']:
            score += 15
        
        # Environmental condition bonuses (0-15 points)
        if dry_soil and 'Organic' in fertilizer['name']:
            score += 10  # Organic matter improves water retention
        if wet_soil and 'Urea' not in fertilizer['name']:
            score += 5  # Avoid urea in waterlogged conditions
        if high_temp and fertilizer['k_content'] > 0:
            score += 5  # Potassium helps stress tolerance
        if low_temp and 'DAP' in fertilizer['name']:
            score += 5  # Phosphorus improves cold tolerance
        
        # Crop-specific adjustments (0-10 points)
        crop_lower = crop_type.lower() if crop_type else ''
        if 'rice' in crop_lower or 'wheat' in crop_lower:
            if 'Urea' in fertilizer['name']:
                score += 8
        if 'potato' in crop_lower or 'tomato' in crop_lower:
            if fertilizer['k_content'] > 0:
                score += 8
        if 'legume' in crop_lower or 'pulse' in crop_lower:
            if fertilizer['p_content'] > 0:
                score += 8
        
        # Normalize score to 0-100 scale
        final_score = min(100, score)
        confidence = round(final_score, 1)
        
        # Determine priority based on confidence
        if confidence >= 70:
            priority = 'High'
        elif confidence >= 45:
            priority = 'Medium'
        else:
            priority = 'Low'
        
        recommendations.append({
            'name': fertilizer['name'],
            'dosage': fertilizer['dosage'],
            'usage': fertilizer['usage'],
            'note': fertilizer['note'],
            'probability': final_score / 100,
            'confidence_percentage': confidence,
            'priority': priority
        })

    # Sort by confidence score (highest first)
    recommendations.sort(key=lambda x: x['confidence_percentage'], reverse=True)
    
    # Return top 6 recommendations
    return recommendations[:6]


# Helper function for fertilizer categorization
def get_fertilizer_category(fetilizer_name):
    fetilizer_name = fetilizer_name.lower().strip()
    
    categories = {
        'Nitrogenous': ['urea', 'ammonium sulfate', 'calcium ammonium nitrate'],
        'Phosphatic': ['dap', 'single super phosphate', 'triple super phosphate'],
        'Potassic': ['mop', 'muriate of potash', 'sulfate of potash'],
        'Complex (NPK)': ['npk', 'balanced npk fertilizer', '19-19-19', '20-20-0-13', '10-26-26'],
        'Organic & Soil Amendments': ['compost', 'organic fertilizer', 'lime', 'gypsum', 'water retaining fertilizer']
    }
    
    # Check for direct match or partial match
    for category, fertilizers in categories.items():
        if any(f in fetilizer_name for f in fertilizers):
            return category
            
    # Default category
    return 'Other Fertilizers'

@fertilizer_bp.route('/recommend', methods=['GET', 'POST'])
@login_required
def fertilizer_recommend():
    if request.method == 'GET':
        # Get available options from ML model
        available_soils = []
        available_crops = []
        if ml_predictor:
            try:
                available_soils = ml_predictor.get_available_soils()
                available_crops = ml_predictor.get_available_crops()
            except:
                pass
        
        return render_template('fertilizer_recommend.html',
                               user_name=session.get('user_name', 'Farmer'),
                               current_date=datetime.now().strftime('%B %d, %Y'),
                               available_soils=available_soils,
                               available_crops=available_crops)

    # POST: Get ML-based recommendations
    try:
        # Get form data - support both old and new format
        temperature = float(request.form.get('temperature', 0))
        moisture = float(request.form.get('moisture', request.form.get('humidity', 0))) / 100.0 if 'humidity' in request.form else float(request.form.get('moisture', 0))
        rainfall = float(request.form.get('rainfall', 200))
        ph = float(request.form.get('ph', 7))
        nitrogen = float(request.form.get('nitrogen', 0))
        phosphorous = float(request.form.get('phosphorous', 0))
        potassium = float(request.form.get('potassium', 0))
        carbon = float(request.form.get('carbon', 1.5))
        soil = request.form.get('soil', 'Loamy Soil')
        crop = request.form.get('crop_type', request.form.get('crop', 'rice'))

        recommendations = []
        is_ml_prediction = False

        # Use ML model if available
        if ml_predictor:
            result = ml_predictor.predict(
                temperature=temperature,
                moisture=moisture,
                rainfall=rainfall,
                ph=ph,
                nitrogen=nitrogen,
                phosphorous=phosphorous,
                potassium=potassium,
                carbon=carbon,
                soil=soil,
                crop=crop
            )
            
            if result.get('success'):
                is_ml_prediction = True
                # Format recommendations for template
                raw_recommendations = result.get('top_recommendations', [])
                
                # Convert to standardized format
                for rec in raw_recommendations:
                    recommendations.append({
                        'name': rec['fertilizer'],
                        'dosage': rec['dosage'],
                        'usage': rec['use'],
                        'note': rec['notes'],
                        'confidence_percentage': rec['confidence'],
                        'priority': 'High' if rec['confidence'] >= 60 else 'Medium' if rec['confidence'] >= 30 else 'Low',
                        'probability': rec['confidence'] / 100.0
                    })
            else:
                flash(f'ML Model Error: {result.get("error")}', 'error')
        
        # Fallback to rule-based if ML failed or not available
        if not recommendations:
            # Use rules
            recommendations = generate_fertilizer_recommendations(
                crop, nitrogen, phosphorous, potassium, temperature, moisture * 100, moisture * 100
            )


        # Categorize recommendations
        categorized_recommendations = {}
        for rec in recommendations:
            category = get_fertilizer_category(rec['name'])
            if category not in categorized_recommendations:
                categorized_recommendations[category] = []
            categorized_recommendations[category].append(rec)
        
        # Sort categories based on preferred order
        preferred_order = ['Organic & Soil Amendments', 'Complex (NPK)', 'Nitrogenous', 'Phosphatic', 'Potassic', 'Other Fertilizers']
        sorted_categorized = {k: categorized_recommendations[k] for k in preferred_order if k in categorized_recommendations}
        # Add remaining
        for k, v in categorized_recommendations.items():
            if k not in sorted_categorized:
                sorted_categorized[k] = v
        categorized_recommendations = sorted_categorized
        
        input_data = {
            'crop_type': crop,
            'soil_type': soil,
            'nitrogen': nitrogen,
            'phosphorous': phosphorous,
            'potassium': potassium,
            'temperature': temperature,
            'humidity': moisture * 100,
            'soil_moisture': moisture * 100
        }
        
        msg = '🧪 AI-powered fertilizer recommendations generated!' if is_ml_prediction else '✅ Fertilizer recommendations generated successfully!'
        flash(msg, 'success')

        return render_template('fertilizer_recommend.html',
                               recommendations=recommendations,
                               categorized_recommendations=categorized_recommendations,
                               input_data=input_data,
                               user_name=session.get('user_name', 'Farmer'),
                               current_date=datetime.now().strftime('%B %d, %Y'),
                               available_soils=ml_predictor.get_available_soils() if ml_predictor else [],
                               available_crops=ml_predictor.get_available_crops() if ml_predictor else [])

    except ValueError as e:
        flash(f'❌ Please provide valid numeric inputs: {e}', 'error')
        return redirect(url_for('fertilizer.fertilizer_recommend'))
    except Exception as e:
        flash(f'❌ Unexpected error: {e}', 'error')
        return redirect(url_for('fertilizer.fertilizer_recommend'))

@fertilizer_bp.route('/save', methods=['POST'])
@login_required
def save_fertilizer():
    user_id = session.get('user_id')
    try:
        fertilizer_data = {
            'name': request.form.get('fertilizer_name'),
            'crop_type': request.form.get('crop_type'),
            'priority': request.form.get('priority'),
            'dosage': request.form.get('dosage', 'Not specified'),
            'usage': request.form.get('usage', 'Follow package instructions'),
            'note': request.form.get('note', ''),
            'confidence': request.form.get('confidence', '0'),
            'soil_type': request.form.get('soil_type', ''),
            'nitrogen': request.form.get('nitrogen', ''),
            'phosphorus': request.form.get('phosphorus', ''),
            'potassium': request.form.get('potassium', '')
        }

        if save_fertilizer_recommendation:
            save_fertilizer_recommendation(user_id, fertilizer_data)
            flash('✅ Fertilizer recommendation saved to dashboard!', 'success')
        else:
            # fallback: store in session (simple)
            session.setdefault('saved_fertilizers', []).append(fertilizer_data)
            flash('💾 Saved locally (DB not configured).', 'info')

    except Exception as e:
        flash(f'❌ Error saving recommendation: {e}', 'error')

    return redirect(url_for('dashboard.dashboard'))

@fertilizer_bp.route('/delete/<fertilizer_id>', methods=['POST'])
@login_required
def delete_fertilizer(fertilizer_id):
    """Delete a saved fertilizer recommendation"""
    from flask import jsonify
    
    user_id = session.get('user_id')
    try:
        if delete_fertilizer_recommendation:
            success = delete_fertilizer_recommendation(fertilizer_id, user_id)
            if success:
                return jsonify({'success': True, 'message': 'Fertilizer deleted successfully'})
            else:
                return jsonify({'success': False, 'message': 'Fertilizer not found'}), 404
        else:
            return jsonify({'success': False, 'message': 'Delete function not available'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
