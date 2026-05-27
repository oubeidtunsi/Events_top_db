from flask import Blueprint, request, jsonify
from utils.decorators import token_required
from repositories.auth_repository import AuthRepository
from repositories.favorite_repository import FavoriteRepository
from repositories.review_repository import ReviewRepository
from database import Database
from helpers.format_helper import dict_format, dict_format_single
from werkzeug.security import generate_password_hash
import traceback

users_bp = Blueprint('users', __name__)


# ── DASHBOARD: GET lista ─────────────────────────────────────────────────────

@users_bp.route('/', methods=['GET'], strict_slashes=False)
def get_users():
    """Dashboard — lista utenti con filtri opzionali (username, email)."""
    try:
        conn = Database().get_connection()
        sql  = """
            SELECT id, username, email,
                   first_name, last_name,
                   is_verified, private_favorites, private_reviews,
                   gender, date_of_birth, profile_image
            FROM users
            WHERE 1=1
        """
        params   = {}
        username = request.args.get('username')
        email    = request.args.get('email')

        if username:
            sql += " AND LOWER(username) LIKE LOWER(:username)"
            params['username'] = f'%{username}%'
        if email:
            sql += " AND LOWER(email) LIKE LOWER(:email)"
            params['email'] = f'%{email}%'

        sql += " ORDER BY id DESC"
        rows  = conn.run(sql, **params)
        users = dict_format(conn, rows)

        # Rinomina is_verified → verified per compatibilità con l'HTML
        for u in users:
            u['verified'] = u.pop('is_verified', False)

        return jsonify({'users': users}), 200
    except Exception:
        traceback.print_exc()
        return jsonify({'error': 'Errore nel recupero utenti'}), 500


# ── DASHBOARD: POST crea ─────────────────────────────────────────────────────

@users_bp.route('/', methods=['POST'], strict_slashes=False)
def create_user():
    """Dashboard — crea un nuovo utente (già verificato, senza flusso OTP)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Body JSON obbligatorio'}), 400

        required = ('username', 'email', 'password', 'first_name', 'last_name', 'date_of_birth')
        missing  = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({'error': f'Campi obbligatori: {", ".join(missing)}'}), 400

        conn = Database().get_connection()

        # Verifica duplicati
        dup = conn.run(
            "SELECT id FROM users WHERE username = :u OR email = :e",
            u=data['username'], e=data['email']
        )
        if dup:
            return jsonify({'error': 'Username o email già in uso'}), 409

        full_name     = f"{data.get('first_name','')} {data.get('last_name','')}".strip()
        password_hash = generate_password_hash(data['password'])

        rows = conn.run(
            """
            INSERT INTO users
                (username, email, password_hash,
                 first_name, last_name, full_name,
                 date_of_birth, gender, is_verified,
                 private_favorites, private_reviews, profile_image)
            VALUES
                (:username, :email, :password_hash,
                 :first_name, :last_name, :full_name,
                 :date_of_birth, :gender, :is_verified,
                 :private_favorites, :private_reviews, :profile_image)
            RETURNING id
            """,
            username=data['username'],
            email=data['email'],
            password_hash=password_hash,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            full_name=full_name,
            date_of_birth=data.get('date_of_birth'),
            gender=data.get('gender', 'guest'),
            is_verified=bool(data.get('verified', False)),
            private_favorites=bool(data.get('private_favorites', False)),
            private_reviews=bool(data.get('private_reviews', False)),
            profile_image=data.get('avatar_url') or None,
        )
        conn.run("COMMIT")
        new_id = rows[0][0]
        return jsonify({'message': 'Utente creato', 'id': new_id}), 201
    except Exception:
        traceback.print_exc()
        return jsonify({'error': 'Errore nella creazione utente'}), 500


# ── DASHBOARD: PUT aggiorna ──────────────────────────────────────────────────

@users_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Dashboard — aggiorna i campi di un utente esistente."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Body JSON obbligatorio'}), 400

        # Mappa campo HTML → colonna DB
        field_map = {
            'username':          'username',
            'email':             'email',
            'first_name':        'first_name',
            'last_name':         'last_name',
            'date_of_birth':     'date_of_birth',
            'gender':            'gender',
            'verified':          'is_verified',
            'private_favorites': 'private_favorites',
            'private_reviews':   'private_reviews',
            'avatar_url':        'profile_image',
        }

        sets   = []
        params = {'uid': user_id}

        for html_key, col in field_map.items():
            if html_key in data:
                pk = f'v_{col}'
                sets.append(f"{col} = :{pk}")
                params[pk] = data[html_key] if data[html_key] != '' else None

        # Password opzionale: aggiorna solo se fornita
        if data.get('password'):
            sets.append("password_hash = :v_password_hash")
            params['v_password_hash'] = generate_password_hash(data['password'])

        # Aggiorna full_name se cambiano first o last name
        fn = data.get('first_name', '')
        ln = data.get('last_name', '')
        if fn or ln:
            # Ricostruisce full_name dal valore aggiornato o dall'esistente
            if fn and ln:
                sets.append("full_name = :v_full_name")
                params['v_full_name'] = f'{fn} {ln}'.strip()

        if not sets:
            return jsonify({'error': 'Nessun campo da aggiornare'}), 400

        conn = Database().get_connection()
        conn.run(f"UPDATE users SET {', '.join(sets)} WHERE id = :uid", **params)
        conn.run("COMMIT")
        return jsonify({'message': 'Utente aggiornato'}), 200
    except Exception:
        traceback.print_exc()
        return jsonify({'error': "Errore nell'aggiornamento utente"}), 500


# ── DASHBOARD: DELETE ────────────────────────────────────────────────────────

@users_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Dashboard — elimina un utente (CASCADE su favoriti, recensioni, ecc.)."""
    try:
        conn = Database().get_connection()
        conn.run("DELETE FROM friendships WHERE user_id_1 = :id OR user_id_2 = :id", id=user_id)
        conn.run("DELETE FROM reviews WHERE user_id = :id", id=user_id)
        conn.run("DELETE FROM favorites WHERE user_id = :id", id=user_id)
        conn.run("DELETE FROM event_responses WHERE user_id = :id", id=user_id)
        conn.run("DELETE FROM event_reminders WHERE user_id = :id", id=user_id)
        conn.run("DELETE FROM notifications WHERE user_id = :id", id=user_id)
        conn.run("DELETE FROM event_proposals WHERE from_user_id = :id OR to_user_id = :id", id=user_id)
        conn.run("DELETE FROM users WHERE id = :id", id=user_id)
        conn.run("COMMIT")
        return jsonify({'message': 'Utente eliminato'}), 200
    except Exception:
        traceback.print_exc()
        return jsonify({'error': "Errore nell'eliminazione utente"}), 500


