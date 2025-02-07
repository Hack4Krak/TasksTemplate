import os
import json

import rich
import yaml
import typer
from click.exceptions import Exit
from jsonschema import validate, ValidationError


def verify(context: typer.Context):
    """
    Verifies configuration of all tasks.
    """
    tasks_directory = context.obj["tasks_directory"]

    schema_path = os.path.join(tasks_directory, 'schema.json')
    with open(schema_path, 'r') as schema_file:
        schema = json.load(schema_file)

    valid_count = 0
    invalid_count = 0

    rich.print(f"[dim]Validating tasks...")
    for subdir in os.listdir(tasks_directory):
        subdir_path = os.path.join(tasks_directory, subdir)
        config_path = os.path.join(subdir_path, 'config.yaml')
        description_path = os.path.join(subdir_path, 'description.md')

        if os.path.isdir(subdir_path) and os.path.isfile(config_path):
            if not os.path.isfile(description_path):
                invalid_count += 1
                rich.print(f"[red]Missing description file for {subdir_path}")
                continue

            with open(config_path, 'r', encoding='utf-8') as yaml_file:
                yaml_data = yaml.safe_load(yaml_file.read())

            try:
                validate(instance=yaml_data, schema=schema)
                valid_count += 1
            except ValidationError as e:
                invalid_count += 1
                rich.print(f"[red]Validation error in {config_path}: {e.message}")

    total_tasks = valid_count + invalid_count
    rich.print(f"\nFinished validating all tasks: {total_tasks} tasks processed.")
    rich.print(f"[green]{valid_count} tasks are valid.")

    if invalid_count > 0:
        rich.print(f"[red]{invalid_count} tasks are invalid.")
        raise Exit(code=1)

