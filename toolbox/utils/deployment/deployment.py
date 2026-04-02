from pathlib import Path

import yaml

from toolbox.utils.config import DeploymentsConfig, DeploymentTargetConfig
from toolbox.utils.tasks import find_docker_compose_file, find_tasks

from .models import ComposeServiceSpec, TaskDeployment
from .stack import task_stack_name


def load_deployments_config(config_directory: Path) -> DeploymentsConfig:
    return DeploymentsConfig.from_config_directory_optional(config_directory)


def get_target_config(config_directory: Path, target_name: str) -> DeploymentTargetConfig:
    deployments = load_deployments_config(config_directory)
    try:
        return deployments.targets[target_name]
    except KeyError as exception:
        available = ", ".join(sorted(deployments.targets))
        raise RuntimeError(f"Unknown deploy target '{target_name}'. Available targets: {available}") from exception


def resolve_main_compose_path(config_directory: Path, target_name: str, main_compose: Path | None) -> Path:
    project_root = config_directory.parent
    candidate = main_compose or Path(
        get_target_config(config_directory, target_name).main_compose or "docker-compose.yaml"
    )
    return candidate if candidate.is_absolute() else project_root / candidate


def create_docker_client(
    compose_files: list[str | Path] | None = None,
    compose_project_directory: Path | None = None,
):
    from python_on_whales import DockerClient

    kwargs: dict = {"client_type": "docker"}
    if compose_files:
        kwargs["compose_files"] = compose_files
    if compose_project_directory:
        kwargs["compose_project_directory"] = compose_project_directory
    return DockerClient(**kwargs)


def list_task_deployments(
    tasks_directory: Path,
    config_directory: Path,
    requested_target: str | None = None,
    requested_tasks: set[str] | None = None,
) -> list[TaskDeployment]:
    from toolbox.utils.tasks import get_task_deployment_targets

    default_target = load_deployments_config(config_directory).default_target
    current_target = requested_target or default_target
    deployments: list[TaskDeployment] = []

    for task_directory in find_tasks(tasks_directory):
        if requested_tasks and task_directory.name not in requested_tasks:
            continue

        compose_file = find_docker_compose_file(task_directory)
        if compose_file is None:
            continue

        task_targets = get_task_deployment_targets(task_directory)
        if task_targets and current_target not in task_targets:
            continue

        deployments.append(
            TaskDeployment(
                task_id=task_directory.name,
                target=current_target,
                stack_name=task_stack_name(task_directory.name),
                compose_file=compose_file,
            )
        )

    return deployments


def load_compose_service_specs(compose_file: Path) -> list[ComposeServiceSpec]:
    compose = yaml.safe_load(compose_file.read_text(encoding="utf-8")) or {}
    services = compose.get("services", {})
    result: list[ComposeServiceSpec] = []

    for service_name, service_config in services.items():
        if not isinstance(service_config, dict):
            continue
        deploy = service_config.get("deploy") or {}
        replicas_raw = deploy.get("replicas", 1)
        replicas = None if deploy.get("mode") == "global" else int(replicas_raw)
        result.append(ComposeServiceSpec(name=service_name, replicas=replicas))

    return result


def compose_has_build(compose_file: Path) -> bool:
    compose = yaml.safe_load(compose_file.read_text(encoding="utf-8")) or {}
    services = compose.get("services", {})
    return any(isinstance(s, dict) and "build" in s for s in services.values())
