from flask import Blueprint, request, jsonify, session
from utils.auth import login_required
from utils.db import get_all_equipment, save_equipment, update_equipment_status, find_user_by_id, add_notification
from datetime import datetime

equipment_bp = Blueprint('equipment', __name__)

@equipment_bp.route('/api/equipment', methods=['GET'])
@login_required
def get_equipment():
    """Get all equipment available for sharing"""
    equipment = get_all_equipment()
    return jsonify(equipment)

@equipment_bp.route('/api/equipment', methods=['POST'])
@login_required
def add_equipment():
    """List new equipment for sharing"""
    data = request.json
    user_id = session.get('user_id')
    user = find_user_by_id(user_id)
    
    # Fallback to session data if user not found in DB (common with mock DB on restart)
    if not user:
        user = {
            '_id': user_id,
            'name': session.get('user_name', 'Unknown Farmer'),
            'district': session.get('user_district', 'Local'),
            'state': session.get('user_state', '')
        }
    
    new_item = {
        'name': data.get('name'),
        'type': data.get('type'),
        'rate': data.get('rate'),
        'rate_unit': data.get('rate_unit', 'hr'),
        'owner_id': user_id,
        'owner_name': user.get('name'),
        'location': f"{user.get('district')}, {user.get('state')}",
        'description': data.get('description'),
        'image_emoji': data.get('image_emoji', '🚜')
    }
    
    equipment_id = save_equipment(new_item)
    if equipment_id:
        return jsonify({'success': True, 'id': equipment_id}), 201
    return jsonify({'error': 'Failed to save equipment'}), 500

@equipment_bp.route('/api/equipment/<equipment_id>/rent', methods=['POST'])
@login_required
def rent_equipment(equipment_id):
    """Submit rental request for equipment"""
    user_name = session.get('user_name', 'A farmer')
    user_id = session.get('user_id')
    
    # Find equipment to get owner info
    equipment_list = get_all_equipment()
    item = next((i for i in equipment_list if i.get('_id') == equipment_id), None)
    
    if not item:
        return jsonify({'error': 'Equipment not found'}), 404
        
    # Update status to requested instead of rented
    # We also store the requester_id directly on the item temporarily or just rely on the notification flow
    success = update_equipment_status(equipment_id, 'requested')
    
    if success:
        # Notify the owner with actionable request
        owner_id = item.get('owner_id')
        if owner_id and owner_id != 'system':
            add_notification(
                owner_id, 
                'rental_request', 
                f"🤝 {user_name} wants to rent your {item.get('name')}. Accept/Reject?",
                'high',
                data={
                    'equipment_id': equipment_id, 
                    'requester_id': user_id,
                    'requester_name': user_name,
                    'is_actionable': True
                }
            )
        return jsonify({'success': True, 'message': 'Request sent to owner'})
    return jsonify({'error': 'Failed to submit request'}), 500

@equipment_bp.route('/api/equipment/<equipment_id>/accept', methods=['POST'])
@login_required
def accept_request(equipment_id):
    """Accept a rental request"""
    data = request.json
    notification_id = data.get('notification_id')
    requester_id = data.get('requester_id')
    
    # 1. Update equipment status to 'rented'
    if update_equipment_status(equipment_id, 'rented'):
        
        # 2. Notify the requester
        if requester_id:
            item = next((i for i in get_all_equipment() if i.get('_id') == equipment_id), None)
            item_name = item.get('name', 'Equipment') if item else 'Equipment'
            
            add_notification(
                requester_id,
                'equipment',
                f"✅ Your request for {item_name} was ACCEPTED!",
                'high'
            )
            
        # 3. Remove the actionable notification
        if notification_id:
            from utils.db import delete_notification
            delete_notification(notification_id)
            
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to accept request'}), 500

@equipment_bp.route('/api/equipment/<equipment_id>/reject', methods=['POST'])
@login_required
def reject_request(equipment_id):
    """Reject a rental request"""
    data = request.json
    notification_id = data.get('notification_id')
    requester_id = data.get('requester_id')
    
    # 1. Update equipment status back to 'available'
    if update_equipment_status(equipment_id, 'available'):
        
        # 2. Notify the requester
        if requester_id:
            item = next((i for i in get_all_equipment() if i.get('_id') == equipment_id), None)
            item_name = item.get('name', 'Equipment') if item else 'Equipment'
            
            add_notification(
                requester_id,
                'equipment',
                f"❌ Your request for {item_name} was REJECTED.",
                'medium'
            )
            
        # 3. Remove the actionable notification
        if notification_id:
            from utils.db import delete_notification
            delete_notification(notification_id)
            
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to reject request'}), 500
