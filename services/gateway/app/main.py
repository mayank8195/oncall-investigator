"""The gateway: the entry point that takes requests from outside.

Run with: uv run --directory services/gateway uvicorn app.main:app --reload
"""

from fastapi import FastAPI

app = FastAPI(title="gateway")


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the process is up and able to answer requests."""
    return {"status": "ok"}
