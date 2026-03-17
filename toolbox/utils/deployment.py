from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import yaml
from python_on_whales import DockerClient
from python_on_whales.exceptions import DockerException, NoSuchService, NotASwarmManager

from toolbox.utils.cli import run
from toolbox.utils.config import DeploymentTargetConfig, DeploymentsConfig
from toolbox.utils.tasks import find_docker_compose_file, find_tasks, load_task_config

MAIN_STACK_NAME = "hack4krak-main"
TASK_STACK_PREFIX = "hack4krak-task"
DEFAULT_STACK_NETWORK = "ctf-services-net"
DEFAULT_ROOTLESS_NETWORK = "bridge"


@dataclass(frozen=True)
class ComposeServiceSpec:
    name: str
    replicas: int | None
    published_ports: list[dict]


@dataclass(frozen=True)
class TaskDeployment:
    task_id: str
    target: str
    stack_name: str
    compose_file: Path


@dataclass(frozen=True)
class StackStatus:
    state: str
    details: str
    cpu: str = "-"
    memory: str = "-"
    network_rx: str = "-"
    network_tx: str = "-"


@dataclass(frozen=True)
class ResolvedTargetConfig:
    base: DeploymentTargetConfig
    rootless: bool
    traefik_provider: str
    stack_network: str
    publish_mode: str
    docker_socket: str


def resolve_repo_path(base_directory: Path, value: str | Path | None, default: str | Path | None = None) -> Path | None:
    candidate = value if value is not None else default
    if candidate is None:
        return None

    path = Path(candidate)
    if not path.is_absolute():
        path = base_directory / path
    return path


def load_deployments_config(config_directory: Path) -> DeploymentsConfig:
    return DeploymentsConfig.from_config_directory_optional(config_directory)


def get_default_target_name(config_directory: Path) -> str:
    return load_deployments_config(config_directory).default_target


def get_target_config(config_directory: Path, target_name: str) -> DeploymentTargetConfig:
    deployments = load_deployments_config(config_directory)
    try:
        return deployments.targets[target_name]
    except KeyError as exc:
        available = ", ".join(sorted(deployments.targets))
        raise RuntimeError(f"Unknown deploy target '{target_name}'. Available targets: {available}") from exc


def resolve_main_compose_path(config_directory: Path, target_name: str, main_compose: Path | None) -> Path:
    project_root = config_directory.parent
    if main_compose is not None:
        resolved = resolve_repo_path(project_root, main_compose)
    else:
        target_config = get_target_config(config_directory, target_name)
        resolved = resolve_repo_path(project_root, target_config.main_compose, default="docker-compose.yaml")

    if resolved is None:
        raise RuntimeError("Unable to resolve main compose file path")
    return resolved


def create_docker_client(
    target: DeploymentTargetConfig,
    *,
    compose_files: list[Path] | None = None,
    compose_project_directory: Path | None = None,
) -> DockerClient:
    client_kwargs = {"client_type": "docker"}
    if target.docker_context:
        client_kwargs["context"] = target.docker_context
    if target.docker_host:
        client_kwargs["host"] = target.docker_host
    if target.docker_tls is not None:
        client_kwargs["tls"] = target.docker_tls
    if target.docker_tls_verify is not None:
        client_kwargs["tlsverify"] = target.docker_tls_verify
    if target.docker_tls_ca_cert:
        client_kwargs["tlscacert"] = target.docker_tls_ca_cert
    if target.docker_tls_cert:
        client_kwargs["tlscert"] = target.docker_tls_cert
    if target.docker_tls_key:
        client_kwargs["tlskey"] = target.docker_tls_key
    if compose_files:
        client_kwargs["compose_files"] = compose_files
    if compose_project_directory:
        client_kwargs["compose_project_directory"] = compose_project_directory
    return DockerClient(**client_kwargs)


def docker_rootless(docker: DockerClient) -> bool:
    try:
        info = docker.system.info()
    except DockerException:
        return False
    security_options = info.security_options or []
    return any("rootless" in str(option) for option in security_options)


