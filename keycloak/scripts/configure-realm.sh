#!/bin/bash
set -euo pipefail

if [[ -z "${SMTP_SERVER:-}" || -z "${SMTP_FROM:-}" || -z "${SMTP_PASSWORD:-}" ]]; then
  echo "[keycloak-init] SMTP vars missing, skipping realm mail configuration."
  exit 0
fi

KEYCLOAK_URL="${KEYCLOAK_URL:-http://keycloak:8080}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-hippoject}"
KEYCLOAK_ADMIN_USER="${KEYCLOAK_ADMIN:-admin}"
KEYCLOAK_ADMIN_PASS="${KEYCLOAK_ADMIN_PASSWORD:-admin}"
SMTP_PORT="${SMTP_PORT:-587}"
SMTP_USERNAME="${SMTP_USERNAME:-$SMTP_FROM}"
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
  -s "smtpServer.host=$SMTP_SERVER" \
  -s "smtpServer.port=$SMTP_PORT" \
  -s "smtpServer.from=$SMTP_FROM" \
  -s "smtpServer.fromDisplayName=Hippoject" \
  -s "smtpServer.user=$SMTP_USERNAME" \
  -s "smtpServer.password=$SMTP_PASSWORD" \
  -s "smtpServer.auth=true" \
  -s "smtpServer.starttls=true"

/opt/keycloak/bin/kcadm.sh update "realms/$KEYCLOAK_REALM" \
  -s "attributes.frontendUrl=$APP_FRONTEND_URL"

echo "[keycloak-init] realm SMTP configuration updated."
