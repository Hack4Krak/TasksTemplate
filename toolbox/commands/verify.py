import json
from pathlib import Path

import rich
import typer
import yaml
from click.exceptions import Exit
from jsonschema import ValidationError, validate

from toolbox.utils.tasks import find_tasks


def verify(context: typer.Context):
    """
    Verifies configuration of all tasks.
    """
    tasks_directory: Path = context.obj["tasks_directory"]

    schema_path = tasks_directory / 'schema.json'
    schema = json.loads(schema_path.read_text())

    valid_count = 0
    invalid_count = 0

    rich.print("[dim]Validating tasks...")
    for subdir_path in find_tasks(tasks_directory):
        config_path = subdir_path / 'config.yaml'
        description_path = subdir_path / 'description.md'

        if not config_path.is_file():
            continue

        if not description_path.is_file():
            invalid_count += 1
            rich.print(f"[red]Missing description file for {subdir_path}")
            continue

        try:
            # print(yaml.sa
            # fe_load(config_path.read_text(encoding='utf-8')))
            yaml_data = yaml.safe_load(config_path.read_text(encoding='utf-8'))
            validate(yaml_data, schema)
            valid_count += 1
        except ValidationError as error:
            invalid_count += 1
            rich.print(f"[red]Validation error in {config_path}: {error.message}")

    total_tasks = valid_count + invalid_count
    rich.print(f"\nFinished validating all tasks: {total_tasks} tasks processed.")
    rich.print(f"[green]{valid_count} tasks are valid.")

    if invalid_count > 0:
        rich.print(f"[red]{invalid_count} tasks are invalid.")
        raise Exit(code=1)

