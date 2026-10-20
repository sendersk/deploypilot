
# DeployPilot

Python-based deployment orchestration tool for automated deployments,
health checks, failure handling, and rollback workflows.

## Project Status

Under development.

## Goals

- Automate repeatable deployment workflows.
- Validate deployment steps and their outcomes.
- Perform health checks after deployment.
- Handle failures and support controlled rollback workflows.
- Provide reliable tests and clear execution reports.

## Requirements

- Python 3.13+
- uv


## Development Setup

```powershell
uv sync
```

## Usage

Display the available commands:

```powershell
uv run deploypilot --help
```

Display the application version:

```powershell
uv run deploypilot --version
```

Alternatively, run the application as a Python module:

```powershell
uv run python -m deploypilot --help
```

Validate a workflow configuration without executing deployment steps:

```powershell
uv run deploypilot validate resources/example-workflow.yaml
```

A successful validation displays the workflow name and the number of
deployment and rollback steps. Invalid configurations return a nonzero
exit code.


## Quality Checks

```powershell
uv run pytest
uv run ruff check .
uv run mypy src
```
