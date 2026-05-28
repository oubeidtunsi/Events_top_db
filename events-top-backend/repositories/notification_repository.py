from database import Database
from helpers.format_helper import dict_format, dict_format_single

_DATE_COALESCE = """COALESCE(
        (SELECT to_char(MIN(eri.show_date), 'YYYY-MM-DD')
         FROM event_replicas eri
         WHERE eri.event_id = e.id AND eri.show_date >= NOW()),
        NULLIF(e.event_date::TEXT, '')
    ) AS event_date"""

_CITY_COALESCE = """COALESCE(
        NULLIF(e.city, ''),
        (SELECT li.city FROM event_replicas eri
         JOIN locations li ON li.id = eri.location_id
         WHERE eri.event_id = e.id ORDER BY eri.show_date LIMIT 1)
    ) AS event_city"""


class NotificationRepository:
    @staticmethod
    def create(notification_data):
        db = Database()
        conn = db.get_connection()
        conn.run(
            """INSERT INTO notifications (user_id, type, content, related_id, from_user_id)
               VALUES (:user_id, :type, :content, :related_id, :from_user_id)""",
            user_id=notification_data['user_id'],
            type=notification_data['type'],
            content=notification_data['content'],
            related_id=notification_data.get('related_id'),
            from_user_id=notification_data.get('from_user_id')
        )
        conn.run("COMMIT")

    @staticmethod
    def find_by_user(user_id, unread_only=False):
        db = Database()
        conn = db.get_connection()
        query = """
            SELECT n.id, n.type, n.content, n.related_id,
                   n.from_user_id, u.username AS from_username,
                   n.is_read, n.created_at,
                   e.title AS event_title
            FROM notifications n
            LEFT JOIN users u ON n.from_user_id = u.id
            LEFT JOIN events e
                   ON e.id = n.related_id
                  AND n.type IN ('event_proposal', 'proposal_response')
            WHERE n.user_id = :user_id
        """
        params = {'user_id': user_id}
        if unread_only:
            query += " AND n.is_read = false"
        query += " ORDER BY n.created_at DESC"
        rows = conn.run(query, **params)
        return dict_format(conn, rows)

    @staticmethod
    def mark_as_read(notification_id, user_id):
        db = Database()
        conn = db.get_connection()
        conn.run(
            "UPDATE notifications SET is_read = true WHERE id = :id AND user_id = :user_id",
            id=notification_id, user_id=user_id
        )
        conn.run("COMMIT")

    @staticmethod
    def mark_all_read(user_id):
        db = Database()
        conn = db.get_connection()
        conn.run(
            "UPDATE notifications SET is_read = true WHERE user_id = :user_id AND is_read = false",
            user_id=user_id
        )
        conn.run("COMMIT")

    @staticmethod
    def delete(notification_id, user_id):
        db = Database()
        conn = db.get_connection()
        conn.run(
            "DELETE FROM notifications WHERE id = :id AND user_id = :uid",
            id=notification_id, uid=user_id
        )
        conn.run("COMMIT")

    # ---- Promemoria eventi ----

    @staticmethod
    def create_reminder(user_id, event_id, remind_at):
        db = Database()
        conn = db.get_connection()
        rows = conn.run(
            """INSERT INTO event_reminders (user_id, event_id, remind_at)
               VALUES (:uid, :eid, :rat)
               ON CONFLICT (user_id, event_id) DO UPDATE SET remind_at = EXCLUDED.remind_at
               RETURNING id""",
            uid=user_id, eid=event_id, rat=remind_at
        )
        # dict_format non usato: prendiamo solo l'id direttamente
        result_id = rows[0][0] if rows else None
        conn.run("COMMIT")
        return result_id

    @staticmethod
    def delete_reminder(user_id, event_id):
        db = Database()
        conn = db.get_connection()
        conn.run(
            "DELETE FROM event_reminders WHERE user_id = :uid AND event_id = :eid",
            uid=user_id, eid=event_id
        )
        conn.run("COMMIT")

    @staticmethod
    def delete_reminder_by_id(user_id, reminder_id):
        db = Database()
        conn = db.get_connection()
        conn.run(
            "DELETE FROM event_reminders WHERE id = :rid AND user_id = :uid",
            rid=reminder_id, uid=user_id
        )
        conn.run("COMMIT")

    @staticmethod
    def find_reminders_by_user(user_id):
        db = Database()
        conn = db.get_connection()
        rows = conn.run(
            f"""SELECT r.id, r.event_id, r.remind_at, r.created_at,
                      e.title AS event_title,
                      {_DATE_COALESCE},
                      {_CITY_COALESCE}
               FROM event_reminders r
               JOIN events e ON r.event_id = e.id
               WHERE r.user_id = :uid
               ORDER BY r.remind_at ASC""",
            uid=user_id
        )
        return dict_format(conn, rows)

    @staticmethod
    def find_reminder(user_id, event_id):
        db = Database()
        conn = db.get_connection()
        rows = conn.run(
            "SELECT id, remind_at FROM event_reminders WHERE user_id = :uid AND event_id = :eid",
            uid=user_id, eid=event_id
        )
        return dict_format_single(conn, rows)
