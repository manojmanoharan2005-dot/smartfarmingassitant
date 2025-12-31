from flask import Blueprint, jsonify, session
from utils.auth import login_required
from utils.db import (
    get_user_crops, 
    get_user_fertilizers, 
    get_user_growing_activities,
    find_user_by_id,
    get_db,
    get_dashboard_notifications,
    get_user_expenses
)
from controllers.dashboard_routes import weather_cache, price_predictions_cache, get_weather_notifications, get_price_predictions
import json
import os

from datetime import datetime, timedelta
from bson import ObjectId

report_bp = Blueprint('report', __name__)

@report_bp.route('/api/report/crop-plan', methods=['GET'])
@login_required
def get_crop_plan_data():
    """Get crop plan data for PDF generation"""
    try:
        user_id = session.get('user_id')
        
        # Get active growing activities
        activities = get_user_growing_activities(user_id)
        
        if not activities:
            return jsonify({
                'success': False,
                'message': 'No active crops found. Start growing a crop to generate this report.',
                'data': None
            })
        
        # Get crop suggestions
        crops = get_user_crops(user_id)
        
        # Get fertilizer recommendations
        fertilizers = get_user_fertilizers(user_id)
        
        # Prepare crop plan data
        crop_plan = []
        for activity in activities:
            plan_item = {
                'crop': activity.get('crop', 'Unknown'),
                'stage': activity.get('current_stage', 'Unknown'),
                'started': activity.get('started', 'N/A'),
                'progress': activity.get('progress', 0),
                'current_day': activity.get('current_day', 0),
                'notes': activity.get('notes', '')
            }
            crop_plan.append(plan_item)
        
        # Get user info with session fallback
        user = find_user_by_id(user_id)
        if not user:
            user = {
                'name': session.get('user_name', 'Farmer'),
                'district': session.get('user_district', ''),
                'state': session.get('user_state', '')
            }
        
        return jsonify({
            'success': True,
            'data': {
                'crops': crop_plan,
                'fertilizers': fertilizers[:5] if fertilizers else [],
                'user': {
                    'name': user.get('name', session.get('user_name', 'Farmer')),
                    'district': user.get('district', session.get('user_district', '')),
                    'state': user.get('state', session.get('user_state', ''))
                },
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching crop plan data: {str(e)}',
            'data': None
        }), 500


@report_bp.route('/api/report/harvest', methods=['GET'])
@login_required
def get_harvest_data():
    """Get harvest report data"""
    try:
        user_id = session.get('user_id')
        
        # Stage names for conversion
        STAGE_NAMES = ['Seed Sowing', 'Germination', 'Seedling', 'Vegetative Growth', 
                       'Flowering', 'Fruit Development', 'Maturity', 'Harvest Ready']
        
        now = datetime.now()
        processed_activities = []
        for activity in activities:
            try:
                start_date = activity.get('start_date', '')
                if not start_date:
                    continue
                
                start = datetime.strptime(start_date, '%Y-%m-%d')
                days_since = (now - start).days
                duration = activity.get('duration_days', 90)
                time_progress = min(100, int((days_since / duration) * 100))
                
                # Get stage-based progress
                current_stage = activity.get('current_stage', 'Growing')
                stage_progress = 0
                if isinstance(current_stage, int):
                    stage_progress = int((current_stage + 1) / len(STAGE_NAMES) * 100)
                    current_stage = STAGE_NAMES[current_stage] if current_stage < len(STAGE_NAMES) else 'Growing'
                elif current_stage in STAGE_NAMES:
                    stage_idx = STAGE_NAMES.index(current_stage)
                    stage_progress = int((stage_idx + 1) / len(STAGE_NAMES) * 100)
                
                # Use max progress
                activity['progress'] = max(time_progress, stage_progress)
                activity['current_stage'] = current_stage
                activity['current_day'] = days_since
                activity['started'] = start.strftime('%b %d')
                processed_activities.append(activity)
            except:
                continue

        # Filter crops ready for harvest or near harvest (using the newly calculated progress)
        harvest_ready = [a for a in processed_activities if a.get('progress', 0) >= 50 or a.get('current_stage') == 'Harvest Ready']
        
        if not harvest_ready:
            return jsonify({
                'success': False,
                'message': 'No crops are ready for harvest yet. Update your crop stage to "Harvest Ready" or wait for maturity.',
                'data': None
            })
        
        # Get user info
        user = find_user_by_id(user_id)
        
        # Prepare harvest data
        harvest_data = []
        for activity in harvest_ready:
            harvest_item = {
                'crop': activity.get('crop', 'Unknown'),
                'stage': activity.get('current_stage', 'Unknown'),
                'progress': activity.get('progress', 0),
                'current_day': activity.get('current_day', 0),
                'started': activity.get('started', 'N/A'),
                'estimated_yield': calculate_estimated_yield(activity),
                'harvest_window': calculate_harvest_window(activity),
                'notes': activity.get('notes', '')
            }
            harvest_data.append(harvest_item)
        
        # Get user info with session fallback
        user = find_user_by_id(user_id)
        if not user:
            user = {
                'name': session.get('user_name', 'Farmer'),
                'district': session.get('user_district', ''),
                'state': session.get('user_state', '')
            }
        
        return jsonify({
            'success': True,
            'data': {
                'crops': harvest_data,
                'user': {
                    'name': user.get('name', session.get('user_name', 'Farmer')),
                    'district': user.get('district', session.get('user_district', '')),
                    'state': user.get('state', session.get('user_state', ''))
                },
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching harvest data: {str(e)}',
            'data': None
        }), 500


@report_bp.route('/api/report/profit', methods=['GET'])
@login_required
def get_profit_data():
    """Get profit summary data from expense calculator"""
    try:
        user_id = session.get('user_id')
        db = get_db()
        
        # Get expense entries from unified storage
        expenses = get_user_expenses(user_id)
        
        if not expenses:
            return jsonify({
                'success': False,
                'message': 'No expense data found. Use the Expense Calculator to track your farming costs.',
                'data': None
            })
        
        # Calculate totals
        total_revenue = 0
        total_expenses = 0
        crop_wise_data = {}
        
        for expense in expenses:
            crop = expense.get('crop_type', expense.get('cropType', 'Unknown'))
            
            # Calculate revenue with robust key handling
            land_area = float(expense.get('land_area', expense.get('landArea', 0)))
            expected_yield = float(expense.get('expected_yield', expense.get('expectedYield', 0)))
            market_price = float(expense.get('market_price', expense.get('marketPrice', 0)))
            
            # Match frontend calculation: Revenue = Total Yield * Price
            revenue = expected_yield * market_price
            
            # Calculate expenses with robust key handling for both nested and flat structure
            exp_details = expense.get('expenses', {})
            
            seed_cost = float(expense.get('seed_cost', exp_details.get('seed', 0)))
            fertilizer_cost = float(expense.get('fertilizer_cost', exp_details.get('fertilizer', 0)))
            pesticide_cost = float(expense.get('pesticide_cost', exp_details.get('pesticide', 0)))
            irrigation_cost = float(expense.get('irrigation_cost', exp_details.get('irrigation', 0)))
            labor_cost = float(expense.get('labor_cost', exp_details.get('labor', 0)))
            machinery_cost = float(expense.get('machinery_cost', exp_details.get('machinery', 0)))
            other_cost = float(expense.get('other_cost', exp_details.get('other', 0)))
            
            expense_total = (seed_cost + fertilizer_cost + pesticide_cost + 
                           irrigation_cost + labor_cost + machinery_cost + other_cost)
            
            total_revenue += revenue
            total_expenses += expense_total
            
            # Track crop-wise data
            if crop not in crop_wise_data:
                crop_wise_data[crop] = {
                    'revenue': 0,
                    'expenses': 0,
                    'entries': 0
                }
            
            crop_wise_data[crop]['revenue'] += revenue
            crop_wise_data[crop]['expenses'] += expense_total
            crop_wise_data[crop]['entries'] += 1
        
        net_profit = total_revenue - total_expenses
        roi = ((net_profit / total_expenses) * 100) if total_expenses > 0 else 0
        
        # Get user info with session fallback
        user = find_user_by_id(user_id)
        if not user:
            user = {
                'name': session.get('user_name', 'Farmer'),
                'district': session.get('user_district', ''),
                'state': session.get('user_state', '')
            }
        
        return jsonify({
            'success': True,
            'data': {
                'total_revenue': round(total_revenue, 2),
                'total_expenses': round(total_expenses, 2),
                'net_profit': round(net_profit, 2),
                'roi': round(roi, 2),
                'crop_wise': crop_wise_data,
                'total_entries': len(expenses),
                'user': {
                    'name': user.get('name', session.get('user_name', 'Farmer')),
                    'district': user.get('district', session.get('user_district', '')),
                    'state': user.get('state', session.get('user_state', ''))
                },
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching profit data: {str(e)}',
            'data': None
        }), 500


@report_bp.route('/api/report/market-watch', methods=['GET'])
@login_required
def get_market_report_data():
    """Get market report data for the user's district"""
    try:
        user_id = session.get('user_id')
        user = find_user_by_id(user_id)
        
        # Session fallback
        district = user.get('district') if user else session.get('user_district')
        state = user.get('state') if user else session.get('user_state')
        name = user.get('name') if user else session.get('user_name', 'Farmer')
        
        if not district:
            return jsonify({
                'success': False,
                'message': 'User district not set. Please update your profile.',
                'data': None
            })
        
        # Load market data
        market_file = 'data/market_prices.json'
        if not os.path.exists(market_file):
            return jsonify({'success': False, 'message': 'Market data file missing'})
            
        with open(market_file, 'r', encoding='utf-8') as f:
            market_data = json.load(f)
            
        # Filter for user's district
        all_data = market_data.get('data', [])
        district_prices = [item for item in all_data if item.get('district') == district]
        
        if not district_prices:
            # Fallback to state data if district is empty
            district_prices = [item for item in all_data if item.get('state') == state][:20]
        
        # Smart selection: ensure fruits are included
        fruits_list = ['Apple', 'Banana', 'Mango', 'Orange', 'Grapes', 'Papaya', 'Pineapple', 
                      'Guava', 'Watermelon', 'Muskmelon', 'Pomegranate', 'Strawberry', 
                      'Cherry', 'Kiwi', 'Lemon', 'Pear', 'Peach', 'Plum', 'Coconut']
        
        selected_prices = []
        vegetables = []
        fruits = []
        
        for item in district_prices:
            is_fruit = any(f.lower() in item.get('commodity', '').lower() for f in fruits_list)
            if is_fruit:
                fruits.append(item)
            else:
                vegetables.append(item)
                
        # If district has no fruits, try to get some from the state
        if not fruits and state:
            state_fruits = [item for item in all_data 
                           if item.get('state') == state and 
                           any(f.lower() in item.get('commodity', '').lower() for f in fruits_list)]
            fruits = state_fruits[:10]
            
        # Combine: 10 vegetables + up to 10 fruits
        selected_prices = vegetables[:10] + fruits[:10]
        
        # Final safety check if still empty
        if not selected_prices:
             selected_prices = district_prices[:15]

        return jsonify({
            'success': True,
            'data': {
                'prices': selected_prices,
                'user': {
                    'name': name,
                    'district': district,
                    'state': state
                },
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@report_bp.route('/api/report/weather', methods=['GET'])
@login_required
def get_weather_report_data():
    """Get 7-day weather forecast report data"""
    try:
        user_id = session.get('user_id')
        user = find_user_by_id(user_id)
        
        # Session fallback
        district = user.get('district') if user else session.get('user_district')
        state = user.get('state') if user else session.get('user_state')
        name = user.get('name') if user else session.get('user_name', 'Farmer')
        
        if not district:
            return jsonify({'success': False, 'message': 'Location not set'})
        
        # Use existing weather function from dashboard_routes
        weather_data = get_weather_notifications(district, state)
        
        return jsonify({
            'success': True,
            'data': {
                'weather': weather_data,
                'user': {
                    'name': name,
                    'district': district,
                    'state': state
                },
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500



def calculate_estimated_yield(activity):
    """Calculate estimated yield based on crop type and progress"""
    crop = activity.get('crop', '').lower()
    progress = activity.get('progress', 0)
    
    # Base yields per acre (in quintals)
    base_yields = {
        'rice': 45,
        'wheat': 40,
        'maize': 50,
        'cotton': 35,
        'sugarcane': 350,
        'potato': 200,
        'tomato': 250,
        'onion': 180,
        'soybean': 25,
        'groundnut': 30
    }
    
    base_yield = base_yields.get(crop, 40)
    
    # Adjust based on progress (assuming optimal conditions at 100%)
    adjusted_yield = base_yield * (progress / 100)
    
    return f"{int(adjusted_yield)}-{int(base_yield)} Quintals/Acre"


def calculate_harvest_window(activity):
    """Calculate harvest window based on current progress"""
    progress = activity.get('progress', 0)
    
    if progress >= 90:
        return "Ready to harvest now"
    elif progress >= 70:
        return "Next 7-10 days"
    elif progress >= 50:
        return "Next 15-20 days"
    else:
        return "More than 30 days"
