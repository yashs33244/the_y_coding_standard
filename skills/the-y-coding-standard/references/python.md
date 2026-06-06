# Python Standards

Yash's opinions. No diplomacy. If you disagree, fork the skill.

## Python Version

Always the LATEST stable Python at scaffolding time. Right now that is **Python 3.14** (3.14.5 shipped May 2026). Before you scaffold, verify with WebSearch. Query examples:

- "latest stable Python release"
- "Python current LTS version"
- "Python end of life schedule"

Reference for live status: https://devguide.python.org/versions/

Pin in three places, every project:

1. `.python-version` -> `3.14`
2. `pyproject.toml` -> `requires-python = ">=3.14"`
3. `README.md` under "Requirements" -> exact minor version expected.

Drop EOL Python versions the day they hit EOL. No "we still support 3.9 because one customer asked". Cut it.

## Package Manager

Pick one. Stick to it. Never mix.

**Default: `uv`.** It is 10-100x faster than pip+venv, written in Rust, ships its own resolver. Lockfile is `uv.lock`.

```bash
uv init                # new project
uv add fastapi         # add runtime dep
uv add --dev pytest    # add dev dep
uv sync                # install from lock
uv run python -m app   # run inside the env
uv lock --upgrade      # bump locks
```

**Fallback: `poetry`.** Use only when the project already ships `poetry.lock` or depends on a poetry-specific plugin. Lockfile is `poetry.lock`.

```bash
poetry init
poetry add fastapi
poetry install
poetry run python -m app
```

**Banned for new projects:**

- Mixing `uv` and `poetry` in one repo. Pick one.
- Raw `pip install -r requirements.txt`. Legacy only. New projects always have a lockfile.
- `pipenv`. Dead. Move on.
- `conda install <pypi-package>`. Use conda for Python itself, not for PyPI installs.

## Environment Management

Conda owns the Python interpreter and the OS-level env. `uv` (or poetry) owns the PyPI dependency graph inside that env.

Convention: **env name == repo slug**. If the repo is `the-y-coding-standard`, the env is `the-y-coding-standard`. No clever names.

Document the env name in the README under "Setup". Copy-paste runnable.

```
## Setup
conda create -n the-y-coding-standard python=3.14
conda activate the-y-coding-standard
uv sync
```

Secrets:

- `.env` files for local secrets. Never commit. `.gitignore` it.
- `.env.example` checked in with placeholder values for every key the app reads.
- Settings loaded via `pydantic-settings.BaseSettings` in `config.py`. No `os.environ.get` scattered through the codebase.

## Style Baseline

- PEP 8 strict. Non-negotiable.
- `ruff` for lint AND format. One tool. Replaces `black`, `isort`, `flake8`, `pyupgrade`, `pydocstyle`. Configure in `pyproject.toml`.
- Line length: 88. Ruff default. Do not bikeshed.
- Type hints everywhere. No untyped public function. Private helpers may skip annotations only if the return type is obvious from a one-line body.
- `from __future__ import annotations` at the top of every module that uses forward references on Python below 3.12. On 3.12+ it is optional but harmless.
- `mypy --strict src/` in CI. Failing means the PR does not merge.

## Naming

| Thing | Convention | Example |
|---|---|---|
| Variables, functions | snake_case | `get_user_by_email` |
| Classes | PascalCase | `UserService` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_CONNECTIONS` |
| Private | prefix `_` | `_session_token` |
| Module-private | prefix `__` | rarely |
| Modules | snake_case | `user_service.py` |
| Packages | snake_case, short | `users/`, `auth/` |
| Type aliases | PascalCase | `UserId = NewType("UserId", UUID)` |
| Enums | PascalCase class, SCREAMING values | `class Role(Enum): ADMIN = "admin"` |

No `l`, `I`, `O` as single-letter names. No Hungarian notation. No `str_user_name`.

## File Modularity Rules

Yash's non-negotiables. Each of these gets **its own file**. Always.

- `enums.py` -> every `Enum` class for that package
- `constants.py` -> module-level constants (`MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- `types.py` -> `TypedDict`, `NewType`, `Protocol`, type aliases
- `exceptions.py` -> the custom exception hierarchy for that domain
- `config.py` -> `pydantic-settings.BaseSettings`
- `schemas.py` -> Pydantic models for I/O validation
- `models.py` -> ORM models OR domain dataclasses (never both in the same file)
- `service.py` -> business logic
- `repository.py` -> data access

