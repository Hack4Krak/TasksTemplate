import importlib.metadata
import os
from collections import defaultdict
from typing import Annotated, Optional

import typer

app = typer.Typer(name="Hack4Krak Toolbox", help="CLI for managing tasks for Hack4Krak CTF", no_args_is_help=True)

def version_callback(is_version_parameter_set: bool):
    if is_version_parameter_set:
        version = importlib.metadata.metadata("hack4krak-toolbox")["Version"]
        print(f"Hack4Krak Toolbox v{version}")
        raise typer.Exit()


@app.callback()
def main(
    _version: Annotated[
        Optional[bool], typer.Option("--version", callback=version_callback, is_eager=True, help="Shows app version")
    ] = None,
):
    return


if __name__ == "__main__":
    app()
