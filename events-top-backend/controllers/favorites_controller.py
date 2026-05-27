from flask import Blueprint, request, jsonify
from services.favorites_service import FavoritesService
from utils.decorators import token_required

favorites_bp = Blueprint('favorites', __name__)

@favorites_bp.route('/', methods=['POST'])
@token_required
def add_favorite(current_user):
    try:
        data = request.get_json()
        result = FavoritesService.add_favorite(current_user['user_id'], data['event_id'])
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@favorites_bp.route('/', methods=['GET'])
@token_required
def get_favorites(current_user):
    try:
        favorites = FavoritesService.get_favorites(current_user['user_id'])
        return jsonify({'favorites': favorites}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@favorites_bp.route('/<int:event_id>', methods=['DELETE'])
@token_required
def remove_favorite(current_user, event_id):
    try:
        result = FavoritesService.remove_favorite(current_user['user_id'], event_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@favorites_bp.route('/<int:event_id>/check', methods=['GET'])
@token_required
def check_favorite(current_user, event_id):
    try:
        is_fav = FavoritesService.is_favorite(current_user['user_id'], event_id)
        return jsonify({'is_favorite': is_fav}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500