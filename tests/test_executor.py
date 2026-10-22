"""Tests for deployment step execution."""

from unittest.mock import MagicMock

import pytest

from deploypilot.executor import StepExecutor
from deploypilot.models import DeploymentStep, StepType
from deploypilot.results import StepResult, StepStatus


def test_execute_command_step_uses_command_runner() -> None:
    """Pass command details to the command runner."""
    step = DeploymentStep(
        name="check-python",
        type=StepType.COMMAND,
        command=["python", "--version"],
        timeout=12,
    )
    expected_result = StepResult(
        step_name="check-python",
        status=StepStatus.SUCCEEDED,
        duration_seconds=0.2,
        exit_code=0,
    )
    command_runner = MagicMock()
    command_runner.run.return_value = expected_result

    executor = StepExecutor(command_runner=command_runner)
    result = executor.execute(step)

    assert result == expected_result
    command_runner.run.assert_called_once_with(
        step_name="check-python",
        command=["python", "--version"],
        timeout=12,
    )


def test_execute_rejects_http_health_check() -> None:
    """Reject a step type that this executor does not support yet."""
    step = DeploymentStep(
        name="check-service",
        type=StepType.HTTP_HEALTH_CHECK,
        url="https://example.com/",
    )

    with pytest.raises(ValueError, match="Unsupported step type"):
        StepExecutor().execute(step)


def test_execute_rejects_verification_step() -> None:
    """Reject verification steps until their executor is implemented."""
    step = DeploymentStep(
        name="verify-deployment",
        type=StepType.VERIFICATION,
        command=["python", "--version"],
    )

    with pytest.raises(ValueError, match="Unsupported step type"):
        StepExecutor().execute(step)
