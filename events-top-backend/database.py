import pg8000.native
from flask import g
from config import Config


class Database:
    """
    Fornisce una connessione pg8000 per-request tramite Flask g.
    Ogni request ottiene una connessione fresca; viene chiusa a fine request
    da teardown_appcontext registrato in init_db().
    Non usa singleton globale: elimina ConnectionResetError e race conditions.
    """

    def get_connection(self):
        if 'pg_conn' not in g:
            try:
                conn = pg8000.native.Connection(
                    host=Config.DB_HOST,
                    port=int(Config.DB_PORT),
                    database=Config.DB_NAME,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                )
                g.pg_conn = conn
            except Exception as e:
                print(f"❌ Errore connessione DB: {e}")
                raise
        return g.pg_conn


def init_db(app):
    @app.teardown_appcontext
    def close_connection(exception):
        conn = g.pop('pg_conn', None)
        if conn is not None:
            try:
                if exception:
                    conn.run("ROLLBACK")
                conn.close()
            except Exception:
                pass

    print("✅ Database PostgreSQL pronto (connessioni per-request)")
