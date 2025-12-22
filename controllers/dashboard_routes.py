from flask import Blueprint, render_template, session, redirect, url_for
from utils.auth import login_required
from utils.db import get_user_crops, get_user_fertilizers, find_user_by_id, get_dashboard_notifications, get_user_growing_activities
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    
    # Get complete user data from database (excluding password)
    user = find_user_by_id(user_id)
    
    # If user not found in database, use session data as fallback
    if not user:
        user = {
            '_id': user_id,
            'name': session.get('user_name', 'Unknown User'),
            'email': session.get('user_email', 'No email'),
            'phone': session.get('user_phone', 'Not provided'),
            'state': session.get('user_state', 'Not provided'), 
            'district': session.get('user_district', 'Not provided'),
            'created_at': datetime.utcnow()
        }
    else:
        # Ensure created_at exists for existing users
        if 'created_at' not in user or user['created_at'] is None:
            user['created_at'] = datetime.utcnow()
    
    saved_crops = get_user_crops(user_id)
    saved_fertilizers = get_user_fertilizers(user_id)
    growing_activities = get_user_growing_activities(user_id)
    notifications = get_dashboard_notifications(user_id)
    
    # Calculate statistics
    stats = {
        'total_recommendations': len(saved_crops) + len(saved_fertilizers),
        'crops_suggested': len(saved_crops),
        'fertilizers_saved': len(saved_fertilizers),
        'active_crops': len(growing_activities)
    }
    
    return render_template('dashboard.html', 
                         user=user,  # Complete user object with real data
                         saved_crops=saved_crops,
                         saved_fertilizers=saved_fertilizers,
                         growing_activities=growing_activities,
                         notifications=notifications,
                         stats=stats)
