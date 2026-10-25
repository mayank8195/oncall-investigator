"""The shapes of the request bodies the gateway accepts.

These are the gateway's own models. They are not imported from orders: the
two services share only the JSON that crosses the network.
"""

from pydantic import BaseModel, Field


class CreateOrder(BaseModel):
    customer_email: str = Field(
        min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+$"
    )
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=20)


class PayOrder(BaseModel):
    card_number: str = Field(pattern=r"^\d{12,19}$")
