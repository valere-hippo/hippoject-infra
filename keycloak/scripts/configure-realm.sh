#!/bin/bash
set -euo pipefail

KEYCLOAK_URL="${KEYCLOAK_URL:-http://keycloak:8080}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-hippoject}"
KEYCLOAK_ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
KEYCLOAK_ADMIN_PASS="${KEYCLOAK_ADMIN_PASSWORD:-admin}"
KEYCLOAK_FRONTEND_CLIENT_ID="${KEYCLOAK_FRONTEND_CLIENT_ID:-hippoject-frontend}"
SMTP_PORT="${SMTP_PORT:-587}"
SMTP_USERNAME="${SMTP_USERNAME:-${SMTP_FROM:-}}"
APP_FRONTEND_URL="${APP_FRONTEND_URL:-http://localhost:4200}"

until /opt/keycloak/bin/kcadm.sh config credentials \
  --server "$KEYCLOAK_URL" \
  --realm master \
  --user "$KEYCLOAK_ADMIN_USER" \
  --password "$KEYCLOAK_ADMIN_PASS" >/dev/null 2>&1; do
  echo "[keycloak-init] waiting for Keycloak..."
  sleep 3
done

/opt/keycloak/bin/kcadm.sh update "realms/$KEYCLOAK_REALM" \
  -s "displayName=Hippoject" \
  -s "loginWithEmailAllowed=true" \
  -s "resetPasswordAllowed=true" \
  -s "verifyEmail=true" \
  -s "attributes.frontendUrl=$APP_FRONTEND_URL"

frontend_client_uuid="$({ /opt/keycloak/bin/kcadm.sh get clients -r "$KEYCLOAK_REALM" -q clientId="$KEYCLOAK_FRONTEND_CLIENT_ID" --fields id,clientId 2>/dev/null || true; } | tr -d '\n' | sed -E 's/.*"id"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')"

if [[ -n "$frontend_client_uuid" ]]; then
  /opt/keycloak/bin/kcadm.sh update "clients/$frontend_client_uuid" -r "$KEYCLOAK_REALM" \
    -s "rootUrl=$APP_FRONTEND_URL" \
    -s "baseUrl=$APP_FRONTEND_URL" \
    -s "redirectUris=[\"$APP_FRONTEND_URL/*\"]" \
    -s "webOrigins=[\"$APP_FRONTEND_URL\"]"
  echo "[keycloak-init] frontend client URLs updated."
else
  echo "[keycloak-init] frontend client not found, skipping client URL update."
fi

if [[ -n "${SMTP_SERVER:-}" && -n "${SMTP_FROM:-}" && -n "${SMTP_PASSWORD:-}" ]]; then
  /opt/keycloak/bin/kcadm.sh update "realms/$KEYCLOAK_REALM" \
    -s "smtpServer.host=$SMTP_SERVER" \
    -s "smtpServer.port=$SMTP_PORT" \
    -s "smtpServer.from=$SMTP_FROM" \
    -s "smtpServer.fromDisplayName=Hippoject" \
    -s "smtpServer.user=$SMTP_USERNAME" \
    -s "smtpServer.password=$SMTP_PASSWORD" \
    -s "smtpServer.auth=true" \
    -s "smtpServer.starttls=true"
  echo "[keycloak-init] realm SMTP configuration updated."
else
  echo "[keycloak-init] SMTP vars missing, skipping realm mail configuration."
fi