**Never mix** enums, constants, types, exceptions, and business logic in one "utils.py" dumping ground. If you find a `utils.py` longer than 100 lines, split it.

File length: **300 lines soft cap, 400 hard cap.** If a file goes past 400, split by responsibility, not by "the first half and the second half".

## Project Structure

General `src/` layout. Every feature is a self-contained package with its own enums/constants/types.

```
project-root/
  pyproject.toml
  uv.lock
  .python-version
  .env.example
  README.md
  src/
    my_package/
      __init__.py
      main.py
      config.py
      enums.py
      constants.py
      types.py
      exceptions.py
      features/
        users/
          __init__.py
          service.py
          repository.py
          schemas.py
          models.py
          enums.py
          constants.py
          types.py
          exceptions.py
        billing/
          __init__.py
          service.py
          repository.py
          schemas.py
          models.py
          enums.py
          constants.py
          types.py
          exceptions.py
      shared/
        logger.py
        utils.py
  tests/
    unit/
    integration/
    e2e/
    conftest.py
```

Each feature folder is a vertical slice. You can delete `features/billing/` and the rest of the app still compiles.

## FastAPI Layout

```
app/
  __init__.py
  main.py                  # FastAPI factory, middleware, lifespan
  config.py                # pydantic-settings
  dependencies.py          # shared Depends (db session, current user)
  enums.py
  constants.py
  types.py
  exceptions.py
  middleware/
    __init__.py
    auth.py
    logging.py
    rate_limit.py
  features/
    users/
      __init__.py
      router.py            # APIRouter, thin
      service.py           # business logic
      repository.py        # DB access
      schemas.py           # Pydantic I/O
      models.py            # ORM
      enums.py
      constants.py
      exceptions.py
  shared/
    utils.py
    logger.py
tests/
  unit/
  integration/
  conftest.py
```

**Router rule: routers are THIN.** No SQL. No business logic. No transactions. Three jobs only: parse input, call service, return response.

```python
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await service.get_by_id(user_id)
```

If the router function body exceeds 5 lines, you are doing it wrong. Push it into the service.

`main.py` does four things: build the FastAPI app, register middleware, register exception handlers, wire the lifespan. Nothing else.

## Django Layout

```
project/
  manage.py
  config/
    __init__.py
    settings/
      base.py
      development.py
      production.py
      test.py
    urls.py
    wsgi.py
    asgi.py
  apps/
    users/
      __init__.py
      apps.py
      models.py
      views.py
      services.py
      serializers.py
      urls.py
      enums.py
      constants.py
      exceptions.py
      admin.py
    billing/
      ...
```

Views stay thin. Logic lives in `services.py`. Serializers do validation only. Same split rule as FastAPI.

## Pydantic Usage

Pydantic is a validation library. It is not a domain model framework. Use it at boundaries, drop to dataclasses inside.

**Pydantic IS for:**

- HTTP request/response validation (FastAPI `body`, `query`, `response_model`).
- Settings via `pydantic-settings.BaseSettings`.
- External API response parsing. Validate before you trust.
- Inter-service contracts (queue payloads, RPC schemas).

**Pydantic IS NOT for:**

- Internal domain models. Use `@dataclass(frozen=True, slots=True)`. Faster, no validation overhead, no surprise coercions.
- ORM models. Use SQLAlchemy ORM or SQLModel.
- Internal helper function arguments. Use `TypedDict` or a dataclass.

