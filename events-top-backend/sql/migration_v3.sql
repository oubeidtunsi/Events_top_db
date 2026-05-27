-- ─────────────────────────────────────────────────────────────────────────────
-- Migration v3 — Profilo utente & impostazioni applicazione
-- Eseguire una sola volta sul database PostgreSQL già migrato a v2
-- ─────────────────────────────────────────────────────────────────────────────

-- 1. Aggiunge la colonna profile_image alla tabella users (se non esiste)
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image VARCHAR(255);

-- 2. Tabella chiave-valore per le impostazioni globali dell'applicazione
CREATE TABLE IF NOT EXISTS app_settings (
    key   VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL
);

-- 3. Inserisce la password di accesso alla configurazione URL (modificabile da DB)
INSERT INTO app_settings (key, value)
VALUES ('config_password', 'Admin1234')
ON CONFLICT (key) DO NOTHING;
