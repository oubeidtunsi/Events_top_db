from flask import Blueprint, request, jsonify
from services.reviews_service import ReviewsService
from utils.decorators import token_required

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('/', methods=['POST'])
@token_required
def add_review(current_user):
    try:
        data = request.get_json()
        replica_id = data.get('replica_id')
        # -1 è il valore sentinella del client per "legacy / nessuna replica selezionata"
        if replica_id == -1:
            replica_id = None
        result = ReviewsService.add_review(
            current_user['user_id'],
            data['event_id'],
            data['rating'],
            data.get('comment') or '',
            replica_id=replica_id,
        )
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reviews_bp.route('/event/<int:event_id>', methods=['GET'])
def get_event_reviews(event_id):
    try:
        reviews = ReviewsService.get_event_reviews(event_id)
        return jsonify({'reviews': reviews}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reviews_bp.route('/user', methods=['GET'])
@token_required
def get_user_reviews(current_user):
    try:
        reviews = ReviewsService.get_user_reviews(current_user['user_id'])
        return jsonify({'reviews': reviews}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reviews_bp.route('/<int:review_id>', methods=['DELETE'])
@token_required
def delete_review(current_user, review_id):
    try:
        result = ReviewsService.delete_review(current_user['user_id'], review_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500