from pathlib import Path
from typing import Generator


def find_tasks(tasks_directory: str) -> Generator[Path, None, None]:
    tasks_directory = Path(tasks_directory)
    if not tasks_directory.is_dir():
        raise NotADirectoryError()

    for subdir in tasks_directory.iterdir():
        if subdir.is_dir():
            yield subdir
