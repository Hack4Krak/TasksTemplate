import json
import os
import sys
from pathlib import Path
from subprocess import CompletedProcess

import requests

from toolbox.utils.cli import run


class Podman:
    def run_pod(self, *args, capture_output: bool = False) -> CompletedProcess[str] | None:
        podman_compose = PodmanCompose()
        if args:
            args = ["pod"] + list(args) + [podman_compose.pod]

        return self.run(*args, capture_output=capture_output)

    @staticmethod
    def run(*args, capture_output: bool = False) -> CompletedProcess[str] | None:
        return run("podman", *args, capture_output=capture_output)

    @staticmethod
    def get_data(command: str, args: list[str]):
        podman = Podman()
        try:
            stats_result = podman.run(command, *args, "--format", "json", capture_output=True)
            stats_data = json.loads(stats_result.stdout)
            return stats_data
        except Exception as exception:
            print(f"Failed to get stats: {exception}")
            return {}
        except json.JSONDecodeError as exception:
            print(f"Error decoding JSON: {exception}")
            return {}


class PodmanCompose:
    executable: list[str]
    pod: str

    def __init__(self, pod="hack4krak"):
        self.executable = self._detect_executable()
        self._verify_installed()
        self.pod = pod

    def up(self, file: str | Path | None = None, labels: dict[str, str] | None = None) -> None:
        args = ["--in-pod", self.pod, "--podman-run-args=--replace"]
        if file:
            args.append("-f")
            args.append(str(file))
        if labels:
            for label_name, label_value in labels.items():
                args.append(f"--podman-run-args=--label={label_name}={label_value}")
        args += ["up", "-d", "--build"]
        self.run(*args)

    def services(self, cwd: str) -> list[str]:
        args = ["config", "--services"]
        return self.run(*args, cwd=cwd).stdout.splitlines()

    def _verify_installed(self):
        result = self.run("--help")
        if result.returncode != 0:
            raise OSError("Invalid podman compose installation")

        # Temporary check for #3d47849 until the new version is released
        if "use a custom pod with" not in result.stdout:
            print("You are not using a prerelease version of podman-compose.")
            print("You can download latest version using toolbox services install")
            raise OSError("podman-compose prerelease required")

    def run(self, *args, cwd: str | None = None):
        if isinstance(self.executable, list):
            command = [*self.executable, *args]
        else:
            command = [self.executable, *args]

        env = os.environ.copy()
        env["UID"] = str(os.getuid())
        env["GID"] = str(os.getgid())

        return run(*command, cwd=cwd, env=env)

    @staticmethod
    def install():
        url = "https://raw.githubusercontent.com/containers/podman-compose/refs/heads/main/podman_compose.py"
        response = requests.get(url)

        os.makedirs("./bin", exist_ok=True)
        with open("./bin/podman_compose.py", "wb") as f:
            f.write(response.content)

    @staticmethod
    def _detect_executable() -> list[str]:
        local_exec = "./bin/podman_compose.py"
        if os.path.isfile(local_exec):
            full_path = os.path.abspath(local_exec)
            return [sys.executable, full_path]
        return ["podman-compose"]
