
# DeployPilot — Project Scope

## 1. Purpose

DeployPilot is a Python-based deployment orchestration tool that executes
repeatable deployment workflows, verifies deployment health, handles failures,
and supports controlled rollback.

The project demonstrates software engineering practices relevant to DevOps,
Production Support, and Site Reliability Engineering.

## 2. Target Version

The initial stable release is version 1.0.0.

The implementation must remain within the scope defined in this document.

## 3. Core Features

### 3.1 Workflow Configuration
- Load deployment workflows from YAML files.
- Validate configuration structure and required fields.
- Reject invalid configurations before executing any deployment steps.

### 3.2 Deployment Steps
- Support predefined steps: command execution, HTTP health checks,
  and deployment verification.
- Execute steps in the configured order.
- Stop execution when a required step fails.
- Apply configurable timeouts to executable operations.

### 3.3 Execution Results
- Track the status and duration of each step.
- Distinguish successful, failed, and skipped steps.
- Produce a final workflow execution summary.

### 3.4 Failure Handling
- Capture errors without exposing sensitive information.
- Support a configurable rollback workflow after deployment failure.
- Record rollback outcomes separately from deployment outcomes.
- Never report a successful rollback unless it has actually succeeded.

### 3.5 Command-Line Interface
- Validate a workflow configuration.
- Execute a workflow.
- Display a clear execution summary.
- Return meaningful exit codes for success and failure.

### 3.6 Reliability and Quality
- Use structured application logging.
- Validate external inputs.
- Provide unit and integration tests.
- Support static analysis and strict type checking.
- Document installation, configuration, usage, and limitations.

## 4. Technical Constraints

- Python 3.13+
- uv for dependency and environment management
- pytest and pytest-cov for testing
- Ruff for linting and formatting
- MyPy in strict mode
- Pydantic for data validation where appropriate
- PyYAML for YAML configuration
- Docker for isolated integration testing where useful

## 5. Safety Requirements

- Never execute a workflow during configuration validation.
- Never execute arbitrary configuration content as Python code.
- Use explicit timeouts for subprocess execution.
- Avoid logging secrets, credentials, or environment variable values.
- Make command execution behavior explicit and documented.
- Rollback must be an explicitly configured operation.
- Do not claim that rollback restores a previous state unless the
  configured rollback operation completes successfully.

## 6. Out of Scope

- Cloud-provider-specific deployments
- Kubernetes orchestration
- A web interface or graphical dashboard
- Distributed workflow execution
- A remote job queue or scheduler
- Secret-management integrations
- A built-in production deployment service
- Automatic rollback without an explicitly configured rollback operation

## 7. Definition of Done

Version 1.0.0 is complete when:

- All core features are implemented.
- Unit and integration tests pass.
- Ruff and MyPy checks pass.
- Error handling and exit codes are documented and tested.
- The README contains installation and usage instructions.
- The package can be installed and its CLI invoked.
- No known critical defects remain in the tested workflows.
