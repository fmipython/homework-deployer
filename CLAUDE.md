# homework-deployer

Deploys homework materials for a university Python course between a private "staging" GitHub
repo (where the course team develops homeworks) and a public "production" GitHub repo (what
students see), and wires up test-running infrastructure ([Cove](https://github.com/lyubolp/py-cove)
+ pygrader) so both the course team and students can grade solutions against hidden tests.

**Scope note:** `main` (aka v1) contains an older, unrelated design — an `at`-scheduled CLI
(`register`/`list`/`deregister`/`run`, backed by `db.py`/`event.py`/`executor.py`/`cli.py`) for
copying files between repos on a schedule. **That branch/design is out of scope and should be
ignored.** All active work happens on `v2`, which is a ground-up rewrite around the flow below.
The root `README.md` still describes the v1 CLI and is stale — don't trust it over this file or
the actual `v2` code.

## The flow (sequence diagram)

The intended end-to-end flow has three phases. "Automation" = this script.

**1. Homework development** — course team iterates on a homework in the staging repo; automation
verifies the solution passes the tests before anything ships.
- Python Team pushes homework statement, tests, and solution to the **staging GitHub repo**.
- Staging repo triggers Automation (trigger mechanism — CI webhook vs. manual run — is
  **undecided**, see Open questions).
- Automation clones the staging repo, pushes the homework tests into **Staging Cove**, and runs
  pygrader against the solution (pygrader fetches tests from Staging Cove).
- Pygrader reports results to Automation, which reports them to the Python Team (delivery
  mechanism is **undecided**, see Open questions).

**2. Homework starts** — once verified, the homework is promoted to production for students.
- Automation pulls the homework statement and tests from the staging repo.
- Automation pushes the statement to the **production GitHub repo** and the tests to
  **Production Cove**.

**3. Homework ongoing** — no code in this repo; documented for context only.
- Students read the statement from the production repo, develop their solution, and run pygrader
  themselves; pygrader fetches tests from Production Cove and reports results directly to the
  student.

## Current implementation state (`v2` branch)

Only phase 1 ("Homework development") has code, and it's partial. Entry point is
`homework-deployer.py:stage()`:

1. Clones `settings.staging_repo` to a temp dir (`homework_deployer/services/git.py:clone_repository`).
2. Builds a `DeploymentConfig` — **currently hardcoded to empty values** (`# TODO - Read from the
   actual file`). Intended source: **a per-homework manifest file** in the staging repo (format
   not yet designed) listing `test_files`, `solution_files`, `config_file`, `structure_file`. See
   Open questions.
3. Uploads test files + a patched pygrader config into Cove
   (`homework_deployer/services/cove.py:load_pygrader_config_in_cove`).
4. **Not implemented yet** (TODOs in `stage()`): run pygrader against the solution, collect
   results, report results.

Phase 2 ("Homework starts": pushing statement to prod repo, tests to prod Cove) has **no code
yet** — no function/entry point exists for it.

### Module map

- `homework-deployer.py` — script entry point; currently just `stage()` plus a `Hello world!`
  `__main__` guard. Not yet wired to `homework_deployer.__init__` (that file, and
  `services/__init__.py`, are currently empty).
- `homework_deployer/config.py` — `pydantic-settings` `Settings`, loaded from `.env` (see
  `.env.example`). Separate `staging_*` and `production_*` groups: `*_repo`, `*_cove_url`,
  `*_cove_api_key`, `*_cove_project`.
- `homework_deployer/models.py` — `DeploymentConfig` (test_files, config_file, solution_files,
  structure_file — note: no explicit statement-file field yet, needed for phase 2) and
  `CoveConfig` (url, api_key, project).
- `homework_deployer/exceptions.py` — `CoveException`.
- `homework_deployer/services/git.py` — `clone_repository(repo_url, destination)` via GitPython.
  **Known issue:** it catches and only prints exceptions instead of raising, despite its
  docstring claiming it raises `git.exc.GitCommandError` — callers currently can't detect clone
  failure.
- `homework_deployer/services/cove.py` — `load_pygrader_config_in_cove(homework_dir, deployment,
  cove_config)`: fetches the Cove project, deletes existing items, uploads each test file as a
  Cove `python_item` (key `test_code/<relative path>`), loads the homework's raw pygrader JSON
  config, patches the `checks[].tests_path` entry (where `check["name"] == "tests"`) to point at
  the uploaded items' `cove://` URIs, uploads the patched config as a Cove `json_item` (key
  `"config"`), and returns that config's `cove://` URI.

### The Cove SDK (`cove_sdk`, PyPI package `py-cove`, pinned via git to `v1.4.0` in `pyproject.toml`)

Cove is a small key/value item store used to hand pygrader its tests and config without exposing
them in a public repo. Relevant surface used here:
- `CoveClient(base_url, api_key)` — context manager; `.projects`, `.python_items`, `.json_items`
  resources.
- Items are addressed by `cove://<host>/<resource>/<project_id>/<key>` URIs
  (`ResourceType.JSON_ITEM | KEY_VALUE | PYTHON_ITEM`, built via `build_uri`).
- `client.projects.get(project_id)`, `client.projects.delete_items(project_id)`,
  `client.python_items.create(project_id, key, code)`,
  `client.json_items.create(project_id, key, value)`.

## Open questions (undecided as of this writing — check with the user before assuming)

- **Manifest format**: confirmed to be a per-homework manifest file, but its exact shape/location
  in the staging repo isn't designed yet.
- **Result reporting**: how pygrader results reach the Python Team (phase 1) — console output,
  GitHub PR/commit comment, email, Slack, etc. — is not decided.
- **Automation trigger**: whether "trigger automation" (staging repo → Automation) is a CI
  webhook/GitHub Actions workflow or a manual CLI invocation is not decided.
- Phase 2 ("Homework starts") has no design/code yet beyond what the diagram specifies.

## Dev workflow

Uses `uv` + `just`. Key recipes in `justfile`:
- `just lint` — pylint (`--fail-under 9`), mypy (`--ignore-missing-imports`), flake8, complexipy.
- `just test` — `python3 -m unittest discover -s tests`. Note: `tests/tests.py` is currently
  empty — no test coverage exists yet for the `v2` rewrite.
- `just coverage` — coverage run + report, `--fail-under 75`.
- `just run` — `python3 -m homework_deployer` (currently a no-op since `__init__.py` is empty).
- `just build` — `uv build`.

Style: max line length 120 (`.flake8`), mypy strict-ish (`disallow_untyped_defs`,
`check_untyped_defs`, `no_implicit_optional`), complexipy max complexity 10.

The CI workflow at `.github/workflows/python-app.yml` is stale — it references a `src` dir and
`*/*.py` glob that don't match this repo's layout (`homework_deployer/`, `homework-deployer.py`),
and installs from `requirements.txt` (pinned 2022-era lint tooling) rather than the `uv`/
`pyproject.toml` setup actually in use.
