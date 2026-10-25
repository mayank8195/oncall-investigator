# The mock-bank image.
# Built from the repository root, because the lock file shared by all Python
# services lives there:  docker build -f services/mock-bank/Dockerfile .

FROM python:3.12.15-slim-bookworm

# The uv binary, copied out of its official image
COPY --from=ghcr.io/astral-sh/uv:0.12.24 /uv /usr/local/bin/uv

# UV_PROJECT_ENVIRONMENT: where uv creates the virtual environment
# UV_COMPILE_BYTECODE:    compile .py files at build time, for a faster start
# UV_LINK_MODE=copy:      copy packages into the environment (no hard links across layers)
# UV_PYTHON_DOWNLOADS:    use the image's Python, never download another
# PYTHONUNBUFFERED:       print log lines immediately
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /repo

# Dependencies first. These files change rarely, so this layer is reused from
# the cache on most builds. uv needs every workspace member's pyproject.toml
# to read the shared lock file, but installs only this service's packages.
COPY pyproject.toml uv.lock .python-version ./
COPY services/gateway/pyproject.toml services/gateway/
COPY services/orders/pyproject.toml services/orders/
COPY services/mock-bank/pyproject.toml services/mock-bank/
RUN uv sync --frozen --no-dev --package mock-bank

# The code last. It changes often, and only this layer is rebuilt when it does.
COPY services/mock-bank/app services/mock-bank/app

# Run as an ordinary user, not root
RUN useradd --system --no-create-home app
USER app

WORKDIR /repo/services/mock-bank
EXPOSE 8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
