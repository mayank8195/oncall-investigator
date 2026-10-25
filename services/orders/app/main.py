"""The orders service: lists products, creates and lists orders, and has them paid.

Run with: uv run --directory services/orders uvicorn app.main:app --port 8001
"""

import logging
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.cache import ProductCache, get_cache
from app.db import get_session
from app.models import Order, Product
from app.payments import PaymentsClient, PaymentsError, PaymentsTimeout, get_payments
from app.schemas import OrderIn, OrderOut, PayIn, ProductOut

logger = logging.getLogger("orders")

app = FastAPI(title="orders")

# The most orders returned for one customer in a single reply
MAX_ORDERS_LISTED = 20

# What an endpoint asks for, and the function FastAPI calls to supply it
SessionDep = Annotated[Session, Depends(get_session)]
CacheDep = Annotated[ProductCache, Depends(get_cache)]
PaymentsDep = Annotated[PaymentsClient, Depends(get_payments)]


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness: the process is up. Touches nothing outside it."""
    return {"status": "ok"}


@app.get("/ready")
def ready(session: SessionDep) -> dict[str, str]:
    """Readiness: the database answers, so the service can do useful work."""
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="database unavailable") from None
    return {"status": "ready"}


@app.get("/products")
def list_products(session: SessionDep, cache: CacheDep) -> list[ProductOut]:
    """List every product, from the cache when possible and the database otherwise."""
    cached = cache.get_products()
    if cached is not None:
        return [ProductOut(**product) for product in cached]

    rows = session.scalars(select(Product).order_by(Product.id)).all()
    products = [ProductOut.model_validate(row) for row in rows]
    cache.set_products([product.model_dump() for product in products])
    return products


@app.post("/orders", status_code=201)
def create_order(body: OrderIn, session: SessionDep) -> OrderOut:
    product = session.get(Product, body.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="product not found")

    order = Order(
        customer_email=body.customer_email,
        merchant_id=product.merchant_id,
        product_id=product.id,
        quantity=body.quantity,
        amount_paise=product.price_paise * body.quantity,
        status="pending",
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return OrderOut.model_validate(order)


@app.get("/orders")
def list_orders(customer_email: str, session: SessionDep) -> list[OrderOut]:
    """List one customer's most recent orders. Relies on the index on customer_email."""
    rows = session.scalars(
        select(Order)
        .where(Order.customer_email == customer_email)
        .order_by(Order.id.desc())
        .limit(MAX_ORDERS_LISTED)
    ).all()
    return [OrderOut.model_validate(row) for row in rows]


@app.get("/orders/{order_id}")
def get_order(order_id: int, session: SessionDep) -> OrderOut:
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    return OrderOut.model_validate(order)


@app.post("/orders/{order_id}/pay")
def pay_order(
    order_id: int,
    body: PayIn,
    session: SessionDep,
    payments: PaymentsDep,
    x_request_id: Annotated[str, Header()] = "-",
) -> OrderOut:
    """Charge the order through payments, then record the outcome."""
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    if order.status == "paid":
        raise HTTPException(status_code=409, detail="order is already paid")

    # Copy what the call needs, then end the read transaction, so that no
    # database connection is held while waiting on payments.
    amount_paise, merchant_id = order.amount_paise, order.merchant_id
    session.commit()

    try:
        approved = payments.charge(
            order_id=order_id,
            amount_paise=amount_paise,
            card_number=body.card_number,
            merchant_id=merchant_id,
            request_id=x_request_id,
        )
    except PaymentsTimeout:
        logger.warning(
            "payments timed out: order_id=%s request_id=%s", order_id, x_request_id
        )
        raise HTTPException(
            status_code=504, detail="payments did not answer in time"
        ) from None
    except PaymentsError as error:
        logger.warning(
            "payments failed: order_id=%s request_id=%s error=%s",
            order_id,
            x_request_id,
            error,
        )
        raise HTTPException(status_code=502, detail="payments failed") from None

    order = session.get(Order, order_id)
    order.status = "paid" if approved else "payment_failed"
    session.commit()
    session.refresh(order)
    return OrderOut.model_validate(order)
