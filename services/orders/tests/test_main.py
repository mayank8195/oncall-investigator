"""Tests for orders.

Nothing outside the process is needed. Postgres is replaced by an in-memory
SQLite database, and Redis and payments by small fakes.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.cache import get_cache
from app.db import Base, get_session
from app.main import app
from app.models import Product
from app.payments import PaymentsError, PaymentsTimeout, get_payments

CARD = {"card_number": "4111111111111111"}


class FakeCache:
    """A cache held in memory. With `broken=True` it behaves like Redis being down."""

    def __init__(self, broken: bool = False) -> None:
        self.broken = broken
        self.stored = None
        self.reads = 0

    def get_products(self):
        self.reads += 1
        return None if self.broken else self.stored

    def set_products(self, products) -> None:
        if not self.broken:
            self.stored = products


class FakePayments:
    """Stands in for the payments service. `outcome` is what a charge does."""

    def __init__(self, outcome=True) -> None:
        self.outcome = outcome
        self.calls = []

    def charge(self, **kwargs) -> bool:
        self.calls.append(kwargs)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        session.add(
            Product(
                id=1, name="Kinnow crate", price_paise=49900, merchant_id="MRC000001"
            )
        )
        session.commit()
    return factory


@pytest.fixture
def cache():
    return FakeCache()


@pytest.fixture
def payments():
    return FakePayments()


@pytest.fixture
def client(session_factory, cache, payments):
    def override_session():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_cache] = lambda: cache
    app.dependency_overrides[get_payments] = lambda: payments
    yield TestClient(app)
    app.dependency_overrides.clear()


def create_order(client) -> dict:
    response = client.post(
        "/orders",
        json={"customer_email": "asha@example.com", "product_id": 1, "quantity": 2},
    )
    assert response.status_code == 201
    return response.json()


def test_health_says_ok(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ready_when_the_database_answers(client):
    assert client.get("/ready").json() == {"status": "ready"}


def test_products_come_from_the_database_then_from_the_cache(client, cache):
    first = client.get("/products").json()
    assert first == [
        {
            "id": 1,
            "name": "Kinnow crate",
            "price_paise": 49900,
            "merchant_id": "MRC000001",
        }
    ]
    assert cache.stored == first

    cache.stored = [
        {"id": 9, "name": "From cache", "price_paise": 1, "merchant_id": "MRC000009"}
    ]
    assert client.get("/products").json()[0]["name"] == "From cache"


def test_products_still_work_when_the_cache_is_down(client, cache):
    cache.broken = True

    response = client.get("/products")

    assert response.status_code == 200
    assert response.json()[0]["name"] == "Kinnow crate"


def test_order_amount_is_price_times_quantity(client):
    order = create_order(client)

    assert order["amount_paise"] == 99800
    assert order["status"] == "pending"
    assert order["merchant_id"] == "MRC000001"


def test_order_for_unknown_product_is_404(client):
    response = client.post(
        "/orders",
        json={"customer_email": "asha@example.com", "product_id": 999, "quantity": 1},
    )

    assert response.status_code == 404


def test_orders_are_listed_by_customer_newest_first(client):
    first = create_order(client)
    second = create_order(client)

    listed = client.get("/orders", params={"customer_email": "asha@example.com"}).json()

    assert [order["id"] for order in listed] == [second["id"], first["id"]]
    assert (
        client.get("/orders", params={"customer_email": "nobody@example.com"}).json()
        == []
    )


def test_unknown_order_is_404(client):
    assert client.get("/orders/999").status_code == 404


def test_approved_payment_marks_the_order_paid(client, payments):
    order = create_order(client)

    response = client.post(
        f"/orders/{order['id']}/pay", json=CARD, headers={"X-Request-ID": "abc123"}
    )

    assert response.json()["status"] == "paid"
    assert payments.calls == [
        {
            "order_id": order["id"],
            "amount_paise": 99800,
            "card_number": "4111111111111111",
            "merchant_id": "MRC000001",
            "request_id": "abc123",
        }
    ]


def test_declined_payment_marks_the_order_failed(client, payments):
    payments.outcome = False
    order = create_order(client)

    response = client.post(f"/orders/{order['id']}/pay", json=CARD)

    assert response.status_code == 200
    assert response.json()["status"] == "payment_failed"


def test_paying_twice_is_refused(client, payments):
    order = create_order(client)
    client.post(f"/orders/{order['id']}/pay", json=CARD)

    response = client.post(f"/orders/{order['id']}/pay", json=CARD)

    assert response.status_code == 409
    assert len(payments.calls) == 1


def test_payments_timeout_becomes_504_and_the_order_stays_pending(client, payments):
    payments.outcome = PaymentsTimeout("too slow")
    order = create_order(client)

    response = client.post(f"/orders/{order['id']}/pay", json=CARD)

    assert response.status_code == 504
    assert client.get(f"/orders/{order['id']}").json()["status"] == "pending"


def test_payments_failure_becomes_502(client, payments):
    payments.outcome = PaymentsError("payments answered 500")
    order = create_order(client)

    response = client.post(f"/orders/{order['id']}/pay", json=CARD)

    assert response.status_code == 502
