from database import Database
from helpers.format_helper import dict_format, dict_format_single


class CouponsRepository:

    @staticmethod
    def create_coupon(code, discount_value, description=None, cost_points=100,
                      max_redemptions=None, expires_at=None):
        conn = Database().get_connection()
        rows = conn.run(
            """
            INSERT INTO coupons
                (code, discount_value, description, cost_points, max_redemptions, expires_at,
                 is_active, redemption_count)
            VALUES
                (:code, :discount_value, :description, :cost_points, :max_redemptions, :expires_at,
                 TRUE, 0)
            RETURNING id
            """,
            code=code,
            discount_value=discount_value,
            description=description,
            cost_points=cost_points,
            max_redemptions=max_redemptions,
            expires_at=expires_at,
        )
        conn.run("COMMIT")
        return rows[0][0]

    @staticmethod
    def find_by_code(code):
        conn = Database().get_connection()
        rows = conn.run(
            "SELECT * FROM coupons WHERE code = :code",
            code=code,
        )
        return dict_format_single(conn, rows)

    @staticmethod
    def find_active_coupons():
        conn = Database().get_connection()
        rows = conn.run(
            """
            SELECT * FROM coupons
            WHERE is_active = TRUE
            ORDER BY id ASC
            """
        )
        return dict_format(conn, rows)

    @staticmethod
    def check_user_redemption(user_id, coupon_id):
        conn = Database().get_connection()
        rows = conn.run(
            """
            SELECT id FROM coupon_redemptions
            WHERE user_id = :user_id AND coupon_id = :coupon_id
            """,
            user_id=user_id,
            coupon_id=coupon_id,
        )
        return len(rows) > 0

    @staticmethod
    def redeem_coupon(user_id, coupon_id):
        conn = Database().get_connection()
        rows = conn.run(
            """
            INSERT INTO coupon_redemptions (user_id, coupon_id, redeemed_at, email_sent)
            VALUES (:user_id, :coupon_id, NOW(), FALSE)
            RETURNING id
            """,
            user_id=user_id,
            coupon_id=coupon_id,
        )
        conn.run(
            """
            UPDATE coupons
            SET redemption_count = COALESCE(redemption_count, 0) + 1
            WHERE id = :coupon_id
            """,
            coupon_id=coupon_id,
        )
        conn.run("COMMIT")
        return rows[0][0]

    @staticmethod
    def mark_email_sent(redemption_id):
        conn = Database().get_connection()
        conn.run(
            "UPDATE coupon_redemptions SET email_sent = TRUE WHERE id = :id",
            id=redemption_id,
        )
        conn.run("COMMIT")

    @staticmethod
    def get_user_redemptions(user_id):
        conn = Database().get_connection()
        rows = conn.run(
            """
            SELECT
                cr.id,
                cr.redeemed_at,
                cr.email_sent,
                c.code,
                c.discount_value,
                c.description
            FROM coupon_redemptions cr
            JOIN coupons c ON c.id = cr.coupon_id
            WHERE cr.user_id = :user_id
            ORDER BY cr.redeemed_at DESC
            """,
            user_id=user_id,
        )
        return dict_format(conn, rows)
