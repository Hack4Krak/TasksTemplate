import json
from pathlib import Path
from typing import Annotated

import rich
import typer
from rich.table import Table

from toolbox.utils.deployment import (
    MAIN_STACK_NAME,
    build_compose,
    compose_has_build,
    create_docker_client,
    deploy_stack,
    enable_stack_service,
    ensure_network,
    ensure_swarm_ready,
    format_bytes,
    get_default_target_name,
    get_service_container_stats,
    get_service_inspection,
    get_service_logs,
    get_stack_status,
    get_target_config,
    group_task_deployments_by_target,
    inspect_stack_service,
    list_task_deployments,
    load_compose_service_specs,
    remove_stack,
    resolve_main_compose_path,
    resolve_target_runtime,
    restart_stack_service,
    scale_stack_service,
    service_full_name,
)

app = typer.Typer(no_args_is_help=True)
status_app = typer.Typer(no_args_is_help=True)
stack_app = typer.Typer(no_args_is_help=True)
service_app = typer.Typer(no_args_is_help=True)
dev_app = typer.Typer(no_args_is_help=True)

app.add_typer(status_app, name="status")
app.add_typer(stack_app, name="stack")
app.add_typer(service_app, name="service")
app.add_typer(dev_app, name="dev")


@app.callback()
def main(
    context: typer.Context,
    main_compose: Annotated[
        Path | None, typer.Option("--main-compose", help="Path to main compose file for the selected target")
    ] = None,
):
    context.ensure_object(dict)
    context.obj["main_compose"] = main_compose


def _normalize_tasks(tasks: list[str] | None) -> set[str] | None:
    return set(tasks) if tasks else None


def _group_requested_tasks(context: typer.Context, target: str | None, tasks: list[str] | None):
    return group_task_deployments_by_target(
        context.obj["tasks_directory"],
        context.obj["config_directory"],
        requested_target=target,
        requested_tasks=_normalize_tasks(tasks),
    )


def _main_compose_for_target(context: typer.Context, target_name: str) -> Path:
    return resolve_main_compose_path(context.obj["config_directory"], target_name, context.obj.get("main_compose"))


def _deployment_for_task(context: typer.Context, task: str):
    deployments = list_task_deployments(
        context.obj["tasks_directory"],
        context.obj["config_directory"],
        requested_tasks={task},
    )
    if not deployments:
        raise typer.BadParameter(f"Task '{task}' does not define a deployable compose stack")
    return deployments[0]


def _runtime_and_client(context: typer.Context, target_name: str):
    target_config = get_target_config(context.obj["config_directory"], target_name)
    docker = create_docker_client(target_config)
    runtime = resolve_target_runtime(docker, target_config)
    return docker, target_config, runtime


@status_app.command("tasks")
def status_tasks(
    context: typer.Context,
    target: Annotated[str | None, typer.Option("--target", help="Show tasks only for a specific deploy target")] = None,
):
    """
    List deployable tasks, state, and resource usage.
    """
    deployments = list_task_deployments(
        context.obj["tasks_directory"], context.obj["config_directory"], requested_target=target
    )
    if not deployments:
        rich.print("[yellow]No deployable tasks found for the selected target.[/yellow]")
        return

    table = Table(expand=True)
    table.add_column("Task", style="magenta")
    table.add_column("Target", style="cyan")
    table.add_column("Stack", style="white")
    table.add_column("State", style="green")
    table.add_column("CPU", style="yellow")
    table.add_column("Memory", style="blue")
    table.add_column("RX", style="white")
    table.add_column("TX", style="white")
    table.add_column("Details", style="dim")

    grouped: dict[str, list] = {}
    for deployment in deployments:
        grouped.setdefault(deployment.target, []).append(deployment)

    for target_name in sorted(grouped):
        docker, _, _runtime = _runtime_and_client(context, target_name)
        for deployment in grouped[target_name]:
            expected_services = load_compose_service_specs(deployment.compose_file)
            stack_status = get_stack_status(docker, deployment.stack_name, expected_services)
            table.add_row(
                deployment.task_id,
                target_name,
                deployment.stack_name,
                stack_status.state,
                stack_status.cpu,
                stack_status.memory,
                stack_status.network_rx,
                stack_status.network_tx,
                stack_status.details,
            )

    rich.print(table)


