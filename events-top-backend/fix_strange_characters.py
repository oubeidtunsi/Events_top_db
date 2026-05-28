import pg8000
from config import Config
 
conn = pg8000.connect(
    host=Config.DB_HOST,
    port=Config.DB_PORT,
    database=Config.DB_NAME,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD
)
c = conn.cursor()
 
c.execute("SELECT id, title FROM events WHERE title LIKE '%Boh%'")
rows = c.fetchall()
print("Trovati:", rows)
 
c.execute("UPDATE events SET title = 'La Bohème' WHERE title LIKE '%Boh%me%'")
print(c.rowcount, "righe aggiornate")
 
conn.commit()
conn.close()
print("Fatto.")