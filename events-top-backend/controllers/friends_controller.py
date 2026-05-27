from flask import Blueprint, request, jsonify
from services.friends_service import FriendsService
from utils.decorators import token_required
import traceback

friends_bp = Blueprint('friends', __name__)

@friends_bp.route('/request', methods=['POST'])
@token_required
def send_friend_request(current_user):
    try:
        data = request.get_json()
        friend_id = data.get('friend_id')
        if not friend_id:
            return jsonify({'error': 'ID amico obbligatorio'}), 400
        result = FriendsService.send_request(current_user['user_id'], int(friend_id))
        return jsonify(result), 201
    except ValueError as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 409
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@friends_bp.route('/requests', methods=['GET'])
@token_required
def get_pending_requests(current_user):
    try:
        requests = FriendsService.get_pending_requests(current_user['user_id'])
        return jsonify({'requests': requests}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@friends_bp.route('/respond', methods=['POST'])
@token_required
def respond_to_request(current_user):
    try:
        data = request.get_json()
        result = FriendsService.respond_to_request(data['request_id'], data['response'])
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@friends_bp.route('/list', methods=['GET'])
@token_required
def get_friends_list(current_user):
    try:
        friends = FriendsService.get_friends(current_user['user_id'])
        return jsonify({'friends': friends}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500