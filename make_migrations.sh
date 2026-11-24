#!/usr/bin/env bash
# ТОЛЬКО ЛОКАЛЬНО
set -e

if [ -z "$1" ]; then
  echo "Укажи название миграции: ./makemigrations.sh \"add_user_field\""
  exit 1
fi

docker compose up -d postgres
docker compose run --rm migrate alembic -c /app/alembic/alembic.ini revision --autogenerate -m "$1"

# Если запускаешь впервые на БД с существующими таблицами:
# docker compose run --rm migrate alembic -c /app/alembic/alembic.ini stamp head
# Если таблиц нет, то просто запускай docker compose, там будет upgrade head

# Изменил модели - запускаешь этот скрипт. Затем обязательно смотришь в versions/ файл, чтоб были нужные операции.