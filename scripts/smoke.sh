#!/usr/bin/env bash
# One request through every service: gateway -> orders -> payments -> toxiproxy -> mock-bank.
# Needs the system running (`make up`) and seeded (`make seed`).
# Run with: make smoke

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

echo "1. Health"
curl -fsS "$BASE_URL/health"
echo

echo "2. Create an order"
order=$(curl -fsS -X POST "$BASE_URL/orders" \
  -H 'Content-Type: application/json' \
  -d '{"customer_email": "smoke@example.com", "product_id": 1, "quantity": 2}')
echo "$order"
order_id=$(echo "$order" | sed -E 's/^\{"id":([0-9]+).*/\1/')

echo "3. Pay for order $order_id (this reaches the bank)"
paid=$(curl -fsS -X POST "$BASE_URL/orders/$order_id/pay" \
  -H 'Content-Type: application/json' \
  -d '{"card_number": "4111111111111111"}')
echo "$paid"

case "$paid" in
  *'"status":"paid"'*) echo "OK: the request reached the bank and came back." ;;
  *) echo "FAILED: the order was not paid." >&2; exit 1 ;;
esac
