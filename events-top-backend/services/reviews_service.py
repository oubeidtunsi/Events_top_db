from datetime import date
from database import Database
from repositories.review_repository import ReviewRepository
from repositories.event_repository import EventRepository


class ReviewsService:
    @staticmethod
    def add_review(user_id, event_id, rating, comment):
        if rating < 1 or rating > 5:
            raise ValueError('Rating tra 1 e 5')

        event = EventRepository.find_by_id(event_id)
        if not event:
            raise ValueError('Evento non trovato')

        ReviewsService._check_event_occurred(event_id, event)

        existing = ReviewRepository.find_by_user_and_event(user_id, event_id)
        if existing:
            raise ValueError('Hai già recensito questo evento')

        review = ReviewRepository.create({
            'user_id':  user_id,
            'event_id': event_id,
            'rating':   rating,
            'comment':  comment,
        })
        return {'message': 'Recensione aggiunta!', 'review': review}

    @staticmethod
    def _check_event_occurred(event_id, event):
        """Lancia ValueError se nessuna occorrenza dell'evento è già avvenuta.

        Logica:
        1. Conta le repliche con show_date <= NOW().
        2. Se almeno una → evento avvenuto, ok.
        3. Se zero repliche passate → fallback su event_date legacy.
           - event_date nel futuro → blocca.
           - event_date nel passato o assente → consenti (dati incompleti, non punire l'utente).
        """
        conn = Database().get_connection()
        past_count = conn.run(
            "SELECT COUNT(*) FROM event_replicas "
            "WHERE event_id = :eid AND show_date <= NOW()",
            eid=event_id
        )[0][0]

        if past_count > 0:
            return  # almeno una replica già avvenuta

        # Nessuna replica passata: controlla event_date legacy
        event_date_raw = event.get('event_date')
        if not event_date_raw:
            return  # nessuna data disponibile, non blocchiamo

        try:
            event_date = date.fromisoformat(str(event_date_raw)[:10])
            if event_date > date.today():
                raise ValueError(
                    f"Non puoi recensire un evento non ancora avvenuto "
                    f"(data evento: {event_date.strftime('%d/%m/%Y')})"
                )
        except ValueError:
            raise  # rilancia sia "Non puoi recensire" che errori di parsing

    @staticmethod
    def delete_review(user_id, review_id):
        ReviewRepository.delete(review_id, user_id)
        return {'message': 'Recensione eliminata'}

    @staticmethod
    def get_event_reviews(event_id):
        return ReviewRepository.find_by_event(event_id)

    @staticmethod
    def get_user_reviews(user_id):
        return ReviewRepository.find_by_user(user_id)
