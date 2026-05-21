from python_on_whales import DockerClient
from python_on_whales.exceptions import DockerException, NoSuchService, NotASwarmManager

from .models import ComposeServiceSpec, StackStatus
from .service import inspect_stack_service, service_replicas

type ServiceStats = dict[str, tuple[float, int, int, int]]


def compute_overall_state(states: list[str]) -> str:
    state_set = set(states)
    if state_set == {"running"}:
        return "running"
    if state_set == {"stopped"}:
        return "stopped"
    if "failed" in state_set:
        return "failed"
    if "rejected" in state_set:
        return "rejected"
    return "partial"


def get_stack_status(
    docker: DockerClient,
    stack_name: str,
    expected_services: list[ComposeServiceSpec],
    existing_stacks: set[str] | None = None,
    service_stats: ServiceStats | None = None,
) -> StackStatus:
    if existing_stacks is None:
        try:
            existing_stacks = {stack.name for stack in docker.stack.list()}
        except NotASwarmManager:
            return StackStatus("swarm inactive", "docker swarm is not initialized on this target")
    if stack_name not in existing_stacks:
        return StackStatus("not deployed", "stack missing")

    service_states: list[tuple[str, str]] = []
    cpu_total = 0.0
    mem_total = 0
    network_bytes_received = 0
    network_bytes_sent = 0

    for service_spec in expected_services:
        try:
            service = inspect_stack_service(docker, stack_name, service_spec.name)
        except NoSuchService:
            service_states.append((service_spec.name, "missing"))
            continue

        state = summarize_service_state(service)
        service_states.append((service_spec.name, state))

        cpu, memory, network_rx, network_tx = (service_stats or {}).get(service.spec.name, (0.0, 0, 0, 0))
        cpu_total += cpu
        mem_total += memory
        network_bytes_received += network_rx
        network_bytes_sent += network_tx

    states = [state for _, state in service_states]
    details = ", ".join(f"{name}: {state}" for name, state in service_states)
    overall = compute_overall_state(states)

    return StackStatus(
        overall,
        details or "services present",
        cpu=f"{cpu_total:.1f}%" if cpu_total else "0.0%",
        memory=format_bytes(mem_total),
        network_rx=format_bytes(network_bytes_received),
        network_tx=format_bytes(network_bytes_sent),
    )


def summarize_service_state(service) -> str:
    replicas = service_replicas(service)
    if replicas == 0:
        return "stopped"

    try:
        tasks = service.ps()
    except DockerException:
        return "unknown"

    if not tasks:
        return "pending"
    return compute_overall_state([t.status.state for t in tasks if t.status])


def get_existing_stacks(docker: DockerClient) -> set[str] | None:
    try:
        return {stack.name for stack in docker.stack.list()}
    except NotASwarmManager:
        return None


def get_all_service_stats(docker: DockerClient) -> ServiceStats:
    containers = docker.container.list()
    if not containers:
        return {}

    container_services: dict[str, str] = {}
    for container in containers:
        service_name = _container_label(container, "com.docker.swarm.service.name")
        if not service_name:
            continue
        container_services[container.id] = service_name
        container_services[container.id[:12]] = service_name
    if not container_services:
        return {}

    service_stats: ServiceStats = {}
    try:
        stats_list = docker.container.stats(containers)
    except DockerException:
        return {}

    for stats in stats_list:
        container_id = _stats_container_id(stats)
        if not container_id:
            continue
        service_name = container_services.get(container_id)
        if not service_name:
            continue

        cpu, memory, network_rx, network_tx = service_stats.get(service_name, (0.0, 0, 0, 0))
        service_stats[service_name] = (
            cpu + float(stats.cpu_percentage or 0),
            memory + int(stats.memory_used or 0),
            network_rx + int(stats.net_download or 0),
            network_tx + int(stats.net_upload or 0),
        )

    return service_stats


def _container_label(container, label: str) -> str | None:
    config = getattr(container, "config", None)
    labels = getattr(config, "labels", None) or getattr(container, "labels", None) or {}
    if isinstance(config, dict):
        labels = config.get("Labels") or config.get("labels") or labels
    return labels.get(label)


def _stats_container_id(stats) -> str | None:
    return getattr(stats, "container_id", None) or getattr(stats, "id", None) or getattr(stats, "container", None)


def format_bytes(value: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}B"
