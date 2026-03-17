# Deployment

Some tasks require services like databases, web apps, or other infrastructure.
TasksTemplate uses Docker Swarm to deploy them in a way that stays close to regular Compose files.

## Prerequisites

- Docker Engine with `docker compose`
- Docker Swarm enabled on the selected target

The toolbox can initialize a single-node swarm automatically on the current machine when needed.

## Configuration

Each task can define a `docker-compose.yaml` file.
You can read more about it in [structure/docker-compose.md](structure/docker-compose.md).

Deploy targets are configured in `config/deployments.yaml`.
Each target can point to a Docker context, remote Docker host, TLS options, and a target-specific main compose file.

Example:

```yaml
default-target: dev

targets:
  dev:
    main-compose: docker-compose.yaml

  prod:
    main-compose: docker-compose.prod.yaml
    docker-context: production
    with-registry-auth: true
```

Tasks can override the default target in their `config.yaml`:

```yaml
deployment:
  target: prod
```

## Traefik in Swarm

Traefik uses the Swarm provider, so routing labels must live under `deploy.labels`.
For HTTP services, define the router rule and the internal service port explicitly.

Example task service:

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

## CLI workflow

List all deployable task stacks and their status:

```shell
toolbox services status
```

Deploy the main stack and all task stacks for the default target:

```shell
toolbox services deploy
```

Deploy only selected tasks:

```shell
toolbox services deploy --tasks simple-task-example
```

Deploy only one target:

```shell
toolbox services deploy --target prod
```

Stop a whole task stack:

```shell
toolbox services stop simple-task-example
```

Stop one service inside a task stack:

```shell
toolbox services stop simple-task-example --service whoami
```

Restart a whole task stack:

```shell
toolbox services restart simple-task-example
```

Restart one service inside a task stack:

```shell
toolbox services restart simple-task-example --service whoami
```

## Notes

- `toolbox services deploy` builds local images first when the compose file contains `build` sections.
- The main reverse-proxy network is `ctf-services-net` and is created automatically as an overlay network.
- `toolbox services stop <task>` removes the stack; `restart` deploys it again.
