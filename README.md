# Hippoject

Hippoject is a Jira-inspired project management platform built with **Spring Boot**, **Angular**, **PostgreSQL**, and **Keycloak**.
It already covers the core end-to-end workflows teams need to plan, track, and collaborate on delivery work, including projects, issues, epics, sprints, notifications, archive/restore flows, and realtime updates.

## Why Hippoject?

Hippoject was built to be more than a UI prototype.
The goal was to create a working product foundation with real backend flows, real persistence, authentication, team roles, and live behavior across the application.

## Core Features

- **Projects** with archive and restore flows
- **Issues** with priorities, labels, types, assignees, comments, and archive/restore
- **Epics** with child issue progress tracking
- **Sprints** with planning, lifecycle actions, backlog assignment, and restore flow
- **Kanban board** with drag-and-drop and mobile-friendly quick move controls
- **Issue navigator** with saved filters and archived issue view
- **Role-based collaboration** with Keycloak integration
- **Project members** and workspace directory
- **Notification inbox** plus SMTP-backed email notifications
- **Project activity feed** and persisted audit history
- **Realtime updates** over WebSocket
- **PostgreSQL + Flyway** persistence and schema migrations

## Tech Stack

### Backend
- Java 21
- Spring Boot
- Spring Security
- Flyway
- PostgreSQL
- WebSocket realtime

### Frontend
- Angular
- TypeScript
- standalone component-based SPA

### Auth / Infra
- Keycloak
- Docker Compose
- PostgreSQL 16

## Repository Structure

This project is split into three repos:

- `hippoject-backend` → Spring Boot API
- `hippoject-frontend` → Angular application
- `hippoject-infra` → local infrastructure, setup, and release helpers

## Local Development

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

### 3. Run backend

In `hippoject-backend`:

```bash
./mvnw spring-boot:run
```

### 4. Run frontend

In `hippoject-frontend`:

```bash
npm install --include=dev
npm start
```

## Authentication

Hippoject is designed for Keycloak-backed authentication and role-based access.
For local development, the frontend and backend can be wired to the included local Keycloak realm.

Important backend auth variables:

- `SECURITY_ENABLED`
- `JWT_JWK_SET_URI`

Important frontend auth variables:

- Keycloak `url`
- Keycloak `realm`
- Keycloak `clientId`

## Email Notifications

Hippoject can send SMTP-backed email notifications for important events such as mentions, assignments, and sprint changes.

Configure via environment variables:

- `EMAIL_NOTIFICATIONS_ENABLED=true`
- `SMTP_SERVER=smtp.gmail.com`
- `SMTP_PORT=587`
- `EMAIL=...`
- `PASSWORD=...`

## Realtime Behavior

The application uses **WebSocket-based realtime updates** to keep the UI fresh without depending on constant polling.
This includes live refresh behavior for project activity and notifications, with heartbeat/reconnect handling built into the frontend.

## Demo Flow

A good Hippoject demo flow is:

1. Create a project
2. Add project members
3. Create a sprint
4. Create an epic and child issues
5. Move issues across the board
6. Add a comment with a mention
7. Show live notifications
8. Archive and restore an issue, sprint, or project

## Release / Handoff

For a final verification pass, see:

- `RELEASE_CHECKLIST.md`

## Current State

Hippoject is already in a strong state for:

- demos
- portfolio presentation
- internal showcase
- further product expansion

It is not just a static concept, but a working foundation for a modern Jira-like delivery platform.
