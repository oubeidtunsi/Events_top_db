from functools import wraps
from flask import request, jsonify
from config import Config
import jwt


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Token mancante. Effettua il login.'}), 401

        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            current_user = {
                'user_id': data['user_id'],
                'email':   data['email']
            }
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token scaduto. Effettua nuovamente il login.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token non valido.'}), 401

        return f(current_user, *args, **kwargs)

    return decorated