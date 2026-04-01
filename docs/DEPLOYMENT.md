# Deployment

TasksTemplate introduces a **task deployment model**: instead of managing individual Docker containers or services directly, you work with *tasks* - self-contained challenge units that each carry their own `docker-compose.yaml`.
The toolbox deploys every task as an isolated Docker Swarm stack, connected by a shared Traefik reverse proxy, so you can start, stop, restart, and inspect any task independently without touching the others.

```
toolbox services <command> [task] [options]
```

## Prerequisites

- Docker Engine with `docker compose` (or Podman with the Docker-compatible socket)
- A single-node Docker Swarm (the toolbox initialises one automatically when needed)

## How it works

1. Each task lives in `tasks/<task-name>/` and optionally contains a `docker-compose.yaml`.
2. Running `toolbox services start` deploys the **main stack** (Traefik) plus every task stack.
3. Each task stack is namespaced as `hack4krak-task-<task-name>`, keeping all resources separate.
4. Traefik reads labels from the running stacks and routes HTTP traffic accordingly - no manual port mapping needed.

## Local environment setup

Before starting services for the first time, copy `.env.example` to `.env` and set `DOCKER_SOCK` to match your setup:

| Setup                    | Socket path                                                |
|--------------------------|------------------------------------------------------------|
| Rootless Docker          | `/run/user/<UID>/docker.sock` (find your UID with `id -u`) |
| Rootful Docker (default) | `/var/run/docker.sock`                                     |
| Rootless Podman          | `/run/user/<UID>/podman/podman.sock`                       |

## Task compose files

Each task's `docker-compose.yaml` is a standard Compose file deployed under Swarm.
Because Traefik uses the Swarm provider, routing labels must go under `deploy.labels`:

```yaml
services:
  whoami:
    image: docker.io/traefik/whoami
    networks:
      - ctf-services-net
    deploy:
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.whoami.rule=Host(`whoami.docker.localhost`)"
        - "traefik.http.services.whoami.loadbalancer.server.port=80"

networks:
  ctf-services-net:
    external: true
```

See [structure/docker-compose.md](structure/docker-compose.md) for the full reference.

## CLI reference

### Up (start)

```bash
# Start main stack + all tasks (builds images if needed)
toolbox services up --all

# Start only selected tasks
toolbox services up simple-task-example

# Skip rebuilding images
toolbox services up --all --no-build
```

Aliases: `start`

### Down (stop)

```bash
# Stop a task stack
toolbox services down simple-task-example

# Stop all tasks (including main stack)
toolbox services down --all
```

Aliases: `stop`

### Restart

```bash
# Restart a task stack (rebuilds by default)
toolbox services restart simple-task-example

# Restart without rebuilding
toolbox services restart simple-task-example --no-build

# Restart all tasks
toolbox services restart --all
```

### Status

```bash
# Show status of all stacks (main + tasks)
toolbox services status

# Show status of a specific task
toolbox services status simple-task-example
```

Aliases: `ps`, `ls`

### Logs

```bash
# View logs for a task (all its services)
toolbox services logs simple-task-example

# Show more lines
toolbox services logs simple-task-example --tail 500

# Stream logs directly via Docker
docker service logs hack4krak-task-simple-task-example_whoami --follow
```

## Common workflows

### First-time setup

```bash
cp .env.example .env   # set DOCKER_SOCK for your environment
toolbox services up --all
toolbox services status
```

### Rebuild after a code change

```bash
toolbox services restart simple-task-example
# or, without auto-build:
toolbox services restart simple-task-example --no-build
toolbox services logs simple-task-example --tail 100
```

### Full clean restart

```bash
toolbox services down --all
toolbox services up --all
```

### Rebuild after a code change

```bash
toolbox services restart simple-task-example
# or, without auto-build:
toolbox services restart simple-task-example --no-build
toolbox services logs simple-task-example --tail 100
```

### Full clean restart

```bash
toolbox services down --all
toolbox services up --all
```

## Inspecting Docker resources directly

```bash
# All stacks
docker stack ls

# Services inside a task stack
docker stack services hack4krak-task-simple-task-example

# Containers for a stack
docker ps -a --filter label=com.docker.stack.namespace=hack4krak-task-simple-task-example

# Check Traefik is running
docker service ls | grep traefik
```
