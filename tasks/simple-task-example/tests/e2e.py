from pathlib import Path

import pytest

from toolbox.utils.test_utils import RequestHelper, check_status_code, load_flag_hash

task_path = Path(__file__).parent.parent
request = RequestHelper(default_host="whoami.docker.localhost")


def test_main_page_loads():
    response = request.get()
    check_status_code(response, 200)
