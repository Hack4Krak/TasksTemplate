from pathlib import Path

import yaml

from toolbox.utils.hash import hash_flag

EXPECTED_FLAG = "simple_example_flag"
EXPECTED_FLAG_HASH = hash_flag(EXPECTED_FLAG)

task_path = Path(__file__).parent.parent
config_file = task_path / "config.yaml"


def test_flag_hash_matches_expected():
    config = yaml.safe_load(config_file.read_text())
    assert config["flag_hash"] == EXPECTED_FLAG_HASH, (
        f"flag_hash in config.yaml does not match hash of '{EXPECTED_FLAG}'"
    )
