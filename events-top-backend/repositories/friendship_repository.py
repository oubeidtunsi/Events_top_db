from database import Database
from helpers.format_helper import dict_format, dict_format_single

class FriendshipRepository:
    @staticmethod
    def find_friendship(user1, user2):
        db = Database()
        conn = db.get_connection()
        rows = conn.run(
            "SELECT * FROM friendships WHERE (user_id_1 = :u1 AND user_id_2 = :u2) "
            "OR (user_id_1 = :u2 AND user_id_2 = :u1)",
            u1=user1, u2=user2
        )
        return dict_format_single(conn, rows)

    @staticmethod
    def create_request(sender_id, receiver_id):
        db = Database()
        conn = db.get_connection()
        conn.run(
            "INSERT INTO friendships (user_id_1, user_id_2, status) VALUES (:u1, :u2, 'pending')",
            u1=sender_id, u2=receiver_id
        )
        conn.run("COMMIT")

    @staticmethod
    def get_pending_requests(user_id):
        # Le richieste ricevute sono quelle dove user_id_2 = user_id (receiver)
        db = Database()
        conn = db.get_connection()
        rows = conn.run(
            """SELECT f.id AS friendship_id, f.status,
                      u.id AS user_id, u.username, u.email, u.profile_image
               FROM friendships f
               JOIN users u ON f.user_id_1 = u.id
               WHERE f.user_id_2 = :uid AND f.status = 'pending'""",
            uid=user_id
        )
        return dict_format(conn, rows)

    @staticmethod
    def get_friends(user_id):
        db = Database()
        conn = db.get_connection()
        rows = conn.run(
            """SELECT f.id AS friendship_id, f.status,
                      u.id AS user_id, u.username, u.email, u.profile_image
               FROM friendships f
               JOIN users u ON (CASE WHEN f.user_id_1 = :uid
                                     THEN f.user_id_2 ELSE f.user_id_1 END) = u.id
               WHERE (f.user_id_1 = :uid OR f.user_id_2 = :uid)
               AND f.status = 'accepted'""",
            uid=user_id
        )
        return dict_format(conn, rows)

    @staticmethod
    def update_status(request_id, new_status):
        db = Database()
        conn = db.get_connection()
        conn.run(
            "UPDATE friendships SET status = :s WHERE id = :id",
            s=new_status, id=request_id
        )
        conn.run("COMMIT")