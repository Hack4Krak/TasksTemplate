from collections.abc import Generator
from pathlib import Path

import yaml

SUPPORTED_DOCKER_COMPOSE_FILES = ["docker-compose.yaml", "docker-compose.yml", "compose.yml", "compose.yaml"]


def find_tasks(tasks_directory: Path) -> Generator[Path]:
    if not tasks_directory.is_dir():
        raise NotADirectoryError()

    for subdir in tasks_directory.iterdir():
        if subdir.is_dir():
            yield subdir


def find_docker_compose_file(task_directory: Path) -> Path | None:
    for filename in SUPPORTED_DOCKER_COMPOSE_FILES:
        docker_compose_file = task_directory / filename
        if docker_compose_file.is_file():
            return docker_compose_file
    return None


def find_docker_compose_files(tasks_directory: Path) -> Generator[Path]:
    for subdir in find_tasks(tasks_directory):
        docker_compose_file = find_docker_compose_file(subdir)
        if docker_compose_file is not None:
            yield docker_compose_file


def load_task_config(task_directory: Path) -> dict:
    return yaml.safe_load((task_directory / "config.yaml").read_text(encoding="utf-8"))


def get_task_deployment_target(task_directory: Path) -> str | None:
    deployment = load_task_config(task_directory).get("deployment", {})
    if isinstance(deployment, dict):
        target = deployment.get("target")
        if isinstance(target, str) and target:
            return target
    return None
