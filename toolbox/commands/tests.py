from typing import Annotated

import typer

from toolbox.utils.tests import run_tests

app = typer.Typer()


@app.command("static")
def static(context: typer.Context):
    """Run static tests (tests/static.py)."""
    run_tests(context.obj["tasks_directory"], test_type="static", push=False)


@app.command("e2e")
def e2e(
    context: typer.Context,
    push: Annotated[bool, typer.Option(help="Push metrics to Prometheus Pushgateway")] = False,
    pushgateway: Annotated[str, typer.Option(help="Prometheus Pushgateway URL")] = "http://localhost:9091",
):
    """Run E2E tests (tests/e2e.py)."""
    run_tests(context.obj["tasks_directory"], test_type="e2e", push=push, pushgateway=pushgateway)
