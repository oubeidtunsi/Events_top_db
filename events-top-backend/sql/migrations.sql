-- ============================================================
-- MIGRATION: tabelle e modifiche necessarie per le nuove funzionalità
-- Esegui questo script sul database events_top_db una volta sola.
-- ============================================================

-- 1. Colonna otp_code deve essere TEXT per contenere hash bcrypt (~72 char)
ALTER TABLE users ALTER COLUMN otp_code TYPE TEXT;
<<<<<<< HEAD
=======
ALTER TABLE users ADD COLUMN IF NOT EXISTS total_score INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS max_score INTEGER DEFAULT 0;
>>>>>>> 7712ff0 (aggiunti endpoint x i punti)

-- 2. Tabella promemoria eventi (one reminder per user per event)
CREATE TABLE IF NOT EXISTS event_reminders (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id    INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    remind_at   TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_user_event_reminder UNIQUE (user_id, event_id)
);

-- 3. Fix tabella friendships: rimuovi NOT NULL da action_user_id se esiste
--    (oppure la colonna non è richiesta dal codice aggiornato)
--    Esegui solo se la colonna esiste e ha vincolo NOT NULL:
-- ALTER TABLE friendships ALTER COLUMN action_user_id DROP NOT NULL;

-- 4. Fix tabella notifications: is_read deve essere BOOLEAN (non INT)
--    Se il tipo è già BOOLEAN salta questi comandi.
-- ALTER TABLE notifications ALTER COLUMN is_read TYPE BOOLEAN USING (is_read::boolean);
-- ALTER TABLE notifications ALTER COLUMN is_read SET DEFAULT FALSE;
