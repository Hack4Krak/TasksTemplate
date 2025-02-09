import importlib.metadata
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Annotated, Optional

import typer

import toolbox.commands.verify
import toolbox.commands.summary
from toolbox import commands

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
            Optional[bool], typer.Option("--version", callback=version_callback, is_eager=True,
                                         help="Shows app version")
        ] = None,
        tasks: Path = typer.Option("tasks/", "--tasks", help="Path to tasks directory")
):
    ctx.obj = {"tasks_directory": tasks}
    return


def common_options(
        ctx: typer.Context,
        tasks: Path = typer.Option(..., "--tasks", help="Path to tasks directory")
):
    ctx.obj = {"tasks_directory": tasks}


app.command()(commands.verify.verify)
app.command()(commands.summary.summary)

if __name__ == "__main__":
    app()
