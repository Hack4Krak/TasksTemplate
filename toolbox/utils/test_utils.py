import os
import re
from pathlib import Path

import requests
import yaml

FLAG_PATTERN = r"hack4KrakCTF\{[^}]+\}"


class RequestHelper:
    def __init__(
        self,
        base_url: str | None = None,
        default_timeout: float = 10.0,
        default_host: str | None = None,
    ):
        self.base_url = base_url or os.getenv("TASKS_DEPLOYMENT_URL", "http://localhost:8000")
        self.default_timeout = default_timeout
        self.default_host = default_host

    def _prepare(
        self, path: str, host: str | None, timeout: float | None, headers: dict[str, str] | None
    ) -> tuple[str, float, dict[str, str]]:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}" if path else self.base_url
        resolved_headers = dict(headers or {})
        if effective_host := host or self.default_host:
            resolved_headers["Host"] = effective_host
        return url, timeout if timeout is not None else self.default_timeout, resolved_headers

    def get(
        self,
        path: str = "",
        host: str | None = None,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> requests.Response:
        url, timeout, headers = self._prepare(path, host, timeout, headers)
        return requests.get(url, headers=headers, timeout=timeout, **kwargs)

    def post(
        self,
        path: str = "",
        host: str | None = None,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> requests.Response:
        url, timeout, headers = self._prepare(path, host, timeout, headers)
        return requests.post(url, headers=headers, timeout=timeout, **kwargs)


def find_flag(text: str, pattern: str | None = None) -> str | None:
    m = re.search(pattern or FLAG_PATTERN, text)
    return m.group(0) if m else None


def find_all_flags(text: str, pattern: str | None = None) -> list[str]:
    return re.findall(pattern or FLAG_PATTERN, text)


def validate_flag_hash(flag_content: str, expected_hash: str) -> bool:
    from toolbox.utils.hash import hash_flag

    return hash_flag(flag_content) == expected_hash


def load_flag_hash(task_path: Path) -> str | None:
    config_file = task_path / "config.yaml"
    if not config_file.exists():
        return None
    return yaml.safe_load(config_file.read_text()).get("flag_hash")


def check_status_code(response: requests.Response, expected: int = 200) -> None:
    if response.status_code != expected:
        raise AssertionError(f"Expected status {expected}, got {response.status_code}")


def check_text_contains(response: requests.Response, text: str, should_contain: bool = True) -> None:
    contains = text in response.text
    if should_contain and not contains:
        raise AssertionError(f"Response does not contain '{text}'")
    if not should_contain and contains:
        raise AssertionError(f"Response unexpectedly contains '{text}'")


def check_header_present(response: requests.Response, header: str, expected_value: str | None = None) -> None:
    if header not in response.headers:
        raise AssertionError(f"Header '{header}' not found")
    if expected_value is not None and (actual := response.headers[header]) != expected_value:
        raise AssertionError(f"Header '{header}': expected '{expected_value}', got '{actual}'")


def check_flag_in_response(
    response: requests.Response, expected_hash: str | None = None, pattern: str | None = None
) -> None:
    flag = find_flag(response.text, pattern)
    if not flag:
        raise AssertionError("No flag found in response")
    if expected_hash:
        m = re.match(r"hack4KrakCTF\{([^}]+)\}", flag)
        if not m:
            raise AssertionError(f"Flag has invalid format: {flag}")
        if not validate_flag_hash(m.group(1), expected_hash):
            raise AssertionError(f"Flag hash doesn't match: {flag}")
