from flask import Blueprint, request, jsonify
from services.notifications_service import NotificationsService
from utils.decorators import token_required
import traceback

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/', methods=['GET'])
@token_required
def get_notifications(current_user):
    try:
        unread_only = request.args.get('unread', 'false').lower() == 'true'
        notifs = NotificationsService.get_notifications(current_user['user_id'], unread_only)
        return jsonify({'notifications': notifs}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/<int:notif_id>', methods=['DELETE'])
@token_required
def delete_notification(current_user, notif_id):
    try:
        result = NotificationsService.delete_notification(notif_id, current_user['user_id'])
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/<int:notif_id>/read', methods=['PUT'])
@token_required
def mark_read(current_user, notif_id):
    try:
        result = NotificationsService.mark_read(notif_id, current_user['user_id'])
        return jsonify(result), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/read-all', methods=['PUT'])
@token_required
def mark_all_read(current_user):
    try:
        result = NotificationsService.mark_all_read(current_user['user_id'])
        return jsonify(result), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ---- Promemoria eventi ----

@notifications_bp.route('/reminders', methods=['GET'])
@token_required
def get_reminders(current_user):
    try:
        reminders = NotificationsService.get_reminders(current_user['user_id'])
        return jsonify({'reminders': reminders}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/reminder', methods=['POST'])
@token_required
def set_reminder(current_user):
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        remind_at = data.get('remind_at')
        if not event_id or not remind_at:
            return jsonify({'error': 'event_id e remind_at obbligatori'}), 400
        result = NotificationsService.set_reminder(current_user['user_id'], int(event_id), remind_at)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/reminder/<int:event_id>', methods=['DELETE'])
@token_required
def delete_reminder(current_user, event_id):
    try:
        result = NotificationsService.delete_reminder(current_user['user_id'], event_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/reminder/<int:event_id>', methods=['GET'])
@token_required
def get_reminder(current_user, event_id):
    try:
        reminder = NotificationsService.get_reminder(current_user['user_id'], event_id)
        return jsonify({'reminder': reminder}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
