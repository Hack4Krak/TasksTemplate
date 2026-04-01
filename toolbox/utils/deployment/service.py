from python_on_whales import DockerClient

from .stack import service_full_name


def inspect_stack_service(docker: DockerClient, stack_name: str, service_name: str):
    return docker.service.inspect(service_full_name(stack_name, service_name))


def service_replicas(service) -> int | None:
    replicated = service.spec.mode.get("Replicated") if service.spec.mode else None
    if replicated is None:
        return None
    return replicated.get("Replicas")


def get_service_logs(docker: DockerClient, service_name: str, tail: int = 100) -> str:
    logs = docker.service.logs(service_name, tail=tail, timestamps=True)
    if isinstance(logs, bytes):
        return logs.decode()
    return logs


def get_stack_logs(docker: DockerClient, stack_name: str, compose_file, tail: int = 100) -> str:
    from .deployment import load_compose_service_specs

    specs = load_compose_service_specs(compose_file)
    logs = []
    for spec in specs:
        full_name = service_full_name(stack_name, spec.name)
        try:
            service_logs = get_service_logs(docker, full_name, tail=tail)
            logs.append(f"--- {spec.name} ---\n{service_logs}")
        except Exception as exception:
            logs.append(f"--- {spec.name} ---\nError: {exception}")
    return "\n\n".join(logs)


def list_service_containers(docker: DockerClient, service_name: str):
    return docker.container.list(all=True, filters={"label": f"com.docker.swarm.service.name={service_name}"})


def get_service_container_stats(docker: DockerClient, service_name: str):
    containers = list_service_containers(docker, service_name)
    if not containers:
        return []
    return docker.container.stats(containers)
