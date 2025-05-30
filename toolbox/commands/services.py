import json
from pathlib import Path
from typing import Annotated

import rich
import typer
from rich.table import Table

from toolbox.utils.podman import Podman, PodmanCompose
from toolbox.utils.tasks import find_docker_compose_files

app = typer.Typer()


@app.callback()
def main(
    context: typer.Context,
    main_compose: Annotated[
        Path | None, typer.Option("--main-compose", help="Path to main docker-compose.yaml")
    ] = Path("docker-compose.yaml"),
):
    context.ensure_object(dict)
    context.obj["main_compose"] = main_compose
    return


@app.command()
def install():
    """
    Download and install podman_compose.py script to ./bin directory.
    """
    print("Downloading podman_compose...")
    PodmanCompose.install()
    print("podman-compose installed successfully in ./bin/podman_compose.py")


@app.command()
def up(context: typer.Context):
    """
    Start all services and add them to the pod
    """
    podman_compose = PodmanCompose()
    compose_files = list(find_docker_compose_files(context.obj["tasks_directory"]))

    for file in compose_files:
        print(f"Starting {file}...")
        podman_compose.up(file, labels={"pl.hack4krak.toolbox.task_id": file.parent.name})

    print("Starting main compose...")
    podman_compose.up(context.obj["main_compose"])

    print("All services are up and running")


@app.command()
def down():
    """
    Stop all services in the pod.
    """
    run("stop")
    print("Stopped all services")


@app.command()
def run(command: str = typer.Argument(None)):
    """
    Run `podman pod` commands for the 'tasks' pod.
    Useful subcommands: stats, restart, pause, rm.
    """
    podman = Podman()
    podman.run_pod(command)


@app.command()
def ps(context: typer.Context):
    """
    List all running services in the pod, their state, CPU and memory usage.
    """
    podman = Podman()
    podman_compose = PodmanCompose()

    expected_services = {
        directory.parent.name: podman_compose.services(cwd=str(directory.parent))
        for directory in find_docker_compose_files(context.obj["tasks_directory"])
    }

    podman_inspect = json.loads(podman.run_pod("inspect", capture_output=True).stdout)
    containers = (podman_inspect[0] if isinstance(podman_inspect, list) else podman_inspect)["Containers"]

    containers_data = podman.get_data("ps", [])
    containers_data = {container["Id"]: container for container in containers_data}

    running_services, unassigned = {}, []
    for container in containers:
        stats = podman.get_data("stats", [container["Id"], "--no-stream"])[0]
        task_id = containers_data[container["Id"]]["Labels"].get("pl.hack4krak.toolbox.task_id")
        entry = {
            "name": container["Name"],
            "state": container["State"],
            "cpu": stats.get("cpu_percent", "N/A"),
            "mem": stats.get("mem_usage", "N/A"),
        }

        if task_id:
            running_services.setdefault(task_id, []).append(entry)
        else:
            unassigned.append(entry)

    table = Table(expand=True)
    table.add_column(f"Name (in {podman_compose.pod} pod)", style="magenta")
    table.add_column("Task Id", style="white")
    table.add_column("State", style="green")
    table.add_column("CPU %", style="yellow")
    table.add_column("Memory", style="blue")

    for task_id, expected in expected_services.items():
        running = running_services.get(task_id, [])
        shown = {e["name"] for e in running}
        for entry in running:
            table.add_row(entry["name"], task_id, entry["state"], entry["cpu"], entry["mem"])
        for service in expected:
            if not any(service in name for name in shown):
                table.add_row(f"[dim]not running ({service})[/dim]", task_id, "[red]missing[/red]", "-", "-")
        table.add_section()

    for entry in unassigned:
        table.add_row(entry["name"], "[dim]unassigned[/dim]", entry["state"], entry["cpu"], entry["mem"])
    if unassigned:
        table.add_section()

    rich.print(table)
