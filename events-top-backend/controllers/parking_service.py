# services/parking_service.py
# Business logic per la gestione dei parcheggi

from repositories.parking_repository import ParkingRepository

class ParkingService:
    """Servizio per il salvataggio e recupero dei parcheggi"""
    
    @staticmethod
    def save_parking(user_id, latitude, longitude, notes=''):
        """
        Salva un nuovo parcheggio
        
        Args:
            user_id: ID dell'utente
            latitude: Latitudine del parcheggio
            longitude: Longitudine del parcheggio
            notes: Note opzionali (es. descrizione del posto)
        """
        parking = ParkingRepository.create({
            'user_id': user_id,
            'latitude': latitude,
            'longitude': longitude,
            'notes': notes
        })
        
        return {
            'message': 'Parcheggio salvato con successo!',
            'parking': parking
        }
    
    @staticmethod
    def get_user_parkings(user_id):
        """Recupera tutti i parcheggi di un utente, ordinati per data"""
        return ParkingRepository.find_by_user(user_id)
    
    @staticmethod
    def delete_parking(parking_id, user_id):
        """
        Elimina un parcheggio (solo se appartiene all'utente)
        """
        parking = ParkingRepository.find_by_id(parking_id)
        
        if not parking:
            raise ValueError('Parcheggio non trovato')
        
        if parking['user_id'] != user_id:
            raise ValueError('Non autorizzato ad eliminare questo parcheggio')
        
        ParkingRepository.delete(parking_id)
        return {'message': 'Parcheggio eliminato con successo'}