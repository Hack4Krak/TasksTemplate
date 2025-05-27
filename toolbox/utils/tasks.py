from collections.abc import Generator
from pathlib import Path

SUPPORTED_DOCKER_COMPOSE_FILES = ["docker-compose.yaml", "docker-compose.yml", "compose.yml", "compose.yaml"]


def find_tasks(tasks_directory: Path) -> Generator[Path]:
    if not tasks_directory.is_dir():
        raise NotADirectoryError()

    for subdir in tasks_directory.iterdir():
        if subdir.is_dir():
            yield subdir


def find_docker_compose_files(tasks_directory: Path) -> Generator[Path]:
    for subdir in find_tasks(tasks_directory):
        for filename in SUPPORTED_DOCKER_COMPOSE_FILES:
            docker_compose_file = subdir / filename
            if docker_compose_file.is_file():
                yield docker_compose_file
