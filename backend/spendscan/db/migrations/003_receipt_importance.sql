-- Drop coins from users; add importance (0-3) to receipts.
ALTER TABLE users DROP COLUMN IF EXISTS coins;

ALTER TABLE receipts
    ADD COLUMN IF NOT EXISTS importance INTEGER NOT NULL DEFAULT 0;

ALTER TABLE receipts
    DROP CONSTRAINT IF EXISTS receipts_importance_range;

ALTER TABLE receipts
    ADD CONSTRAINT receipts_importance_range CHECK (importance BETWEEN 0 AND 3);
