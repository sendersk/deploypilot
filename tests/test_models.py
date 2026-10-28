"""Tests for deployment workflow data models."""

import pytest
from pydantic import ValidationError

from deploypilot.models import DeploymentStep, StepType, WorkflowConfig


def test_command_step_is_valid() -> None:
    """Accept a command step with a valid command."""
    step = DeploymentStep(
        name="deploy",
        type=StepType.COMMAND,
        command=["python", "--version"],
    )

    assert step.name == "deploy"
    assert step.timeout == 30.0
    assert step.required is True


def test_http_health_check_is_valid() -> None:
    """Accept an HTTP health check with a valid URL."""
    step = DeploymentStep(
        name="health-check",
        type=StepType.HTTP_HEALTH_CHECK,
        url="https://example.com/health",
    )

    assert str(step.url) == "https://example.com/health"
    assert step.command is None


def test_verification_step_requires_a_command() -> None:
    """Reject verification steps without a command."""
    with pytest.raises(ValidationError, match="require a command"):
        DeploymentStep(name="verify", type=StepType.VERIFICATION)


def test_http_health_check_requires_a_url() -> None:
    """Reject HTTP health checks without a URL."""
    with pytest.raises(ValidationError, match="require a URL"):
        DeploymentStep(
            name="health-check",
            type=StepType.HTTP_HEALTH_CHECK,
        )


def test_http_health_check_rejects_a_command() -> None:
    """Reject commands on HTTP health check steps."""
    with pytest.raises(ValidationError, match="cannot define a command"):
        DeploymentStep(
            name="health-check",
            type=StepType.HTTP_HEALTH_CHECK,
            url="https://example.com/health",
            command=["echo", "unexpected"],
        )


@pytest.mark.parametrize("timeout", [0, -1, 301])
def test_step_rejects_invalid_timeout(timeout: float) -> None:
    """Reject timeouts outside the supported range."""
    with pytest.raises(ValidationError):
        DeploymentStep(
            name="deploy",
            type=StepType.COMMAND,
            command=["echo", "deploy"],
            timeout=timeout,
        )


def test_step_rejects_unknown_fields() -> None:
    """Reject fields not defined by the model."""
    with pytest.raises(ValidationError, match="extra_forbidden"):
        DeploymentStep(
            name="deploy",
            type=StepType.COMMAND,
            command=["echo", "deploy"],
            unexpected_field="value",
        )


def test_workflow_requires_at_least_one_step() -> None:
    """Reject workflows without deployment steps."""
    with pytest.raises(ValidationError):
        WorkflowConfig(name="release", steps=[])


def test_workflow_rejects_duplicate_deployment_step_names() -> None:
    """Reject duplicate names within the deployment phase."""
    step = DeploymentStep(
        name="deploy",
        type=StepType.COMMAND,
        command=["echo", "deploy"],
    )

    with pytest.raises(ValidationError, match="must be unique"):
        WorkflowConfig(name="release", steps=[step, step])


def test_workflow_accepts_rollback_steps() -> None:
    """Accept a workflow with a separate rollback phase."""
    deploy = DeploymentStep(
        name="deploy",
        type=StepType.COMMAND,
        command=["echo", "deploy"],
    )
    rollback = DeploymentStep(
        name="restore",
        type=StepType.COMMAND,
        command=["echo", "restore"],
    )

    workflow = WorkflowConfig(
        name="release",
        steps=[deploy],
        rollback_steps=[rollback],
    )

    assert len(workflow.steps) == 1
    assert len(workflow.rollback_steps) == 1


def test_workflow_rejects_empty_name() -> None:
    """Reject workflows with an empty name."""
    with pytest.raises(ValidationError):
        WorkflowConfig(
            name=" ",
            steps=[
                DeploymentStep(
                    name="deploy",
                    type=StepType.COMMAND,
                    command=["echo", "deploy"],
                )
            ],
        )
