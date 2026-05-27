from database import Database
from helpers.format_helper import dict_format, dict_format_single

class ParkingRepository:
    @staticmethod
    def create(parking_data):
        db = Database()
        conn = db.get_connection()
        rows = conn.run(
            """INSERT INTO parking_spots (user_id, latitude, longitude, notes) 
               VALUES (:uid, :lat, :lng, :notes) RETURNING *""",
            uid=parking_data['user_id'], lat=parking_data['latitude'],
            lng=parking_data['longitude'], notes=parking_data['notes']
        )
        conn.run("COMMIT")
        return dict_format_single(conn, rows)
    
    @staticmethod
    def find_by_user(user_id):
        db = Database()
        conn = db.get_connection()
        rows = conn.run("SELECT * FROM parking_spots WHERE user_id = :uid ORDER BY saved_at DESC", uid=user_id)
        return dict_format(conn, rows)
    
    @staticmethod
    def delete(parking_id):
        db = Database()
        conn = db.get_connection()
        conn.run("DELETE FROM parking_spots WHERE id = :id", id=parking_id)
        conn.run("COMMIT")