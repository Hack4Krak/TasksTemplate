import typer
from python_on_whales import DockerClient

from toolbox.utils.tasks import find_tasks


def get_docker_client(context: typer.Context) -> DockerClient:
    files = [context.obj["main_compose"]]

    for task in find_tasks(context.obj["tasks_directory"]):
        docker_compose_file = task / "docker-compose.yaml"
        if docker_compose_file.is_file():
            files.append(str(docker_compose_file))

    return DockerClient(compose_files=files)