def resolve_target_runtime(docker: DockerClient, target: DeploymentTargetConfig) -> ResolvedTargetConfig:
    rootless = docker_rootless(docker)
    if rootless:
        traefik_provider = target.traefik_provider or "docker"
        stack_network = target.stack_network or DEFAULT_ROOTLESS_NETWORK
        publish_mode = target.publish_mode or "host"
        docker_socket = target.docker_socket or "/run/user/1000/docker.sock"
    else:
        traefik_provider = target.traefik_provider or "swarm"
        stack_network = target.stack_network or DEFAULT_STACK_NETWORK
        publish_mode = target.publish_mode or "ingress"
        docker_socket = target.docker_socket or "/var/run/docker.sock"

    return ResolvedTargetConfig(
        base=target,
        rootless=rootless,
        traefik_provider=traefik_provider,
        stack_network=stack_network,
        publish_mode=publish_mode,
        docker_socket=docker_socket,
    )


def task_stack_name(task_id: str) -> str:
    return f"{TASK_STACK_PREFIX}-{task_id}"


def get_task_target(task_directory: Path, default_target: str) -> str:
    deployment = load_task_config(task_directory).get("deployment", {})
    if isinstance(deployment, dict):
        target = deployment.get("target")
        if isinstance(target, str) and target:
            return target
    return default_target


def list_task_deployments(
    tasks_directory: Path,
    config_directory: Path,
    requested_target: str | None = None,
    requested_tasks: set[str] | None = None,
) -> list[TaskDeployment]:
    default_target = get_default_target_name(config_directory)
    deployments: list[TaskDeployment] = []

    for task_directory in find_tasks(tasks_directory):
        if requested_tasks and task_directory.name not in requested_tasks:
            continue

        compose_file = find_docker_compose_file(task_directory)
        if compose_file is None:
            continue

        target = get_task_target(task_directory, default_target)
        if requested_target and target != requested_target:
            continue

        deployments.append(
            TaskDeployment(
                task_id=task_directory.name,
                target=target,
                stack_name=task_stack_name(task_directory.name),
                compose_file=compose_file,
            )
        )

    return deployments


def group_task_deployments_by_target(
    tasks_directory: Path,
    config_directory: Path,
    requested_target: str | None = None,
    requested_tasks: set[str] | None = None,
) -> dict[str, list[TaskDeployment]]:
    grouped: dict[str, list[TaskDeployment]] = defaultdict(list)
    for deployment in list_task_deployments(tasks_directory, config_directory, requested_target, requested_tasks):
        grouped[deployment.target].append(deployment)
    return dict(grouped)


def load_compose_service_specs(compose_file: Path) -> list[ComposeServiceSpec]:
    compose = yaml.safe_load(compose_file.read_text(encoding="utf-8")) or {}
    services = compose.get("services", {})
    result: list[ComposeServiceSpec] = []

    for service_name, service_config in services.items():
        deploy = service_config.get("deploy", {}) if isinstance(service_config, dict) else {}
        ports = service_config.get("ports", []) if isinstance(service_config, dict) else []
        normalized_ports = []
        for port in ports:
            if isinstance(port, dict):
                normalized_ports.append(port)
        if deploy.get("mode") == "global":
            replicas = None
        else:
            replicas = int(deploy.get("replicas", 1))
        result.append(ComposeServiceSpec(name=service_name, replicas=replicas, published_ports=normalized_ports))

    return result


def compose_has_build(compose_file: Path) -> bool:
    compose = yaml.safe_load(compose_file.read_text(encoding="utf-8")) or {}
    services = compose.get("services", {})
    return any(isinstance(service_config, dict) and "build" in service_config for service_config in services.values())


def ensure_swarm_ready(docker: DockerClient, target: DeploymentTargetConfig) -> None:
    info = docker.system.info()
    swarm = info.swarm
    if swarm.local_node_state == "active":
        return
    if swarm.local_node_state not in {"inactive", "pending"}:
        raise RuntimeError(f"Docker swarm is not ready: {swarm.local_node_state}")
    docker.swarm.init(
        advertise_address=target.swarm_advertise_address,
        listen_address=target.swarm_listen_address,
    )


