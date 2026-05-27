from database import Database

def seed():
    db = Database()
    conn = db.get_connection()
    
    # LISTA ASSOCIAZIONI: [('slug-teatro', 'percorso/foto.jpg', 'percorso/planimetria.jpg')]
    data = [
        ('ancona-est', 'static/images/foto_luoghi/foto_teatri/ancona_est.jpg', 'static/images/foto_luoghi/planimetrie/ancona_plan.jpg'),
        # Aggiungi qui gli altri basandoti sui file che hai
    ]

    for slug, img_url, plan_url in data:
        res = conn.run("SELECT id FROM locations WHERE slug = :slug", slug=slug)
        if res:
            loc_id = res[0]['id']
            
            # Inserisce Immagine
            conn.run("""
                INSERT INTO location_images (location_id, url, alt, image_order)
                VALUES (:id, :url, 'Foto', 1) ON CONFLICT DO NOTHING
            """, id=loc_id, url=img_url)
            
            # Inserisce Planimetria (Crea tabella se manca: id, location_id, url)
            conn.run("""
                INSERT INTO location_planimetrie (location_id, url)
                VALUES (:id, :url) ON CONFLICT DO NOTHING
            """, id=loc_id, url=plan_url)

if __name__ == "__main__":
    seed()
    print("Fatto.")