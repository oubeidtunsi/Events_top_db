from datetime import date
from database import Database
from repositories.review_repository import ReviewRepository
from repositories.event_repository import EventRepository


class ReviewsService:
    @staticmethod
    def add_review(user_id, event_id, rating, comment, replica_id=None):
        if rating < 1 or rating > 5:
            raise ValueError('Rating tra 1 e 5')

        event = EventRepository.find_by_id(event_id)
        if not event:
            raise ValueError('Evento non trovato')

        ReviewsService._check_event_occurred(event_id, event, replica_id)

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
    def _check_event_occurred(event_id, event, replica_id=None):
        """Lancia ValueError se nessuna occorrenza dell'evento è già avvenuta.

        Logica:
        1. Se replica_id è fornito, verifica che quella specifica replica sia passata.
        2. Altrimenti conta le repliche con show_date <= NOW().
        3. Se almeno una → evento avvenuto, ok.
        4. Se zero repliche passate → fallback su event_date legacy.
           - event_date nel futuro → blocca.
           - event_date nel passato o assente → consenti (dati incompleti, non punire l'utente).
        """
        conn = Database().get_connection()

        if replica_id:
            rows = conn.run(
                "SELECT show_date FROM event_replicas "
                "WHERE id = :rid AND event_id = :eid",
                rid=replica_id, eid=event_id
            )
            if not rows:
                raise ValueError('Replica non valida per questo evento')
            from datetime import datetime as _dt
            show_dt_raw = rows[0][0]
            # show_dt_raw può essere un datetime Python oppure una stringa ISO
            if isinstance(show_dt_raw, str):
                show_dt = _dt.fromisoformat(show_dt_raw[:19])
            else:
                show_dt = show_dt_raw
            if show_dt > _dt.utcnow():
                raise ValueError(
                    f"Non puoi recensire uno spettacolo non ancora avvenuto "
                    f"({show_dt.strftime('%d/%m/%Y %H:%M')})"
                )
            return

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
