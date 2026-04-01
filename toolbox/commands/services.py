from pathlib import Path
from typing import Annotated

import rich
import typer
from python_on_whales import DockerClient
from rich.table import Table

from toolbox.utils.deployment.deployment import (
    compose_has_build,
    create_docker_client,
    get_target_config,
    list_task_deployments,
    load_compose_service_specs,
    load_deployments_config,
    resolve_main_compose_path,
)
from toolbox.utils.deployment.network import (
    ensure_stack_network,
    ensure_swarm_ready,
)
from toolbox.utils.deployment.service import get_stack_logs
from toolbox.utils.deployment.stack import MAIN_STACK_NAME, deploy_stack, remove_stack
from toolbox.utils.deployment.stats import get_stack_status

app = typer.Typer(no_args_is_help=True, help="Manage CTF task services")


def _get_deployments(context: typer.Context, task: str | None, target: str | None):
    requested_tasks = {task} if task else None
    deployments = list_task_deployments(
        context.obj["tasks_directory"],
        context.obj["config_directory"],
        requested_target=target,
        requested_tasks=requested_tasks,
    )
    if task and not deployments:
        raise typer.BadParameter(f"Task '{task}' does not define a deployable compose stack")
    return deployments


def _group_by_target(deployments) -> dict[str, list]:
    by_target: dict[str, list] = {}
    for deployment in deployments:
        by_target.setdefault(deployment.target, []).append(deployment)
    return by_target


def _build_and_deploy(docker: DockerClient, stack_name: str, compose_file: Path, build: bool):
    if build and compose_has_build(compose_file):
        create_docker_client(
            compose_files=[compose_file],
            compose_project_directory=compose_file.parent,
        ).compose.build()
    deploy_stack(docker, stack_name, compose_file)


@app.command("status")
def status(
    context: typer.Context,
    task: Annotated[str | None, typer.Argument(help="Show status for specific task (omit for all tasks)")] = None,
    target: Annotated[str | None, typer.Option("--target", help="Filter by deploy target")] = None,
):
    """Show status of all stacks including the main stack."""
    deployments = _get_deployments(context, task, target)

    if not target:
        target = load_deployments_config(context.obj["config_directory"]).default_target

    table = Table(expand=True, title="Services Status" if not task else None)
    table.add_column("Stack", style="magenta")
    table.add_column("Target", style="cyan")
    table.add_column("State", style="green")
    table.add_column("CPU", style="yellow")
    table.add_column("Memory", style="blue")
    table.add_column("RX", style="white")
    table.add_column("TX", style="white")
    table.add_column("Services", style="dim")

    by_target = _group_by_target(deployments)

    for target_name in sorted(by_target):
        docker = create_docker_client()
        if not task:
            main_compose = resolve_main_compose_path(context.obj["config_directory"], target_name, None)
            expected_services = load_compose_service_specs(main_compose)
            stack_status = get_stack_status(docker, MAIN_STACK_NAME, expected_services)
            table.add_row(
                MAIN_STACK_NAME,
                target_name,
                stack_status.state,
                stack_status.cpu,
                stack_status.memory,
                stack_status.network_rx,
                stack_status.network_tx,
                stack_status.details,
            )
        for deployment in by_target[target_name]:
            expected_services = load_compose_service_specs(deployment.compose_file)
            stack_status = get_stack_status(docker, deployment.stack_name, expected_services)
            table.add_row(
                deployment.task_id,
                target_name,
                stack_status.state,
                stack_status.cpu,
                stack_status.memory,
                stack_status.network_rx,
                stack_status.network_tx,
                stack_status.details,
            )

    rich.print(table)


