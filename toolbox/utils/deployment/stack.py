from pathlib import Path

from python_on_whales import DockerClient

MAIN_STACK_NAME = "hack4krak-main"
TASK_STACK_PREFIX = "hack4krak-task"


def task_stack_name(task_id: str) -> str:
    return f"{TASK_STACK_PREFIX}-{task_id}"


def service_full_name(stack_name: str, service_name: str) -> str:
    return f"{stack_name}_{service_name}"


def deploy_stack(docker: DockerClient, stack_name: str, compose_file: Path) -> None:
    docker.stack.deploy(stack_name, compose_files=[compose_file], prune=True)


def remove_stack(docker: DockerClient, stack_name: str) -> bool:
    existing = {stack.name for stack in docker.stack.list()}
    if stack_name not in existing:
        return False
    docker.stack.remove(stack_name)
    return True