**Rule: validate at the boundary, plain dataclasses inside.**

```python
# schemas.py - boundary
from pydantic import BaseModel, EmailStr, Field, SecretStr

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: SecretStr = Field(min_length=12)

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    created_at: datetime
```

```python
# models.py - internal
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    email: str
    created_at: datetime
```

Service takes the Pydantic request, converts to the internal dataclass, does work, returns an internal dataclass, router converts back to a response schema. Boundaries are obvious.

## Error Handling

Skip this section and your app will leak stack traces, eat exceptions silently, and 500 in production with no breadcrumbs. Read it twice.

**Rules:**

1. Define a custom exception hierarchy in `exceptions.py`. Root: `AppError`. Subclasses per domain.
2. Never `except Exception:` without re-raising or logging the full traceback.
3. Never bare `except:`. It catches `SystemExit` and `KeyboardInterrupt`. You will hate yourself.
4. Every external call (HTTP, DB, filesystem, subprocess, LLM) gets explicit error handling. No "we will deal with it later".
5. FastAPI: register exception handlers in `main.py` that map `AppError` subclasses to HTTP responses. No `HTTPException` raised from inside services.
6. Pick one error style per module: `result` pattern (return value) or exception pattern (raise). Never both.
7. Log with `logger.exception()` inside the `except` block. It includes the full traceback automatically.

**Hierarchy:**

```python
# exceptions.py
class AppError(Exception):
    """Base for all app errors."""

class NotFoundError(AppError):
    """Entity not found."""

class ValidationError(AppError):
    """Domain validation failed."""

class ConflictError(AppError):
    """State conflict, e.g. duplicate."""

class ExternalServiceError(AppError):
    """Upstream dependency failed."""
```

**FastAPI handler:**

```python
# main.py
@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})

@app.exception_handler(ExternalServiceError)
async def external_handler(request: Request, exc: ExternalServiceError) -> JSONResponse:
    logger.exception("external service failure", exc_info=exc)
    return JSONResponse(status_code=502, content={"detail": "upstream failure"})
```

**Inside the service:**

```python
async def get_by_id(self, user_id: UUID) -> User:
    user = await self.repo.find(user_id)
    if user is None:
        raise NotFoundError(f"user {user_id} not found")
    return user
```

Routers never `try/except`. The service raises, the global handler maps to HTTP. Clean.

## Python Pitfalls

The 20 mistakes that produce 80% of Python production fires. Memorise.

1. **Mutable default arguments.** `def f(x=[]):` shares the list across all calls. Fix: default to `None`, allocate inside.
   ```python
   def f(x: list[int] | None = None) -> None:
       if x is None:
           x = []
   ```
2. **Late-binding closures in loops.** `[lambda: i for i in range(3)]` all return 2. Fix: bind via default arg.
   ```python
   fs = [lambda i=i: i for i in range(3)]
   ```
3. **`is` vs `==`.** `is` checks identity. Never `if x is "foo"`. Use `==` for value equality, `is` only for `None`, `True`, `False`.
4. **`assert` for input validation.** Asserts get stripped with `python -O`. Use real exceptions.
5. **Floating point equality.** `0.1 + 0.2 != 0.3`. Use `math.isclose()` for floats, `decimal.Decimal` for money.
6. **Shared global state.** Module-level mutable singletons break tests and parallelism. Inject dependencies.
7. **`pickle` on untrusted input.** Arbitrary code execution. Use `json` or `msgpack`. Pickle is for trusted local caches only.
8. **`eval` / `exec` on user input.** Code injection. There is no safe sandbox in stdlib. Do not try.
9. **`subprocess(..., shell=True)` with user input.** Command injection. Use list-form args and `shell=False`.
   ```python
   subprocess.run(["git", "log", "--oneline"], check=True)
   ```
