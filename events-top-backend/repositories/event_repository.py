from database import Database
from helpers.format_helper import dict_format, dict_format_single


class EventRepository:

    @staticmethod
    def search(city=None, category=None, date=None, query=None, location_id=None,
               only_upcoming=False, start_date=None, end_date=None, include_past=False):
        db = Database()
        conn = db.get_connection()
        params = {}

        # Teatro (location_id presente): comanda solo include_past.
        # Ricerca globale: real_include_past unisce include_past e only_upcoming.
        if location_id:
            real_include_past = include_past
        else:
            real_include_past = include_past or (not only_upcoming)

        # EXISTS clause: per il teatro costruiamo prima location + data opzionale,
        # così con real_include_past=True si controlla solo l'esistenza nel teatro
        # senza alcun vincolo temporale.
        if location_id:
            params['loc_id'] = location_id
            exists_parts = ["eri.event_id = e.id", "eri.location_id = :loc_id"]
            if not real_include_past:
                exists_parts.append("eri.show_date >= NOW()")
        else:
            exists_parts = ["eri.event_id = e.id"]
            if not real_include_past:
                exists_parts.append("eri.show_date >= NOW()")
        if date:
            exists_parts.append("eri.show_date::date = :date")
            params['date'] = date
        if start_date:
            exists_parts.append("eri.show_date::date >= :start_date")
            params['start_date'] = start_date
        if end_date:
            exists_parts.append("eri.show_date::date <= :end_date")
            params['end_date'] = end_date

        exists_where = " AND ".join(exists_parts)
        exists_clause = (
            f"AND EXISTS (SELECT 1 FROM event_replicas eri WHERE {exists_where})"
            if len(exists_parts) > 1 else ""
        )

        # Replica display filter: controlla quali repliche finiscono nel JSON.
        display_parts = ["eri.event_id = e.id"]
        if not real_include_past:
            display_parts.append("eri.show_date >= NOW()")
        if location_id:
            display_parts.append("eri.location_id = :loc_id")
        if start_date:
            display_parts.append("eri.show_date::date >= :start_date")
        if end_date:
            display_parts.append("eri.show_date::date <= :end_date")
        display_where = " AND ".join(display_parts)

        # Frammenti per next_show_date e ORDER BY, pilotati da real_include_past.
        _n_loc  = "AND eri_n.location_id = :loc_id"  if location_id else ""
        _n2_loc = "AND eri_n2.location_id = :loc_id" if location_id else ""
        _o_loc  = "AND eri_o.location_id = :loc_id"  if location_id else ""
        if real_include_past:
            _n_date  = ""
            _n2_date = ""
            _n_ord   = "DESC"
            _o_date  = ""
            _o_agg   = "MAX"
            _o_dir   = "DESC"
        else:
            _n_date  = "AND eri_n.show_date >= NOW()"
            _n2_date = "AND eri_n2.show_date >= NOW()"
            _n_ord   = "ASC"
            _o_date  = "AND eri_o.show_date >= NOW()"
            _o_agg   = "MIN"
            _o_dir   = "ASC NULLS LAST"

        sql = f"""
            SELECT
                e.id,
                e.slug,
                e.title,
                e.title_eng,
                e.description,
                e.description_eng,
                e.category,
                e.duration,
                e.info_url_it,
                e.info_url_eng,
                COALESCE(
                    (SELECT json_agg(json_build_object('url', ei.url, 'alt', ei.alt)
                             ORDER BY ei.image_order)
                     FROM event_images ei
                     WHERE ei.event_id = e.id), '[]'
                ) AS images,
                ROUND(COALESCE(
                    (SELECT AVG(r.rating)::numeric FROM reviews r WHERE r.event_id = e.id), 0
                ), 1) AS avg_rating,
                (SELECT COUNT(*) FROM reviews r WHERE r.event_id = e.id) AS review_count,
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'id',                 eri.id,
                        'show_date',          eri.show_date,
                        'ticket_url',         eri.ticket_url,
                        'location_id',        eri.location_id,
                        'location_name',      li.name,
                        'location_city',      li.city,
                        'location_image_est', li.image_est,
                        'location_image_int', li.image_int,
                        'is_past',            eri.show_date < NOW()
                    ) ORDER BY eri.show_date)
                    FROM event_replicas eri
                    JOIN locations li ON li.id = eri.location_id
                    WHERE {display_where}
                ), '[]') AS replicas,
                (SELECT eri_n.show_date
                 FROM event_replicas eri_n
                 WHERE eri_n.event_id = e.id {_n_loc} {_n_date}
                 ORDER BY eri_n.show_date {_n_ord} LIMIT 1) AS next_show_date,
                (SELECT li_n.name
                 FROM event_replicas eri_n2
                 JOIN locations li_n ON li_n.id = eri_n2.location_id
                 WHERE eri_n2.event_id = e.id {_n2_loc} {_n2_date}
                 ORDER BY eri_n2.show_date {_n_ord} LIMIT 1) AS next_location_name
            FROM events e
            WHERE 1=1
            {exists_clause}
        """

        if query:
            sql += (
                " AND (LOWER(e.title) LIKE LOWER(:q)"
                " OR LOWER(e.description) LIKE LOWER(:q)"
                " OR LOWER(COALESCE(e.title_eng, '')) LIKE LOWER(:q))"
            )
            params['q'] = f"%{query}%"
        if category:
            sql += " AND LOWER(e.category) = LOWER(:cat)"
            params['cat'] = category
        if city:
            sql += " AND LOWER(e.city) = LOWER(:city)"
            params['city'] = city

        sql += f"""
            ORDER BY (
                SELECT {_o_agg}(eri_o.show_date)
                FROM event_replicas eri_o
                WHERE eri_o.event_id = e.id {_o_loc} {_o_date}
            ) {_o_dir}, e.id ASC
        """

        rows = conn.run(sql, **params)
        return dict_format(conn, rows)

    @staticmethod
    def find_by_id(event_id, include_past=False):
        db = Database()
        conn = db.get_connection()

        date_filter = "" if include_past else "AND eri.show_date >= NOW()"

        sql = f"""
            SELECT
                e.id,
                e.slug,
                e.title,
                e.title_eng,
                e.description,
                e.description_eng,
                e.category,
                e.duration,
                e.info_url_it,
                e.info_url_eng,
                COALESCE(
                    (SELECT json_agg(json_build_object('url', ei.url, 'alt', ei.alt)
                             ORDER BY ei.image_order)
                     FROM event_images ei
                     WHERE ei.event_id = e.id), '[]'
                ) AS images,
                ROUND(COALESCE(
                    (SELECT AVG(r.rating)::numeric FROM reviews r WHERE r.event_id = e.id), 0
                ), 1) AS avg_rating,
                (SELECT COUNT(*) FROM reviews r WHERE r.event_id = e.id) AS review_count,
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'id',                 eri.id,
                        'show_date',          eri.show_date,
                        'ticket_url',         eri.ticket_url,
                        'location_id',        eri.location_id,
                        'location_name',      li.name,
                        'location_city',      li.city,
                        'location_image_est', li.image_est,
                        'location_image_int', li.image_int,
                        'is_past',            eri.show_date < NOW()
                    ) ORDER BY eri.show_date)
                    FROM event_replicas eri
                    JOIN locations li ON li.id = eri.location_id
                    WHERE eri.event_id = e.id
                    {date_filter}
                ), '[]') AS replicas
            FROM events e
            WHERE e.id = :id
        """
        rows = conn.run(sql, id=event_id)
        return dict_format_single(conn, rows)

    @staticmethod
    def get_images(event_id):
        db = Database()
        conn = db.get_connection()
        return conn.run(
            "SELECT * FROM event_images WHERE event_id = :id ORDER BY image_order",
            id=event_id
        )
