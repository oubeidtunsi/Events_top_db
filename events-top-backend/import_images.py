import sqlite3
import os

# Percorsi
DB_PATH = os.path.join(os.path.dirname(__file__), 'project_work.db')
LOCANDINE_DIR = os.path.join(os.path.dirname(__file__), 'static', 'images', 'foto_luoghi', 'locandine')

def import_images():
    if not os.path.exists(LOCANDINE_DIR):
        print(f"❌ Cartella locandine non trovata: {LOCANDINE_DIR}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    inserted = 0
    for filename in os.listdir(LOCANDINE_DIR):
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue

        slug = os.path.splitext(filename)[0]  # nome file senza estensione
        cursor.execute("SELECT id FROM events WHERE slug = ?", (slug,))
        event = cursor.fetchone()

        if event is None:
            print(f"⚠️  Nessun evento trovato per il file {filename} (slug: {slug})")
            continue

        event_id = event[0]
        url = f"/static/images/foto_luoghi/locandine/{filename}"
        alt = slug.replace('-', ' ').title()

        # Inserisce solo se non esiste già (grazie a INSERT OR IGNORE)
        cursor.execute(
            "INSERT OR IGNORE INTO event_images (event_id, image_order, url, alt) VALUES (?, 1, ?, ?)",
            (event_id, url, alt)
        )

        if cursor.rowcount > 0:
            print(f"✅ Immagine aggiunta per evento {slug}")
            inserted += 1
        else:
            print(f"⏩ Immagine già presente per evento {slug}")

    conn.commit()
    conn.close()
    print(f"\n🏁 Import completato: {inserted} nuove immagini inserite.")

if __name__ == "__main__":
    import_images()