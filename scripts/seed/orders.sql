-- Synthetic data for the orders database: 200 products and one million orders.
-- Everything here is made up. Safe to run again: it empties the tables first.
-- Run with: make seed

BEGIN;

TRUNCATE orders, products RESTART IDENTITY;

-- The same "random" data on every run
SELECT setseed(0.42);

-- 200 products spread over 50 merchants, priced from Rs 49 to Rs 4,999
INSERT INTO products (name, price_paise, merchant_id)
SELECT 'Product ' || n,
       (4900 + floor(random() * 495000))::int,
       'MRC' || lpad((1 + n % 50)::text, 6, '0')
FROM generate_series(1, 200) AS n;

-- One million orders over the past year, from 100,000 customers (about ten each)
INSERT INTO orders (customer_email, merchant_id, product_id, quantity, amount_paise, status, created_at)
SELECT 'user' || s.customer || '@example.com',
       p.merchant_id,
       p.id,
       s.quantity,
       p.price_paise * s.quantity,
       (ARRAY['paid', 'paid', 'paid', 'paid', 'pending', 'payment_failed'])[s.status_pick],
       now() - s.age
FROM (
    SELECT 1 + floor(random() * 100000)::int AS customer,
           1 + floor(random() * 200)::int    AS product_id,
           1 + floor(random() * 5)::int      AS quantity,
           1 + floor(random() * 6)::int      AS status_pick,
           random() * interval '365 days'    AS age
    FROM generate_series(1, 1000000)
) AS s
JOIN products AS p ON p.id = s.product_id;

COMMIT;

-- Refresh the statistics the query planner uses to choose between an index and a full scan
ANALYZE products;
ANALYZE orders;
