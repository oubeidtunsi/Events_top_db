from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from repositories.auth_repository import AuthRepository
from services.email_service import EmailService
from config import Config
import jwt


class AuthService:

    _last_otp_request = {}
    _login_attempts = {}
    _register_lock = {}
    _otp_attempts = {}

    @staticmethod
    def _normalize_email(email):
        return (email or "").strip().lower()

    @staticmethod
    def _normalize_gender(gender):
        if not gender:
            return None
        normalized = str(gender).strip().lower()
        mapping = {
            "m": "male",
            "male": "male",
            "f": "female",
            "female": "female",
            "o": "other",
            "other": "other",
            "altro": "other",
            "non-binary": "non-binary",
            "guest": "guest",
        }
        return mapping.get(normalized, normalized)

    @staticmethod
    def _send_otp_or_fail(email, otp, username):
        if not EmailService.send_otp(email, otp, username):
            raise RuntimeError(
                f"Impossibile inviare il codice OTP: {EmailService.get_last_error()}"
            )

    @staticmethod
    def _has_pending_otp(user):
        return bool(user.get("otp_code") or user.get("otp_expires_at"))

    # ----------------------------
    # UTILITY: NORMALIZZA DATETIME
    # ----------------------------
    @staticmethod
    def _to_utc(dt):
        """
        Converte qualsiasi datetime (string / naive / aware)
        in datetime UTC aware.
        """
        if dt is None:
            return None

        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)

        # se è naive → assumo che sia già UTC (caso PostgreSQL classico)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)

        # se è aware → converto in UTC
        return dt.astimezone(timezone.utc)

    # ----------------------------
    # REGISTER
    # ----------------------------
    @staticmethod
    def register_user(username, email, password,
                      first_name=None, last_name=None,
                      birthday=None, gender=None):

        now = datetime.now(timezone.utc)
        username = (username or "").strip()
        email = AuthService._normalize_email(email)
        gender = AuthService._normalize_gender(gender)

        if not EmailService.is_configured():
            raise RuntimeError("Servizio email non configurato")

        last_call = AuthService._register_lock.get(email)
        if last_call and (now - last_call).total_seconds() < 3:
            raise ValueError("Richiesta duplicata")

        AuthService._register_lock[email] = now

        AuthRepository.delete_expired_unverified_users()

        existing_user = AuthRepository.find_by_email(email)

        if existing_user:

            if existing_user.get("is_verified"):
                raise ValueError("Email già registrata")

            hashed = generate_password_hash(password)
            otp = EmailService.generate_otp()
            otp_hash = generate_password_hash(otp)
            expires = now + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)

            AuthRepository.update_unverified_user(
                user_id=existing_user["id"],
                username=username,
                password_hash=hashed,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=birthday,
                gender=gender,
                otp_code=otp_hash,
                otp_expires_at=expires
            )

            AuthService._send_otp_or_fail(email, otp, username)

            return {
                "message": "Nuovo OTP inviato",
                "user_id": existing_user["id"],
                "email": email
            }

        if AuthRepository.find_by_username(username):
            raise ValueError("Username già in uso")

        hashed = generate_password_hash(password)
        otp = EmailService.generate_otp()
        otp_hash = generate_password_hash(otp)
        expires = now + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)

        user_id = AuthRepository.create_user(
            username=username,
            email=email,
            password_hash=hashed,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=birthday,
            gender=gender,
            is_verified=False,
            otp_code=otp_hash,
            otp_expires_at=expires
        )

        AuthService._send_otp_or_fail(email, otp, username)

        return {
            "message": "OTP inviato",
            "user_id": user_id,
            "email": email
        }

    # ----------------------------
    # VERIFY OTP
    # ----------------------------
    @staticmethod
    def verify_otp(user_id, otp_code):

        now = datetime.now(timezone.utc)

        user = AuthRepository.find_by_id(user_id)
        if not user:
            raise ValueError("Utente non trovato")

        if user.get("is_verified"):
            return AuthService._generate_token(user)

        expires = AuthService._to_utc(user.get("otp_expires_at"))

        if expires and now > expires:
            raise ValueError("Codice scaduto — richiedi un nuovo OTP")

        attempts = AuthService._otp_attempts.get(user_id, 0)

        if attempts >= 5:
            raise ValueError("Troppi tentativi OTP")

        stored_hash = user.get("otp_code")

        if not stored_hash or not check_password_hash(stored_hash, otp_code):
            AuthService._otp_attempts[user_id] = attempts + 1
            raise ValueError("Codice non valido")

        AuthService._otp_attempts.pop(user_id, None)

        AuthRepository.verify_user(user_id)

        user = AuthRepository.find_by_id(user_id)
        return AuthService._generate_token(user)

    # ----------------------------
    # RESEND OTP
    # ----------------------------
    @staticmethod
    def resend_otp(user_id):

        now = datetime.now(timezone.utc)

        user = AuthRepository.find_by_id(user_id)
        if not user:
            raise ValueError("Utente non trovato")

        if user.get("is_verified"):
            raise ValueError("Account già verificato")

        last_time = AuthService._last_otp_request.get(user_id)

        if last_time and (now - last_time).total_seconds() < 60:
            raise ValueError("Attendi prima di richiedere un nuovo OTP")

        AuthService._last_otp_request[user_id] = now

        otp = EmailService.generate_otp()
        otp_hash = generate_password_hash(otp)
        expires = now + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)

        AuthRepository.update_otp(user_id, otp_hash, expires)
        AuthService._send_otp_or_fail(user["email"], otp, user["username"])

        return {"message": "Nuovo OTP inviato"}

    # ----------------------------
    # LOGIN
    # ----------------------------
    @staticmethod
    def login_user(email, password):

        now = datetime.now(timezone.utc)
        email = AuthService._normalize_email(email)

        attempts = AuthService._login_attempts.get(email, {
            "count": 0,
            "time": now
        })

        if (now - attempts["time"]).total_seconds() > 300:
            attempts = {"count": 0, "time": now}

        if attempts["count"] >= 5:
            raise ValueError("Troppi tentativi")

        user = AuthRepository.find_by_email(email)

        if not user or not check_password_hash(user["password_hash"], password):
            attempts["count"] += 1
            attempts["time"] = now
            AuthService._login_attempts[email] = attempts
            return None

        if not user.get("is_verified"):
            if AuthService._has_pending_otp(user):
                raise ValueError("Email non verificata")

            # Account creati prima dell'introduzione dell'OTP, o dal pannello admin,
            # non hanno un codice pendente: li consideriamo gia' validi.
            AuthRepository.verify_user(user["id"])
            user = AuthRepository.find_by_id(user["id"])

        AuthService._login_attempts.pop(email, None)

        return AuthService._generate_token(user)

    # ----------------------------
    # PROFILE
    # ----------------------------
    @staticmethod
    def get_user_profile(user_id):

        user = AuthRepository.find_by_id(user_id)
        if not user:
            raise ValueError("Utente non trovato")

        return {
            k: v for k, v in user.items()
            if k not in ("password_hash", "otp_code", "otp_expires_at")
        }

    # ----------------------------
    # CHECK USERNAME AVAILABILITY
    # ----------------------------
    @staticmethod
    def check_username_available(username, user_id):
        from helpers.user_helper import is_valid_username
        if not username or not is_valid_username(username):
            raise ValueError("Username non valido (3-30 caratteri, solo lettere/cifre/._-)")
        return AuthRepository.check_username_available(username, exclude_user_id=user_id)

    # ----------------------------
    # UPDATE PROFILE
    # ----------------------------
    @staticmethod
    def update_user_profile(user_id, data):
        user = AuthRepository.find_by_id(user_id)
        if not user:
            raise ValueError("Utente non trovato")

        username = data.get("username")
        current_password = data.get("current_password")
        new_password = data.get("new_password")
        profile_image = data.get("profile_image")

        update_kwargs = {}

        if username and username != user["username"]:
            from helpers.user_helper import is_valid_username
            if not is_valid_username(username):
                raise ValueError("Username non valido")
            if not AuthRepository.check_username_available(username, exclude_user_id=user_id):
                raise ValueError("Username già in uso")
            update_kwargs["username"] = username

        if new_password:
            if not current_password:
                raise ValueError("Password corrente obbligatoria per cambiare la password")
            if not check_password_hash(user["password_hash"], current_password):
                raise ValueError("Password corrente errata")
            if len(new_password) < 6:
                raise ValueError("La nuova password deve avere almeno 6 caratteri")
            update_kwargs["password_hash"] = generate_password_hash(new_password)

        if profile_image is not None:
            update_kwargs["profile_image"] = profile_image

        if "private_favorites" in data:
            val = data["private_favorites"]
            update_kwargs["private_favorites"] = (val if isinstance(val, bool)
                                                  else str(val).lower() == "true")

        if "private_reviews" in data:
            val = data["private_reviews"]
            update_kwargs["private_reviews"] = (val if isinstance(val, bool)
                                                else str(val).lower() == "true")

        if update_kwargs:
            AuthRepository.update_profile(user_id, **update_kwargs)

        updated_user = AuthRepository.find_by_id(user_id)
        return {
            "message": "Profilo aggiornato",
            "username": updated_user["username"],
            "profile_image": updated_user.get("profile_image")
        }

    # ----------------------------
    # SEARCH USERS
    # ----------------------------
    @staticmethod
    def search_users(query, exclude_user_id=None):

        if not query or len(query.strip()) < 2:
            return []

        results = AuthRepository.search_by_username(query.strip())

        if exclude_user_id:
            results = [u for u in results if u["id"] != exclude_user_id]

        return results

    # ----------------------------
    # JWT
    # ----------------------------
    @staticmethod
    def _generate_token(user):

        token = jwt.encode(
            {
                "user_id": user["id"],
                "email": user["email"],
                "exp": datetime.now(timezone.utc) + timedelta(days=30)
            },
            Config.SECRET_KEY,
            algorithm="HS256"
        )

        return {
            "token": token,
            "user_id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "gender": user.get("gender", "guest"),
            "profile_image": user.get("profile_image"),
            "private_favorites": bool(user.get("private_favorites") or False),
            "private_reviews":   bool(user.get("private_reviews")   or False)
        }
