import json
from pathlib import Path

import rich
import typer
import yaml
from click.exceptions import Exit
from jsonschema import ValidationError, validate

from toolbox.utils.config import EventConfig, LabelsConfig, RegistrationConfig
from toolbox.utils.tasks import find_tasks

app = typer.Typer()


@app.command(name="all")
def verify_all(context: typer.Context):
    """
    Verifies all configurations
    """
    config(context)
    labels(context)
    tasks(context)

    rich.print("[dim]Finished validating entire configuration!")


@app.command()
def config(context: typer.Context):
    """
    Verifies all files in config directory
    """
    config_directory: Path = context.obj["config_directory"]

    try:
        EventConfig.from_config_directory(config_directory)
        RegistrationConfig.from_config_directory(config_directory)
        rich.print("[green]All config files are valid!")
    except Exception as exception:
        rich.print(f"[red]event.yaml config is invalid: {exception}")


@app.command()
def labels(context: typer.Context):
    """
    Verifies all files in labels directory
    """
    config_directory: Path = context.obj["config_directory"]

    labels_icon_dir = config_directory / "assets/labels"
    label_icons = [str(i.name).removesuffix(str(i.suffix)).lower() for i in labels_icon_dir.iterdir()]

    try:
        labels_config = LabelsConfig.from_config_directory(config_directory)
        rich.print("[green]Labels config is valid!")
    except Exception as exception:
        rich.print(f"[red]Labels config file is invalid: {exception}")
        raise Exit(code=1) from None

    invalid_count = 0
    for label in labels_config.labels:
        if label.id not in label_icons:
            invalid_count += 1
            rich.print(f"[red]Missing icon file for label id: {label.id}")
            continue

    if invalid_count > 0:
        rich.print(f"[red]{invalid_count} labels have missing icons!")
        raise Exit(code=1)

    if len(label_icons) != len(labels_config.labels):
        rich.print("[red]Label icons do not match the number of labels!")
        raise Exit(code=1)

    rich.print("[green]All labels are valid!")


@app.command()
def tasks(context: typer.Context):
    """
    Verifies configuration of all tasks.
    """
    tasks_directory: Path = context.obj["tasks_directory"]
    config_directory: Path = context.obj["config_directory"]
    labels_config = [label.id for label in LabelsConfig.from_config_directory(config_directory).labels]

    schema_path = tasks_directory / "schema.json"
    schema = json.loads(schema_path.read_text())

    valid_count = 0
    invalid_count = 0

    rich.print("[dim]Validating tasks...")
    for subdir_path in find_tasks(tasks_directory):
        config_path = subdir_path / "config.yaml"
        for path in ["config.yaml", "description.md", "solution.md"]:
            if not (subdir_path / path).is_file():
                invalid_count += 1
                rich.print(f"[red]Missing {path} for {subdir_path}")
                continue

        yaml_data = yaml.safe_load(config_path.read_text(encoding="utf-8"))

        task_id = yaml_data.get("id", "")
        if task_id != subdir_path.name:
            invalid_count += 1
            rich.print(f"[red]Task id is different than task directory name {subdir_path.name} for {task_id}")
            continue

        try:
            validate(yaml_data, schema)
        except ValidationError as error:
            invalid_count += 1
            rich.print(f"[red]Validation error in {config_path}: {error.message}")
            continue

        assets_path = subdir_path / "assets"
        if not verify_assets(yaml_data, assets_path, subdir_path):
            invalid_count += 1
            continue

        if not verify_pictures(subdir_path / "pictures"):
            invalid_count += 1
            continue

        labels_in_task = yaml_data.get("labels")
        for label in labels_in_task:
            if label not in labels_config:
                rich.print(f"[red]Invalid label format in task {subdir_path}: {label}")
                invalid_count += 1
                continue

        valid_count += 1

    total_tasks = valid_count + invalid_count
    rich.print(f"\nFinished validating all tasks: {total_tasks} tasks processed.")
    rich.print(f"[green]{valid_count} tasks are valid.")

    if invalid_count > 0:
        rich.print(f"[red]{invalid_count} tasks are invalid.")
        raise Exit(code=1)


def verify_assets(yaml_data: dict, assets_path: Path, subdir_path: Path) -> bool:
    assets = yaml_data.get("assets", [])

    config_assets_paths = [asset["path"] for asset in assets]
    try:
        for asset in assets_path.iterdir():
            if asset.is_file() and asset.name not in config_assets_paths:
                rich.print(f"[red]Unregistered asset file {asset.name} for {subdir_path}")
                return False
    except FileNotFoundError:
        pass
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


def verify_pictures(subdir_path: Path) -> bool:
    required_pictures = ["background.png", "icon.png"]
    for picture in required_pictures:
        picture_path = subdir_path.joinpath(picture)
        if not picture_path.is_file():
            rich.print(f"[red]Missing file pictures/{picture} for {subdir_path}")
            return False

    return True
