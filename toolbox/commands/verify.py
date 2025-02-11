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
        assets_path = subdir_path / 'assets'

        if not config_path.is_file():
            continue

        if not description_path.is_file():
            invalid_count += 1
            rich.print(f"[red]Missing description file for {subdir_path}")
            continue

        yaml_data = yaml.safe_load(config_path.read_text(encoding='utf-8'))

        try:
            # print(yaml.sa
            # fe_load(config_path.read_text(encoding='utf-8')))
            validate(yaml_data, schema)
        except ValidationError as error:
            invalid_count += 1
            rich.print(f"[red]Validation error in {config_path}: {error.message}")
            continue

        if not verify_assets(yaml_data, assets_path, subdir_path):
            invalid_count += 1
        else:
            valid_count += 1

    total_tasks = valid_count + invalid_count
    rich.print(f"\nFinished validating all tasks: {total_tasks} tasks processed.")
    rich.print(f"[green]{valid_count} tasks are valid.")

    if invalid_count > 0:
        rich.print(f"[red]{invalid_count} tasks are invalid.")
        raise Exit(code=1)


def verify_assets(yaml_data: dict, assets_path: Path, subdir_path: Path) -> bool:
    """
    Verifies assets for a task.
    """
    assets = yaml_data.get("assets", [])

    assets_paths = [asset["path"] for asset in assets]
    if not find_unregistered_assets(assets_path, assets_paths, subdir_path):
        return False
    if not assets:
        return True
    if not assets_path.is_dir():
        rich.print(f"[red]Missing assets directory for {subdir_path}")
        return False

    for asset in assets:
        asset_path = assets_path / str(asset["path"])
        if not asset_path.is_file():
            rich.print(f"[red]Missing asset file {asset} for {subdir_path}")
            return False

    return True

def find_unregistered_assets(assets_path: Path, assets_paths: list, subdir_path: Path) -> bool:
    for asset in assets_path.iterdir():
        if asset.is_file() and asset.name not in assets_paths:
            rich.print(f"[red]Unregistered asset file {asset.name} for {subdir_path}")
            return False
        if asset.is_dir():
            if not find_unregistered_assets(asset, assets_paths, subdir_path):
                return False

    return True
