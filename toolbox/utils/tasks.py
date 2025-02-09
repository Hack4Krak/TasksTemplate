from pathlib import Path
from typing import Generator


def find_tasks(tasks_directory: Path) -> Generator[Path, None, None]:
    if not tasks_directory.is_dir():
        raise NotADirectoryError()

    for subdir in tasks_directory.iterdir():
        if subdir.is_dir():
            yield subdir