@users_bp.route('/<int:user_id>/profile', methods=['GET'])
@token_required
def get_user_public_profile(current_user, user_id):
    try:
        user = AuthRepository.find_by_id(user_id)
        if not user:
            return jsonify({'error': 'Utente non trovato'}), 404
        return jsonify({
            'user_id':          user['id'],
            'username':         user['username'],
            'profile_image':    user.get('profile_image'),
            'private_favorites': bool(user.get('private_favorites') or False),
            'private_reviews':   bool(user.get('private_reviews')   or False)
        }), 200
    except Exception:
        traceback.print_exc()
        return jsonify({'error': 'Errore server'}), 500


@users_bp.route('/<int:user_id>/favorites', methods=['GET'])
@token_required
def get_user_favorites(current_user, user_id):
    try:
        user = AuthRepository.find_by_id(user_id)
        if not user:
            return jsonify({'error': 'Utente non trovato'}), 404

        if user.get('private_favorites') and current_user['user_id'] != user_id:
            return jsonify({'private': True, 'favorites': []}), 403

        favorites = FavoriteRepository.find_by_user(user_id)
        return jsonify({'favorites': favorites}), 200
    except Exception:
        traceback.print_exc()
        return jsonify({'error': 'Errore server'}), 500


@users_bp.route('/<int:user_id>/reviews', methods=['GET'])
@token_required
def get_user_reviews(current_user, user_id):
    try:
        user = AuthRepository.find_by_id(user_id)
        if not user:
            return jsonify({'error': 'Utente non trovato'}), 404

        if user.get('private_reviews') and current_user['user_id'] != user_id:
            return jsonify({'private': True, 'reviews': []}), 403

        reviews = ReviewRepository.find_by_user(user_id)
        return jsonify({'reviews': reviews}), 200
    except Exception:
        traceback.print_exc()
        return jsonify({'error': 'Errore server'}), 500
