from pathlib import Path
from typing import Annotated, Optional

import rich
import typer
from rich.table import Table

from toolbox.utils.docker import get_docker_client

app = typer.Typer()


@app.callback()
def main(
        context: typer.Context,
        main_compose: Annotated[
            Optional[Path],
            typer.Option("--main-compose", help="Path to main docker-compose.yaml")
        ] = Path("docker-compose.yaml")
):
    context.ensure_object(dict)
    context.obj["main_compose"] = main_compose
    return


@app.command()
def up(context: typer.Context):
    """
    Starts all tasks services
    """
    docker = get_docker_client(context)

    docker.compose.build()
    docker.compose.up(detach=True)

    print("All services are up and running")


@app.command()
def down(context: typer.Context):
    """
    Stops all running services
    """
    docker = get_docker_client(context)

    docker.compose.down()

    print("All services are down")


@app.command()
def ps(context: typer.Context):
    """
    Displays status of all Docker containers in a modern full-screen table.
    """
    docker = get_docker_client(context)
    services_amount = len(docker.compose.config().services)

    table = Table(expand=True)

    table.add_column("Name", style="magenta")
    table.add_column("Status", style="green")

    running_containers = docker.compose.ps(all=True)
    for container in running_containers:
        status_color = "green" if container.state.running else "red"
        table.add_row(
            container.name,
            f"[{status_color}]{container.state.status}[/{status_color}]",
        )

    rich.print(table)
    rich.print(f"There are {len(running_containers)}/{services_amount} containers running")
