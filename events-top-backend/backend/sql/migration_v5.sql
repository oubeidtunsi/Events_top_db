-- ============================================================================
-- Migration v5 — Allinea il vincolo users_gender_check ai valori dell'app
-- Valori accettati: 'M', 'F', 'O' (registrazione) · 'guest' (default ospite)
-- NULL è permesso per retrocompatibilità con righe pre-esistenti senza genere
-- ============================================================================

ALTER TABLE users DROP CONSTRAINT IF EXISTS users_gender_check;

ALTER TABLE users ADD CONSTRAINT users_gender_check
    CHECK (gender IS NULL OR gender IN ('M', 'F', 'O', 'guest'));
