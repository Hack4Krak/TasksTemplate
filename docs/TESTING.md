# Testing

The toolbox has its own unit tests (`toolbox/tests/`) - this document covers **task tests**.

Task tests live in `tasks/<name>/tests/` and are run via `toolbox tests static` or `toolbox tests e2e`.

## Task test files

Each task can have:
- `tests/static.py` - static checks to verify task solutions in CI. No running service needed.
- `tests/static/*.py` - directory with multiple test files (useful for large test suites)
- `tests/e2e.py` - end-to-end checks against a deployed service.
- `tests/e2e/*.py` - directory with multiple test files

See `tasks/simple-task-example/tests/` for minimal example.

## Utilities (`toolbox/utils/test_utils.py`)

Source code: [`toolbox/utils/test_utils.py`](toolbox/utils/test_utils.py)

| Symbol                                   | Purpose                                                       |
|------------------------------------------|---------------------------------------------------------------|
| `RequestHelper`                          | HTTP client pre-configured with base URL and Host header      |
| `find_flag(text)`                        | Extract first `hack4KrakCTF{...}` match from text             |
| `find_all_flags(text)`                   | Extract all flag matches                                      |
| `validate_flag_hash(content, hash)`      | Compare flag content against SHA-256 hash                     |
| `load_flag_hash(task_path)`              | Read `flag_hash` from `config.yaml`                           |
| `check_status_code(response, expected)`  | Raise `AssertionError` on mismatch                            |
| `check_text_contains(response, text)`    | Raise if text absent (or present when `should_contain=False`) |
| `check_header_present(response, header)` | Raise if header missing or value wrong                        |
| `check_flag_in_response(response, hash)` | Find flag and optionally verify its hash                      |

`RequestHelper` reads `TASKS_DEPLOYMENT_URL` (default `http://localhost:8000`) and accepts a `default_host` for the `Host` header.

The timeout in `pyproject.toml` is a default (15s) - it can be overridden per-test with `@pytest.mark.timeout(seconds)`.

## Running

```bash
# All task static tests
toolbox tests static

# All task e2e tests (requires TASKS_DEPLOYMENT_URL pointing to your deployed service)
toolbox tests e2e [--push --pushgateway http://localhost:9091]

# Manually calling single task
pytest tasks/<name>/tests/e2e.py -v

# Manually calling from test directory
pytest tasks/<name>/tests/e2e/test_something.py -v
```
