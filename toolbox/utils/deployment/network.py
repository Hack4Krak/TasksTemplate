from python_on_whales import DockerClient
from python_on_whales.exceptions import DockerException


def docker_rootless(docker: DockerClient) -> bool:
    try:
        info = docker.system.info()
    except DockerException:
        return False
    security_options = info.security_options or []
    return any("rootless" in str(option) for option in security_options)


def ensure_swarm_ready(docker: DockerClient) -> None:
    info = docker.system.info()
    swarm = info.swarm
    if swarm is None:
        raise RuntimeError("Docker swarm info unavailable")
    if swarm.local_node_state == "active":
        return
    if swarm.local_node_state not in {"inactive", "pending"}:
        raise RuntimeError(f"Docker swarm is not ready: {swarm.local_node_state}")
    docker.swarm.init()


def ensure_stack_network(docker: DockerClient, network_name: str) -> None:
    existing = docker.network.list(filters={"name": network_name})
    if any(n.name == network_name for n in existing):
        return

    if docker_rootless(docker):
        docker.network.create(network_name, driver="bridge")
    else:
        docker.network.create(network_name, driver="overlay", attachable=True)
