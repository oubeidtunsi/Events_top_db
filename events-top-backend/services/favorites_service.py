import traceback
from repositories.favorite_repository import FavoriteRepository
from repositories.event_repository import EventRepository

class FavoritesService:
    @staticmethod
    def add_favorite(user_id, event_id):
        event = EventRepository.find_by_id(event_id)
        if not event:
            raise ValueError('Evento non trovato')
        FavoriteRepository.add(user_id, event_id)
        return {'message': 'Evento aggiunto ai preferiti!'}

    @staticmethod
    def remove_favorite(user_id, event_id):
        FavoriteRepository.remove(user_id, event_id)
        return {'message': 'Evento rimosso dai preferiti'}

    @staticmethod
    def get_favorites(user_id):
        # Il filtro title è già applicato nel repository — nessuna ridondanza qui
        try:
            return FavoriteRepository.find_by_user(user_id)
        except Exception as e:
            print(f"❌ FavoritesService.get_favorites(user_id={user_id!r})"
                  f" — {type(e).__name__}: {e}")
            traceback.print_exc()
            return []

    @staticmethod
    def is_favorite(user_id, event_id):
        return FavoriteRepository.is_favorite(user_id, event_id)