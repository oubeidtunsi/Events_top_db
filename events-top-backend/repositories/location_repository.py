from database import Database
from helpers.format_helper import dict_format, dict_format_single


class LocationRepository:

    _BASE_SELECT = """
        SELECT
            l.id,
            l.slug,
            l.name,
            l.address,
            l.city,
            l.region,
            l.latitude,
            l.longitude,
            l.capacity,
            l.services,
            l.services_it,
            l.link,
            l.image_est,
            l.image_int,
            l.floor_plan,
            l.description_it,
            l.description_en
        FROM locations l
        WHERE 1=1
    """

    @staticmethod
    def find_all(city=None, region=None, name=None):
        db   = Database()
        conn = db.get_connection()

        query  = LocationRepository._BASE_SELECT
        params = {}

        if name:
            query += " AND LOWER(l.name) LIKE LOWER(:name)"
            params['name'] = f'%{name}%'
        if city:
            query += " AND LOWER(l.city) = LOWER(:city)"
            params['city'] = city
        if region:
            query += " AND LOWER(l.region) = LOWER(:region)"
            params['region'] = region

        query += " ORDER BY l.name"

        rows = conn.run(query, **params)
        return dict_format(conn, rows)

    @staticmethod
    def find_by_id(location_id, include_past=False):
        db   = Database()
        conn = db.get_connection()

        date_filter = "" if include_past else "AND er.show_date >= NOW()"

        query = f"""
            SELECT
                l.id,
                l.slug,
                l.name,
                l.address,
                l.city,
                l.region,
                l.latitude,
                l.longitude,
                l.capacity,
                l.services,
                l.services_it,
                l.link,
                l.image_est,
                l.image_int,
                l.floor_plan,
                l.description_it,
                l.description_en,
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'replica_id',      er.id,
                        'event_id',        er.event_id,
                        'event_title',     e.title,
                        'event_title_eng', e.title_eng,
                        'event_category',  e.category,
                        'event_duration',  e.duration,
                        'show_date',       er.show_date,
                        'ticket_url',      er.ticket_url,
                        'is_past',         er.show_date < NOW()
                    ) ORDER BY er.show_date)
                    FROM event_replicas er
                    JOIN events e ON e.id = er.event_id
                    WHERE er.location_id = l.id
                    {date_filter}
                ), '[]') AS events
            FROM locations l
            WHERE l.id = :id
        """
        rows = conn.run(query, id=location_id)
        return dict_format_single(conn, rows)
