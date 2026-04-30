# Hippoject production runbook

This file is the operational handoff for the single-host production deployment.

## Production endpoints

- Frontend: `https://hippoject.<domain>`
- API: `https://hippoject-api.<domain>`
- Keycloak: `https://auth.<domain>`
- Monitoring: `https://monitoring.<domain>`
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
grep -E '^(POSTGRES_USER|POSTGRES_PASSWORD|POSTGRES_DB|KEYCLOAK_REALM|KEYCLOAK_ADMIN|KEYCLOAK_ADMIN_PASSWORD|GHCR_USERNAME|EMAIL_NOTIFICATIONS_ENABLED|SMTP_SERVER|SMTP_PORT|EMAIL)=' .env.production
```

## Mail configuration

Mail is driven through `.env.production` and is already wired into both the backend and `keycloak-init`.

Relevant variables:

```bash
EMAIL_NOTIFICATIONS_ENABLED=false
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL=bat.hipposideros@gmail.com
PASSWORD=<gmail-app-password>
```

After changing mail settings, refresh the stack:

```bash
cd /opt/hippoject-infra
./scripts/prod-pull.sh
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

### Connect from IntelliJ, pgAdmin, DBeaver, or another local SQL client

Use an SSH tunnel to the production host, then connect to localhost on your own machine.

Example:

```bash
ssh -L 5432:127.0.0.1:5432 ansible@46.225.179.25
```

Then use this JDBC URL locally:

```text
jdbc:postgresql://127.0.0.1:5432/hippoject
```

Typical client settings:

- Host: `127.0.0.1`
- Port: `5432`
- Database: `hippoject`
- User: `hippoject`
- Password: value of `POSTGRES_PASSWORD`

Important: `jdbc:postgresql://46.225.179.25:5432/hippoject` will normally fail from the public internet because port `5432` is intentionally not exposed.

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

## Deployment pipelines

### If you change `hippoject-backend`

Run or let GitHub run:

- workflow: `hippoject-backend-deploy`

This builds the backend image, pushes it to GHCR, then the self-hosted runner pulls and restarts only `backend`.

### If you change `hippoject-frontend`

Run or let GitHub run:

- workflow: `hippoject-frontend-deploy`

This builds the frontend image, pushes it to GHCR, then the self-hosted runner pulls and restarts only `frontend`.

### If you change `hippoject-infra`

Run or let GitHub run:

- workflow: `hippoject-infra-sync`

Use the infra pipeline when you changed files such as:

- `compose.production.yml`
- scripts under `scripts/`
- Keycloak import or config scripts
- Ansible/bootstrap assets that must be synced to `/opt/hippoject-infra`
- runbooks/ops files that you also want present on the server

The infra pipeline syncs the repo to `DEPLOY_PATH` and runs `./scripts/prod-pull.sh`.

### Practical rule

- app code change only → run backend or frontend pipeline
- infra/config/script change → run infra pipeline
- changed app repo and infra repo → run both, usually infra first if the app depends on new infra config, otherwise app pipeline alone is enough

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

In the current infra repo, Uptime Kuma can be exposed directly through Traefik at:

- `https://monitoring.<domain>`

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
