# Hippoject Infra

Local infrastructure for Hippoject development.

## Includes

- PostgreSQL 16
- Keycloak 26
- preloaded `hippoject` realm
- ready-to-use frontend and backend clients
- example environment file for SMTP notification wiring

## Quick start

```bash
cp .env.example .env
./scripts/dev-up.sh
```

## Local endpoints

- PostgreSQL: `localhost:5432`
- Keycloak: `http://localhost:8081`
- Keycloak Admin: `admin / admin`
- Demo realm: `hippoject`

## Default Keycloak clients

- `hippoject-frontend` (public PKCE client)
- `hippoject-backend` (bearer-style API client)

## Expected app wiring

### Backend

- Spring Boot API on `http://localhost:8080`
- WebSocket realtime endpoint on `ws://localhost:8080/ws/realtime`

### Frontend

- Angular app on `http://localhost:4200`
- backend API base `http://localhost:8080/api`

## Optional email notification env vars

Add these to `.env` for SMTP-backed notifications:

- `EMAIL_NOTIFICATIONS_ENABLED=true`
- `SMTP_SERVER=smtp.gmail.com`
- `SMTP_PORT=587`
- `EMAIL=...`
- `PASSWORD=...`

## Stop

```bash
./scripts/dev-down.sh
```

## Release prep

See `RELEASE_CHECKLIST.md` for a short final verification pass before demo or handoff.
