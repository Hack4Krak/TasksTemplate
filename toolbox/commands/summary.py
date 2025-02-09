import random

import cowsay
import typer

from toolbox.utils.tasks import find_tasks


def summary(context: typer.Context):
    """
    Displays silly tasks summary
    """

    random_function = random.choice(list(cowsay.char_funcs.values()))
    tasks = list(find_tasks(context.obj["tasks_directory"]))
    random_function(f"Whoa! This repo has {len(tasks)} tasks waiting to be pushed to prod, brb fixing bugs!")