@status_app.command("services")
def status_services(
    context: typer.Context,
    task: Annotated[str, typer.Argument(help="Task id to inspect")],
):
    """
    Show per-service status for a task stack.
    """
    deployment = _deployment_for_task(context, task)
    docker, _, _runtime = _runtime_and_client(context, deployment.target)

    table = Table(expand=True)
    table.add_column("Service", style="magenta")
    table.add_column("State", style="green")
    table.add_column("Replicas", style="cyan")
    table.add_column("CPU", style="yellow")
    table.add_column("Memory", style="blue")
    table.add_column("RX", style="white")
    table.add_column("TX", style="white")

    for service_spec in load_compose_service_specs(deployment.compose_file):
        service = inspect_stack_service(docker, deployment.stack_name, service_spec.name)
        stats = get_service_container_stats(docker, service.spec.name)
        cpu = sum(float(item.cpu_percentage) for item in stats)
        memory = sum(int(item.memory_used) for item in stats)
        rx = sum(int(item.net_download) for item in stats)
        tx = sum(int(item.net_upload) for item in stats)
        table.add_row(
            service_spec.name,
            get_stack_status(docker, deployment.stack_name, [service_spec]).details.split(": ", 1)[-1],
            str(service.spec.mode.get("Replicated", {}).get("Replicas", 1) if service.spec.mode else 1),
            f"{cpu:.1f}%",
            format_bytes(memory),
            format_bytes(rx),
            format_bytes(tx),
        )

    rich.print(table)


@stack_app.command("deploy")
def stack_deploy(
    context: typer.Context,
    build: Annotated[bool, typer.Option("--build/--no-build", help="Build compose images before deploying")] = True,
    target: Annotated[str | None, typer.Option("--target", help="Deploy only stacks assigned to this target")] = None,
    tasks: Annotated[list[str] | None, typer.Option("--tasks", help="Deploy only selected tasks")] = None,
    include_main: Annotated[bool, typer.Option("--main/--no-main", help="Deploy the shared main stack")] = True,
):
    """
    Deploy stacks for the selected targets.
    """
    grouped = _group_requested_tasks(context, target, tasks)
    if not grouped and not include_main:
        rich.print("[yellow]Nothing to deploy for the selected filters.[/yellow]")
        return

    targets_to_process = sorted(set(grouped) | ({target} if target else set()))
    if not targets_to_process:
        targets_to_process = [get_default_target_name(context.obj["config_directory"])]

    for target_name in targets_to_process:
        docker, target_config, runtime = _runtime_and_client(context, target_name)
        ensure_swarm_ready(docker, target_config)
        ensure_network(docker, runtime.stack_network, rootless=runtime.rootless)

        if include_main:
            main_compose = _main_compose_for_target(context, target_name)
            rich.print(
                f"[cyan]Deploying main stack for target '{target_name}' ({runtime.traefik_provider}/{runtime.publish_mode})...[/cyan]"
            )
            if build and compose_has_build(main_compose):
                build_client = create_docker_client(
                    target_config,
                    compose_files=[main_compose],
                    compose_project_directory=main_compose.parent,
                )
                build_compose(build_client)
            deploy_stack(
                docker,
                MAIN_STACK_NAME,
                main_compose,
                runtime=runtime,
                with_registry_auth=target_config.with_registry_auth,
            )

        for deployment in grouped.get(target_name, []):
            rich.print(f"[cyan]Deploying task '{deployment.task_id}' to target '{target_name}'...[/cyan]")
            if build and compose_has_build(deployment.compose_file):
                build_client = create_docker_client(
                    target_config,
                    compose_files=[deployment.compose_file],
                    compose_project_directory=deployment.compose_file.parent,
                )
                build_compose(build_client)
            deploy_stack(
                docker,
                deployment.stack_name,
                deployment.compose_file,
                runtime=runtime,
                with_registry_auth=target_config.with_registry_auth,
            )

    rich.print("[green]Deployment finished.[/green]")


@stack_app.command("stop")
def stack_stop(
    context: typer.Context,
    task: Annotated[str, typer.Argument(help="Task id to stop")],
):
    """
    Remove a whole task stack.
    """
    deployment = _deployment_for_task(context, task)
    docker, _, _runtime = _runtime_and_client(context, deployment.target)
    removed = remove_stack(docker, deployment.stack_name)
    if not removed:
        rich.print(f"[yellow]Stack '{deployment.stack_name}' is not deployed.[/yellow]")
        return
    rich.print(f"[green]Stopped task '{task}'.[/green]")


@stack_app.command("restart")
def stack_restart(
    context: typer.Context,
    task: Annotated[str, typer.Argument(help="Task id to restart")],
    build: Annotated[bool, typer.Option("--build/--no-build", help="Build images before redeploying")] = True,
):
    """
    Redeploy a whole task stack.
    """
    deployment = _deployment_for_task(context, task)
    docker, target_config, runtime = _runtime_and_client(context, deployment.target)
    ensure_swarm_ready(docker, target_config)
    ensure_network(docker, runtime.stack_network, rootless=runtime.rootless)

    remove_stack(docker, deployment.stack_name)
    if build and compose_has_build(deployment.compose_file):
        build_client = create_docker_client(
            target_config,
            compose_files=[deployment.compose_file],
            compose_project_directory=deployment.compose_file.parent,
        )
        build_compose(build_client)
    deploy_stack(
        docker,
        deployment.stack_name,
        deployment.compose_file,
        runtime=runtime,
        with_registry_auth=target_config.with_registry_auth,
    )
    rich.print(f"[green]Restarted task '{task}'.[/green]")


