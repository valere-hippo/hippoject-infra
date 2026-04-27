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

Target platform now includes **Hetzner Cloud CPX62** as the recommended first production host.

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

Current scope for the **Hetzner Cloud CPX62** path:

- creates the Hetzner Cloud server
- creates and attaches a firewall
- creates and attaches a persistent volume
- imports the bootstrap SSH public key into Hetzner Cloud
- bootstraps the VM with cloud-init
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
terraform output server_ipv4
```

Useful outputs:

- `server_ipv4`
- `ansible_inventory_entry`
- `ssh_command`

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

There is also a short helper note in `ansible/README.md`.

## DNS required

Point these records to the server IP:

- `hippoject.<domain>`
- `hippoject-api.<domain>`
- `auth.<domain>`

## CPX62 recommendation

A **CPX62** is a Hetzner Cloud VM, so it fits this repo very well.

That means:

- Terraform can provision the VM itself
- Terraform can also wire DNS and base firewalling
- Ansible can bootstrap the host after provisioning
- GitHub Actions self-hosted runner can live on the same machine for the first deployment stage

If you later move to multiple hosts, this repo can still be split by role, but CPX62 is a very solid first step.

## Release / handoff

For a final verification pass, see:

- `RELEASE_CHECKLIST.md`
