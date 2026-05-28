from datetime import datetime, timezone, timedelta
from database import Database
from repositories.notification_repository import NotificationRepository
from repositories.event_repository import EventRepository


class RemindersService:
    @staticmethod
    def get_reminders(user_id):
        return NotificationRepository.find_reminders_by_user(user_id)

    @staticmethod
    def create_reminder(user_id, event_id, remind_at_str):
        event = EventRepository.find_by_id(event_id)
        if not event:
            raise ValueError('Evento non trovato')

        try:
            remind_at = datetime.fromisoformat(remind_at_str.replace('Z', '+00:00'))
            if remind_at.tzinfo is None:
                remind_at = remind_at.replace(tzinfo=timezone.utc)
        except (ValueError, AttributeError):
            raise ValueError('Formato data non valido — usa ISO 8601 (es. 2025-06-01T18:00:00)')

        if remind_at <= datetime.now(timezone.utc):
            raise ValueError('La data del promemoria deve essere nel futuro')

        RemindersService._check_remind_before_event(event_id, event, remind_at)

        reminder_id = NotificationRepository.create_reminder(user_id, event_id, remind_at)
        return {'message': 'Promemoria impostato!', 'reminder_id': reminder_id}

    @staticmethod
    def _check_remind_before_event(event_id, event, remind_at):
        """Lancia ValueError se remind_at supera la scadenza dell'evento.

        Logica:
        1. Cerca la prossima show_date futura da event_replicas → usa quella come deadline.
        2. Se nessuna replica futura esiste → fallback su event_date legacy.
        3. Se nessuna data disponibile → salta il controllo (non bloccare l'utente).
        Deadline = data evento + 1 giorno (margine operativo).
        """
        conn = Database().get_connection()
        row = conn.run(
            "SELECT MIN(show_date) FROM event_replicas "
            "WHERE event_id = :eid AND show_date > NOW()",
            eid=event_id
        )
        next_show = row[0][0] if row and row[0][0] else None

        if next_show is not None:
            if next_show.tzinfo is None:
                next_show = next_show.replace(tzinfo=timezone.utc)
            deadline = next_show + timedelta(days=1)
            if remind_at > deadline:
                raise ValueError("Il promemoria deve essere impostato entro la data dell'evento")
            return

        # Fallback su event_date legacy
        event_date_raw = event.get('event_date')
        if not event_date_raw:
            return  # nessuna data disponibile, non blocchiamo

        try:
            date_str = str(event_date_raw)[:10]
            parts = [int(x) for x in date_str.split('-')]
            deadline = datetime(*parts, tzinfo=timezone.utc) + timedelta(days=1)
            if remind_at > deadline:
                raise ValueError("Il promemoria deve essere impostato entro la data dell'evento")
        except (ValueError, TypeError):
            pass

    @staticmethod
    def delete_reminder(user_id, reminder_id):
        NotificationRepository.delete_reminder_by_id(user_id, reminder_id)
        return {'message': 'Promemoria rimosso'}
