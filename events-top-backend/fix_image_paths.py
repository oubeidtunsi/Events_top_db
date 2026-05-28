# fix_image_paths.py  — esegui con: python fix_image_paths.py

import pg8000
from config import Config

# Mappa: parola chiave nel titolo evento → nome file reale in locandine/
IMAGE_MAP = {
    "notre dame":              "notre_dame_locandina.jpg",
    "simon boccanegra":        "simon_boccanegra_locandina.jpg",
    "rigoletto":               "rigoletto_locandina.gif",
    "traviata":                "traviata_locandina.jpg",
    "aida":                    "aida_locandina.jpg",
    "amadeus":                 "amadeus_locandina.jpg",
    "amleto":                  "amleto2_locandina.jpg",
    "balanchine":              "balanchine_locandina.jpg",
    "boh":                     "boheme_locandina.png",
    "boheme":                  "boheme_locandina.png",
    "bubaro":                  "bubaro_dei_bubari_locandina.jpg",
    "cantando sotto la pioggia": "cantando_sotto_la_pioggia_locandina.jpg",
    "caravaggio":              "caravaggio_locandina.webp",
    "carmen":                  "carmen_locandina.jpg",
    "cavalleria rusticana":    "cavalleria_rusticana_locandina.jpg",
    "don giovanni":            "don_giovanni_locandina.jpg",
    "don quixote":             "don_quixote_locandina.jpg",
    "dreamers":                "dreamers_locandina.jpg",
    "elektra":                 "elektra_locandina.jpeg",
    "elisir":                  "elisir_damore_locandina.jpg",
    "el cimarron":             "el_cimarron_locandina.jpg",
    "enrico di borgogna":      "enrico_di_borgogna_locandina.jpg",
    "falstaff":                "falstaff_locandina.jpg",
    "giselle":                 "giselle_locandina.webp",
    "hair":                    "hair_locandina.webp",
    "hamburger":               "hamburger_kammerballett_locandina.avif",
    "idomeneo":                "idomeneo_locandina.jpg",
    "improvvisamente":         "improvvisamente_estate_scorsa_locandina.jpg",
    "bella addormentata":      "la_bella_addormentata_locandina.jpg",
    "fanciulla del west":      "la_fanciulla_del_west_locandina.jpg",
    "locandiera":              "la_locandiera_locandina.jpg",
    "nozze di figaro":         "le_nozze_di_figaro_locandina.png",
    "lucia":                   "lucia_locandina.jpg",
    "lucrezia borgia":         "lucrezia_borgia_locandina.jpg",
    "madama butterfly":        "madama_butterfly_locandina.jpg",
    "manon lescaut":           "manon_lescaut_locandina.jpg",
    "nabucco":                 "nabucco_locandina.png",
    "norma":                   "norma_locandina.jpg",
    "olympia":                 "olympia_locandina.jpg",
    "orfeo":                   "orfeo_e_euridice_locandina.png",
    "otello":                  "otello_locandina.jpg",
    "pagliacci":               "pagliacci_locandina.jpg",
    "romanzo criminale":       "romanzo_criminale_locandina.jpg",
    "semele":                  "semele_locandina.jpg",
    "tosca":                   "tosca_locandina.jpg",
    "trouble in tahiti":       "trouble_in_tahiti_locandina.jpg",
    "trovatore":               "trovatore_locandina.jpg",
    "turandot":                "turandot_locandina.jpg",
    "venere":                  "venere_e_adone_locandina.png",
    "wozzeck":                 "wozzeck_locandina.jpg",
}

def find_image(title):
    title_lower = title.lower()
    for keyword, filename in IMAGE_MAP.items():
        if keyword in title_lower:
            return "/assets/events/" + filename
    return None

conn = pg8000.connect(
    host=Config.DB_HOST,
    port=Config.DB_PORT,
    database=Config.DB_NAME,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD
)
cursor = conn.cursor()

cursor.execute("SELECT id, title FROM events")
events = cursor.fetchall()

updated = 0
skipped = 0

for event_id, title in events:
    new_path = find_image(title)
    if not new_path:
        print(f"  [SKIP] Nessuna immagine trovata per: {title}")
        skipped += 1
        continue

    # Aggiorna se esiste già, inserisce se non esiste
    cursor.execute("SELECT id FROM event_images WHERE event_id = %s", (event_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            "UPDATE event_images SET url = %s WHERE event_id = %s",
            (new_path, event_id)
        )
    else:
        cursor.execute(
            "INSERT INTO event_images (event_id, url, alt) VALUES (%s, %s, %s)",
            (event_id, new_path, title)
        )

    print(f"  [OK] {title} → {new_path}")
    updated += 1

conn.commit()
cursor.close()
conn.close()

print(f"\nDone: {updated} aggiornati, {skipped} saltati.")