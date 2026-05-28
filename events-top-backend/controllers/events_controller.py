from flask import Blueprint, request, jsonify
from services.event_service import EventService
from database import Database
from helpers.format_helper import dict_format, dict_format_single
import traceback

events_bp = Blueprint('events', __name__)


# ── DASHBOARD: GET lista ─────────────────────────────────────────────────────

@events_bp.route('/', methods=['GET'], strict_slashes=False)
def get_events():
    """Dashboard — lista eventi con tutti i campi schema + repliche aggregate."""
    try:
        conn = Database().get_connection()
        sql  = """
            SELECT
                e.id,
                e.slug,
                e.title,
                e.title_eng,
                e.category,
                e.description,
                e.description_eng,
                e.duration,
                e.info_url_it,
                e.info_url_eng,
                e.location_id,
                e.event_date,
                COALESCE((
                    SELECT json_agg(json_build_object(
                        'id',            eri.id,
                        'show_date',     to_char(eri.show_date, 'YYYY-MM-DD HH24:MI'),
                        'ticket_url',    eri.ticket_url,
                        'location_id',   eri.location_id,
                        'location_name', li.name,
                        'location_city', li.city,
                        'is_past',       eri.show_date < NOW()
                    ) ORDER BY eri.show_date ASC)
                    FROM event_replicas eri
                    JOIN locations li ON li.id = eri.location_id
                    WHERE eri.event_id = e.id
                ), '[]'::json) AS replicas,
                (SELECT to_char(MIN(eri.show_date), 'YYYY-MM-DD HH24:MI')
                 FROM event_replicas eri
                 WHERE eri.event_id = e.id AND eri.show_date >= NOW()
                ) AS next_show_date,
                (SELECT li.name
                 FROM event_replicas eri
                 JOIN locations li ON li.id = eri.location_id
                 WHERE eri.event_id = e.id AND eri.show_date >= NOW()
                 ORDER BY eri.show_date ASC LIMIT 1
                ) AS next_location_name
            FROM events e
            WHERE 1=1
        """
        params   = {}
        title    = request.args.get('title')
        city     = request.args.get('city')
        category = request.args.get('category')

        if title:
            sql += """ AND (
                LOWER(e.title) LIKE LOWER(:title)
                OR LOWER(COALESCE(e.title_eng, '')) LIKE LOWER(:title)
            )"""
            params['title'] = f'%{title}%'
        if city:
            sql += """ AND (
                LOWER(e.city) = LOWER(:city)
                OR EXISTS (
                    SELECT 1 FROM event_replicas eri
                    JOIN locations li ON li.id = eri.location_id
                    WHERE eri.event_id = e.id AND LOWER(li.city) = LOWER(:city)
                )
            )"""
            params['city'] = city
        if category:
            sql += " AND LOWER(e.category) = LOWER(:category)"
            params['category'] = category

        sql += """
            ORDER BY (
                SELECT MIN(eri.show_date) FROM event_replicas eri
                WHERE eri.event_id = e.id AND eri.show_date >= NOW()
            ) ASC NULLS LAST, e.event_date DESC"""

        rows   = conn.run(sql, **params)
        events = dict_format(conn, rows)
        return jsonify({'events': events}), 200
    except Exception:
        traceback.print_exc()
        return jsonify({'error': 'Errore nel recupero eventi'}), 500


# ── DASHBOARD: POST crea ─────────────────────────────────────────────────────

