"""A stub for the external bank API that payments charges cards through.

It stands in for a third party we do not control. It approves most cards,
declines a known test card, and takes a few milliseconds to answer.

Run with: uv run --directory services/mock-bank uvicorn app.main:app --port 8002
"""

import asyncio
import os
import random
import uuid

from fastapi import FastAPI
from pydantic import BaseModel, Field

# The bank takes between these two times to answer, in milliseconds
MIN_LATENCY_MS = int(os.environ.get("BANK_MIN_LATENCY_MS", "20"))
MAX_LATENCY_MS = int(os.environ.get("BANK_MAX_LATENCY_MS", "80"))

# Cards ending in these digits are declined, like a real bank's test cards
DECLINED_SUFFIX = "0002"

app = FastAPI(title="mock-bank")


class AuthorizeRequest(BaseModel):
    amount_paise: int = Field(gt=0)
    card_number: str = Field(pattern=r"^\d{12,19}$")
    merchant_id: str = Field(min_length=1, max_length=32)


class AuthorizeResponse(BaseModel):
    approved: bool
    reference: str
    reason: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/authorize")
async def authorize(body: AuthorizeRequest) -> AuthorizeResponse:
    """Approve or decline a charge, after a short realistic delay."""
    await asyncio.sleep(random.uniform(MIN_LATENCY_MS, MAX_LATENCY_MS) / 1000)
    reference = f"BNK-{uuid.uuid4().hex[:12].upper()}"
    if body.card_number.endswith(DECLINED_SUFFIX):
        return AuthorizeResponse(
            approved=False, reference=reference, reason="insufficient_funds"
        )
    return AuthorizeResponse(approved=True, reference=reference)
