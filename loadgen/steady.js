// Steady background traffic through the gateway, for k6.
// A fixed number of requests start every second, whatever the response times are.
// Run with: make load        (or: make load RATE=20 DURATION=10m)

import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const RATE = parseInt(__ENV.RATE || '10', 10);
const DURATION = __ENV.DURATION || '2m';

const JSON_HEADERS = { headers: { 'Content-Type': 'application/json' } };

// The seed data: customers user1..user100000 and products 1..200
const CUSTOMERS = 100000;
const PRODUCTS = 200;

export const options = {
  scenarios: {
    steady: {
      executor: 'constant-arrival-rate',
      rate: RATE,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: 20,
      maxVUs: 100,
    },
  },
  // The run fails if these are not met
  thresholds: {
    checks: ['rate>0.99'],
    http_req_duration: ['p(95)<500'],
  },
};

function randomInt(max) {
  return 1 + Math.floor(Math.random() * max);
}

function randomCustomer() {
  return `user${randomInt(CUSTOMERS)}@example.com`;
}

// Looking around: the product list, then one customer's recent orders
function browse() {
  const products = http.get(`${BASE_URL}/products`, { tags: { name: 'GET /products' } });
  check(products, { 'products listed': (r) => r.status === 200 });

  const email = encodeURIComponent(randomCustomer());
  const orders = http.get(`${BASE_URL}/orders?customer_email=${email}`, {
    tags: { name: 'GET /orders' },
  });
  check(orders, { 'orders listed': (r) => r.status === 200 });
}

function createOrder() {
  const body = JSON.stringify({
    customer_email: randomCustomer(),
    product_id: randomInt(PRODUCTS),
    quantity: randomInt(5),
  });
  const response = http.post(`${BASE_URL}/orders`, body, {
    ...JSON_HEADERS,
    tags: { name: 'POST /orders' },
  });
  check(response, { 'order created': (r) => r.status === 201 });
  return response.status === 201 ? response.json('id') : null;
}

function createAndPay() {
  const orderId = createOrder();
  if (orderId === null) {
    return;
  }
  // About one card in twenty ends in 0002, which the bank declines
  const card = Math.random() < 0.05 ? '4000000000000002' : '4111111111111111';
  const response = http.post(
    `${BASE_URL}/orders/${orderId}/pay`,
    JSON.stringify({ card_number: card }),
    { ...JSON_HEADERS, tags: { name: 'POST /orders/{id}/pay' } },
  );
  check(response, {
    'payment answered': (r) => r.status === 200,
    'order paid or declined': (r) =>
      r.status === 200 && ['paid', 'payment_failed'].includes(r.json('status')),
  });
}

// Each iteration is one visitor: 60% browse, 25% create an order, 15% create and pay
export default function () {
  const pick = Math.random();
  if (pick < 0.6) {
    browse();
  } else if (pick < 0.85) {
    createOrder();
  } else {
    createAndPay();
  }
}