@events_bp.route('/', methods=['POST'], strict_slashes=False)
def create_event():
    """Dashboard — crea un evento con tutti i campi schema e le sue repliche."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Body JSON obbligatorio'}), 400

        required = ('title', 'slug', 'category', 'description')
        missing  = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({'error': f'Campi obbligatori: {", ".join(missing)}'}), 400

        replicas = data.get('replicas') or []
        # backward-compat: corpo piatto con date/location_id
        if not replicas and data.get('date') and data.get('location_id'):
            replicas = [{
                'location_id': data['location_id'],
                'date':        data['date'],
                'time':        data.get('time') or '00:00',
                'ticket_url':  data.get('ticket_url'),
            }]

        conn = Database().get_connection()

        id_row          = conn.run("SELECT COALESCE(MAX(id), 0) + 1 FROM events")
        new_id          = id_row[0][0]
        prod_row        = conn.run("SELECT id FROM productions LIMIT 1")
        default_prod_id = prod_row[0][0] if prod_row else 1

        primary_loc_id = int(replicas[0]['location_id']) if replicas else (
            int(data['location_id']) if data.get('location_id') else None
        )
        city = ''
        if primary_loc_id:
            loc_row = conn.run("SELECT city FROM locations WHERE id = :id", id=primary_loc_id)
            if not loc_row:
                return jsonify({'error': 'Location non trovata'}), 404
            city = loc_row[0][0]

        primary_date = replicas[0]['date'] if replicas else data.get('date') or None

        conn.run(
            """
            INSERT INTO events
                (id, slug, production_id, location_id, title, title_eng,
                 description, description_eng, category, city, event_date,
                 duration, info_url_it, info_url_eng)
            VALUES
                (:id, :slug, :production_id, :location_id, :title, :title_eng,
                 :description, :description_eng, :category, :city, :event_date,
                 :duration, :info_url_it, :info_url_eng)
            """,
            id=new_id,
            slug=data['slug'],
            production_id=data.get('production_id') or default_prod_id,
            location_id=primary_loc_id,
            title=data['title'],
            title_eng=data.get('title_eng')       or None,
            description=data['description'],
            description_eng=data.get('description_eng') or None,
            category=data['category'],
            city=city,
            event_date=primary_date,
            duration=data.get('duration')         or None,
            info_url_it=data.get('info_url_it')   or None,
            info_url_eng=data.get('info_url_eng') or None,
        )

        if replicas:
            r_id_row  = conn.run("SELECT COALESCE(MAX(id), 0) + 1 FROM event_replicas")
            next_r_id = r_id_row[0][0]
            for i, rep in enumerate(replicas):
                time_part = rep.get('time') or '00:00'
                show_dt   = f"{rep['date']} {time_part}:00"
                conn.run(
                    """
                    INSERT INTO event_replicas (id, event_id, location_id, show_date, ticket_url)
                    VALUES (:id, :event_id, :location_id, :show_date, :ticket_url)
                    """,
                    id=next_r_id + i,
                    event_id=new_id,
                    location_id=int(rep['location_id']),
                    show_date=show_dt,
                    ticket_url=rep.get('ticket_url') or None,
                )

        conn.run("COMMIT")
        return jsonify({'message': 'Evento creato', 'id': new_id}), 201
    except Exception:
        traceback.print_exc()
        return jsonify({'error': 'Errore nella creazione evento'}), 500


# ── DASHBOARD: PUT aggiorna ──────────────────────────────────────────────────

@events_bp.route('/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    """Dashboard — aggiorna campi base evento; se 'replicas' presente, sostituisce tutte le repliche."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Body JSON obbligatorio'}), 400

        field_map = {
            'title':           'title',
            'title_eng':       'title_eng',
            'slug':            'slug',
            'category':        'category',
            'date':            'event_date',
            'duration':        'duration',
            'description':     'description',
            'description_eng': 'description_eng',
            'location_id':     'location_id',
            'info_url_it':     'info_url_it',
            'info_url_eng':    'info_url_eng',
        }

        sets   = []
        params = {'ev_id': event_id}

        for html_key, col in field_map.items():
            if html_key in data:
                pk = f'v_{col}'
                sets.append(f"{col} = :{pk}")
                params[pk] = data[html_key] if data[html_key] != '' else None

        conn = Database().get_connection()

        if sets:
            if 'v_location_id' in params and params['v_location_id']:
                loc_row = conn.run("SELECT city FROM locations WHERE id = :id",
                                   id=int(params['v_location_id']))
                if loc_row:
                    sets.append("city = :v_city")
                    params['v_city'] = loc_row[0][0]
            conn.run(f"UPDATE events SET {', '.join(sets)} WHERE id = :ev_id", **params)

        # Se 'replicas' è presente, sostituisce interamente le repliche (delete + re-insert)
        replicas = data.get('replicas')
        if replicas is not None:
            conn.run("DELETE FROM event_replicas WHERE event_id = :id", id=event_id)
            if replicas:
                r_id_row  = conn.run("SELECT COALESCE(MAX(id), 0) + 1 FROM event_replicas")
                next_r_id = r_id_row[0][0]
                for i, rep in enumerate(replicas):
                    time_part = rep.get('time') or '00:00'
                    show_dt   = f"{rep['date']} {time_part}:00"
                    conn.run(
                        """
                        INSERT INTO event_replicas (id, event_id, location_id, show_date, ticket_url)
                        VALUES (:id, :event_id, :location_id, :show_date, :ticket_url)
                        """,
                        id=next_r_id + i,
                        event_id=event_id,
                        location_id=int(rep['location_id']),
                        show_date=show_dt,
                        ticket_url=rep.get('ticket_url') or None,
                    )

        conn.run("COMMIT")
        return jsonify({'message': 'Evento aggiornato'}), 200
    except Exception:
        traceback.print_exc()
        return jsonify({'error': "Errore nell'aggiornamento evento"}), 500


# ── DASHBOARD: DELETE ────────────────────────────────────────────────────────

@events_bp.route('/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Dashboard — elimina evento e pulizia tabelle senza CASCADE."""
    try:
        conn = Database().get_connection()
        conn.run("DELETE FROM event_proposals WHERE event_id = :id", id=event_id)
        conn.run("DELETE FROM event_replicas  WHERE event_id = :id", id=event_id)
        conn.run("DELETE FROM events          WHERE id       = :id", id=event_id)
        conn.run("COMMIT")
        return jsonify({'message': 'Evento eliminato'}), 200
    except Exception:
        traceback.print_exc()
        return jsonify({'error': "Errore nell'eliminazione evento"}), 500


# ── APP: search + detail (usati dall'app mobile) ─────────────────────────────

@events_bp.route('/search', methods=['GET'])
def search_events():
    try:
        city          = request.args.get('city')
        category      = request.args.get('category')
        date          = request.args.get('date')
        query         = request.args.get('query')
        loc_raw       = request.args.get('location_id')
        location_id   = int(loc_raw) if loc_raw and loc_raw.isdigit() else None
        only_upcoming = request.args.get('only_upcoming', 'false').lower() == 'true'
        include_past  = request.args.get('include_past',  'false').lower() == 'true'
        start_date    = request.args.get('start_date') or None
        end_date      = request.args.get('end_date') or None

        events = EventService.search_events(
            city, category, date, query, location_id,
            only_upcoming, start_date, end_date, include_past
        )
        return jsonify({'events': events}), 200
    except Exception:
        traceback.print_exc()
        return jsonify({'error': 'Errore nella ricerca eventi'}), 500


@events_bp.route('/<int:event_id>', methods=['GET'])
def get_event(event_id):
    try:
        include_past = request.args.get('include_past', 'false').lower() == 'true'
        event = EventService.get_event_detail(event_id, include_past=include_past)
        return jsonify({'event': event}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception:
        traceback.print_exc()
        return jsonify({'error': 'Errore nel caricamento evento'}), 500