10. **SQL string interpolation.** SQL injection. Use parameterised queries. SQLAlchemy or `cursor.execute("... WHERE id = %s", (id,))`.
11. **`yaml.load` instead of `yaml.safe_load`.** Default loader can construct arbitrary Python objects. Always `safe_load`.
12. **`requests.get(url, verify=False)`.** Disables TLS verification. MITM-friendly. Never in production.
13. **Path traversal.** `os.path.join(base, user_input)` does not sandbox. Resolve and check.
    ```python
    target = (pathlib.Path(base) / user_input).resolve()
    if not target.is_relative_to(pathlib.Path(base).resolve()):
        raise ValidationError("path escape")
    ```
14. **Catching `Exception` to make tests pass.** You are hiding bugs. Catch specific types or fix the call site.
15. **Logging secrets.** Filter env vars, auth headers, request bodies before logging. Use a redaction filter.
16. **`datetime.utcnow()` returns naive datetime.** Always use `datetime.now(timezone.utc)`. Naive UTC bites you on serialisation.
17. **`requirements.txt` without pinned versions.** Reproducibility broken. Use `uv.lock` or `poetry.lock`. Commit the lock.
18. **Long-lived `requests.Session` never closed.** File-descriptor leak. Use a context manager or switch to `httpx.AsyncClient`.
19. **Missing `__init__.py`.** Namespace package surprises in tooling. Add the file even if empty.
20. **`time.sleep` in async code.** Blocks the entire event loop. Use `await asyncio.sleep`. Same for blocking IO inside async handlers, wrap in `asyncio.to_thread`.

## Testing

- `pytest` always. Never `unittest` for new code.
- Layout: `tests/unit/`, `tests/integration/`, `tests/e2e/`.
- `conftest.py` at each level for shared fixtures.
- Coverage target: **90% lines on business logic, 100% on critical paths** (auth, billing, anything that touches money or PII).
- `pytest-asyncio` for async code. `pytest-mock` for mocks. `pytest-cov` for coverage.
- HTTP mocking: use `respx` or `httpx.MockTransport`. Never `mock.patch('requests.get')`. Patching the network layer is a recipe for false positives.
- Fixtures over `setUp`. Parametrise over copy-paste.
- One assert per test when practical. Multiple asserts allowed when they describe one behaviour.
- Test names are sentences: `def test_get_user_raises_not_found_when_missing()`.

## CI/CD Minimums

Every Python project, every CI pipeline:

```
uv sync --frozen
ruff check .
ruff format --check .
mypy --strict src/
pytest --cov=src --cov-fail-under=90
```

Pre-commit hook runs ruff + mypy on changed files, plus pytest on the affected modules. Hook file: `.pre-commit-config.yaml`. Install on `make setup`.

CI runs the full matrix. Pre-commit runs the fast subset.

## Logging

- `structlog` for structured JSON logs. Always.
- Never `print()` in production code. `print` is a debugging tool you forgot to delete.
- Levels:
  - `DEBUG` -> local dev only, verbose internals.
  - `INFO` -> state changes worth knowing about ("user created", "order shipped").
  - `WARNING` -> recoverable issues, retry triggered, fallback used.
  - `ERROR` -> a single operation failed, request returned 5xx.
  - `CRITICAL` -> process is dying or data corrupted.
- Every log line includes a `request_id` or `trace_id` bound via `structlog.contextvars`. If you cannot trace a log line back to a request, the log is useless.
- Never log raw secrets, full auth headers, full request bodies. Redact at the formatter.

## Tools To Install Per Project

Runtime:

- `pydantic`, `pydantic-settings`
- `structlog`

Dev:

- `ruff`
- `mypy`
- `pytest`, `pytest-cov`, `pytest-asyncio`, `pytest-mock`
- `pre-commit`
- `respx` (only if the project makes outbound HTTP)

Install via `uv add` for runtime, `uv add --dev` for dev. Commit `uv.lock`. Done.
