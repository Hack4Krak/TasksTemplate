from pathlib import Path
from unittest.mock import Mock

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestFlagUtils:
    def test_find_flag(self):
        from toolbox.utils.test_utils import find_flag

        assert find_flag("prefix hack4KrakCTF{test_flag_123} suffix") == "hack4KrakCTF{test_flag_123}"

    def test_find_flag_not_present(self):
        from toolbox.utils.test_utils import find_flag

        assert find_flag("no flags here") is None

    def test_find_all_flags(self):
        from toolbox.utils.test_utils import find_all_flags

        flags = find_all_flags("hack4KrakCTF{flag1} and hack4KrakCTF{flag2}")
        assert flags == ["hack4KrakCTF{flag1}", "hack4KrakCTF{flag2}"]

    def test_custom_pattern(self):
        from toolbox.utils.test_utils import find_flag

        assert find_flag("FLAG{custom_format}", pattern=r"FLAG\{[^}]+\}") == "FLAG{custom_format}"

    def test_validate_flag_hash(self):
        from toolbox.utils.hash import hash_flag
        from toolbox.utils.test_utils import validate_flag_hash

        content = "test_flag_123"
        assert validate_flag_hash(content, hash_flag(content))


class TestRequestHelper:
    def test_initialization(self):
        from toolbox.utils.test_utils import RequestHelper

        helper = RequestHelper(base_url="http://example.com", default_timeout=5.0)
        assert helper.base_url == "http://example.com"
        assert helper.default_timeout == 5.0

    def test_env_var(self, monkeypatch):
        from toolbox.utils.test_utils import RequestHelper

        monkeypatch.setenv("TASKS_DEPLOYMENT_URL", "http://custom.url")
        assert RequestHelper().base_url == "http://custom.url"


class TestHelperFunctions:
    def test_check_status_code_success(self):
        from toolbox.utils.test_utils import check_status_code

        response = Mock(status_code=200)
        check_status_code(response, 200)  # must not raise

    def test_check_status_code_failure(self):
        from toolbox.utils.test_utils import check_status_code

        response = Mock(status_code=404)
        with pytest.raises(AssertionError, match="404"):
            check_status_code(response, 200)

    def test_check_text_contains(self):
        from toolbox.utils.test_utils import check_text_contains

        response = Mock(text="Hello World")
        check_text_contains(response, "World")

        with pytest.raises(AssertionError):
            check_text_contains(response, "Goodbye")

    def test_check_text_not_contains(self):
        from toolbox.utils.test_utils import check_text_contains

        response = Mock(text="Hello World")
        check_text_contains(response, "Goodbye", should_contain=False)

        with pytest.raises(AssertionError):
            check_text_contains(response, "World", should_contain=False)

    def test_check_header_present(self):
        from toolbox.utils.test_utils import check_header_present

        response = Mock(headers={"Content-Type": "text/html"})
        check_header_present(response, "Content-Type")
        check_header_present(response, "Content-Type", "text/html")

        with pytest.raises(AssertionError, match="application/json"):
            check_header_present(response, "Content-Type", "application/json")

    def test_check_header_missing(self):
        from toolbox.utils.test_utils import check_header_present

        with pytest.raises(AssertionError, match="Content-Type"):
            check_header_present(Mock(headers={}), "Content-Type")
