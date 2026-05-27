-- ─────────────────────────────────────────────────────────────────────────────
-- Migration v4 — Impostazioni privacy utente
-- Eseguire dopo migration_v3.sql
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE users ADD COLUMN IF NOT EXISTS private_favorites BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS private_reviews   BOOLEAN DEFAULT FALSE;
