"""The client for the payments service."""

import httpx

from app import config


class PaymentsError(Exception):
    """Payments could not give a usable answer."""


class PaymentsTimeout(PaymentsError):
    """Payments did not answer within the time limit."""


class PaymentsClient:
    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def charge(
        self,
        *,
        order_id: int,
        amount_paise: int,
        card_number: str,
        merchant_id: str,
        request_id: str,
    ) -> bool:
        """Ask payments to charge a card. Returns True if the bank approved it."""
        try:
            response = self._client.post(
                "/charges",
                json={
                    "order_id": order_id,
                    "amount_paise": amount_paise,
                    "card_number": card_number,
                    "merchant_id": merchant_id,
                },
                headers={"X-Request-ID": request_id},
            )
        except httpx.TimeoutException as error:
            raise PaymentsTimeout("payments did not answer in time") from error
        except httpx.TransportError as error:
            raise PaymentsError("payments could not be reached") from error
        if response.status_code >= 400:
            raise PaymentsError(f"payments answered {response.status_code}")
        return response.json()["status"] == "approved"


_payments = PaymentsClient(
    httpx.Client(base_url=config.PAYMENTS_URL, timeout=config.PAYMENTS_TIMEOUT_SECONDS)
)


def get_payments() -> PaymentsClient:
    return _payments
