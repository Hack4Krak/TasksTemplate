# `docker-compose.yaml`

This optional file is required for configuring services for tasks.

> ![NOTE]
> All paths (volumes, Dockerfile) are relative to the root of the repository.
> You can change it by providing `--main-compose` parameter.

```yaml
# Here you can define any service you want
# Minecraft Server, db, simple web service etc.
services:
  whoami:
    image: traefik/whoami
    labels:
      - "traefik.http.routers.whoami.rule=Host(`whoami.docker.localhost`)"
    networks:
      - ctf-services-net

# It is required for traefik to be able to redirect
# to your service, you probably don't want to change it.
networks:
  ctf-services-net:
    external: true
```