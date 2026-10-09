"""Tests for the bank stub."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

CHARGE = {
    "amount_paise": 49900,
    "card_number": "4111111111111111",
    "merchant_id": "MRC000001",
}


def test_health_says_ok():
    assert client.get("/health").json() == {"status": "ok"}


def test_ordinary_card_is_approved():
    response = client.post("/authorize", json=CHARGE)

    assert response.status_code == 200
    body = response.json()
    assert body["approved"] is True
    assert body["reference"].startswith("BNK-")


def test_test_card_is_declined_with_a_reason():
    response = client.post(
        "/authorize", json={**CHARGE, "card_number": "4000000000000002"}
    )

    body = response.json()
    assert body["approved"] is False
    assert body["reason"] == "insufficient_funds"


def test_malformed_card_number_is_rejected():
    response = client.post("/authorize", json={**CHARGE, "card_number": "not-a-card"})

    assert response.status_code == 422
