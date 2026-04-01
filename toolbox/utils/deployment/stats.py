from python_on_whales import DockerClient
from python_on_whales.exceptions import DockerException, NoSuchService, NotASwarmManager

from .models import ComposeServiceSpec, StackStatus
from .service import get_service_container_stats, inspect_stack_service, service_replicas


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


def get_stack_status(docker: DockerClient, stack_name: str, expected_services: list[ComposeServiceSpec]) -> StackStatus:
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

        for stats in get_service_container_stats(docker, service.spec.name):
            cpu_total += float(stats.cpu_percentage or 0)
            mem_total += int(stats.memory_used or 0)
            network_bytes_received += int(stats.net_download or 0)
            network_bytes_sent += int(stats.net_upload or 0)

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


def format_bytes(value: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f}{unit}"
        size /= 1024
