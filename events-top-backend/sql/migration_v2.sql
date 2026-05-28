-- ============================================================================
-- Events-TOP — Migration v2
-- Script PostgreSQL eseguibile su PgAdmin 4
-- Eseguire in ordine; ogni blocco è idempotente (non fallisce se già eseguito)
-- ============================================================================

-- ────────────────────────────────────────────────────────────────────────────
-- 1. Aggiunge il campo 'gender' agli utenti (se non esiste già)
-- ────────────────────────────────────────────────────────────────────────────
ALTER TABLE users ADD COLUMN IF NOT EXISTS gender VARCHAR(10) DEFAULT 'guest';
ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name  VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name  VARCHAR(200);
ALTER TABLE users ADD COLUMN IF NOT EXISTS date_of_birth DATE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_code VARCHAR(10);
ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;
<<<<<<< HEAD
=======
ALTER TABLE users ADD COLUMN IF NOT EXISTS total_score INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS max_score INTEGER DEFAULT 0;
>>>>>>> 7712ff0 (aggiunti endpoint x i punti)

-- ────────────────────────────────────────────────────────────────────────────
-- 1b. Aggiunge production_id agli eventi (usato per raggruppare repliche)
-- ────────────────────────────────────────────────────────────────────────────
ALTER TABLE events ADD COLUMN IF NOT EXISTS production_id INTEGER DEFAULT 0;

-- ────────────────────────────────────────────────────────────────────────────
-- 1c. Aggiunge action_user_id alle amicizie (chi ha effettuato l'ultima azione)
-- ────────────────────────────────────────────────────────────────────────────
ALTER TABLE friendships ADD COLUMN IF NOT EXISTS action_user_id INTEGER REFERENCES users(id);
ALTER TABLE friendships ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- ────────────────────────────────────────────────────────────────────────────
-- 1d. Aggiunge from_user_id alle notifiche (FK all'utente mittente)
-- ────────────────────────────────────────────────────────────────────────────
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS from_user_id INTEGER REFERENCES users(id);

-- ────────────────────────────────────────────────────────────────────────────
-- 2. Aggiunge 'blocked' allo stato amicizie
-- ────────────────────────────────────────────────────────────────────────────
-- Rimuove il vecchio vincolo CHECK e ne aggiunge uno aggiornato
ALTER TABLE friendships DROP CONSTRAINT IF EXISTS friendships_status_check;
ALTER TABLE friendships ADD CONSTRAINT friendships_status_check
    CHECK (status IN ('pending', 'accepted', 'rejected', 'blocked'));

-- ────────────────────────────────────────────────────────────────────────────
-- 3. Aggiunge username mittente/destinatario alle proposte (denormalizzato
--    per semplificare le query del frontend senza JOIN aggiuntivi)
-- ────────────────────────────────────────────────────────────────────────────
ALTER TABLE event_proposals ADD COLUMN IF NOT EXISTS message TEXT;

-- ────────────────────────────────────────────────────────────────────────────
-- 4. Aggiunge from_username alle notifiche (evita JOIN al momento della lettura)
-- ────────────────────────────────────────────────────────────────────────────
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS from_username VARCHAR(100);

-- ────────────────────────────────────────────────────────────────────────────
-- 5. Indici aggiuntivi per performance
-- ────────────────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_friendships_user1   ON friendships(user_id_1);
CREATE INDEX IF NOT EXISTS idx_friendships_user2   ON friendships(user_id_2);
CREATE INDEX IF NOT EXISTS idx_proposals_to_user   ON event_proposals(to_user_id);
CREATE INDEX IF NOT EXISTS idx_proposals_from_user ON event_proposals(from_user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user  ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read  ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_favorites_user      ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_event       ON reviews(event_id);
CREATE INDEX IF NOT EXISTS idx_users_username      ON users(username);

-- ────────────────────────────────────────────────────────────────────────────
-- 6. Crea le tabelle se non esistono (per installazioni nuove)
--    Queste CREATE IF NOT EXISTS sono sicure da rieseguire
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(100) UNIQUE NOT NULL,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name    VARCHAR(100),
    last_name     VARCHAR(100),
    full_name     VARCHAR(200),
    date_of_birth DATE,
    gender        VARCHAR(10) DEFAULT 'guest',
    is_verified   BOOLEAN DEFAULT FALSE,
    otp_code      VARCHAR(10),
    otp_expires_at TIMESTAMP,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login    TIMESTAMP
);

CREATE TABLE IF NOT EXISTS locations (
    id       SERIAL PRIMARY KEY,
    slug     VARCHAR(200) UNIQUE NOT NULL,
    name     TEXT NOT NULL,
    address  TEXT NOT NULL,
    city     TEXT NOT NULL,
    region   TEXT NOT NULL,
    latitude  REAL,
    longitude REAL,
    capacity  INTEGER,
    services  TEXT,
    link      TEXT
);

CREATE TABLE IF NOT EXISTS location_images (
    id           SERIAL PRIMARY KEY,
    location_id  INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    image_order  INTEGER NOT NULL,
    url          TEXT NOT NULL,
    alt          TEXT,
    UNIQUE(location_id, image_order)
);

CREATE TABLE IF NOT EXISTS events (
    id          SERIAL PRIMARY KEY,
    slug        VARCHAR(200) UNIQUE NOT NULL,
    title       TEXT NOT NULL,
    description TEXT,
    category    TEXT,
    city        TEXT NOT NULL,
    event_date  DATE NOT NULL,
    start_time  TIME,
    duration    TEXT,
    price       REAL,
    ticket_url  TEXT,
    source_url  TEXT,
    location_id INTEGER REFERENCES locations(id),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_images (
    id          SERIAL PRIMARY KEY,
    event_id    INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    image_order INTEGER NOT NULL,
    url         TEXT NOT NULL,
    alt         TEXT,
    UNIQUE(event_id, image_order)
);

CREATE TABLE IF NOT EXISTS parking_spots (
    id        SERIAL PRIMARY KEY,
    user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    latitude  REAL NOT NULL,
    longitude REAL NOT NULL,
    notes     TEXT,
    saved_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reviews (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id   INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    rating     INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment    TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, event_id)
);

CREATE TABLE IF NOT EXISTS favorites (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id   INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, event_id)
);

CREATE TABLE IF NOT EXISTS friendships (
    id             SERIAL PRIMARY KEY,
    user_id_1      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_id_2      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status         TEXT DEFAULT 'pending'
                   CHECK (status IN ('pending','accepted','rejected','blocked')),
    action_user_id INTEGER REFERENCES users(id),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id_1, user_id_2)
);

CREATE TABLE IF NOT EXISTS event_proposals (
    id           SERIAL PRIMARY KEY,
    from_user_id INTEGER NOT NULL REFERENCES users(id),
    to_user_id   INTEGER NOT NULL REFERENCES users(id),
    event_id     INTEGER NOT NULL REFERENCES events(id),
    status       TEXT DEFAULT 'pending'
                 CHECK (status IN ('pending','accepted','declined','maybe')),
    message      TEXT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type          TEXT NOT NULL,
    content       TEXT,
    related_id    INTEGER,
    from_user_id  INTEGER REFERENCES users(id),
    from_username VARCHAR(100),
    is_read       INTEGER DEFAULT 0,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ────────────────────────────────────────────────────────────────────────────
-- 7. Indici eventi (già presenti nello schema originale, resi sicuri)
-- ────────────────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_events_city     ON events(city);
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
CREATE INDEX IF NOT EXISTS idx_events_date     ON events(event_date);

-- ============================================================================
-- FINE MIGRATION v2
-- ============================================================================