@app.command("up")
def up(
    context: typer.Context,
    task: Annotated[str | None, typer.Argument(help="Task to start (omit for all tasks)")] = None,
    build: Annotated[bool, typer.Option("--build/--no-build", help="Build images before starting")] = True,
    target: Annotated[str | None, typer.Option("--target", help="Target environment")] = None,
):
    """Start one task or all tasks (default)."""
    deployments = _get_deployments(context, task, target)

    if not deployments:
        rich.print("[yellow]Nothing to start.[/yellow]")
        return

    if not target:
        target = load_deployments_config(context.obj["config_directory"]).default_target

    by_target = _group_by_target(deployments)

    for target_name in sorted(by_target):
        target_config = get_target_config(context.obj["config_directory"], target_name)
        docker = create_docker_client()
        ensure_swarm_ready(docker)
        ensure_stack_network(docker, target_config.stack_network or "ctf-services-net")

        main_compose = resolve_main_compose_path(context.obj["config_directory"], target_name, None)
        rich.print(f"[cyan]Starting main stack (Traefik) on '{target_name}'...[/cyan]")
        _build_and_deploy(docker, MAIN_STACK_NAME, main_compose, build)

        for deployment in by_target.get(target_name, []):
            rich.print(f"[cyan]Starting task '{deployment.task_id}' on '{target_name}'...[/cyan]")
            _build_and_deploy(docker, deployment.stack_name, deployment.compose_file, build)

    rich.print("[green]Done.[/green]")


@app.command("down")
def down(
    context: typer.Context,
    task: Annotated[str | None, typer.Argument(help="Task to stop")] = None,
    all_tasks: Annotated[bool, typer.Option("--all", help="Stop all tasks")] = False,
    target: Annotated[str | None, typer.Option("--target", help="Target environment")] = None,
):
    """Stop one task or all tasks (with --all flag)."""
    if not task and not all_tasks:
        raise typer.BadParameter("Specify a TASK or use --all to stop everything")

    deployments = _get_deployments(context, task, target)

    if not deployments:
        rich.print("[yellow]No tasks to stop.[/yellow]")
        return

    if not target:
        target = load_deployments_config(context.obj["config_directory"]).default_target

    by_target = _group_by_target(deployments)

    for target_name in sorted(by_target):
        docker = create_docker_client()
        for deployment in by_target[target_name]:
            if remove_stack(docker, deployment.stack_name):
                rich.print(f"[green]Stopped task '{deployment.task_id}'[/green]")
            else:
                rich.print(f"[yellow]Task '{deployment.task_id}' was not running[/yellow]")

        if all_tasks:
            if remove_stack(docker, MAIN_STACK_NAME):
                rich.print("[green]Stopped main stack[/green]")
            else:
                rich.print("[yellow]Main stack was not running[/yellow]")


@app.command("restart")
def restart(
    context: typer.Context,
    task: Annotated[str | None, typer.Argument(help="Task to restart")] = None,
    all_tasks: Annotated[bool, typer.Option("--all", help="Restart all tasks")] = False,
    build: Annotated[bool, typer.Option("--build/--no-build", help="Build images before restarting")] = True,
    target: Annotated[str | None, typer.Option("--target", help="Target environment")] = None,
):
    """Restart one task or all tasks (with --all flag)."""
    if not task and not all_tasks:
        raise typer.BadParameter("Specify a TASK or use --all to restart everything")

    down(context, task, all_tasks, target)
    up(context, task, build, target)


@app.command("logs")
def logs(
    context: typer.Context,
    task: Annotated[str, typer.Argument(help="Task to view logs")],
    tail: Annotated[int, typer.Option("--tail", help="Show only last n log lines per service")] = 100,
    target: Annotated[str | None, typer.Option("--target", help="Target environment")] = None,
):
    """Show logs for all services in a task."""
    deployments = _get_deployments(context, task, target)
    if not deployments:
        return

    deployment = deployments[0]
    docker = create_docker_client()
    rich.print(get_stack_logs(docker, deployment.stack_name, deployment.compose_file, tail=tail))


# Aliases
app.command("start", hidden=True)(up)
app.command("stop", hidden=True)(down)
app.command("ps", hidden=True)(status)
app.command("ls", hidden=True)(status)
