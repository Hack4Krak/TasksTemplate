# `docker-compose.yaml`

This optional file is required for configuring services for tasks.

> [!NOTE]
> Task compose files are deployed with Docker Swarm.
> Labels used by Traefik should be defined in `deploy.labels`.

```yaml
# Here you can define any service you want
# Minecraft Server, db, simple web service etc.
services:
  whoami:
    image: traefik/whoami
    deploy:
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.whoami.rule=Host(`whoami.docker.localhost`)"
        - "traefik.http.services.whoami.loadbalancer.server.port=80"
    networks:
      - ctf-services-net

# It is required for traefik to be able to redirect
# to your service, you probably don't want to change it.
networks:
  ctf-services-net:
    external: true
```

If a task should be deployed to a non-default environment, set `deployment.target` in its `config.yaml`.
