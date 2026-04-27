#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
./scripts/ghcr-login.sh
docker compose --env-file .env.production -f compose.production.yml pull
docker compose --env-file .env.production -f compose.production.yml up -d
