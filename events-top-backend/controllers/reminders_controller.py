from flask import Blueprint, request, jsonify
from services.reminders_service import RemindersService
from utils.decorators import token_required
import traceback

reminders_bp = Blueprint('reminders', __name__)

@reminders_bp.route('/', methods=['GET'])
@token_required
def get_reminders(current_user):
    try:
        reminders = RemindersService.get_reminders(current_user['user_id'])
        return jsonify({'reminders': reminders}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@reminders_bp.route('/', methods=['POST'])
@token_required
def create_reminder(current_user):
    try:
        data = request.get_json()
        event_id  = data.get('event_id')
        remind_at = data.get('remind_at')
        if not event_id or not remind_at:
            return jsonify({'error': 'event_id e remind_at obbligatori'}), 400
        result = RemindersService.create_reminder(
            current_user['user_id'], int(event_id), remind_at)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@reminders_bp.route('/<int:reminder_id>', methods=['DELETE'])
@token_required
def delete_reminder(current_user, reminder_id):
    try:
        result = RemindersService.delete_reminder(current_user['user_id'], reminder_id)
        return jsonify(result), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
