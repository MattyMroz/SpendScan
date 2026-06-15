--
-- Cleanup receipt schema after OCR persistence extension.
-- Monetary values are stored as integer cents/grosze.
--

BEGIN;

--
-- Copy legacy receipt values into the new receipt columns before removing them.
--

UPDATE public.receipts
SET
    merchant_name = COALESCE(merchant_name, shop_name),
    receipt_date = COALESCE(receipt_date, purchase_date)
WHERE shop_name IS NOT NULL
   OR purchase_date IS NOT NULL;

--
-- Copy legacy item price into total_price before removing price.
-- Migration 002 converted price from integer cents to numeric without scaling.
-- Therefore the numeric value still represents cents/grosze.
--

UPDATE public.receipt_items
SET total_price = price
WHERE price IS NOT NULL
  AND (
      total_price IS NULL
      OR total_price = 0
  );

--
-- Drop old CHECK constraints before changing/removing columns.
--

ALTER TABLE ONLY public.receipts
    DROP CONSTRAINT IF EXISTS receipts_total_amount_check,
    DROP CONSTRAINT IF EXISTS receipts_subtotal_amount_check,
    DROP CONSTRAINT IF EXISTS receipts_tax_amount_check,
    DROP CONSTRAINT IF EXISTS receipts_total_discount_amount_check,
    DROP CONSTRAINT IF EXISTS receipts_importance_level_check;

ALTER TABLE ONLY public.receipt_items
    DROP CONSTRAINT IF EXISTS receipt_items_price_check,
    DROP CONSTRAINT IF EXISTS receipt_items_unit_price_check,
    DROP CONSTRAINT IF EXISTS receipt_items_total_price_check,
    DROP CONSTRAINT IF EXISTS receipt_items_discount_amount_check;

--
-- Convert receipt monetary columns back to integer cents/grosze.
-- We use ROUND(value)::integer because migration 002 converted existing integer cents
-- to numeric without dividing by 100.
--

ALTER TABLE ONLY public.receipts
    ALTER COLUMN total_amount DROP DEFAULT,
    ALTER COLUMN total_amount TYPE integer USING ROUND(total_amount)::integer,
    ALTER COLUMN total_amount SET DEFAULT 0,
    ALTER COLUMN subtotal_amount TYPE integer USING ROUND(subtotal_amount)::integer,
    ALTER COLUMN tax_amount TYPE integer USING ROUND(tax_amount)::integer,
    ALTER COLUMN total_discount_amount TYPE integer USING ROUND(total_discount_amount)::integer;

--
-- Convert item monetary columns to integer cents/grosze.
--

ALTER TABLE ONLY public.receipt_items
    ALTER COLUMN unit_price TYPE integer USING ROUND(unit_price)::integer,
    ALTER COLUMN total_price DROP DEFAULT,
    ALTER COLUMN total_price TYPE integer USING ROUND(total_price)::integer,
    ALTER COLUMN total_price SET DEFAULT 0,
    ALTER COLUMN discount_amount TYPE integer USING ROUND(discount_amount)::integer;

--
-- Recreate CHECK constraints for integer money columns.
--

ALTER TABLE ONLY public.receipts
    ADD CONSTRAINT receipts_total_amount_check CHECK (total_amount >= 0),
    ADD CONSTRAINT receipts_subtotal_amount_check CHECK (
        subtotal_amount IS NULL OR subtotal_amount >= 0
    ),
    ADD CONSTRAINT receipts_tax_amount_check CHECK (
        tax_amount IS NULL OR tax_amount >= 0
    ),
    ADD CONSTRAINT receipts_total_discount_amount_check CHECK (
        total_discount_amount IS NULL OR total_discount_amount >= 0
    );

ALTER TABLE ONLY public.receipt_items
    ADD CONSTRAINT receipt_items_unit_price_check CHECK (
        unit_price IS NULL OR unit_price >= 0
    ),
    ADD CONSTRAINT receipt_items_total_price_check CHECK (total_price >= 0),
    ADD CONSTRAINT receipt_items_discount_amount_check CHECK (
        discount_amount IS NULL OR discount_amount >= 0
    );

--
-- Remove legacy receipt columns replaced by the OCR persistence schema.
--

ALTER TABLE ONLY public.receipts
    DROP COLUMN IF EXISTS image_path,
    DROP COLUMN IF EXISTS shop_name,
    DROP COLUMN IF EXISTS purchase_date,
    DROP COLUMN IF EXISTS importance_level;

--
-- Remove legacy item price column replaced by unit_price / total_price.
--

ALTER TABLE ONLY public.receipt_items
    DROP COLUMN IF EXISTS price;

COMMIT;
