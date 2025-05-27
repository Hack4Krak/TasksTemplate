import importlib.metadata
from pathlib import Path
from typing import Annotated

import typer

from toolbox.commands import hash_flag, services, summary, tests, verify

app = typer.Typer(name="Hack4Krak Toolbox", help="CLI for managing tasks for Hack4Krak CTF", no_args_is_help=True)


def version_callback(is_version_parameter_set: bool):
    if is_version_parameter_set:
        version = importlib.metadata.metadata("hack4krak-toolbox")["Version"]
        print(f"Hack4Krak Toolbox v{version}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    _version: Annotated[
        bool | None, typer.Option("--version", callback=version_callback, is_eager=True, help="Shows app version")
    ] = None,
    tasks: Annotated[Path | None, typer.Option("--tasks", help="Path to tasks directory")] = Path("tasks"),
    config: Annotated[Path | None, typer.Option("--config", help="Path to configuration directory")] = Path("config"),
):
    ctx.obj = {
        "tasks_directory": tasks,
        "config_directory": config,
    }
    return


app.command()(summary.summary)
app.command()(hash_flag.hash_flag)
app.add_typer(verify.app, name="verify", help="Verify configurations", no_args_is_help=True)
app.add_typer(services.app, name="services", help="Start and manage services", no_args_is_help=True)
app.add_typer(tests.app, name="tests", help="Run tests for services", no_args_is_help=True)

if __name__ == "__main__":
    app()
