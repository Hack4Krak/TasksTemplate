# `docker-compose.yaml`

This optional file configures services for a task (databases, web apps, etc.).
Tasks are deployed as Docker Swarm stacks. Use `docker stack deploy` compatible syntax.

## Traefik labels

Traefik uses the **Docker provider** (`--providers.docker`), which reads labels directly from running containers - not from the service spec. Put Traefik labels at the **service level** (`labels:`), not under `deploy.labels:`.

```yaml
services:
  app:
    image: traefik/whoami
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app.rule=Host(`app.docker.localhost`)"
      - "traefik.http.services.app.loadbalancer.server.port=80"
    networks:
      - ctf-services-net

networks:
  ctf-services-net:
    external: true
```

The `ctf-services-net` network declaration is required so Traefik can reach the container.

## Swarm compatibility notes

`docker stack deploy` silently ignores fields that Swarm doesn't support. The following are safe to omit:

- `container_name` - ignored by Swarm (containers are named by the stack)
- `restart` - use `deploy.restart_policy` instead if you need restart behaviour

## Full example

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
    deploy:
      restart_policy:
        condition: on-failure
    networks:
      - ctf-services-net

  app:
    image: my-ctf-app
    build: .
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app.rule=Host(`app.docker.localhost`)"
      - "traefik.http.services.app.loadbalancer.server.port=8080"
    depends_on:
      - db
    networks:
      - ctf-services-net

networks:
  ctf-services-net:
    external: true
```
