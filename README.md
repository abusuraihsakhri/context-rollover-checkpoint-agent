# Context Rollover Checkpoint Agent

### [Open the Live Application →](https://abusuraihsakhri.github.io/context-rollover-checkpoint-agent/)

Utilities for evaluating context-rollover triggers, capturing state checkpoints, comparing restore diffs, and running deterministic local task-evaluation workflows.

## Features

- Configurable rollover triggers for token count, elapsed time, error count, context usage, and turn count.
- JSON checkpoint serialization with optional zlib compression and filesystem containment under a configured root.
- Field-level state diffs and selective restore, including nested dictionaries and lists.
- In-memory HMAC-SHA256 chained audit records with signature verification.
- CLI and CSV batch processing, plus optional FastAPI endpoints.
- A dependency-free browser workspace for trigger evaluation, local checkpoints, JSON export, and restore-diff inspection.
- Light and dark themes with responsive layouts for desktop and mobile.

## Live application

The browser application runs entirely client-side. Edit the JSON state, adjust thresholds, and choose **Analyze rollover**. You can save checkpoints in the browser, change the current state, compare it with a saved checkpoint, and export checkpoint JSON.

Browser checkpoints are stored in this site's `localStorage`. The application does not upload state or checkpoint content to a server. Clearing site data removes saved browser checkpoints.

The browser interface is implemented in HTML, CSS, and JavaScript rather than Pyodide/PyScript. The Python package remains the reference implementation; avoiding a Python WebAssembly runtime keeps the static application smaller and faster to load.

## Python installation

Python 3.9 or newer is required.

```bash
git clone https://github.com/abusuraihsakhri/context-rollover-checkpoint-agent.git
cd context-rollover-checkpoint-agent

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`.

Run the test suite:

```bash
pytest -q
```

## CLI

After installation:

```bash
context-rollover-checkpoint-agent audit \
  --task-id TASK-001 \
  --target KEY-001 \
  --primary 12 \
  --secondary 4 \
  --status NOMINAL
```

Batch processing accepts CSV input:

```bash
context-rollover-checkpoint-agent batch -i sample.csv -o results.csv
```

The CSV `is_critical_flag` field accepts common boolean values such as `true`/`false`, `yes`/`no`, and `1`/`0`.

## Optional API

Install the API dependencies:

```bash
python -m pip install -e ".[api]"
context-rollover-checkpoint-agent serve --host 127.0.0.1 --port 8000
```

The API is intended for local or separately secured deployment. This repository does not configure authentication, TLS termination, or internet-facing production infrastructure.

## Security and data handling

- Checkpoint file operations can be restricted to a configured base directory.
- The audit trail uses an HMAC chain and verifies each stored signature.
- The identifier guard is heuristic regular-expression matching. It can detect several configured identifier formats, but it is **not** a de-identification system and does not establish HIPAA or other regulatory compliance.
- External LLM providers are not implemented. The compatibility supervisor uses a deterministic local mock interface and makes no external model call.
- No credentials or API keys are required by the browser application.

## Technology

- Python standard library and Pydantic 2
- Optional FastAPI and Uvicorn
- HTML, CSS, and vanilla JavaScript
- Pytest and pip-audit in GitHub Actions
- GitHub Pages for the static browser application

## Browser compatibility

The browser application uses standard `localStorage`, `Blob`, and modern JavaScript APIs and is intended for current Chrome, Edge, Firefox, and Safari releases. CI validates JavaScript syntax, asset serving, and the deployed Pages endpoint.

## License

MIT. See [LICENSE](LICENSE).
