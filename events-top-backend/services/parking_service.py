# services/parking_service.py
from repositories.parking_repository import ParkingRepository

class ParkingService:
    @staticmethod
    def save_parking(user_id, latitude, longitude, notes=''):
        parking = ParkingRepository.create({
            'user_id': user_id,
            'latitude': latitude,
            'longitude': longitude,
            'notes': notes
        })
        
        return {
            'message': 'Parcheggio salvato!',
            'parking': parking
        }
    
    @staticmethod
    def get_user_parkings(user_id):
        return ParkingRepository.find_by_user(user_id)
    
    @staticmethod
    def delete_parking(parking_id, user_id):
        parking = ParkingRepository.find_by_id(parking_id)
        
        if not parking:
            raise ValueError('Parcheggio non trovato')
        
        if parking['user_id'] != user_id:
            raise ValueError('Non autorizzato')
        
        ParkingRepository.delete(parking_id)
        return {'message': 'Parcheggio eliminato'}