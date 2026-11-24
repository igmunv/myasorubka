#!/usr/bin/env bash
# ТОЛЬКО НА СЕРВЕРЕ
docker compose run --rm migrate
docker compose restart public_bot admin_bot battle_manager