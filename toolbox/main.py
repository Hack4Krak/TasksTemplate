import importlib.metadata
from pathlib import Path
from typing import Annotated, Optional

import typer

from toolbox.commands import encrypt_flag, services, summary, verify

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
        tasks: Annotated[
            Optional[Path],
            typer.Option("--tasks", help="Path to tasks directory")
        ] = Path("tasks")
):
    ctx.obj = {"tasks_directory": tasks}
    return


app.command()(summary.summary)
app.command()(encrypt_flag.encrypt_flag)
app.add_typer(verify.app, name="verify", help="Verify configurations", no_args_is_help=True)
app.add_typer(services.app, name="services", help="Start and manage services", no_args_is_help=True)

if __name__ == "__main__":
    app()
