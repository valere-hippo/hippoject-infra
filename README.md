# Hippoject Infra

Local infrastructure for Hippoject development.

## Includes

- PostgreSQL 16
- Keycloak 26
- preloaded `hippoject` realm
- ready-to-use frontend and backend clients

## Quick start

```bash
cp .env.example .env
./scripts/dev-up.sh
```

Endpoints:

- PostgreSQL: `localhost:5432`
- Keycloak: `http://localhost:8081`
- Keycloak Admin: `admin / admin`
- Demo realm: `hippoject`

## Default Keycloak clients

- `hippoject-frontend` (public PKCE client)
- `hippoject-backend` (bearer-only API client)

## Stop

```bash
./scripts/dev-down.sh
```
