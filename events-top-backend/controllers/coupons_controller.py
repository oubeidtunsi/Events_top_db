from flask import Blueprint, request, jsonify
from services.coupons_service import CouponsService
from services.email_service import EmailService
from repositories.auth_repository import AuthRepository
from utils.decorators import token_required
from datetime import datetime
import traceback

coupons_bp = Blueprint('coupons', __name__)


@coupons_bp.route('/send-email', methods=['POST'])  # Registra l'endpoint POST /api/coupons/send-email.
@token_required  # Richiede che la richiesta abbia un token JWT valido.
def send_coupon_email(current_user):  # Definisce la funzione Flask che invia il coupon all'utente autenticato.
    """Invia via email un coupon generato dal gioco."""  # Documenta lo scopo della funzione.
    try:  # Avvia un blocco protetto per gestire eventuali errori runtime.
        data = request.get_json() or {}  # Legge il JSON ricevuto dal gioco oppure usa un dizionario vuoto.
        coupon_code = data.get('coupon_code', '').strip()  # Estrae il codice coupon dal JSON e rimuove spazi inutili.
        discount = data.get('discount', 0)  # Estrae il valore dello sconto oppure usa 0 come default.

        if not coupon_code:  # Controlla se il codice coupon è mancante.
            return jsonify({'error': 'coupon_code obbligatorio'}), 400  # Risponde con errore 400 se manca il codice coupon.

        user = AuthRepository.find_by_id(current_user['user_id'])  # Recupera l'utente completo dal database usando l'id del token.
        email_address = current_user.get('email') or (user.get('email') if user else None)  # Recupera l'email dal token o dal database.
        username = (user.get('username') if user else None) or 'Utente'  # Recupera lo username oppure usa un valore generico.

        if not email_address:  # Controlla se non è stata trovata nessuna email valida.
            return jsonify({'error': 'Email utente non trovata'}), 400  # Risponde con errore 400 se manca l'email.

        if not EmailService.is_configured():  # Controlla che il backend abbia le credenziali SMTP.
            return jsonify({'error': 'Servizio email non configurato'}), 503  # Evita falsi successi quando l'email non puo' partire.

        discount_str = str(discount) + '%'  # Converte lo sconto in stringa percentuale, esempio 10%.
        html_body = CouponsService._compose_coupon_email(username, coupon_code, discount_str)  # Crea il corpo HTML dell'email.

        sent = EmailService.send_coupon_email(  # Chiama il servizio centralizzato per inviare l'email.
            recipient_email=email_address,  # Passa l'indirizzo email del destinatario.
            username=username,  # Passa il nome utente da mostrare nell'email.
            coupon_code=coupon_code,  # Passa il codice coupon da inviare.
            discount=discount_str,  # Passa lo sconto formattato.
            html_body=html_body  # Passa il contenuto HTML dell'email.
        )  # Chiude la chiamata al servizio email.

        if sent:  # Verifica se l'invio email è andato a buon fine.
            return jsonify({'message': 'Email inviata con successo'}), 200  # Risponde con successo al client.

        return jsonify({
            'error': f"Errore durante l'invio dell'email: {EmailService.get_last_error()}"
        }), 503  # Risponde con errore se il servizio email fallisce.

    except Exception:  # Intercetta qualunque errore imprevisto.
        traceback.print_exc()  # Stampa il traceback nei log di Render per il debug.
        return jsonify({'error': 'Errore interno'}), 500  # Restituisce una risposta di errore generica.


@coupons_bp.route('/redeem', methods=['POST'])
@token_required
def redeem_coupon(current_user):
    """
    Riscatta un coupon per l'utente autenticato e invia via email.
    
    Body JSON:
    {
        "coupon_code": "SAVE20"
    }
    """
    try:
        data = request.get_json() or {}

        # Validazione parametri
        if 'coupon_code' not in data or not data['coupon_code'].strip():
            return jsonify({'error': 'Parametro coupon_code obbligatorio'}), 400

        coupon_code = data['coupon_code'].strip().upper()

        # Validazione formato coupon_code
        if not all(c.isalnum() or c in '-_' for c in coupon_code):
            return jsonify({'error': 'coupon_code contiene caratteri non validi'}), 400

        if len(coupon_code) > 50:
            return jsonify({'error': 'coupon_code troppo lungo (max 50 caratteri)'}), 400

        # Chiama il servizio per riscattare il coupon
        result = CouponsService.redeem_coupon(
            user_id=current_user['user_id'],
            coupon_code=coupon_code
        )

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception:
        traceback.print_exc()
        return jsonify({'error': 'Errore durante il riscatto del coupon'}), 500


