import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from click.exceptions import Exit

from toolbox.commands.verify import verify, verify_assets


@pytest.fixture
def mock_context():
    context = MagicMock()
    context.obj = {"tasks_directory": Path("mocked/tasks_directory")}
    return context


@pytest.fixture
def valid_schema():
    return {
        "type": "object",
        "properties": {"task_name": {"type": "string"}, "enabled": {"type": "boolean"}},
        "required": ["task_name", "enabled"],
    }


@pytest.fixture
def valid_task_config():
    return {"task_name": "Task 1", "enabled": True}


@pytest.fixture
def invalid_task_config():
    return {"task_name": "Task 1"}


@pytest.fixture
def valid_assets():
    return {
        "assets": [
            {
                "description": "dziengiel",
                "path": "asset1.txt",
            },
            {
                "description": "dziengiel",
                "path": "asset2.txt",
            },
        ]
    }


@patch.object(Path, "iterdir")
@patch.object(Path, "is_dir")
@patch.object(Path, "is_file")
@patch.object(Path, "read_text")
@patch("toolbox.commands.verify.verify_assets")
def test_verify_valid(
    mock_verify_assets,
    mock_read_text,
    mock_is_file,
    mock_is_dir,
    mock_iterdir,
    mock_context,
    valid_schema,
    valid_task_config,
):
    mock_verify_assets.return_value = True
    mock_iterdir.return_value = [Path("valid_task")]
    mock_is_dir.return_value = True
    mock_is_file.return_value = True
    mock_read_text.side_effect = [json.dumps(valid_schema), yaml.dump(valid_task_config)]

    verify(mock_context)

    mock_read_text.assert_called()


@patch.object(Path, "iterdir")
@patch.object(Path, "is_dir")
@patch.object(Path, "is_file")
@patch.object(Path, "read_text")
def test_verify_invalid(
    mock_read_text, mock_is_file, mock_is_dir, mock_iterdir, mock_context, valid_schema, invalid_task_config
):
    mock_iterdir.return_value = [Path("invalid_task")]
    mock_is_dir.return_value = True
    mock_is_file.return_value = True
    mock_read_text.side_effect = [json.dumps(valid_schema), yaml.dump(invalid_task_config)]

    with pytest.raises(Exit):
        verify(mock_context)


@patch.object(Path, "iterdir")
@patch.object(Path, "is_file")
@patch.object(Path, "is_dir")
def test_verify_assets_valid(mock_is_dir, mock_is_file, mock_iterdir, valid_assets):
    mock_iterdir.return_value = [Path("asset1.txt"), Path("asset2.txt")]
    mock_is_file.return_value = True
    mock_is_dir.return_value = True

    assert verify_assets(valid_assets, Path("assets"), Path("subdir_path")) is True


@patch.object(Path, "iterdir")
@patch.object(Path, "is_dir")
def test_verify_assets_missing_asset(mock_isdir, mock_iterdir, valid_assets):
    mock_iterdir.return_value = [Path("asset1.txt")]
    mock_isdir.return_value = True

    assert verify_assets(valid_assets, Path("assets"), Path("subdir_path")) is False


@patch.object(Path, "iterdir")
@patch.object(Path, "is_dir")
@patch.object(Path, "is_file")
def test_verify_assets_unregistered_asset(mock_is_file, mock_is_dir, mock_iterdir, valid_assets):
    mock_iterdir.return_value = [Path("asset1.txt"), Path("asset2.txt"), Path("asset3.txt")]
    mock_is_file.return_value = True
    mock_is_dir.return_value = True

    assert verify_assets(valid_assets, Path("assets"), Path("subdir_path")) is False
