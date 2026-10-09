"""The gateway: the entry point that takes requests from outside.

It checks each request, gives it an ID, and passes it to the orders service
with a time limit.

Run with: uv run --directory services/gateway uvicorn app.main:app --reload
"""

import logging
import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request, Response

from app import config
from app.schemas import CreateOrder, PayOrder

logger = logging.getLogger("gateway")

REQUEST_ID_HEADER = "X-Request-ID"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open one HTTP client for the life of the process, and close it at the end."""
    app.state.orders = httpx.AsyncClient(
        base_url=config.ORDERS_URL,
        timeout=config.DOWNSTREAM_TIMEOUT_SECONDS,
    )
    yield
    await app.state.orders.aclose()


app = FastAPI(title="gateway", lifespan=lifespan)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Give every request an ID, and return it in the response."""
    request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = request_id
    return response


async def forward(request: Request, method: str, path: str, **kwargs) -> Response:
    """Send a request to orders and hand its answer back unchanged."""
    client: httpx.AsyncClient = request.app.state.orders
    request_id = request.state.request_id
    try:
        upstream = await client.request(
            method, path, headers={REQUEST_ID_HEADER: request_id}, **kwargs
        )
    except httpx.TimeoutException:
        logger.warning(
            "orders timed out: %s %s request_id=%s", method, path, request_id
        )
        raise HTTPException(
            status_code=504, detail="orders did not answer in time"
        ) from None
    except httpx.TransportError as error:
        logger.warning(
            "orders unreachable: %s %s request_id=%s error=%r",
            method,
            path,
            request_id,
            error,
        )
        raise HTTPException(
            status_code=502, detail="orders could not be reached"
        ) from None
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type"),
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the process is up and able to answer requests."""
    return {"status": "ok"}


@app.get("/products")
async def list_products(request: Request) -> Response:
    return await forward(request, "GET", "/products")


@app.get("/orders")
async def list_orders(request: Request, customer_email: str) -> Response:
    return await forward(
        request, "GET", "/orders", params={"customer_email": customer_email}
    )


@app.get("/orders/{order_id}")
async def get_order(request: Request, order_id: int) -> Response:
    return await forward(request, "GET", f"/orders/{order_id}")


@app.post("/orders", status_code=201)
async def create_order(request: Request, body: CreateOrder) -> Response:
    return await forward(request, "POST", "/orders", json=body.model_dump())


@app.post("/orders/{order_id}/pay")
async def pay_order(request: Request, order_id: int, body: PayOrder) -> Response:
    return await forward(
        request, "POST", f"/orders/{order_id}/pay", json=body.model_dump()
    )
