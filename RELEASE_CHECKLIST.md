# Hippoject Release / Demo Checklist

## 1. Infrastructure

- [ ] `cp .env.example .env`
- [ ] `./scripts/dev-up.sh`
- [ ] PostgreSQL reachable on `localhost:5432`
- [ ] Keycloak reachable on `http://localhost:8081`

## 2. Backend

- [ ] Java 21 available
- [ ] backend starts cleanly
- [ ] Flyway migrations apply successfully
- [ ] API responds on `http://localhost:8080/api`
- [ ] WebSocket endpoint accepts connections on `/ws/realtime`

## 3. Frontend

- [ ] `npm install --include=dev`
- [ ] `npm run build`
- [ ] frontend can log in with Keycloak
- [ ] dashboard loads without archived projects leaking into counts
- [ ] projects overview can archive and restore projects
- [ ] board updates work on desktop and mobile-sized layout
- [ ] issue navigator can show archived issues and restore them
- [ ] backlog can show archived sprints and restore them
- [ ] notification inbox updates live

## 4. Auth

- [ ] `SECURITY_ENABLED=true` verified once before demo/handoff
- [ ] `JWT_JWK_SET_URI` points to the active Keycloak realm certs
- [ ] WebSocket realtime works with auth enabled

## 5. Email notifications

- [ ] SMTP env vars set only in runtime config, not committed
- [ ] mention notification tested
- [ ] assignee notification tested
- [ ] sprint lifecycle notification tested

## 6. Demo flow suggestion

- [ ] create project
- [ ] add project members
- [ ] create sprint
- [ ] create epic + child issues
- [ ] move issue across board
- [ ] add comment with mention
- [ ] show live notification update
- [ ] archive and restore an issue/sprint/project

## 7. Nice-to-clean before external handoff

- [ ] review repo READMEs
- [ ] verify no secrets are committed
- [ ] confirm demo users / test data are intentional
- [ ] note Java toolchain requirement clearly for backend users
