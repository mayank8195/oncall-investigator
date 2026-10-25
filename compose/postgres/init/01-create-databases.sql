-- Runs once, the first time the Postgres container starts with an empty volume.
-- One database and one login per service: neither service can read the other's tables.
-- These passwords are for local development only.

CREATE ROLE orders LOGIN PASSWORD 'orders';
CREATE DATABASE orders OWNER orders;

CREATE ROLE payments LOGIN PASSWORD 'payments';
CREATE DATABASE payments OWNER payments;
