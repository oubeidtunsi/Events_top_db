import traceback
from flask import Blueprint, request, jsonify
from services.proposal_service import ProposalService
from utils.decorators import token_required

proposals_bp = Blueprint('proposals', __name__)


@proposals_bp.route('/', methods=['POST'])
@token_required
def propose_event(current_user):
    """
    Invia una proposta evento a un amico.
    Body: { "to_user_id": int, "event_id": int }
    """
    try:
        data = request.get_json() or {}
        to_user_id = data.get('to_user_id')
        event_id   = data.get('event_id')
        if not to_user_id or not event_id:
            return jsonify({'error': 'to_user_id e event_id sono obbligatori'}), 400

        result = ProposalService.propose_event(
            current_user['user_id'], int(to_user_id), int(event_id)
        )
        return jsonify(result), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@proposals_bp.route('/respond', methods=['POST'])
@token_required
def respond_proposal(current_user):
    """
    L'utente risponde a una proposta con un'emoji.
    Body: { "event_id": int, "response_emoji": "👍" | "👎" | "🤔" }
    """
    print(">>> [respond_proposal] Dati ricevuti da Android:", request.get_json())
    try:
        data = request.get_json() or {}
        event_id       = data.get('event_id')
        response_emoji = data.get('response_emoji')
        if not event_id or not response_emoji:
            return jsonify({'error': 'event_id e response_emoji sono obbligatori'}), 400

        result = ProposalService.respond(
            current_user['user_id'], int(event_id), response_emoji
        )
        return jsonify(result), 200

    except ValueError as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@proposals_bp.route('/status', methods=['GET'])
@token_required
def get_proposal_status(current_user):
    """
    Proposte inviate dall'utente con l'emoji di risposta dell'amico.
    Response: { "proposals": [ { ..., "response_emoji": "👍" | null } ] }
    """
    try:
        proposals = ProposalService.get_status(current_user['user_id'])
        return jsonify({'proposals': proposals}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@proposals_bp.route('/received', methods=['GET'])
@token_required
def get_received_proposals(current_user):
    """
    Proposte ricevute ancora in attesa di risposta.
    Response: { "proposals": [ { "id", "event_id", "from_username", ... } ] }
    """
    try:
        proposals = ProposalService.get_received(current_user['user_id'])
        return jsonify({'proposals': proposals}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
