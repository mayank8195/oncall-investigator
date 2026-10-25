"""Tests for the gateway. No real orders service is needed: its replies are faked."""

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app


def use_fake_orders(handler) -> None:
    """Replace the HTTP client to orders with one that calls `handler` instead."""
    app.state.orders = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://orders"
    )


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_says_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_response_carries_a_request_id(client):
    response = client.get("/health")

    assert len(response.headers["X-Request-ID"]) == 32


def test_request_id_from_the_caller_is_kept_and_passed_on(client):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["request_id"] = request.headers["X-Request-ID"]
        return httpx.Response(200, json=[])

    use_fake_orders(handler)

    response = client.get("/products", headers={"X-Request-ID": "abc123"})

    assert response.headers["X-Request-ID"] == "abc123"
    assert seen["request_id"] == "abc123"


def test_answer_from_orders_is_passed_back_unchanged(client):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "order not found"})

    use_fake_orders(handler)

    response = client.get("/orders/42")

    assert response.status_code == 404
    assert response.json() == {"detail": "order not found"}


def test_invalid_order_is_rejected_without_calling_orders(client):
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("orders should not be called")

    use_fake_orders(handler)

    response = client.post(
        "/orders",
        json={"customer_email": "not-an-email", "product_id": 1, "quantity": 1},
    )

    assert response.status_code == 422


def test_timeout_from_orders_becomes_504(client):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("too slow", request=request)

    use_fake_orders(handler)

    response = client.get("/products")

    assert response.status_code == 504


def test_orders_being_down_becomes_502(client):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    use_fake_orders(handler)

    response = client.get("/products")

    assert response.status_code == 502
