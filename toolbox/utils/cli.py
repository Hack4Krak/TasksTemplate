import subprocess
from subprocess import CompletedProcess


def run(*args, capture_output: bool = True, cwd: str | None = None, env=None) -> CompletedProcess[str] | None:
    cmd: list[str] = []

    for arg in args:
        cmd.append(arg)

    try:
        result = subprocess.run(cmd, capture_output=capture_output, text=True, check=True, cwd=cwd, env=env)
        return result
    except subprocess.CalledProcessError as exception:
        print(f"Error running command: {exception}")
        print(f"Command: {cmd}")
        print(f"Stderr: {exception.stderr}")
        print(f"Stdout: {exception.stdout}")
        raise
