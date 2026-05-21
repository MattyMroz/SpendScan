--
-- Receipt persistence extensions for OCR-backed multi-receipt uploads.
--

ALTER TABLE ONLY public.receipts
    ALTER COLUMN shop_name DROP NOT NULL,
    ALTER COLUMN purchase_date DROP NOT NULL,
    ALTER COLUMN total_amount TYPE numeric(10,2) USING total_amount::numeric(10,2),
    ALTER COLUMN total_amount SET DEFAULT 0;

ALTER TABLE ONLY public.receipts
    ADD COLUMN status text DEFAULT 'completed' NOT NULL,
    ADD COLUMN merchant_name text,
    ADD COLUMN receipt_date date,
    ADD COLUMN currency char(3) DEFAULT 'PLN' NOT NULL,
    ADD COLUMN subtotal_amount numeric(10,2),
    ADD COLUMN tax_amount numeric(10,2),
    ADD COLUMN total_discount_amount numeric(10,2),
    ADD COLUMN payment_method text,
    ADD COLUMN raw_ocr_text text DEFAULT '' NOT NULL,
    ADD COLUMN warnings jsonb DEFAULT '[]'::jsonb NOT NULL,
    ADD COLUMN error text;

ALTER TABLE ONLY public.receipts
    ADD CONSTRAINT receipts_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'completed'::text, 'failed'::text]))),
    ADD CONSTRAINT receipts_subtotal_amount_check CHECK (((subtotal_amount IS NULL) OR (subtotal_amount >= (0)::numeric))),
    ADD CONSTRAINT receipts_tax_amount_check CHECK (((tax_amount IS NULL) OR (tax_amount >= (0)::numeric))),
    ADD CONSTRAINT receipts_total_discount_amount_check CHECK (((total_discount_amount IS NULL) OR (total_discount_amount >= (0)::numeric)));


--
-- Name: receipt_images; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.receipt_images (
    id integer NOT NULL,
    receipt_id integer NOT NULL,
    page_number integer NOT NULL,
    original_filename text NOT NULL,
    stored_path text NOT NULL,
    content_type text,
    ocr_text text DEFAULT '' NOT NULL,
    ocr_engine text DEFAULT '' NOT NULL,
    ocr_processing_time_ms double precision DEFAULT 0 NOT NULL,
    image_width integer,
    image_height integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT receipt_images_page_number_check CHECK ((page_number >= 1)),
    CONSTRAINT receipt_images_processing_time_check CHECK ((ocr_processing_time_ms >= (0)::double precision)),
    CONSTRAINT receipt_images_width_check CHECK (((image_width IS NULL) OR (image_width > 0))),
    CONSTRAINT receipt_images_height_check CHECK (((image_height IS NULL) OR (image_height > 0)))
);


--
-- Name: receipt_images_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.receipt_images ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.receipt_images_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: receipt_images receipt_images_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.receipt_images
    ADD CONSTRAINT receipt_images_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.receipt_images
    ADD CONSTRAINT receipt_images_receipt_id_fkey FOREIGN KEY (receipt_id) REFERENCES public.receipts(id) ON UPDATE CASCADE ON DELETE CASCADE;


ALTER TABLE ONLY public.receipt_items
    ALTER COLUMN price TYPE numeric(10,2) USING price::numeric(10,2),
    ALTER COLUMN price SET DEFAULT 0,
    ALTER COLUMN quantity DROP NOT NULL;

ALTER TABLE ONLY public.receipt_items
    ADD COLUMN unit_price numeric(10,2),
    ADD COLUMN total_price numeric(10,2) DEFAULT 0 NOT NULL,
    ADD COLUMN discount_amount numeric(10,2);

ALTER TABLE ONLY public.receipt_items
    ADD CONSTRAINT receipt_items_unit_price_check CHECK (((unit_price IS NULL) OR (unit_price >= (0)::numeric))),
    ADD CONSTRAINT receipt_items_total_price_check CHECK ((total_price >= (0)::numeric)),
    ADD CONSTRAINT receipt_items_discount_amount_check CHECK (((discount_amount IS NULL) OR (discount_amount >= (0)::numeric)));


CREATE UNIQUE INDEX idx_receipt_images_receipt_page_unique ON public.receipt_images USING btree (receipt_id, page_number);
CREATE INDEX idx_receipts_user_date ON public.receipts USING btree (user_id, receipt_date);
CREATE INDEX idx_receipts_merchant_name ON public.receipts USING btree (merchant_name);
CREATE INDEX idx_receipt_items_receipt_id ON public.receipt_items USING btree (receipt_id);
CREATE INDEX idx_receipt_items_category_id ON public.receipt_items USING btree (category_id);


INSERT INTO public.users (id, username, email, password_hash)
OVERRIDING SYSTEM VALUE
VALUES (1, 'demo', 'demo@spendscan.local', 'demo')
ON CONFLICT (id) DO NOTHING;

SELECT setval('public.users_id_seq', GREATEST((SELECT max(id) FROM public.users), 1), true);
