import json
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml
from click.exceptions import Exit

from toolbox.commands.verify import verify


@pytest.fixture
def mock_context():
    context = MagicMock()
    context.obj = {"tasks_directory": Path("mocked/tasks_directory")}
    return context


@pytest.fixture
def valid_schema():
    return {
        "type": "object",
        "properties": {
            "task_name": {"type": "string"},
            "enabled": {"type": "boolean"}
        },
        "required": ["task_name", "enabled"]
    }


@pytest.fixture
def valid_task_config():
    return {
        "task_name": "Task 1",
        "enabled": True
    }


@pytest.fixture
def invalid_task_config():
    return {
        "task_name": "Task 1"
    }


@patch.object(Path, "iterdir")
@patch.object(Path, "is_dir")
@patch.object(Path, "is_file")
@patch.object(Path, "read_text", new_callable=mock_open)
def test_verify_valid(mock_open_func, mock_isfile, mock_isdir, mock_listdir, mock_context, valid_schema, valid_task_config):
    mock_listdir.return_value = [Path("valid_task")]
    mock_isdir.return_value = True
    mock_isfile.return_value = True
    mock_open_func.side_effect = [
        json.dumps(valid_schema),
        yaml.dump(valid_task_config)
    ]

    verify(mock_context)

    mock_open_func.assert_called()


@patch.object(Path, "iterdir")
@patch.object(Path, "is_dir")
@patch.object(Path, "is_file")
@patch.object(Path, "read_text", new_callable=mock_open)
def test_verify_invalid(mock_open_func, mock_isfile, mock_isdir, mock_listdir, mock_context, valid_schema, invalid_task_config):
    mock_listdir.return_value = [Path("invalid_task")]
    mock_isdir.return_value = True
    mock_isfile.return_value = True
    mock_open_func.side_effect = [
        json.dumps(valid_schema),
        yaml.dump(invalid_task_config)
    ]

    with pytest.raises(Exit):
        verify(mock_context)
