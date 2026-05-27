from datetime import datetime, timezone
from repositories.notification_repository import NotificationRepository
from repositories.event_repository import EventRepository

class NotificationsService:
    @staticmethod
    def get_notifications(user_id, unread_only=False):
        return NotificationRepository.find_by_user(user_id, unread_only)

    @staticmethod
    def mark_read(notification_id, user_id):
        NotificationRepository.mark_as_read(notification_id, user_id)
        return {'message': 'Notifica segnata come letta'}

    @staticmethod
    def mark_all_read(user_id):
        NotificationRepository.mark_all_read(user_id)
        return {'message': 'Tutte le notifiche segnate come lette'}

    @staticmethod
    def delete_notification(notification_id, user_id):
        NotificationRepository.delete(notification_id, user_id)
        return {'message': 'Notifica eliminata'}

    # ---- Promemoria eventi ----

    @staticmethod
    def set_reminder(user_id, event_id, remind_at_str):
        event = EventRepository.find_by_id(event_id)
        if not event:
            raise ValueError('Evento non trovato')

        try:
            remind_at = datetime.fromisoformat(remind_at_str.replace('Z', '+00:00'))
            if remind_at.tzinfo is None:
                remind_at = remind_at.replace(tzinfo=timezone.utc)
        except (ValueError, AttributeError):
            raise ValueError('Formato data non valido — usa ISO 8601 (es. 2025-06-01T18:00:00Z)')

        now = datetime.now(timezone.utc)
        if remind_at <= now:
            raise ValueError('La data del promemoria deve essere nel futuro')

        # Verifica che il promemoria sia entro la data dell'evento
        event_date_raw = event.get('event_date')
        if event_date_raw:
            if isinstance(event_date_raw, str):
                event_date_str = event_date_raw[:10]
                try:
                    from datetime import date
                    event_date_limit = datetime(
                        *[int(x) for x in event_date_str.split('-')], tzinfo=timezone.utc
                    )
                    # Permette promemoria fino alla fine del giorno dell'evento
                    from datetime import timedelta
                    event_date_limit = event_date_limit + timedelta(days=1)
                    if remind_at > event_date_limit:
                        raise ValueError('Il promemoria deve essere impostato entro la data dell\'evento')
                except (ValueError, TypeError):
                    pass

        reminder_id = NotificationRepository.create_reminder(user_id, event_id, remind_at)
        return {'message': 'Promemoria impostato!', 'reminder_id': reminder_id}

    @staticmethod
    def delete_reminder(user_id, event_id):
        NotificationRepository.delete_reminder(user_id, event_id)
        return {'message': 'Promemoria rimosso'}

    @staticmethod
    def get_reminders(user_id):
        return NotificationRepository.find_reminders_by_user(user_id)

    @staticmethod
    def get_reminder(user_id, event_id):
        return NotificationRepository.find_reminder(user_id, event_id)
