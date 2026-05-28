from repositories.location_repository import LocationRepository


class LocationService:

    @staticmethod
    def get_locations(city=None, region=None, name=None):
        return LocationRepository.find_all(city, region, name=name)

    @staticmethod
    def get_location_detail(location_id, include_past=False):
        loc = LocationRepository.find_by_id(location_id, include_past=include_past)
        if not loc:
            raise ValueError('Location non trovata')
        return loc
