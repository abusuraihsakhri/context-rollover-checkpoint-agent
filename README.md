# Context Rollover Checkpoint Agent

### [Open the Live Application →](https://abusuraihsakhri.github.io/context-rollover-checkpoint-agent/)

Utilities for evaluating context-rollover triggers, creating state checkpoints, comparing a current state with a checkpoint, and running a small deterministic task-evaluation workflow.

## Features

- Configurable rollover triggers for token count, elapsed time, error count, context usage, and turn count
- Checkpoint compression and restore-diff calculation
- Browser interface for trigger evaluation, local checkpoint storage, JSON download, and state comparison
- Command-line workflows for single-record evaluation, CSV batch processing, local mock queries, and API serving
- Optional FastAPI applications
- HMAC-SHA256 chained in-memory audit trail used by the compatibility layer
- Heuristic identifier-pattern guard and redaction helpers

The identifier guard is a pattern-based safeguard, not a complete de-identification or compliance system.

## Browser application

The GitHub Pages application is static HTML, CSS, and JavaScript. It does not send checkpoint content to a server. Saved checkpoints use the browser's `localStorage`.

The browser UI implements the trigger and restore-diff behavior directly in JavaScript. It does not require Pyodide or another in-browser Python runtime.

## Python installation

Python 3.9 or newer is required.

```bash
git clone https://github.com/abusuraihsakhri/context-rollover-checkpoint-agent.git
cd context-rollover-checkpoint-agent
python -m pip install -e .
```

Install optional API dependencies:

```bash
python -m pip install -e ".[api]"
```

Install test dependencies:

```bash
python -m pip install -e ".[test]"
```

## Usage

Single task evaluation:

```bash
context-rollover-checkpoint-agent audit \
  --task-id TASK-001 \
  --target TARGET-01 \
  --primary 28.5 \
  --secondary 14.2 \
  --critical \
  --status DISCORDANT
```

Batch CSV processing:

```bash
context-rollover-checkpoint-agent batch -i sample.csv -o results.csv
```

Deterministic local compatibility query:

```bash
context-rollover-checkpoint-agent chat "What is the system status?"
```

Run the optional API server:

```bash
context-rollover-checkpoint-agent serve --host 127.0.0.1 --port 8000
```

## Core Python API

```python
from context_rollover_checkpoint import ContextRolloverEngine

engine = ContextRolloverEngine(token_threshold=4000)

state = {
    "token_count": 4200,
    "error_count": 0,
    "turn_count": 12,
}

if engine.should_rollover(state):
    engine.create_checkpoint("checkpoint-001", state)
```

Additional trigger policies are available from `context_rollover.triggers`.

## Testing

```bash
pytest -q
```

GitHub Actions also compile the Python sources, run the test suite across supported Python versions, smoke-test the API imports, audit installed dependencies, validate the browser JavaScript syntax, and smoke-test the static site.

## Project structure

```text
agents/                      Compatibility-layer API, audit, metrics, and worker modules
context_rollover/            Trigger, compression, restore-diff, CLI, API, and model modules
tests/                       Automated tests
web/                         Browser application JavaScript and CSS
index.html                   GitHub Pages entry point
context_rollover_checkpoint.py
pyproject.toml
sample.csv
simulator.py
```

## Privacy and security

- The GitHub Pages interface processes entered state in the browser.
- Browser checkpoints are stored in `localStorage` until deleted by the user or cleared by the browser.
- No API key or secret is required for the static site.
- `AUDIT_SECRET_KEY` can be supplied for reproducible HMAC audit signing; otherwise the Python compatibility layer generates an in-process key.
- The repository should not be treated as a clinical de-identification system or as a compliance certification mechanism.

## Browser compatibility

The static interface targets current versions of Chromium-based browsers, Firefox, and Safari. It uses modern browser features including `localStorage`, `Blob`, `URL.createObjectURL`, CSS custom properties, and `color-mix()`.

## License

MIT. See [LICENSE](LICENSE).
