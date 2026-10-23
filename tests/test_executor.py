"""Tests for deployment step execution."""

from unittest.mock import MagicMock

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



def test_execute_http_health_check_uses_health_checker() -> None:
    """Pass HTTP health check details to the health checker."""
    step = DeploymentStep(
        name="check-service",
        type=StepType.HTTP_HEALTH_CHECK,
        url="https://example.com/",
        timeout=12,
    )
    expected_result = StepResult(
        step_name="check-service",
        status=StepStatus.SUCCEEDED,
        duration_seconds=0.2,
        message="HTTP health check returned status 200.",
    )
    health_checker = MagicMock()
    health_checker.check.return_value = expected_result

    executor = StepExecutor(health_checker=health_checker)
    result = executor.execute(step)

    assert result == expected_result
    health_checker.check.assert_called_once_with(
        step_name="check-service",
        url="https://example.com/",
        timeout=12,
    )


def test_execute_verification_step_uses_command_runner() -> None:
    """Execute verification steps through the command runner."""
    step = DeploymentStep(
        name="verify-deployment",
        type=StepType.VERIFICATION,
        command=["python", "--version"],
        timeout=15,
    )
    expected_result = StepResult(
        step_name="verify-deployment",
        status=StepStatus.SUCCEEDED,
        duration_seconds=0.2,
        message="Command completed successfully.",
        exit_code=0,
    )
    command_runner = MagicMock()
    command_runner.run.return_value = expected_result

    executor = StepExecutor(command_runner=command_runner)
    result = executor.execute(step)

    assert result == expected_result
    command_runner.run.assert_called_once_with(
        step_name="verify-deployment",
        command=["python", "--version"],
        timeout=15,
    )
