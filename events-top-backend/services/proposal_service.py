from repositories.event_proposal_repository import EventProposalRepository
from repositories.notification_repository import NotificationRepository
from repositories.friendship_repository import FriendshipRepository
from repositories.user_repository import UserRepository

# Mappa emoji → status semantico salvato in event_proposals
EMOJI_TO_STATUS = {
    '\U0001f44d': 'accepted',   # 👍
    '\U0001f44e': 'declined',   # 👎
    '\U0001f914': 'maybe',      # 🤔
}

class ProposalService:

    @staticmethod
    def propose_event(from_user_id, to_user_id, event_id):
        friendship = FriendshipRepository.find_friendship(from_user_id, to_user_id)
        if not friendship or friendship['status'] != 'accepted':
            raise ValueError('Devi essere amico per proporre un evento')

        proposal_id = EventProposalRepository.create(from_user_id, to_user_id, event_id)

        from_user = UserRepository.find_by_id(from_user_id)
        from_username = from_user['username'] if from_user else 'Un utente'

        try:
            NotificationRepository.create({
                'user_id':      to_user_id,
                'type':         'event_proposal',
                'content':      f'{from_username} ti ha proposto un evento!',
                'related_id':   event_id,       # ← event_id per la navigazione Android
                'from_user_id': from_user_id
            })
        except Exception:
            pass  # la notifica non è critica

        return {'message': 'Proposta inviata!', 'proposal_id': proposal_id}

    @staticmethod
    def get_proposals(user_id):
        """Tutte le proposte (inviate + ricevute) — usato internamente."""
        return EventProposalRepository.find_all_for_user(user_id)

    @staticmethod
    def get_status(user_id):
        """
        Proposte inviate dall'utente con l'emoji di risposta dell'amico.
        Usato dall'endpoint GET /api/proposals/status.
        """
        return EventProposalRepository.find_sent_with_responses(user_id)

    @staticmethod
    def get_received(user_id):
        """
        Proposte ricevute ancora in attesa di risposta.
        Usato dall'endpoint GET /api/proposals/received.
        """
        all_proposals = EventProposalRepository.find_all_for_user(user_id)
        return [
            p for p in all_proposals
            if p.get('to_user_id') == user_id and p.get('status') == 'pending'
        ]

    @staticmethod
    def respond(to_user_id, event_id, emoji_string):
        """
        L'utente (to_user_id) risponde con un'emoji a una proposta
        identificata da event_id (non da proposal_id).

        emoji_string: '👍' | '👎' | '🤔'
        """
        if emoji_string not in EMOJI_TO_STATUS:
            raise ValueError("Emoji non valida. Usa 👍, 👎 o 🤔")

        proposal = EventProposalRepository.find_by_event_and_to_user(event_id, to_user_id)
        if not proposal:
            raise ValueError('Proposta non trovata o già gestita')

        status = EMOJI_TO_STATUS[emoji_string]

        # Operazione atomica: aggiorna event_proposals E inserisce in event_responses
        # in un'unica transazione — nessuna possibilità di stato parziale
        EventProposalRepository.respond_and_save(
            proposal['id'], status, to_user_id, event_id, emoji_string
        )

        # 3. Notifica l'Utente 1 (il proponente)
        to_user = UserRepository.find_by_id(to_user_id)
        to_username = to_user['username'] if to_user else 'Un amico'
        try:
            NotificationRepository.create({
                'user_id':      proposal['from_user_id'],
                'type':         'proposal_response',
                'content':      f'{to_username} ha risposto alla tua proposta: {emoji_string}',
                'related_id':   event_id,
                'from_user_id': to_user_id
            })
        except Exception:
            pass

        return {'message': f'Risposta inviata: {emoji_string}'}
