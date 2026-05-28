from flask import Blueprint, request, jsonify
from services.location_service import LocationService
from database import Database
from helpers.format_helper import dict_format, dict_format_single
import traceback

locations_bp = Blueprint('locations', __name__)


# ── HELPER ───────────────────────────────────────────────────────────────────

def _pg_array(lst):
    """Python list → PostgreSQL TEXT[] literal.  ['a', 'b c'] → '{a,"b c"}'"""
    if not isinstance(lst, list) or not lst:
        return '{}'
    parts = []
    for item in lst:
        s = str(item)
        if any(c in s for c in (',', '"', '{', '}', ' ')):
            s = '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
        parts.append(s)
    return '{' + ','.join(parts) + '}'


# ── ROUTES ───────────────────────────────────────────────────────────────────

@locations_bp.route('/', methods=['GET'], strict_slashes=False)
def get_locations():
    city   = request.args.get('city')
    region = request.args.get('region')
    name   = request.args.get('name')
    locations = LocationService.get_locations(city, region, name=name)
    return jsonify({'locations': locations}), 200


@locations_bp.route('/<int:location_id>', methods=['GET'])
def get_location(location_id):
    try:
        include_past = request.args.get('include_past', 'false').lower() == 'true'
        location = LocationService.get_location_detail(location_id, include_past=include_past)
        return jsonify(location), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


# ── DASHBOARD: POST crea ─────────────────────────────────────────────────────

@locations_bp.route('/', methods=['POST'], strict_slashes=False)
def create_location():
    """Dashboard — crea una nuova location con tutti i campi schema."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Body JSON obbligatorio'}), 400

        required = ('name', 'slug', 'city', 'region', 'address')
        missing  = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({'error': f'Campi obbligatori: {", ".join(missing)}'}), 400

        services_val    = _pg_array(data.get('services')    or [])
        services_it_val = _pg_array(data.get('services_it') or [])

        conn   = Database().get_connection()
        id_row = conn.run("SELECT COALESCE(MAX(id), 0) + 1 FROM locations")
        new_id = id_row[0][0]

        conn.run(
            """
            INSERT INTO locations
                (id, slug, name, address, city, region,
                 latitude, longitude, capacity,
                 services, services_it,
                 link, image_est, image_int, floor_plan,
                 description_it, description_en)
            VALUES
                (:id, :slug, :name, :address, :city, :region,
                 :latitude, :longitude, :capacity,
                 :services, :services_it,
                 :link, :image_est, :image_int, :floor_plan,
                 :description_it, :description_en)
            """,
            id=new_id,
            slug=data['slug'],
            name=data['name'],
            address=data['address'],
            city=data['city'],
            region=data['region'],
            latitude=data.get('latitude')          or None,
            longitude=data.get('longitude')        or None,
            capacity=data.get('capacity')          or None,
            services=services_val,
            services_it=services_it_val,
            link=data.get('website')               or None,
            image_est=data.get('img_exterior')     or None,
            image_int=data.get('img_interior')     or None,
            floor_plan=data.get('floor_plan_url')  or None,
            description_it=data.get('description_it') or None,
            description_en=data.get('description_en') or None,
        )
        conn.run("COMMIT")
        return jsonify({'message': 'Location creata', 'id': new_id}), 201
    except Exception:
        traceback.print_exc()
        return jsonify({'error': 'Errore nella creazione location'}), 500


# ── DASHBOARD: PUT aggiorna ──────────────────────────────────────────────────

@locations_bp.route('/<int:location_id>', methods=['PUT'])
def update_location(location_id):
    """Dashboard — aggiorna i campi di una location (tutti i campi schema)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Body JSON obbligatorio'}), 400

        field_map = {
            'name':           'name',
            'slug':           'slug',
            'address':        'address',
            'city':           'city',
            'region':         'region',
            'latitude':       'latitude',
            'longitude':      'longitude',
            'capacity':       'capacity',
            'website':        'link',
            'img_exterior':   'image_est',
            'img_interior':   'image_int',
            'floor_plan_url': 'floor_plan',
            'description_it': 'description_it',
            'description_en': 'description_en',
        }

        sets   = []
        params = {'loc_id': location_id}

        for html_key, col in field_map.items():
            if html_key in data:
                pk = f'v_{col}'
                sets.append(f"{col} = :{pk}")
                params[pk] = data[html_key] if data[html_key] != '' else None

        for arr_key, col in (('services', 'services'), ('services_it', 'services_it')):
            if arr_key in data:
                pk = f'v_{col}'
                sets.append(f"{col} = :{pk}")
                params[pk] = _pg_array(data[arr_key] or [])

        if not sets:
            return jsonify({'error': 'Nessun campo da aggiornare'}), 400

        conn = Database().get_connection()
        conn.run(f"UPDATE locations SET {', '.join(sets)} WHERE id = :loc_id", **params)
        conn.run("COMMIT")
        return jsonify({'message': 'Location aggiornata'}), 200
    except Exception:
        traceback.print_exc()
        return jsonify({'error': "Errore nell'aggiornamento location"}), 500


# ── DASHBOARD: DELETE ────────────────────────────────────────────────────────

@locations_bp.route('/<int:location_id>', methods=['DELETE'])
def delete_location(location_id):
    """Dashboard — elimina una location con pulizia delle dipendenze."""
    try:
        conn = Database().get_connection()
        conn.run(
            "DELETE FROM event_proposals WHERE event_id IN "
            "(SELECT id FROM events WHERE location_id = :id)",
            id=location_id
        )
        conn.run("DELETE FROM event_replicas WHERE location_id = :id", id=location_id)
        conn.run("DELETE FROM events    WHERE location_id = :id", id=location_id)
        conn.run("DELETE FROM locations WHERE id          = :id", id=location_id)
        conn.run("COMMIT")
        return jsonify({'message': 'Location eliminata'}), 200
    except Exception:
        traceback.print_exc()
        return jsonify({'error': "Errore nell'eliminazione location"}), 500