@coupons_bp.route('', methods=['GET'])
@token_required
def get_available_coupons(current_user):
    """
    Recupera lista di coupon disponibili.
    """
    try:
        coupons = CouponsService.get_available_coupons()
        
        # Formatta dati per la risposta
        formatted = []
        for coupon in coupons:
            item = {
                'code': coupon['code'],
                'discount_value': coupon['discount_value'],
                'description': coupon.get('description'),
                'cost_points': coupon.get('cost_points', 100),
                'available_count': coupon.get('max_redemptions', 0) - coupon.get('redemption_count', 0)
                    if coupon.get('max_redemptions') else None
            }
            formatted.append(item)
        
        return jsonify({'coupons': formatted}), 200

    except Exception:
        traceback.print_exc()
        return jsonify({'error': 'Errore nel recupero coupon'}), 500


@coupons_bp.route('/my-history', methods=['GET'])
@token_required
def get_my_redemption_history(current_user):
    """
    Recupera storico dei coupon riscattati dall'utente autenticato.
    """
    try:
        history = CouponsService.get_user_history(current_user['user_id'])
        
        return jsonify({
            'user_id': current_user['user_id'],
            'redeemed_coupons': history
        }), 200

    except Exception:
        traceback.print_exc()
        return jsonify({'error': 'Errore nel recupero storico'}), 500


@coupons_bp.route('/create', methods=['POST'])
@token_required
def create_coupon(current_user):
    """
    ADMIN: Crea un nuovo coupon nel sistema.
    
    Body JSON:
    {
        "code": "SAVE20",
        "discount_value": "20%",
        "description": "Sconto del 20% su tutti gli eventi",
        "cost_points": 100,
        "max_redemptions": 1000,
        "expires_at": "2026-12-31T23:59:59"
    }
    """
    try:
        # TODO: Verificare che l'utente sia admin (aggiungere is_admin nella tabella users)
        # Per ora, consentire a tutti gli utenti autenticati
        
        data = request.get_json() or {}

        # Validazione parametri obbligatori
        if 'code' not in data or not data['code'].strip():
            return jsonify({'error': 'Parametro code obbligatorio'}), 400
        if 'discount_value' not in data or not data['discount_value'].strip():
            return jsonify({'error': 'Parametro discount_value obbligatorio'}), 400

        code = data['code'].strip().upper()
        discount_value = data['discount_value'].strip()
        description = data.get('description', '').strip() or None
        cost_points = data.get('cost_points', 100)
        max_redemptions = data.get('max_redemptions')
        expires_at_str = data.get('expires_at')

        # Validazione formato
        if not all(c.isalnum() or c in '-_' for c in code):
            return jsonify({'error': 'code contiene caratteri non validi'}), 400
        
        if len(code) > 50:
            return jsonify({'error': 'code troppo lungo (max 50 caratteri)'}), 400

        if not isinstance(cost_points, int) or cost_points < 0:
            return jsonify({'error': 'cost_points deve essere un numero positivo'}), 400

        # Parse expires_at se fornito
        expires_at = None
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str)
            except ValueError:
                return jsonify({'error': 'Format expires_at non valido (usa ISO 8601)'}), 400

        # Chiama il servizio
        coupon_id = CouponsService.create_coupon(
            code=code,
            discount_value=discount_value,
            description=description,
            cost_points=cost_points,
            max_redemptions=max_redemptions,
            expires_at=expires_at
        )

        return jsonify({
            'message': 'Coupon creato con successo',
            'coupon_id': coupon_id,
            'code': code
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception:
        traceback.print_exc()
        return jsonify({'error': 'Errore nella creazione del coupon'}), 500
