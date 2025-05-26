# Deployment

Some tasks require service like a database with sql injection, web service etc.
TasksTemplate provides a straightforward and intuitive way to configure and deploy them.

## Prerequisites

We heavily rely on [Podman](https://podman.io/) and [podman-compose](https://github.com/containers/podman-compose/).

> [!WARNING]  
> Currently we require prerelease version of `podman-compose` to work properly.
> You can install it with: `toolbox services install`

## Configuration

Each task can have `docker-compose.yaml` file.
You can read more about it [here](structure/docker-compose.md).

For TCP services, you need to manually open ports.
But for all HTTP tasks we use [`traefik`](https://traefik.io/) reverse proxy.

You can use it to assign subdomains to tasks,  add compression, ssl certificates etc.

## Deployment

Our toolbox has commands for managing docker containers related to your CTF.
They are very similar to `docker compose` commands.

```shell
# Start all services
toolbox services up
```
```shell
# Stop all services
toolbox services down
```
```shell
# List all services
toolbox services ps
```

If our toolbox does not support some feature, you can use `podman` commands instead.