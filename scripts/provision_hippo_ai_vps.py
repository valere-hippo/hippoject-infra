#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from textwrap import indent
from typing import Any
import subprocess

HCLOUD_API_ROOT = "https://api.hetzner.cloud/v1"
CLOUDFLARE_API_ROOT = "https://api.cloudflare.com/client/v4"


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def fail(message: str) -> None:
    raise SystemExit(message)


def mask(value: str) -> None:
    if value:
        print(f"::add-mask::{value}")


def request_json(base_url: str, method: str, path: str, token_header: str, token: str, payload: dict | None = None) -> Any:
    headers = {
        token_header: token,
        "Content-Type": "application/json",
    }
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{base_url}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def wait_for_health(base_url: str, timeout_seconds: int = 3600, interval_seconds: int = 15) -> dict:
    deadline = time.time() + timeout_seconds
    health_url = f"{base_url.rstrip('/')}/health"
    last_error: str | None = None
    while time.time() < deadline:
        try:
            req = urllib.request.Request(health_url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                payload = json.load(resp)
                if isinstance(payload, dict) and payload.get("status") == "ok":
                    return payload
                last_error = f"unexpected payload: {payload!r}"
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
        print(f"Waiting for backend health at {health_url} ...")
        time.sleep(interval_seconds)
    fail(f"Backend did not become healthy within {timeout_seconds}s: {last_error or 'unknown error'}")


def upsert_hcloud_ssh_key(token: str, key_name: str, public_key: str) -> int:
    payload = request_json(HCLOUD_API_ROOT, "GET", "/ssh_keys", "Authorization", f"Bearer {token}")
    keys = payload.get("ssh_keys", []) if isinstance(payload, dict) else []
    existing = next(
        (
            item
            for item in keys
            if item.get("name") == key_name or item.get("public_key") == public_key
        ),
        None,
    )
    if existing and existing.get("id"):
        return int(existing["id"])
    created: dict[str, Any] = {}
    try:
        created = request_json(
            HCLOUD_API_ROOT,
            "POST",
            "/ssh_keys",
            "Authorization",
            f"Bearer {token}",
            {"name": key_name, "public_key": public_key},
        )
    except urllib.error.HTTPError as exc:
        if exc.code == 409:
            payload = request_json(HCLOUD_API_ROOT, "GET", "/ssh_keys", "Authorization", f"Bearer {token}")
            keys = payload.get("ssh_keys", []) if isinstance(payload, dict) else []
            existing = next(
                (
                    item
                    for item in keys
                    if item.get("name") == key_name or item.get("public_key") == public_key
                ),
                None,
            )
            if existing and existing.get("id"):
                return int(existing["id"])
        body = exc.read().decode("utf-8", errors="replace")
        fail(f"Hetzner SSH key creation failed ({exc.code}): {body}")
    ssh_key = created.get("ssh_key", {}) if isinstance(created, dict) else {}
    if not ssh_key.get("id"):
        fail("Hetzner SSH key creation failed.")
    return int(ssh_key["id"])


def find_hcloud_server(token: str, server_name: str) -> dict[str, Any] | None:
    payload = request_json(HCLOUD_API_ROOT, "GET", "/servers", "Authorization", f"Bearer {token}")
    servers = payload.get("servers", []) if isinstance(payload, dict) else []
    return next((server for server in servers if server.get("name") == server_name), None)


def delete_hcloud_server(token: str, server_id: int) -> None:
    request_json(HCLOUD_API_ROOT, "DELETE", f"/servers/{server_id}", "Authorization", f"Bearer {token}")


def wait_for_server_absence(token: str, server_name: str, timeout_seconds: int = 600, interval_seconds: int = 10) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if find_hcloud_server(token, server_name) is None:
            return
        print(f"Waiting for existing server '{server_name}' to disappear before recreate ...")
        time.sleep(interval_seconds)
    fail(f"Existing server '{server_name}' still exists after {timeout_seconds}s")


def upsert_cloudflare_a_record(token: str, zone_id: str, record_name: str, ip_address: str, ttl: int = 300) -> dict:
    q = urllib.parse.urlencode({"name": record_name, "type": "A"})
    payload = request_json(CLOUDFLARE_API_ROOT, "GET", f"/zones/{zone_id}/dns_records?{q}", "Authorization", f"Bearer {token}")
    records = payload.get("result", []) if isinstance(payload, dict) else []
    record = next((item for item in records if item.get("type") == "A" and item.get("name") == record_name), None)
    body = {"type": "A", "name": record_name, "content": ip_address, "ttl": ttl, "proxied": False}
    if record and record.get("id"):
        return request_json(CLOUDFLARE_API_ROOT, "PUT", f"/zones/{zone_id}/dns_records/{record['id']}", "Authorization", f"Bearer {token}", body)
    return request_json(CLOUDFLARE_API_ROOT, "POST", f"/zones/{zone_id}/dns_records", "Authorization", f"Bearer {token}", body)


def run_ssh_command(private_key_path: str, host: str, command: str) -> str:
    result = subprocess.run(
        [
            "ssh",
            "-i",
            private_key_path,
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            f"root@{host}",
            command,
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )
    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        raise RuntimeError(output.strip() or f"ssh command failed with exit code {result.returncode}")
    return output.strip()


def collect_remote_diagnostics(private_key_path: str, host: str) -> None:
    commands = [
        "uname -a",
        "docker ps -a",
        "cd /opt/hippo-ai && docker compose -f docker-compose.yml ps",
        "cd /opt/hippo-ai && docker compose -f docker-compose.yml logs --no-color --tail=200 api postgres redis",
    ]
    print(f"\n### Remote diagnostics for {host}")
    for cmd in commands:
        print(f"\n$ {cmd}")
        try:
            output = run_ssh_command(private_key_path, host, cmd)
            print(output)
        except Exception as exc:  # noqa: BLE001
            print(f"[diagnostic failed] {exc}")


def build_compose(owner: str) -> str:
    return f"""services:
  api:
    image: ghcr.io/{owner}/hippo-ai-api:latest
    container_name: hippo-ai-api
    restart: unless-stopped
    env_file:
      - .env.production
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    ports:
      - \"80:8000\"
    healthcheck:
      test:
        - CMD-SHELL
        - python -c "import json, urllib.request, sys; data = json.load(urllib.request.urlopen('http://127.0.0.1:8000/health')); raise SystemExit(0 if data.get('status') == 'ok' else 1)"
      interval: 10s
      timeout: 5s
      retries: 30
      start_period: 60s

  postgres:
    image: postgres:17
    container_name: hippo-ai-postgres
    restart: unless-stopped
    env_file:
      - .env.production
    volumes:
      - hippo_ai_postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hippo -d hippo_ai"]
      interval: 10s
      timeout: 5s
      retries: 10

  redis:
    image: redis:8-alpine
    container_name: hippo-ai-redis
    restart: unless-stopped
    volumes:
      - hippo_ai_redis_data:/data

volumes:
  hippo_ai_postgres_data:
  hippo_ai_redis_data:
"""


def build_cloud_init(env_lines: list[str], compose: str, ghcr_username: str, ghcr_token: str) -> str:
    return f"""#cloud-config
package_update: true
package_upgrade: true
packages:
  - ca-certificates
  - curl
  - git
  - jq
  - docker.io
  - docker-compose-plugin

bootcmd:
  - mkdir -p /opt/hippo-ai

write_files:
  - path: /opt/hippo-ai/.env.production
    permissions: '0600'
    content: |
{indent(os.linesep.join(env_lines), '      ')}
  - path: /opt/hippo-ai/docker-compose.yml
    permissions: '0644'
    content: |
{indent(compose.rstrip(), '      ')}

runcmd:
  - systemctl enable --now docker
  - [ bash, -lc, 'echo "{ghcr_token}" | docker login ghcr.io -u "{ghcr_username}" --password-stdin' ]
  - [ bash, -lc, 'cd /opt/hippo-ai && docker compose pull' ]
  - [ bash, -lc, 'cd /opt/hippo-ai && docker compose up -d --remove-orphans' ]
  - [ bash, -lc, 'for i in $(seq 1 180); do curl -fsS http://127.0.0.1/health && exit 0; sleep 10; done; echo "Hippo AI health check timed out" >&2; docker compose -f /opt/hippo-ai/docker-compose.yml ps >&2; exit 1' ]
"""


def main() -> int:
    hcloud_token = env("HCLOUD_TOKEN")
    cloudflare_token = env("CLOUDFLARE_API_TOKEN")
    cloudflare_zone_id = env("CLOUDFLARE_ZONE_ID")
    ssh_public_key = env("SSH_PUBLIC_KEY")
    hippo_ai_base_url = env("HIPPO_AI_BASE_URL")
    hippo_ai_model = env("HIPPO_AI_MODEL")
    ghcr_username = env("GHCR_USERNAME")
    ghcr_token = env("GHCR_TOKEN")

    provider = env("INPUT_PROVIDER").lower()
    api_key = env("INPUT_API_KEY")
    server_name = env("INPUT_SERVER_NAME") or "hippo-ai-prod"
    server_type = env("INPUT_SERVER_TYPE") or "cpx31"
    location = env("INPUT_LOCATION") or "nbg1"
    image = env("INPUT_IMAGE") or "ubuntu-24.04"
    public_hostname = env("INPUT_PUBLIC_HOSTNAME") or "hippo-api.hipposideros-cloud.de"
    dns_ttl_raw = env("INPUT_DNS_TTL") or "300"
    dns_ttl: int = 300
    try:
        dns_ttl = int(dns_ttl_raw)
    except ValueError:
        fail(f"Invalid DNS TTL: {dns_ttl_raw}")

    debug_private_key_path = env("DEBUG_SSH_PRIVATE_KEY_PATH")
    debug_public_key_path = env("DEBUG_SSH_PUBLIC_KEY_PATH")
    debug_ssh_public_key = ""
    if debug_public_key_path:
        with open(debug_public_key_path, "r", encoding="utf-8") as fh:
            debug_ssh_public_key = fh.read().strip()

    if not hcloud_token:
        fail("HCLOUD_TOKEN is missing.")
    if not cloudflare_token:
        fail("CLOUDFLARE_API_TOKEN is missing.")
    if not cloudflare_zone_id:
        fail("CLOUDFLARE_ZONE_ID is missing.")
    if not ssh_public_key:
        fail("SSH_PUBLIC_KEY is missing.")
    if provider not in {"openai", "claude"}:
        fail(f"Unsupported provider: {provider}")
    if not api_key:
        fail("API key input is missing.")
    if not hippo_ai_base_url:
        fail("HIPPO_AI_BASE_URL is missing.")
    if not hippo_ai_model:
        fail("HIPPO_AI_MODEL is missing.")
    if not ghcr_username:
        fail("GHCR_USERNAME is missing.")
    if not ghcr_token:
        fail("GHCR_TOKEN is missing.")

    mask(api_key)
    mask(ghcr_username)
    mask(ghcr_token)
    postgres_password = secrets.token_urlsafe(32)
    jwt_secret = secrets.token_urlsafe(48)
    mask(postgres_password)
    mask(jwt_secret)

    owner = env("GITHUB_REPOSITORY_OWNER")
    if not owner:
        fail("GITHUB_REPOSITORY_OWNER is missing.")

    force_recreate = env("INPUT_FORCE_RECREATE").lower() in {"1", "true", "yes", "on"}

    ssh_key_id = upsert_hcloud_ssh_key(hcloud_token, "hippo-ai-bootstrap", ssh_public_key)
    debug_ssh_key_id = None
    if debug_ssh_public_key:
        debug_ssh_key_id = upsert_hcloud_ssh_key(hcloud_token, f"hippo-ai-debug-{env('GITHUB_RUN_ID') or 'manual'}", debug_ssh_public_key)
    existing_server = find_hcloud_server(hcloud_token, server_name)
    if existing_server is not None and not force_recreate:
        fail(
            f"Hetzner server '{server_name}' already exists. Set force_recreate=true to recreate it, or delete the existing server first."
        )
    if existing_server is not None and force_recreate:
        existing_server_id = existing_server.get("id")
        if isinstance(existing_server_id, int):
            print(f"Deleting existing server '{server_name}' before recreate ...")
            delete_hcloud_server(hcloud_token, existing_server_id)
            wait_for_server_absence(hcloud_token, server_name)
            existing_server = None
    env_lines = [
        "APP_ENV=production",
        "POSTGRES_DB=hippo_ai",
        "POSTGRES_USER=hippo",
        f"POSTGRES_PASSWORD={postgres_password}",
        f"JWT_SECRET_KEY={jwt_secret}",
        f"HIPPO_AI_BASE_URL={hippo_ai_base_url}",
        f"HIPPO_AI_MODEL={hippo_ai_model}",
        f"HIPPO_API_KEY={api_key}",
        f"MODEL_PROVIDER={provider}",
        f"OPENAI_API_KEY={api_key if provider == 'openai' else ''}",
        f"ANTHROPIC_API_KEY={api_key if provider == 'claude' else ''}",
        "PCLOUD_API_BASE_URL=https://eapi.pcloud.com",
        f"PCLOUD_ACCESS_TOKEN={env('PCLOUD_ACCESS_TOKEN')}",
    ]

    compose = build_compose(owner)
    cloud_init = build_cloud_init(env_lines, compose, ghcr_username, ghcr_token)

    payload: dict[str, object] = {
        "name": server_name,
        "server_type": server_type,
        "image": image,
        "location": location,
        "user_data": cloud_init,
        "ssh_keys": [ssh_key_id] + ([debug_ssh_key_id] if debug_ssh_key_id is not None else []),
    }

    created: dict = {}
    if existing_server is None:
        try:
            created = request_json(
                HCLOUD_API_ROOT,
                "POST",
                "/servers",
                "Authorization",
                f"Bearer {hcloud_token}",
                payload,
            )
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code == 409 and "server name is already used" in body:
                existing_server = find_hcloud_server(hcloud_token, server_name)
                if existing_server is None:
                    fail(f"Hetzner server creation failed ({exc.code}): {body}")
            else:
                fail(f"Hetzner server creation failed ({exc.code}): {body}")

    server = existing_server or (created.get("server", {}) if isinstance(created, dict) else {})
    public_net = server.get("public_net", {}) or {}
    ipv4 = (public_net.get("ipv4", {}) or {}).get("ip")
    server_id = server.get("id")
    if not ipv4:
        fail("Hetzner server did not return an IPv4 address.")

    upsert_cloudflare_a_record(cloudflare_token, cloudflare_zone_id, public_hostname, str(ipv4), ttl=dns_ttl)

    try:
        ip_health = wait_for_health(f"http://{ipv4}")
        public_health = wait_for_health(f"http://{public_hostname}")
    except SystemExit:
        if debug_private_key_path:
            collect_remote_diagnostics(debug_private_key_path, str(ipv4))
        raise

    created_label = "Reused existing Hetzner server" if existing_server is not None else "Created Hetzner server"
    print(created_label)
    print(f"- id: {server_id}")
    print(f"- name: {server_name}")
    print(f"- ipv4: {ipv4}")
    print(f"- public_hostname: {public_hostname}")
    print(f"- provider: {provider}")
    print(f"- health_ip: {ip_health}")
    print(f"- health_public: {public_health}")

    summary = [
        "## Hippo AI VPS created",
        f"- Server ID: `{server_id}`",
        f"- Name: `{server_name}`",
        f"- IPv4: `{ipv4}`",
        f"- Public hostname: `{public_hostname}`",
        f"- Provider: `{provider}`",
        f"- Backend URL: `http://{public_hostname}`",
        "",
        "### Runtime config on the VPS",
        f"- `HIPPO_AI_BASE_URL` = `{hippo_ai_base_url}`",
        f"- `HIPPO_AI_MODEL` = `{hippo_ai_model}`",
        f"- `MODEL_PROVIDER` = `{provider}`",
    ]
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
        fh.write("\n".join(summary) + "\n")

    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as fh:
            fh.write(f"server_id={server_id or ''}\n")
            fh.write(f"server_ipv4={ipv4}\n")
            fh.write(f"backend_url=http://{public_hostname}\n")
            fh.write(f"provider={provider}\n")
            fh.write(f"public_hostname={public_hostname}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
