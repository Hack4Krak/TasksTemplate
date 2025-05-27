from typing import Annotated

import typer

from toolbox.utils.tests import run_tests

app = typer.Typer()

JOB_NAME = "tasks_tests"


@app.command("run")
def run_only(context: typer.Context):
    """
    Run tests but do NOT push metrics.
    """
    run_tests(context.obj["tasks_directory"], push=False)


@app.command("run-and-push")
def run_and_push(
    context: typer.Context,
    pushgateway: Annotated[str, typer.Option(help="Prometheus Pushgateway URL")] = "http://localhost:9091",
):
    """
    Run tests and PUSH metrics to Prometheus Pushgateway.
    """
    run_tests(context.obj["tasks_directory"], push=True, pushgateway=pushgateway)
