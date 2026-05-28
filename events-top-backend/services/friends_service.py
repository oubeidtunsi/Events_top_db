from repositories.friendship_repository import FriendshipRepository
from repositories.user_repository import UserRepository
from repositories.notification_repository import NotificationRepository

class FriendsService:
    @staticmethod
    def send_request(sender_id, receiver_id):
        if sender_id == receiver_id:
            raise ValueError('Non puoi aggiungere te stesso!')
        receiver = UserRepository.find_by_id(receiver_id)
        if not receiver:
            raise ValueError('Utente non trovato')
        existing = FriendshipRepository.find_friendship(sender_id, receiver_id)
        if existing:
            if existing['status'] == 'accepted':
                raise ValueError('Siete già amici!')
            elif existing['status'] == 'pending':
                raise ValueError('Hai già inviato una richiesta a questo utente')
        FriendshipRepository.create_request(sender_id, receiver_id)
        try:
            NotificationRepository.create({
                'user_id': receiver_id,
                'type': 'friend_request',
                'content': 'Hai ricevuto una richiesta di amicizia',
                'from_user_id': sender_id
            })
        except Exception:
            pass  # notifica non critica, non blocca l'amicizia
        return {'message': 'Richiesta di amicizia inviata!'}

    @staticmethod
    def get_pending_requests(user_id):
        return FriendshipRepository.get_pending_requests(user_id)

    @staticmethod
    def respond_to_request(request_id, response):
        if response not in ('accepted', 'rejected'):
            raise ValueError("Risposta non valida. Usa 'accepted' o 'rejected'")
        FriendshipRepository.update_status(request_id, response)
        message = 'Amicizia accettata!' if response == 'accepted' else 'Richiesta rifiutata'
        return {'message': message}

    @staticmethod
    def get_friends(user_id):
        return FriendshipRepository.get_friends(user_id)
