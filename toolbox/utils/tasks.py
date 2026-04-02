from collections.abc import Generator
from pathlib import Path

from toolbox.utils.config import TaskConfig

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


def load_task_config(task_directory: Path) -> TaskConfig:
    return TaskConfig.from_path(task_directory / "config.yaml")


def get_task_deployment_targets(task_directory: Path) -> list[str]:
    try:
        config = load_task_config(task_directory)
    except FileNotFoundError, TypeError, ValueError:
        return []
    if config.deployment and config.deployment.targets:
        return config.deployment.targets
    return []
