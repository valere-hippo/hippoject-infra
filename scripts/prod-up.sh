#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p traefik/letsencrypt
cp -n .env.production.example .env.production 2>/dev/null || true
touch traefik/letsencrypt/acme.json
chmod 600 traefik/letsencrypt/acme.json

docker compose --env-file .env.production -f compose.production.yml up -d
