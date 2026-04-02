import contextlib
import io
import sys
from pathlib import Path

import pytest
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from toolbox.utils.tasks import find_tasks

console = Console()
JOB_NAME = "tasks_tests"


class _ResultCollector:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures: list[str] = []

    def pytest_runtest_logreport(self, report):
        if report.when != "call":
            return
        if report.passed:
            self.passed += 1
        elif report.failed:
            self.failed += 1
            self.failures.append(str(report.longrepr))


def run_tests(
    tasks_directory: Path, test_type: str = "e2e", push: bool = False, pushgateway: str = "http://localhost:9091"
):
    tasks = list(find_tasks(tasks_directory))
    registry = CollectorRegistry()
    test_result_gauge = Gauge("test_result", "Result of each test file", ["task", "file"], registry=registry)

    console.print(f"\n[bold]Running [cyan]{test_type}[/cyan] tests...[/bold]\n")

    task_failures: list[tuple[str, list[str]]] = []
    passed_tasks = 0
    total_tasks = 0

    for task in tasks:
        test_file = task / "tests" / f"{test_type}.py"
        test_directory = task / "tests" / test_type

        if test_file.exists():
            test_files = [test_file]
        elif test_directory.is_dir():
            test_files = sorted(test_directory.glob("*.py"))
            test_files = [f for f in test_files if f.name != "__init__.py"]
        else:
            continue

        if not test_files:
            continue

        task_passed = 0
        task_failed = 0
        all_failures: list[str] = []
        file_results: list[tuple[str, int, int]] = []

        for test_path in test_files:
            collector = _ResultCollector()
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                pytest.main([str(test_path), "--tb=short", "--no-header"], plugins=[collector])

            task_passed += collector.passed
            task_failed += collector.failed
            all_failures.extend(collector.failures)

            exit_code = 0 if collector.failed == 0 else 1
            file_results.append((test_path.stem, collector.passed, collector.passed + collector.failed))
            test_result_gauge.labels(task=task.name, file=f"{test_type}/{test_path.name}").set(exit_code)

        total_tasks += 1
        total = task_passed + task_failed
        count_str = f"[dim]{task_passed}/{total}[/dim]"

        if task_failed == 0:
            passed_tasks += 1
            console.print(f"  [green]✓[/green] {task.name} {count_str}")
        else:
            console.print(f"  [red]✗[/red] {task.name} {count_str}")
            if all_failures:
                task_failures.append((task.name, all_failures))

        if len(test_files) > 1:
            for name, passed, sub_total in file_results:
                sub_str = f"[dim]{passed}/{sub_total}[/dim]"
                if passed == sub_total:
                    console.print(f"    [green]✓[/green] {name} {sub_str}")
                else:
                    console.print(f"    [red]✗[/red] {name} {sub_str}")

    if task_failures:
        console.print()
        for task_name, failures in task_failures:
            console.print(
                Panel("\n\n".join(failures), title=f"[red]{task_name}[/red]", border_style="red", expand=False)
            )

    _print_summary(total_tasks, passed_tasks)

    if push:
        push_to_gateway(pushgateway, job=JOB_NAME, registry=registry)

    if passed_tasks < total_tasks:
        sys.exit(1)


def _print_summary(total: int, passed: int) -> None:
    failed = total - passed

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(justify="right")
    table.add_column(justify="left")

    table.add_row("[bold]Total[/bold]", str(total))
    table.add_row("[bold green]Passed[/bold green]", f"[green]{passed}[/green]")
    if failed:
        table.add_row("[bold red]Failed[/bold red]", f"[red]{failed}[/red]")

    if not failed:
        status = Text("All tests passed", style="green")
    else:
        status = Text(f"{failed} task(s) failed", style="red bold")
    border = "green" if not failed else "red"
    console.print()
    console.print(Panel(table, title="[bold]Test Summary[/bold]", subtitle=status, border_style=border, expand=False))