def ensure_network(docker: DockerClient, network_name: str, *, rootless: bool) -> None:
    command = [str(part) for part in docker.client_config.docker_cmd] + ["network", "inspect", network_name]
    try:
        run(*command)
        return
    except Exception:
        pass

    if rootless:
        docker.network.create(network_name, driver="bridge")
    else:
        docker.network.create(network_name, driver="overlay", attachable=True)


def build_compose(docker: DockerClient) -> None:
    docker.compose.build()


def rewrite_compose_for_target(compose_file: Path, runtime: ResolvedTargetConfig) -> Path:
    compose = yaml.safe_load(compose_file.read_text(encoding="utf-8")) or {}
    services = compose.get("services", {})
    network_name = runtime.stack_network

    compose["networks"] = {
        "ctf-services-net": {
            "external": True,
            "name": network_name,
        }
    }

    for service_name, service_config in services.items():
        if not isinstance(service_config, dict):
            continue

        if "container_name" in service_config:
            service_config.pop("container_name", None)
        if runtime.rootless and "restart" in service_config:
            service_config.pop("restart", None)

        service_config.setdefault("networks", ["ctf-services-net"])
        deploy = service_config.setdefault("deploy", {})
        labels = _normalize_labels(deploy.get("labels"))
        service_labels = _normalize_labels(service_config.get("labels"))

        if runtime.traefik_provider == "docker":
            labels.clear()
            service_labels.setdefault("traefik.enable", "false")
            for key, value in labels.items():
                service_labels[key] = value
            if service_labels.get("traefik.enable") == "true":
                service_labels["traefik.docker.network"] = network_name
        else:
            service_labels.clear()
            if labels.get("traefik.enable") == "true":
                labels["traefik.swarm.network"] = network_name

        if runtime.rootless:
            service_config.pop("volumes", None)

        _write_labels(service_config, "labels", service_labels)
        _write_labels(deploy, "labels", labels)

        if runtime.publish_mode == "host":
            ports = []
            for port in service_config.get("ports", []):
                if isinstance(port, str):
                    published, target = port.split(":", 1)
                    ports.append({
                        "published": int(published),
                        "target": int(target),
                        "protocol": "tcp",
                        "mode": "host",
                    })
                elif isinstance(port, dict):
                    updated = dict(port)
                    updated["mode"] = "host"
                    ports.append(updated)
            if ports:
                service_config["ports"] = ports

    tmp_dir = compose_file.parent / ".toolbox"
    tmp_dir.mkdir(exist_ok=True)
    target_path = tmp_dir / f"{compose_file.stem}.{runtime.traefik_provider}.{runtime.publish_mode}.stack.yml"
    target_path.write_text(yaml.safe_dump(compose, sort_keys=False), encoding="utf-8")
    return target_path


def _normalize_labels(value) -> dict[str, str]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return {str(key): str(item) for key, item in value.items()}
    labels: dict[str, str] = {}
    for item in value:
        if isinstance(item, str) and "=" in item:
            key, label_value = item.split("=", 1)
            labels[key] = label_value
    return labels


def _write_labels(container: dict, key: str, labels: dict[str, str]) -> None:
    if labels:
        container[key] = [f"{label}={value}" for label, value in labels.items()]
    else:
        container.pop(key, None)


def deploy_stack(
    docker: DockerClient,
    stack_name: str,
    compose_file: Path,
    *,
    runtime: ResolvedTargetConfig,
    with_registry_auth: bool,
) -> Path:
    rewritten_compose = rewrite_compose_for_target(compose_file, runtime)
    docker.stack.deploy(
        stack_name,
        compose_files=[rewritten_compose],
        prune=True,
        with_registry_auth=with_registry_auth,
    )
    return rewritten_compose


def remove_stack(docker: DockerClient, stack_name: str) -> bool:
    existing = {stack.name for stack in docker.stack.list()}
    if stack_name not in existing:
        return False
    docker.stack.remove(stack_name)
    return True


