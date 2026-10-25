-- Synthetic data for the payments database: 200,000 charges.
-- The card numbers are random digits, not real cards. They are here so that
-- the investigator's redaction can be tested against card-like data.
-- Safe to run again: it empties the table first.
-- Run with: make seed

BEGIN;

TRUNCATE charges RESTART IDENTITY;

SELECT setseed(0.42);

INSERT INTO charges (order_id, amount_paise, card_number, merchant_id, status, bank_reference, created_at)
SELECT n,
       (4900 + floor(random() * 495000))::bigint,
       '4' || lpad(floor(random() * 1e15)::bigint::text, 15, '0'),
       'MRC' || lpad((1 + n % 50)::text, 6, '0'),
       CASE WHEN random() < 0.9 THEN 'approved' ELSE 'declined' END,
       'BNK-' || upper(substr(md5(n::text), 1, 12)),
       now() - random() * interval '365 days'
FROM generate_series(1, 200000) AS n;

COMMIT;

ANALYZE charges;
