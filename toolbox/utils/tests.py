import subprocess
from pathlib import Path

import typer
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

from toolbox.utils.tasks import find_tasks

app = typer.Typer()

JOB_NAME = "tasks_tests"


def run_tests(tasks_directory: Path, push: bool = False, pushgateway: str = "http://localhost:9091"):
    tasks = list(find_tasks(tasks_directory))
    registry = CollectorRegistry()
    test_result_gauge = Gauge("test_result", "Result of each test file", ["task", "file"], registry=registry)

    for task in tasks:
        tests_directory = task / "tests"
        if tests_directory.exists() and tests_directory.is_dir():
            for test_file in tests_directory.iterdir():
                if test_file.is_file() and test_file.suffix == ".py":
                    result = subprocess.run(["python", str(test_file)], capture_output=True)
                    exit_code = result.returncode
                    print(f"{test_file.name}: {'PASS' if exit_code == 0 else 'FAIL'}")
                    test_result_gauge.labels(task=task.name, file=test_file.name).set(exit_code)

    if push:
        push_to_gateway(pushgateway, job=JOB_NAME, registry=registry)