def service_full_name(stack_name: str, service_name: str) -> str:
    return f"{stack_name}_{service_name}"


def inspect_stack_service(docker: DockerClient, stack_name: str, service_name: str):
    return docker.service.inspect(service_full_name(stack_name, service_name))


def scale_stack_service(docker: DockerClient, stack_name: str, service_name: str, replicas: int) -> None:
    inspect_stack_service(docker, stack_name, service_name)
    docker.service.update(service_full_name(stack_name, service_name), replicas=replicas)


def restart_stack_service(docker: DockerClient, stack_name: str, service_name: str, replicas: int | None) -> None:
    full_name = service_full_name(stack_name, service_name)
    service = docker.service.inspect(full_name)
    current_replicas = service_replicas(service)

    if replicas is not None and current_replicas == 0:
        docker.service.update(full_name, replicas=replicas)
        return

    docker.service.update(full_name, force=True)


def enable_stack_service(docker: DockerClient, stack_name: str, service_name: str, replicas: int | None) -> None:
    restart_stack_service(docker, stack_name, service_name, replicas)


def service_replicas(service) -> int | None:
    replicated = service.spec.mode.get("Replicated") if service.spec.mode else None
    if replicated is None:
        return None
    return replicated.get("Replicas")


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
    rx_total = 0
    tx_total = 0

    for service_spec in expected_services:
        try:
            service = inspect_stack_service(docker, stack_name, service_spec.name)
        except NoSuchService:
            service_states.append((service_spec.name, "missing"))
            continue

        state = summarize_service_state(service)
        service_states.append((service_spec.name, state))

        for stats in get_service_container_stats(docker, service.spec.name):
            cpu_total += float(stats.cpu_percentage)
            mem_total += int(stats.memory_used)
            rx_total += int(stats.net_download)
            tx_total += int(stats.net_upload)

    states = [state for _, state in service_states]
    details = ", ".join(f"{name}: {state}" for name, state in service_states)
    overall = "partial"
    if states and all(state == "running" for state in states):
        overall = "running"
    elif states and all(state == "stopped" for state in states):
        overall = "stopped"
    elif any(state == "failed" for state in states):
        overall = "failed"
    elif any(state == "missing" for state in states):
        overall = "partial"

    return StackStatus(
        overall,
        details or "services present",
        cpu=f"{cpu_total:.1f}%" if cpu_total else "0.0%",
        memory=format_bytes(mem_total),
        network_rx=format_bytes(rx_total),
        network_tx=format_bytes(tx_total),
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
    if all(task.status.state == "running" for task in tasks if task.status):
        return "running"
    if any(task.status.state == "failed" for task in tasks if task.status):
        return "failed"
    if any(task.status.state == "rejected" for task in tasks if task.status):
        return "rejected"
    return "partial"


def get_service_logs(docker: DockerClient, service_name: str, tail: int = 100) -> str:
    return docker.service.logs(service_name, tail=tail, timestamps=True)


def get_service_inspection(docker: DockerClient, service_name: str) -> dict:
    service = docker.service.inspect(service_name)
    tasks = service.ps()
    containers = []
    for container in list_service_containers(docker, service_name):
        containers.append({
            "name": container.name,
            "status": container.state.status,
            "networks": list((container.network_settings.networks or {}).keys()),
            "ip": container.network_settings.ip_address,
        })

    return {
        "name": service.spec.name,
        "replicas": service_replicas(service),
        "labels": dict(service.spec.labels or {}),
        "endpoint": service.endpoint.model_dump() if service.endpoint else {},
        "tasks": [task._get_inspect_result().model_dump() for task in tasks],
        "containers": containers,
    }


def list_service_containers(docker: DockerClient, service_name: str):
    return docker.container.list(all=True, filters={"label": f"com.docker.swarm.service.name={service_name}"})


def get_service_container_stats(docker: DockerClient, service_name: str):
    containers = list_service_containers(docker, service_name)
    if not containers:
        return []
    return docker.container.stats(containers)


def format_bytes(value: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{value}B"
