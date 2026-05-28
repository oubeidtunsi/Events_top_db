from database import Database
from helpers.format_helper import dict_format, dict_format_single

class UserRepository:
    @staticmethod
    def find_by_email(email):
        db = Database()
        conn = db.get_connection()
        rows = conn.run("SELECT * FROM users WHERE email = :email", email=email)
        return dict_format_single(conn, rows)

    @staticmethod
    def find_by_username(username):
        db = Database()
        conn = db.get_connection()
        rows = conn.run("SELECT * FROM users WHERE username = :username", username=username)
        return dict_format_single(conn, rows)

    @staticmethod
    def find_by_id(user_id):
        db = Database()
        conn = db.get_connection()
        rows = conn.run(
            "SELECT id, username, email, first_name, last_name, date_of_birth "
            "FROM users WHERE id = :user_id",
            user_id=user_id
        )
        return dict_format_single(conn, rows)

    @staticmethod
    def find_by_email_or_username(email, username):
        db = Database()
        conn = db.get_connection()
        rows = conn.run(
            "SELECT * FROM users WHERE email = :email OR username = :username",
            email=email, username=username
        )
        return dict_format_single(conn, rows)

    @staticmethod
    def create(user_data):
        db = Database()
        conn = db.get_connection()
        # Assicurati che i nomi dei parametri :nome corrispondano alle chiavi nel dizionario user_data
        rows = conn.run(
            """INSERT INTO users (username, email, password_hash, first_name, last_name, date_of_birth) 
               VALUES (:username, :email, :password_hash, :firstName, :lastName, :dateOfBirth) 
               RETURNING id, username, email, first_name, last_name, date_of_birth, created_at""",
            **user_data
        )
        conn.run("COMMIT")
        return dict_format_single(conn, rows)

    @staticmethod
    def update_last_login(user_id):
        db = Database()
        conn = db.get_connection()
        conn.run("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = :user_id", user_id=user_id)
        conn.run("COMMIT")

    @staticmethod
    def add_score_to_user(email, score):
        db = Database()
        conn = db.get_connection()
        rows = conn.run(
            """
            UPDATE users
            SET
                total_score = COALESCE(total_score, 0) + :score,
                max_score = GREATEST(COALESCE(max_score, 0), :score)
            WHERE LOWER(email) = LOWER(:email)
            RETURNING id, email, total_score, max_score
            """,
            score=score,
            email=email
        )
        conn.run("COMMIT")
        return dict_format_single(conn, rows)
    
    @staticmethod
    def get_top_users(limit=5):
        db = Database()
        conn = db.get_connection()
        # Seleziona i migliori giocatori ordinati per max_score decrescente
        rows = conn.run(
            "SELECT username, max_score, total_score "
            "FROM users "
            "WHERE max_score IS NOT NULL "
            "ORDER BY max_score DESC "
            "LIMIT :limit",
            limit=limit
        )
        return dict_format(conn, rows)