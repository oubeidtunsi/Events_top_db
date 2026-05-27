import os
import re
import pg8000.native
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

LOCANDINE_DIR = os.path.join(
    os.path.dirname(__file__),
    "static", "images", "foto_luoghi", "locandine"
)

def normalize(text):
    """Rimuove spazi, apostrofi, trattini, punti e mette in minuscolo"""
    return re.sub(r"[\s\-'\"!?\.]+", "", text).lower()

def main():
    conn = pg8000.native.Connection(
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    # Recupera tutti gli eventi
    rows = conn.run("SELECT id, title FROM events")
    # pg8000 restituisce una lista di liste (o tuple)
    events = [(r[0], r[1]) for r in rows]

    # Preparo i file disponibili
    # Estraggo solo la parte "significativa" del nome (es. "traviata" da "traviata_locandina.jpg")
    files = [f for f in os.listdir(LOCANDINE_DIR)
             if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    # Associa ogni normalizzazione al file originale
    norm_to_file = {}
    for f in files:
        base = os.path.splitext(f)[0]
        # Rimuovo suffissi comuni
        for suffix in ["_locandina", "_cover", "_gallery"]:
            if base.endswith(suffix):
                base = base[:-len(suffix)]
                break
        normalized = normalize(base)
        norm_to_file[normalized] = f

    updated = 0
    for event_id, title in events:
        norm_title = normalize(title)
        matched_file = None
        for norm_key, filename in norm_to_file.items():
            if norm_key in norm_title or norm_title in norm_key:
                matched_file = filename
                break

        if not matched_file:
            print(f"Nessuna locandina trovata per: {title}")
            continue

        url = f"/static/images/foto_luoghi/locandine/{matched_file}"
        alt = title

        # Inserisce o aggiorna l'immagine principale (image_order = 1)
        conn.run(
            """
            INSERT INTO event_images (event_id, image_order, url, alt)
            VALUES (:event_id, 1, :url, :alt)
            ON CONFLICT (event_id, image_order) DO UPDATE
            SET url = EXCLUDED.url, alt = EXCLUDED.alt
            """,
            event_id=event_id, url=url, alt=alt
        )
        updated += 1
        print(f"Associato: {matched_file} -> {title}")

    conn.run("COMMIT")
    conn.close()
    print(f"Fatto! Aggiornati {updated} eventi su {len(events)}")

if __name__ == "__main__":
    main()