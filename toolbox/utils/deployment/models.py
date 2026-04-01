from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ComposeServiceSpec:
    name: str
    replicas: int | None


@dataclass(frozen=True)
class TaskDeployment:
    task_id: str
    target: str
    stack_name: str
    compose_file: Path


@dataclass(frozen=True)
class StackStatus:
    state: str
    details: str
    cpu: str = "-"
    memory: str = "-"
    network_rx: str = "-"
    network_tx: str = "-"
