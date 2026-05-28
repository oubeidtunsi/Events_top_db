import traceback
from database import Database
from helpers.format_helper import dict_format, dict_format_single

class FavoriteRepository:
    @staticmethod
    def add(user_id, event_id):
        db = Database()
        conn = db.get_connection()
        rows = conn.run(
            "INSERT INTO favorites (user_id, event_id) VALUES (:user_id, :event_id) "
            "ON CONFLICT DO NOTHING RETURNING *",
            user_id=user_id, event_id=event_id
        )
        # dict_format PRIMA di COMMIT: conn.columns viene azzerato da COMMIT
        result = dict_format_single(conn, rows)
        conn.run("COMMIT")
        return result

    @staticmethod
    def find_by_user(user_id):
        try:
            db = Database()
            conn = db.get_connection()
            rows = conn.run(
                """SELECT
                       f.id          AS favorite_id,
                       f.created_at,
                       f.event_id,
                       e.title,
                       e.category,
                       COALESCE(
                           NULLIF(e.city, ''),
                           (SELECT li.city
                            FROM event_replicas eri
                            JOIN locations li ON li.id = eri.location_id
                            WHERE eri.event_id = e.id
                            ORDER BY eri.show_date
                            LIMIT 1)
                       ) AS city,
                       COALESCE(
                           (SELECT to_char(MIN(eri.show_date), 'YYYY-MM-DD')
                            FROM event_replicas eri
                            WHERE eri.event_id = e.id
                              AND eri.show_date >= NOW()),
                           NULLIF(e.event_date::TEXT, '')
                       ) AS event_date,
                       (SELECT ei.url
                        FROM event_images ei
                        WHERE ei.event_id = e.id
                        ORDER BY ei.image_order
                        LIMIT 1) AS image_url
                   FROM favorites f
                   LEFT JOIN events e ON f.event_id = e.id
                   WHERE f.user_id = :user_id
                   ORDER BY f.created_at DESC""",
                user_id=user_id
            )
            all_rows = dict_format(conn, rows)
            return [r for r in all_rows if r.get("title") is not None]

        except Exception as e:
            print(f"❌ FavoriteRepository.find_by_user(user_id={user_id!r})"
                  f" — {type(e).__name__}: {e}")
            traceback.print_exc()
            return []

    @staticmethod
    def remove(user_id, event_id):
        db = Database()
        conn = db.get_connection()
        conn.run(
            "DELETE FROM favorites WHERE user_id = :user_id AND event_id = :event_id",
            user_id=user_id, event_id=event_id
        )
        conn.run("COMMIT")

    @staticmethod
    def is_favorite(user_id, event_id):
        db = Database()
        conn = db.get_connection()
        rows = conn.run(
            "SELECT 1 FROM favorites WHERE user_id = :user_id AND event_id = :event_id",
            user_id=user_id, event_id=event_id
        )
        return len(rows) > 0
