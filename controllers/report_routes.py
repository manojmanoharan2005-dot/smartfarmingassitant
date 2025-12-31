from flask import Blueprint, jsonify, session
from utils.auth import login_required
from utils.db import (
    get_user_crops, 
    get_user_fertilizers, 
    get_user_growing_activities,
    find_user_by_id,
    get_db
)
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
        
        # Get user info
        user = find_user_by_id(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'crops': crop_plan,
                'fertilizers': fertilizers[:5] if fertilizers else [],
                'user': {
                    'name': user.get('name', 'Farmer'),
                    'district': user.get('district', ''),
                    'state': user.get('state', '')
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
        
        # Get growing activities that are near harvest (>70% progress)
        activities = get_user_growing_activities(user_id)
        
        if not activities:
            return jsonify({
                'success': False,
                'message': 'No crops found. Start growing crops to generate harvest reports.',
                'data': None
            })
        
        # Filter crops ready for harvest or near harvest
        harvest_ready = [a for a in activities if a.get('progress', 0) >= 50]
        
        if not harvest_ready:
            return jsonify({
                'success': False,
                'message': 'No crops are ready for harvest yet. Continue growing your crops.',
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
        
        return jsonify({
            'success': True,
            'data': {
                'crops': harvest_data,
                'user': {
                    'name': user.get('name', 'Farmer'),
                    'district': user.get('district', ''),
                    'state': user.get('state', '')
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
        
        # Get expense entries from database
        expenses = list(db.expenses.find({'user_id': ObjectId(user_id)}).sort('entry_date', -1))
        
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
            crop = expense.get('crop_type', 'Unknown')
            
            # Calculate revenue
            land_area = float(expense.get('land_area', 0))
            expected_yield = float(expense.get('expected_yield', 0))
            market_price = float(expense.get('market_price', 0))
            revenue = land_area * expected_yield * market_price
            
            # Calculate expenses
            seed_cost = float(expense.get('seed_cost', 0))
            fertilizer_cost = float(expense.get('fertilizer_cost', 0))
            pesticide_cost = float(expense.get('pesticide_cost', 0))
            irrigation_cost = float(expense.get('irrigation_cost', 0))
            labor_cost = float(expense.get('labor_cost', 0))
            machinery_cost = float(expense.get('machinery_cost', 0))
            other_cost = float(expense.get('other_cost', 0))
            
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
        
        # Get user info
        user = find_user_by_id(user_id)
        
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
                    'name': user.get('name', 'Farmer'),
                    'district': user.get('district', ''),
                    'state': user.get('state', '')
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
