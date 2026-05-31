---
sidebar_position: 7
title: "Docker"
description: "Running TchuEkaM Agent in Docker and using Docker as a terminal backend"
---

# TchuEkaM Agent — Docker

There are two distinct ways Docker intersects with TchuEkaM Agent:

1. **Running TchuEkaM IN Docker** — the agent itself runs inside a container (this page's primary focus)
2. **Docker as a terminal backend** — the agent runs on your host but executes every command inside a single, persistent Docker sandbox container that survives across tool calls, `/new`, and subagents for the life of the TchuEkaM process (see [Configuration → Docker Backend](./configuration.md#docker-backend))

This page covers option 1. The container stores all user data (config, API keys, sessions, skills, memories) in a single directory mounted from the host at `/opt/data`. The image itself is stateless and can be upgraded by pulling a new version without losing any configuration.

## Quick start

If this is your first time running TchuEkaM Agent, create a data directory on the host and start the container interactively to run the setup wizard:

```sh
mkdir -p ~/.tchuekam
docker run -it --rm \
  -v ~/.tchuekam:/opt/data \
  nousresearch/tchuekam-agent setup
```

This drops you into the setup wizard, which will prompt you for your API keys and write them to `~/.tchuekam/.env`. You only need to do this once. It is highly recommended to set up a chat system for the gateway to work with at this point.

## Running in gateway mode

Once configured, run the container in the background as a persistent gateway (Telegram, Discord, Slack, WhatsApp, etc.):

```sh
docker run -d \
  --name tchuekam \
  --restart unless-stopped \
  -v ~/.tchuekam:/opt/data \
  -p 8642:8642 \
  nousresearch/tchuekam-agent gateway run
```

Port 8642 exposes the gateway's [OpenAI-compatible API server](./features/api-server.md) and health endpoint. It's optional if you only use chat platforms (Telegram, Discord, etc.), but required if you want the dashboard or external tools to reach the gateway.

Note: the API server is gated on `API_SERVER_ENABLED=true`. To expose it beyond `127.0.0.1` inside the container, also set `API_SERVER_HOST=0.0.0.0` and an `API_SERVER_KEY` (minimum 8 characters — generate one with `openssl rand -hex 32`). Example:

```sh
docker run -d \
  --name tchuekam \
  --restart unless-stopped \
  -v ~/.tchuekam:/opt/data \
  -p 8642:8642 \
  -e API_SERVER_ENABLED=true \
  -e API_SERVER_HOST=0.0.0.0 \
  -e API_SERVER_KEY="$(openssl rand -hex 32)" \
  -e API_SERVER_CORS_ORIGINS='*' \
  nousresearch/tchuekam-agent gateway run
```

Opening any port on an internet facing machine is a security risk. You should not do it unless you understand the risks.

## Running the dashboard

The built-in web dashboard runs as an optional side-process inside the same container as the gateway. Set `TCHUEKAM_DASHBOARD=1` to run the dashboard on container loopback (`127.0.0.1`) by default:

```sh
docker run -d \
  --name tchuekam \
  --restart unless-stopped \
  -v ~/.tchuekam:/opt/data \
  -p 8642:8642 \
  -e TCHUEKAM_DASHBOARD=1 \
  nousresearch/tchuekam-agent gateway run
```

The entrypoint starts `tchuekam dashboard` in the background (running as the non-root `tchuekam` user) before `exec`-ing the main command. Dashboard output is prefixed with `[dashboard]` in `docker logs` so it's easy to separate from gateway logs.

| Environment variable | Description | Default |
|---------------------|-------------|---------|
| `TCHUEKAM_DASHBOARD` | Set to `1` (or `true` / `yes`) to launch the dashboard alongside the main command | *(unset — dashboard not started)* |
| `TCHUEKAM_DASHBOARD_HOST` | Bind address for the dashboard HTTP server | `127.0.0.1` |
| `TCHUEKAM_DASHBOARD_PORT` | Port for the dashboard HTTP server | `9119` |
| `TCHUEKAM_DASHBOARD_TUI` | Set to `1` to expose the in-browser Chat tab (embedded `tchuekam --tui` via PTY/WebSocket) | *(unset)* |

By default, the dashboard stays on loopback to avoid exposing the unauthenticated web surface over the network. To publish it intentionally, set `TCHUEKAM_DASHBOARD_HOST=0.0.0.0` and configure your own trusted network boundary/reverse proxy. In that case you must explicitly add `--insecure` behavior by passing host/flags in your command path (the entrypoint no longer auto-enables insecure mode).

:::note
The dashboard side-process is **not supervised** — if it crashes, it stays down until the container restarts. Running it as a separate container is not supported: the dashboard's gateway-liveness detection requires a shared PID namespace with the gateway process.
:::

## Running interactively (CLI chat)

To open an interactive chat session against a running data directory:

```sh
docker run -it --rm \
  -v ~/.tchuekam:/opt/data \
  nousresearch/tchuekam-agent
```

Or if you have already opened a terminal in your running container (via Docker Desktop for instance), just run:

```sh
/opt/tchuekam/.venv/bin/tchuekam
```

## Persistent volumes

The `/opt/data` volume is the single source of truth for all TchuEkaM state. It maps to your host's `~/.tchuekam/` directory and contains:

| Path | Contents |
|------|----------|
| `.env` | API keys and secrets |
| `config.yaml` | All TchuEkaM configuration |
| `SOUL.md` | Agent personality/identity |
| `sessions/` | Conversation history |
| `memories/` | Persistent memory store |
| `skills/` | Installed skills |
| `cron/` | Scheduled job definitions |
| `hooks/` | Event hooks |
| `logs/` | Runtime logs |
| `skins/` | Custom CLI skins |

:::warning
Never run two TchuEkaM **gateway** containers against the same data directory simultaneously — session files and memory stores are not designed for concurrent write access.
:::

## Multi-profile support

TchuEkaM supports [multiple profiles](../reference/profile-commands.md) — separate `~/.tchuekam/` directories that let you run independent agents (different SOUL, skills, memory, sessions, credentials) from a single installation. **When running under Docker, using TchuEkaM' built-in multi-profile feature is not recommended.**

Instead, the recommended pattern is **one container per profile**, with each container bind-mounting its own host directory as `/opt/data`:

```sh
# Work profile
docker run -d \
  --name tchuekam-work \
  --restart unless-stopped \
  -v ~/.tchuekam-work:/opt/data \
  -p 8642:8642 \
  nousresearch/tchuekam-agent gateway run

# Personal profile
docker run -d \
  --name tchuekam-personal \
  --restart unless-stopped \
  -v ~/.tchuekam-personal:/opt/data \
  -p 8643:8642 \
  nousresearch/tchuekam-agent gateway run
```

Why separate containers over profiles in Docker:

- **Isolation** — each container has its own filesystem, process table, and resource limits. A crash, dependency change, or runaway session in one profile can't affect another.
- **Independent lifecycle** — upgrade, restart, pause, or roll back each agent separately (`docker restart tchuekam-work` leaves `tchuekam-personal` untouched).
- **Clean port and network separation** — each gateway binds its own host port; there's no risk of cross-talk between chat platforms or API servers.
- **Simpler mental model** — the container *is* the profile. Backups, migrations, and permissions all follow the bind-mounted directory, with no extra `--profile` flags to remember.
- **Avoids concurrent-write risk** — the warning above about never running two gateways against the same data directory still applies to profiles within a single container.

In Docker Compose, this just means declaring one service per profile with distinct `container_name`, `volumes`, and `ports`:

```yaml
services:
  tchuekam-work:
    image: nousresearch/tchuekam-agent:latest
    container_name: tchuekam-work
    restart: unless-stopped
    command: gateway run
    ports:
      - "8642:8642"
    volumes:
      - ~/.tchuekam-work:/opt/data

  tchuekam-personal:
    image: nousresearch/tchuekam-agent:latest
    container_name: tchuekam-personal
    restart: unless-stopped
    command: gateway run
    ports:
      - "8643:8642"
    volumes:
      - ~/.tchuekam-personal:/opt/data
```

## Environment variable forwarding

API keys are read from `/opt/data/.env` inside the container. You can also pass environment variables directly:

```sh
docker run -it --rm \
  -v ~/.tchuekam:/opt/data \
  -e ANTHROPIC_API_KEY="sk-ant-..." \
  -e OPENAI_API_KEY="sk-..." \
  nousresearch/tchuekam-agent
```

Direct `-e` flags override values from `.env`. This is useful for CI/CD or secrets-manager integrations where you don't want keys on disk.

:::note Looking for Docker as the **terminal backend**?
This page covers running TchuEkaM itself inside Docker. If you want TchuEkaM to execute the agent's `terminal` / `execute_code` calls inside a Docker sandbox container (one persistent container per TchuEkaM process), that's a separate config block — `terminal.backend: docker` plus `terminal.docker_image`, `terminal.docker_volumes`, `terminal.docker_forward_env`, `terminal.docker_run_as_host_user`, and `terminal.docker_extra_args`. See [Configuration → Docker Backend](configuration.md#docker-backend) for the full set.
:::

## Docker Compose example

For persistent deployment with both the gateway and dashboard, a `docker-compose.yaml` is convenient:

```yaml
services:
  tchuekam:
    image: nousresearch/tchuekam-agent:latest
    container_name: tchuekam
    restart: unless-stopped
    command: gateway run
    ports:
      - "8642:8642"   # gateway API
      - "9119:9119"   # dashboard (only reached when TCHUEKAM_DASHBOARD=1)
    volumes:
      - ~/.tchuekam:/opt/data
    environment:
      - TCHUEKAM_DASHBOARD=1
      # Uncomment to forward specific env vars instead of using .env file:
      # - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      # - OPENAI_API_KEY=${OPENAI_API_KEY}
      # - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: "2.0"
```

Start with `docker compose up -d` and view logs with `docker compose logs -f`. Dashboard output is prefixed with `[dashboard]` so it's easy to filter from gateway logs.

## Resource limits

The TchuEkaM container needs moderate resources. Recommended minimums:

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| Memory | 1 GB | 2–4 GB |
| CPU | 1 core | 2 cores |
| Disk (data volume) | 500 MB | 2+ GB (grows with sessions/skills) |

Browser automation (Playwright/Chromium) is the most memory-hungry feature. If you don't need browser tools, 1 GB is sufficient. With browser tools active, allocate at least 2 GB.

Set limits in Docker:

```sh
docker run -d \
  --name tchuekam \
  --restart unless-stopped \
  --memory=4g --cpus=2 \
  -v ~/.tchuekam:/opt/data \
  nousresearch/tchuekam-agent gateway run
```

## What the Dockerfile does

The official image is based on `debian:13.4` and includes:

- Python 3 with all TchuEkaM dependencies (`uv pip install -e ".[all]"`)
- Node.js + npm (for browser automation and WhatsApp bridge)
- Playwright with Chromium (`npx playwright install --with-deps chromium --only-shell`)
- ripgrep, ffmpeg, git, and tini as system utilities
- **`docker-cli`** — so agents running inside the container can drive the host's Docker daemon (bind-mount `/var/run/docker.sock` to opt in) for `docker build`, `docker run`, container inspection, etc.
- **`openssh-client`** — enables the [SSH terminal backend](/docs/user-guide/configuration#ssh-backend) from inside the container. The SSH backend shells out to the system `ssh` binary; without this, it failed silently in containerized installs.
- The WhatsApp bridge (`scripts/whatsapp-bridge/`)

The entrypoint script (`docker/entrypoint.sh`) bootstraps the data volume on first run:
- Creates the directory structure (`sessions/`, `memories/`, `skills/`, etc.)
- Copies `.env.example` → `.env` if no `.env` exists
- Copies default `config.yaml` if missing
- Copies default `SOUL.md` if missing
- Syncs bundled skills using a manifest-based approach (preserves user edits)
- Optionally launches `tchuekam dashboard` as a background side-process when `TCHUEKAM_DASHBOARD=1` (see [Running the dashboard](#running-the-dashboard))
- Then runs `tchuekam` with whatever arguments you pass

:::warning
Do not override the image entrypoint unless you keep `/opt/tchuekam/docker/entrypoint.sh` in the command chain. The entrypoint drops root privileges to the `tchuekam` user before gateway state files are created. Starting `tchuekam gateway run` as root inside the official image is refused by default because it can leave root-owned files in `/opt/data` and break later dashboard or gateway starts. Set `TCHUEKAM_ALLOW_ROOT_GATEWAY=1` only when you intentionally accept that risk.
:::

## Upgrading

Pull the latest image and recreate the container. Your data directory is untouched.

```sh
docker pull nousresearch/tchuekam-agent:latest
docker rm -f tchuekam
docker run -d \
  --name tchuekam \
  --restart unless-stopped \
  -v ~/.tchuekam:/opt/data \
  nousresearch/tchuekam-agent gateway run
```

Or with Docker Compose:

```sh
docker compose pull
docker compose up -d
```

## Skills and credential files

When using Docker as the execution environment (not the methods above, but when the agent runs commands inside a Docker sandbox — see [Configuration → Docker Backend](./configuration.md#docker-backend)), TchuEkaM reuses a single long-lived container for all tool calls and automatically bind-mounts the skills directory (`~/.tchuekam/skills/`) and any credential files declared by skills into that container as read-only volumes. Skill scripts, templates, and references are available inside the sandbox without manual configuration, and because the container persists for the life of the TchuEkaM process, any dependencies you install or files you write stay around for the next tool call.

The same syncing happens for SSH and Modal backends — skills and credential files are uploaded via rsync or the Modal mount API before each command.

## Connecting to local inference servers (vLLM, Ollama, etc.)

When running TchuEkaM in Docker and your inference server (vLLM, Ollama, text-generation-inference, etc.) is also running on the host or in another container, networking requires extra attention.

### Docker Compose (recommended)

Put both services on the same Docker network. This is the most reliable approach:

```yaml
services:
  vllm:
    image: vllm/vllm-openai:latest
    container_name: vllm
    command: >
      --model Qwen/Qwen2.5-7B-Instruct
      --served-model-name my-model
      --host 0.0.0.0
      --port 8000
    ports:
      - "8000:8000"
    networks:
      - tchuekam-net
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]

  tchuekam:
    image: nousresearch/tchuekam-agent:latest
    container_name: tchuekam
    restart: unless-stopped
    command: gateway run
    ports:
      - "8642:8642"
    volumes:
      - ~/.tchuekam:/opt/data
    networks:
      - tchuekam-net

networks:
  tchuekam-net:
    driver: bridge
```

Then in your `~/.tchuekam/config.yaml`, use the **container name** as the hostname:

```yaml
model:
  provider: custom
  model: my-model
  base_url: http://vllm:8000/v1
  api_key: "none"
```

:::tip Key points
- Use the **container name** (`vllm`) as the hostname — not `localhost` or `127.0.0.1`, which refer to the TchuEkaM container itself.
- The `model` value must match the `--served-model-name` you passed to vLLM.
- Set `api_key` to any non-empty string (vLLM requires the header but doesn't validate it by default).
- Do **not** include a trailing slash in `base_url`.
:::

### Standalone Docker run (no Compose)

If your inference server runs directly on the host (not in Docker), use `host.docker.internal` on macOS/Windows, or `--network host` on Linux:

**macOS / Windows:**

```sh
docker run -d \
  --name tchuekam \
  -v ~/.tchuekam:/opt/data \
  -p 8642:8642 \
  nousresearch/tchuekam-agent gateway run
```

```yaml
# config.yaml
model:
  provider: custom
  model: my-model
  base_url: http://host.docker.internal:8000/v1
  api_key: "none"
```

**Linux (host networking):**

```sh
docker run -d \
  --name tchuekam \
  --network host \
  -v ~/.tchuekam:/opt/data \
  nousresearch/tchuekam-agent gateway run
```

```yaml
# config.yaml
model:
  provider: custom
  model: my-model
  base_url: http://127.0.0.1:8000/v1
  api_key: "none"
```

:::warning With `--network host`, the `-p` flag is ignored — all container ports are directly exposed on the host.
:::

### Verifying connectivity

From inside the TchuEkaM container, confirm the inference server is reachable:

```sh
docker exec tchuekam curl -s http://vllm:8000/v1/models
```

You should see a JSON response listing your served model. If this fails, check:

1. Both containers are on the same Docker network (`docker network inspect tchuekam-net`)
2. The inference server is listening on `0.0.0.0`, not `127.0.0.1`
3. The port number matches

### Ollama

Ollama works the same way. If Ollama runs on the host, use `host.docker.internal:11434` (macOS/Windows) or `127.0.0.1:11434` (Linux with `--network host`). If Ollama runs in its own container on the same Docker network:

```yaml
model:
  provider: custom
  model: llama3
  base_url: http://ollama:11434/v1
  api_key: "none"
```

## Troubleshooting

### Container exits immediately

Check logs: `docker logs tchuekam`. Common causes:
- Missing or invalid `.env` file — run interactively first to complete setup
- Port conflicts if running with exposed ports

### "Permission denied" errors

The container's entrypoint drops privileges to the non-root `tchuekam` user (UID 10000) via `gosu`. If your host `~/.tchuekam/` is owned by a different UID, set `TCHUEKAM_UID`/`TCHUEKAM_GID` to match your host user, or ensure the data directory is writable:

```sh
chmod -R 755 ~/.tchuekam
```

### Browser tools not working

Playwright needs shared memory. Add `--shm-size=1g` to your Docker run command:

```sh
docker run -d \
  --name tchuekam \
  --shm-size=1g \
  -v ~/.tchuekam:/opt/data \
  nousresearch/tchuekam-agent gateway run
```

### Gateway not reconnecting after network issues

The `--restart unless-stopped` flag handles most transient failures. If the gateway is stuck, restart the container:

```sh
docker restart tchuekam
```

### Checking container health

```sh
docker logs --tail 50 tchuekam          # Recent logs
docker run -it --rm nousresearch/tchuekam-agent:latest version     # Verify version
docker stats tchuekam                    # Resource usage
```
