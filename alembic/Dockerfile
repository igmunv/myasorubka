FROM python:3.11-slim

WORKDIR /app/alembic

COPY alembic/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic/ .
COPY shared/ ./shared/