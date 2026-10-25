"""The shapes of the JSON that orders accepts and returns."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price_paise: int
    merchant_id: str


class OrderIn(BaseModel):
    customer_email: str = Field(min_length=3, max_length=254)
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=20)


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_email: str
    merchant_id: str
    product_id: int
    quantity: int
    amount_paise: int
    status: str
    created_at: datetime


class PayIn(BaseModel):
    card_number: str = Field(pattern=r"^\d{12,19}$")