@service_app.command("stop")
def service_stop(
    context: typer.Context,
    task: Annotated[str, typer.Argument(help="Task id")],
    service: Annotated[str, typer.Argument(help="Service name from task compose")],
):
    """
    Disable one service by scaling it to zero.
    """
    deployment = _deployment_for_task(context, task)
    docker, _, _runtime = _runtime_and_client(context, deployment.target)
    scale_stack_service(docker, deployment.stack_name, service, replicas=0)
    rich.print(f"[green]Stopped service '{service}' for task '{task}'.[/green]")


@service_app.command("start")
def service_start(
    context: typer.Context,
    task: Annotated[str, typer.Argument(help="Task id")],
    service: Annotated[str, typer.Argument(help="Service name from task compose")],
):
    """
    Enable one service using its configured replica count.
    """
    deployment = _deployment_for_task(context, task)
    docker, _, _runtime = _runtime_and_client(context, deployment.target)
    service_specs = {spec.name: spec for spec in load_compose_service_specs(deployment.compose_file)}
    if service not in service_specs:
        raise typer.BadParameter(f"Service '{service}' is not defined in task '{task}' compose file")
    enable_stack_service(docker, deployment.stack_name, service, service_specs[service].replicas)
    rich.print(f"[green]Started service '{service}' for task '{task}'.[/green]")


@service_app.command("restart")
def service_restart(
    context: typer.Context,
    task: Annotated[str, typer.Argument(help="Task id")],
    service: Annotated[str, typer.Argument(help="Service name from task compose")],
):
    """
    Force a service restart.
    """
    deployment = _deployment_for_task(context, task)
    docker, _, _runtime = _runtime_and_client(context, deployment.target)
    service_specs = {spec.name: spec for spec in load_compose_service_specs(deployment.compose_file)}
    if service not in service_specs:
        raise typer.BadParameter(f"Service '{service}' is not defined in task '{task}' compose file")
    restart_stack_service(docker, deployment.stack_name, service, service_specs[service].replicas)
    rich.print(f"[green]Restarted service '{service}' for task '{task}'.[/green]")


@service_app.command("logs")
def service_logs(
    context: typer.Context,
    task: Annotated[str, typer.Argument(help="Task id")],
    service: Annotated[str, typer.Argument(help="Service name from task compose")],
    tail: Annotated[int, typer.Option("--tail", help="Number of log lines to show")] = 100,
):
    """
    Show service logs.
    """
    deployment = _deployment_for_task(context, task)
    docker, _, _runtime = _runtime_and_client(context, deployment.target)
    rich.print(get_service_logs(docker, service_full_name(deployment.stack_name, service), tail=tail))


@service_app.command("inspect")
def service_inspect(
    context: typer.Context,
    task: Annotated[str, typer.Argument(help="Task id")],
    service: Annotated[str, typer.Argument(help="Service name from task compose")],
):
    """
    Show service inspection data.
    """
    deployment = _deployment_for_task(context, task)
    docker, _, _runtime = _runtime_and_client(context, deployment.target)
    rich.print_json(json.dumps(get_service_inspection(docker, service_full_name(deployment.stack_name, service))))


@dev_app.command("proxy")
def dev_proxy(
    context: typer.Context,
    task: Annotated[str, typer.Argument(help="Task id")],
    service: Annotated[str, typer.Argument(help="Service name from task compose")],
    local_port: Annotated[int, typer.Option("--local-port", help="Port exposed on the host")],
    target_port: Annotated[int, typer.Option("--target-port", help="Port inside the target service")],
):
    """
    Start a local TCP proxy container that forwards host traffic to a task service.
    """
    deployment = _deployment_for_task(context, task)
    docker, _target_config, runtime = _runtime_and_client(context, deployment.target)
    target_service = service_full_name(deployment.stack_name, service)
    proxy_name = f"h4k-proxy-{deployment.task_id}-{service}-{local_port}"
    command = [
        "tcp-listen",
        str(local_port),
        "fork,reuseaddr",
        f"tcp-connect:{target_service}:{target_port}",
    ]

    run_args = [
        *docker.client_config.docker_cmd,
        "run",
        "-d",
        "--rm",
        "--name",
        proxy_name,
        "--network",
        runtime.stack_network,
        "-p",
        f"{local_port}:{local_port}",
        "alpine/socat",
        *command,
    ]
    run(*[str(item) for item in run_args])
    rich.print(
        f"[green]Forwarding localhost:{local_port} to {target_service}:{target_port} on network '{runtime.stack_network}'.[/green]"
    )
