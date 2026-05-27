# seed_data.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'project_work.db')

def seed():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Location di esempio
    c.execute("INSERT OR IGNORE INTO locations (id, slug, name, address, city, region, latitude, longitude, capacity, services) VALUES (1, 'teatro-alla-scala', 'Teatro alla Scala', 'Via Filodrammatici 2', 'Milano', 'Lombardia', 45.467, 9.189, 2000, 'parcheggio,bar,accessibilità')")
    c.execute("INSERT OR IGNORE INTO locations (id, slug, name, address, city, region, latitude, longitude, capacity, services) VALUES (2, 'arena-di-verona', 'Arena di Verona', 'Piazza Bra 1', 'Verona', 'Veneto', 45.438, 10.993, 15000, 'parcheggio,ristoro')")
    
    # Eventi di esempio
    c.execute("INSERT OR IGNORE INTO events (id, slug, title, description, category, city, event_date, price, location_id) VALUES (1, 'concerto-vivaldi', 'Concerto Vivaldi', 'Le quattro stagioni', 'Concerti', 'Milano', '2026-06-15', 25.00, 1)")
    c.execute("INSERT OR IGNORE INTO events (id, slug, title, description, category, city, event_date, price, location_id) VALUES (2, 'opera-aida', 'Aida', 'Opera di Verdi', 'Opera', 'Verona', '2026-07-20', 50.00, 2)")
    
    # Immagini di esempio (location)
    c.execute("INSERT OR IGNORE INTO location_images (location_id, image_order, url, alt) VALUES (1, 1, 'https://example.com/scala1.jpg', 'Facciata Teatro alla Scala')")
    c.execute("INSERT OR IGNORE INTO location_images (location_id, image_order, url, alt) VALUES (1, 2, 'https://example.com/scala2.jpg', 'Interno Teatro alla Scala')")
    c.execute("INSERT OR IGNORE INTO location_images (location_id, image_order, url, alt) VALUES (2, 1, 'https://example.com/arena1.jpg', 'Arena di Verona')")
    
    # Immagini di esempio (eventi)
    c.execute("INSERT OR IGNORE INTO event_images (event_id, image_order, url, alt) VALUES (1, 1, 'https://example.com/vivaldi.jpg', 'Locandina Concerto Vivaldi')")
    c.execute("INSERT OR IGNORE INTO event_images (event_id, image_order, url, alt) VALUES (2, 1, 'https://example.com/aida.jpg', 'Locandina Aida')")
    
    conn.commit()
    conn.close()
    print("✅ Dati di esempio inseriti")

if __name__ == '__main__':
    seed()