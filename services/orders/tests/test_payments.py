"""Tests for the payments client: how each kind of answer from payments is read."""

import httpx
import pytest

from app.payments import PaymentsClient, PaymentsError, PaymentsTimeout

CHARGE = {
    "order_id": 7,
    "amount_paise": 49900,
    "card_number": "4111111111111111",
    "merchant_id": "MRC000001",
    "request_id": "abc123",
}


def client_answering(handler) -> PaymentsClient:
    return PaymentsClient(
        httpx.Client(transport=httpx.MockTransport(handler), base_url="http://payments")
    )


def test_approved_charge_is_true_and_the_request_id_is_passed_on():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["request_id"] = request.headers["X-Request-ID"]
        return httpx.Response(201, json={"status": "approved"})

    assert client_answering(handler).charge(**CHARGE) is True
    assert seen["request_id"] == "abc123"


def test_declined_charge_is_false():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(201, json={"status": "declined"})

    assert client_answering(handler).charge(**CHARGE) is False


def test_no_answer_in_time_is_a_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("too slow", request=request)

    with pytest.raises(PaymentsTimeout):
        client_answering(handler).charge(**CHARGE)


def test_504_from_payments_is_a_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(504, json={"detail": "the bank did not answer in time"})

    with pytest.raises(PaymentsTimeout):
        client_answering(handler).charge(**CHARGE)


def test_any_other_error_status_is_a_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    with pytest.raises(PaymentsError):
        client_answering(handler).charge(**CHARGE)
