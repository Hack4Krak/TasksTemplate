import random

import cowsay
import typer

from toolbox.utils.config import EventConfig
from toolbox.utils.tasks import find_tasks


def summary(context: typer.Context):
    """
    Displays silly tasks summary
    """

    random_function = random.choice(list(cowsay.char_funcs.values()))
    tasks = list(find_tasks(context.obj["tasks_directory"]))
    event_config = EventConfig.from_file(context.obj["config_directory"])

    random_function(f"""
        Whoa! This repo has {len(tasks)} tasks definitions!
        The event will start at {event_config.start_date} and end at {event_config.end_date}. Have fun!
    """)
