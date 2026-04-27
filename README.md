# Hippoject

Hippoject is a Jira-inspired project management platform built with **Spring Boot**, **Angular**, **PostgreSQL**, **Keycloak** and now a production deployment stack around **Traefik**, **Terraform**, **Ansible** and **GitHub Actions self-hosted runners**.

## Repositories

- `hippoject-backend` → Spring Boot API
- `hippoject-frontend` → Angular application
- `hippoject-infra` → infra, compose, bootstrap and deployment automation

## Local development

### 1. Start infrastructure

```bash
cp .env.example .env
./scripts/dev-up.sh
```

### 2. Expected local endpoints

- PostgreSQL: `localhost:5432`
- Keycloak: `http://localhost:8081`
- Backend API: `http://localhost:8080/api`
- Backend WebSocket: `ws://localhost:8080/ws/realtime`
- Frontend: `http://localhost:4200`

## Production architecture

This repo ships a single-host production stack in `compose.production.yml` with:

- `https://hippoject.<domain>` → frontend
- `https://hippoject-api.<domain>` → backend
- `https://auth.<domain>` → Keycloak
- Traefik for reverse proxy and TLS
- PostgreSQL for persistence

## Token-based deployment model

Deployment is prepared to work **without SSH deploy keys**.

### How it works

- backend and frontend repos build Docker images and push them to **GHCR**
- deployment runs on a **self-hosted GitHub Actions runner** installed on the target server
- the runner performs local `docker compose pull` and `docker compose up -d`
- image pulls use **GHCR credentials** stored as GitHub secrets or in `.env.production`

### GitHub secrets expected in app repos

For `hippoject-backend` and `hippoject-frontend`:

- `DEPLOY_PATH`
- `GHCR_USERNAME`
- `GHCR_TOKEN`

Recommended token scope for `GHCR_TOKEN`:

- `read:packages` for pull
- `write:packages` if you also want to reuse it for manual image publishing

### GitHub secrets expected in infra repo

For `hippoject-infra`:

- `DEPLOY_PATH`
- `GHCR_USERNAME`
- `GHCR_TOKEN`

## Manual production startup

```bash
cp .env.production.example .env.production
./scripts/prod-up.sh
```

To refresh after new images are published:

```bash
./scripts/prod-pull.sh
```

## `.env.production`

Main variables:

- `ROOT_DOMAIN`
- `ACME_EMAIL`
- `POSTGRES_PASSWORD`
- `KEYCLOAK_ADMIN_PASSWORD`
- `GHCR_USERNAME`
- `GHCR_TOKEN`
- optional SMTP variables

## Terraform

Directory: `terraform/`

Current scope:

- creates the Hetzner DNS zone
- creates A records for:
  - `auth.<domain>`
  - `hippoject.<domain>`
  - `hippoject-api.<domain>`

Example:

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform apply
```

## Ansible

Directory: `ansible/`

Current scope:

- installs base packages
- installs Docker and Docker Compose plugin
- installs a **self-hosted GitHub Actions runner**
- clones or updates `hippoject-infra` on the server using a **GitHub token**
- renders `.env.production`
- starts the production stack

Recommended permissions for `github_pat` used by Ansible:

- repository read access to `hippoject-infra`
- permission to create repository runner registration tokens

Example:

```bash
cd ansible
cp inventory/production.ini.example inventory/production.ini
cp group_vars/all.example.yml group_vars/all.yml
ansible-playbook -i inventory/production.ini playbooks/bootstrap.yml
```

## DNS required

Point these records to the server IP:

- `hippoject.<domain>`
- `hippoject-api.<domain>`
- `auth.<domain>`

## Important note about Hetzner AX41-NVME

An AX41-NVME is a **Hetzner dedicated server**, not a Hetzner Cloud VM.

That means:

- Terraform here covers **DNS**
- Ansible covers **server bootstrap**
- ordering the dedicated server itself still happens manually in Hetzner

## Release / handoff

For a final verification pass, see:

- `RELEASE_CHECKLIST.md`
