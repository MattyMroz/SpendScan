-- Store receipt image binary data directly in the database.
-- stored_path is kept as a nullable fallback for any rows that already exist.

BEGIN;

ALTER TABLE public.receipt_images
    ADD COLUMN IF NOT EXISTS image_data bytea,
    ALTER COLUMN stored_path DROP NOT NULL;

COMMIT;