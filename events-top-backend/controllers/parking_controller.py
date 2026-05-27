# controllers/parking_controller.py
from flask import Blueprint, request, jsonify
from services.parking_service import ParkingService
from utils.decorators import token_required

parking_bp = Blueprint('parking', __name__)

@parking_bp.route('/', methods=['POST'])
@token_required
def save_parking(current_user):
    """
    Salva parcheggio
    Body: {"latitude": 41.9028, "longitude": 12.4964, "notes": "Posto blu"}
    """
    try:
        data = request.get_json()
        
        if not data.get('latitude') or not data.get('longitude'):
            return jsonify({'error': 'Coordinate obbligatorie'}), 400
        
        result = ParkingService.save_parking(
            current_user['user_id'],
            float(data['latitude']),
            float(data['longitude']),
            data.get('notes', '')
        )
        
        return jsonify(result), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parking_bp.route('/', methods=['GET'])
@token_required
def get_parkings(current_user):
    """Recupera storico parcheggi"""
    try:
        parkings = ParkingService.get_user_parkings(current_user['user_id'])
        return jsonify({'parkings': parkings}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parking_bp.route('/<int:parking_id>', methods=['DELETE'])
@token_required
def delete_parking(current_user, parking_id):
    """Elimina un parcheggio"""
    try:
        result = ParkingService.delete_parking(parking_id, current_user['user_id'])
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500