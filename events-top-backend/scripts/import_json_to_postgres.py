import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
DATA_DIR = ROOT_DIR / "data"
SCHEMA_PATH = BACKEND_DIR / "sql" / "schema.sql"

sys.path.insert(0, str(BACKEND_DIR))

from psycopg2.extras import execute_values

from database import get_db_connection


def load_json(filename):
    path = DATA_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))


def apply_schema(cursor):
    cursor.execute(SCHEMA_PATH.read_text(encoding="utf-8"))


def clear_tables(cursor):
    cursor.execute(
        """
        TRUNCATE TABLE
            reviews,
            favorites,
            users,
            event_images,
            events,
            location_images,
            locations,
            production_images,
            productions
        RESTART IDENTITY CASCADE
        """
    )


def insert_productions(cursor, productions):
    production_rows = [
        (
            item["id"],
            item["slug"],
            item["title"],
            item["description"],
            item["category"],
            item["type"],
            item["duration"],
            item["language"],
            item["suitableFor"],
        )
        for item in productions
    ]
    execute_values(
        cursor,
        """
        INSERT INTO productions (
            id, slug, title, description, category, production_type, duration, language, suitable_for
        ) VALUES %s
        """,
        production_rows,
    )

    image_rows = []
    for item in productions:
        for index, image in enumerate(item.get("images", []), start=1):
            image_rows.append(
                (item["id"], index, image["url"], image.get("alt"))
            )

    if image_rows:
        execute_values(
            cursor,
            """
            INSERT INTO production_images (production_id, image_order, url, alt)
            VALUES %s
            """,
            image_rows,
        )


def insert_locations(cursor, locations):
    location_rows = [
        (
            item["id"],
            item["slug"],
            item["name"],
            item["address"],
            item["city"],
            item["region"],
            item.get("latitude"),
            item.get("longitude"),
            item.get("capacity"),
            item.get("services", []),
            item.get("link"),
        )
        for item in locations
    ]
    execute_values(
        cursor,
        """
        INSERT INTO locations (
            id, slug, name, address, city, region, latitude, longitude, capacity, services, link
        ) VALUES %s
        """,
        location_rows,
    )

    image_rows = []
    for item in locations:
        for index, image in enumerate(item.get("images", []), start=1):
            image_rows.append(
                (item["id"], index, image["url"], image.get("alt"))
            )

    if image_rows:
        execute_values(
            cursor,
            """
            INSERT INTO location_images (location_id, image_order, url, alt)
            VALUES %s
            """,
            image_rows,
        )


def insert_events(cursor, events):
    event_rows = [
        (
            item["id"],
            item["slug"],
            item["productionId"],
            item["locationId"],
            item["title"],
            item["description"],
            item["category"],
            item["city"],
            item["date"],
            item["startTime"],
            item.get("duration"),
            item["price"],
            item.get("ticketUrl"),
            item.get("sourceUrl"),
        )
        for item in events
    ]
    execute_values(
        cursor,
        """
        INSERT INTO events (
            id, slug, production_id, location_id, title, description, category, city,
            event_date, start_time, duration, price, ticket_url, source_url
        ) VALUES %s
        """,
        event_rows,
    )

    image_rows = []
    for item in events:
        for index, image in enumerate(item.get("images", []), start=1):
            image_rows.append(
                (item["id"], index, image["url"], image.get("alt"))
            )

    if image_rows:
        execute_values(
            cursor,
            """
            INSERT INTO event_images (event_id, image_order, url, alt)
            VALUES %s
            """,
            image_rows,
        )


def main():
    productions = load_json("productions.json")
    locations = load_json("locations.json")
    events = load_json("events.json")

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            apply_schema(cursor)
            clear_tables(cursor)
            insert_productions(cursor, productions)
            insert_locations(cursor, locations)
            insert_events(cursor, events)
        connection.commit()

    print(
        "Import completato:",
        f"{len(productions)} productions,",
        f"{len(locations)} locations,",
        f"{len(events)} events",
    )


if __name__ == "__main__":
    main()
