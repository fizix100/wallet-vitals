FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /uvx /bin/
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src

RUN uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH" \
    DATABASE_PATH="/data/wallet_vitals.db"

EXPOSE 8000
VOLUME ["/data"]

CMD ["uvicorn", "wallet_vitals.web.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
