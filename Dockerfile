FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m botuser

WORKDIR /home/botuser/app

COPY pyproject.toml .
RUN pip install --no-cache-dir \
    aiogram==3.7.0 \
    pydantic-settings==2.3.0 \
    sqlalchemy==2.0.30 \
    asyncpg==0.29.0 \
    alembic==1.13.1 \
    "apscheduler==4.0.0a4" \
    redis==5.0.4 \
    structlog==24.1.0 \
    python-dotenv==1.0.1 \
    httpx==0.27.0 \
    google-generativeai==0.8.6 \
    pytz==2024.1 \
    aiohttp==3.9.5 \
    psycopg2-binary==2.9.9

COPY . .

USER botuser

CMD ["sh", "-c", "alembic upgrade head && python -m bot.main"]
