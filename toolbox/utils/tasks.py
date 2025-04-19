from collections.abc import Generator
from pathlib import Path


def find_tasks(tasks_directory: Path) -> Generator[Path]:
    if not tasks_directory.is_dir():
        raise NotADirectoryError()

    for subdir in tasks_directory.iterdir():
        if subdir.is_dir():
            yield subdir
