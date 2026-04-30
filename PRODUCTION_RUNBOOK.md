# Hippoject production runbook

This file is the operational handoff for the single-host production deployment.

## Production endpoints

- Frontend: `https://hippoject.<domain>`
- API: `https://hippoject-api.<domain>`
- Keycloak: `https://auth.<domain>`
- Keycloak admin console: `https://auth.<domain>/admin/master/console/`

## Where the stack lives on the server

Default deployment path:

```bash
/opt/hippoject-infra
```

Main production files:

- `.env.production`
- `compose.production.yml`

## Retrieve the active runtime credentials

On the server:

```bash
cd /opt/hippoject-infra
sed -n '1,120p' .env.production
```

Useful targeted checks:

```bash
grep -E '^(POSTGRES_USER|POSTGRES_PASSWORD|POSTGRES_DB|KEYCLOAK_REALM|KEYCLOAK_ADMIN|KEYCLOAK_ADMIN_PASSWORD|GHCR_USERNAME)=' .env.production
```

## Keycloak admin login

Important: the bootstrap admin account is created in the **master** realm.

Use:

- Console URL: `https://auth.<domain>/admin/master/console/`
- Username: value of `KEYCLOAK_ADMIN`
- Password: value of `KEYCLOAK_ADMIN_PASSWORD`

If the root URL opens but the login fails, verify that you are logging into the **master** realm admin console, not the `hippoject` application realm.

## Database access

PostgreSQL is an internal container service. It is not expected to be reachable directly from the public internet.

### Connect from the server host into the app database

```bash
cd /opt/hippoject-infra
docker compose --env-file .env.production -f compose.production.yml exec postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

### Connect into the Keycloak database

```bash
cd /opt/hippoject-infra
docker compose --env-file .env.production -f compose.production.yml exec postgres \
  psql -U "$POSTGRES_USER" -d keycloak
```

### One-off SQL checks

```bash
cd /opt/hippoject-infra
docker compose --env-file .env.production -f compose.production.yml exec postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\dt'
```

## Service status

```bash
cd /opt/hippoject-infra
docker compose --env-file .env.production -f compose.production.yml ps
```

Useful container names:

- `hippoject-traefik`
- `hippoject-postgres`
- `hippoject-keycloak`
- `hippoject-keycloak-init`
- `hippoject-backend`
- `hippoject-frontend`

## Logs

### Follow the whole stack

```bash
cd /opt/hippoject-infra
docker compose --env-file .env.production -f compose.production.yml logs -f --tail=200
```

### Follow one service

```bash
cd /opt/hippoject-infra
docker compose --env-file .env.production -f compose.production.yml logs -f --tail=200 backend
```

Replace `backend` with one of:

- `frontend`
- `keycloak`
- `keycloak-init`
- `postgres`
- `traefik`

### Quick error scan

```bash
cd /opt/hippoject-infra
docker compose --env-file .env.production -f compose.production.yml logs --tail=300 backend keycloak traefik
```

## Restart operations

### Pull fresh images and refresh the stack

```bash
cd /opt/hippoject-infra
./scripts/prod-pull.sh
```

### Full start

```bash
cd /opt/hippoject-infra
./scripts/prod-up.sh
```

### Restart a single service

```bash
cd /opt/hippoject-infra
docker compose --env-file .env.production -f compose.production.yml restart backend
```

## Health checks

```bash
curl -I https://hippoject.<domain>
curl https://hippoject-api.<domain>/actuator/health
curl https://auth.<domain>/realms/hippoject/.well-known/openid-configuration
```

## Monitoring recommendation

For a simple first step, run **Uptime Kuma** on the same host and monitor:

- `https://hippoject.<domain>`
- `https://hippoject-api.<domain>/actuator/health`
- `https://auth.<domain>/realms/hippoject/.well-known/openid-configuration`

A starter compose file is available in `monitoring/uptime-kuma.compose.yml`.

For a fuller setup later, add:

- Uptime Kuma for external checks
- Node Exporter for host metrics
- cAdvisor for container metrics
- Grafana + Prometheus for dashboards and alerting
- Loki + Promtail for central log search

## Secret rotation checklist

If credentials were ever shared in chat or logs, rotate at least:

- `POSTGRES_PASSWORD`
- `KEYCLOAK_ADMIN_PASSWORD`
- `GHCR_TOKEN`
- `github_pat`
- any SMTP password if configured

After rotation, update:

- server `.env.production`
- `ansible/group_vars/all.yml`
- GitHub repository secrets
