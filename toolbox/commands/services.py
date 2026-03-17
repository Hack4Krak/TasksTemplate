import typer

from toolbox.commands import deploy

app = typer.Typer(help="Compatibility aliases for deployment commands", no_args_is_help=True)


@app.command("status")
def status(context: typer.Context, target: str | None = None):
    deploy.status_tasks(context, target=target)


@app.command("deploy")
def deploy_alias(
    context: typer.Context,
    build: bool = True,
    target: str | None = None,
    tasks: list[str] | None = None,
    main: bool = True,
):
    deploy.stack_deploy(context, build=build, target=target, tasks=tasks, include_main=main)


@app.command("stop")
def stop(context: typer.Context, task: str, service: str | None = None):
    if service:
        deploy.service_stop(context, task=task, service=service)
        return
    deploy.stack_stop(context, task=task)


@app.command("restart")
def restart(context: typer.Context, task: str, service: str | None = None):
    if service:
        deploy.service_restart(context, task=task, service=service)
        return
    deploy.stack_restart(context, task=task)
