import subprocess
from subprocess import CompletedProcess


def run(*args, capture_output: bool = True, cwd: str | None = None) -> CompletedProcess[str] | None:
    cmd: list[str] = []

    for arg in args:
        cmd.append(arg)

    try:
        result = subprocess.run(cmd, capture_output=capture_output, text=True, check=True, cwd=cwd)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print(f"Command: {cmd}")
        print(f"Stderr: {e.stderr}")
        raise
