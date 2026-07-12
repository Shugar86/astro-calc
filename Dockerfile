# astro-calc — stateless ephemeris microservice
#
# pyswisseph is a C extension with no prebuilt linux wheel, so dependencies are
# compiled in a builder stage that carries a toolchain; the runtime stage copies
# only the resulting virtualenv (same base image => matching interpreter path)
# and ships without compilers. The app package is put on PYTHONPATH rather than
# installed as a wheel — no build step, no packaging metadata needed at runtime.

# ---- builder ---------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-install-project

# ---- runtime ---------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS runtime
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app
COPY --from=builder /app/.venv /app/.venv
COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
