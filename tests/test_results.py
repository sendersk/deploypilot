"""Tests for deployment execution result models."""

import pytest
from pydantic import ValidationError

from deploypilot.results import (
    RollbackStatus,
    StepResult,
    StepStatus,
    WorkflowResult,
    WorkflowStatus,
)


def test_step_result_accepts_successful_execution() -> None:
    """Accept a successful step result."""
    result = StepResult(
        step_name="verify-python",
        status=StepStatus.SUCCEEDED,
        duration_seconds=0.42,
        message="Python version verified.",
        exit_code=0,
    )

    assert result.step_name == "verify-python"
    assert result.status == StepStatus.SUCCEEDED
    assert result.duration_seconds == 0.42
    assert result.exit_code == 0


def test_step_result_accepts_failed_execution() -> None:
    """Accept a failed step result."""
    result = StepResult(
        step_name="deploy-application",
        status=StepStatus.FAILED,
        duration_seconds=1.5,
        message="Command failed.",
        exit_code=1,
    )

    assert result.status == StepStatus.FAILED
    assert result.exit_code == 1


def test_step_result_accepts_skipped_execution() -> None:
    """Accept a skipped step result."""
    result = StepResult(
        step_name="verify-deployment",
        status=StepStatus.SKIPPED,
        duration_seconds=0,
        message="A previous required step failed.",
    )

    assert result.status == StepStatus.SKIPPED
    assert result.exit_code is None


def test_step_result_rejects_negative_duration() -> None:
    """Reject a negative execution duration."""
    with pytest.raises(ValidationError):
        StepResult(
            step_name="verify-python",
            status=StepStatus.SUCCEEDED,
            duration_seconds=-1,
        )


def test_step_result_rejects_empty_step_name() -> None:
    """Reject an empty step name."""
    with pytest.raises(ValidationError):
        StepResult(
            step_name=" ",
            status=StepStatus.SUCCEEDED,
            duration_seconds=0,
        )


def test_step_result_rejects_unknown_fields() -> None:
    """Reject fields that are not part of the result model."""
    with pytest.raises(ValidationError):
        StepResult(
            step_name="verify-python",
            status=StepStatus.SUCCEEDED,
            duration_seconds=0,
            unexpected_field="value",
        )


def test_workflow_result_accepts_failure_reason() -> None:
    """Accept an optional workflow failure reason."""
    from deploypilot.results import WorkflowResult, WorkflowStatus

    result = WorkflowResult(
        workflow_name="test-workflow",
        steps=[],
        status=WorkflowStatus.FAILED,
        duration_seconds=1.0,
        failure_reason="Workflow timeout reached.",
    )

    assert result.failure_reason == "Workflow timeout reached."


def test_workflow_result_accepts_successful_execution() -> None:
    """Accept a successful workflow result."""
    result = WorkflowResult(
        workflow_name="test-workflow",
        steps=[
            StepResult(
                step_name="deploy",
                status=StepStatus.SUCCEEDED,
                duration_seconds=1.0,
            )
        ],
        status=WorkflowStatus.SUCCEEDED,
        duration_seconds=1.0,
    )

    assert result.workflow_name == "test-workflow"
    assert result.status == WorkflowStatus.SUCCEEDED
    assert result.failure_reason is None
    assert result.rollback_status == RollbackStatus.NOT_REQUIRED


def test_workflow_result_rejects_negative_duration() -> None:
    """Reject a negative workflow duration."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        WorkflowResult(
            workflow_name="test-workflow",
            steps=[],
            status=WorkflowStatus.SUCCEEDED,
            duration_seconds=-1.0,
        )


def test_workflow_result_rejects_unknown_fields() -> None:
    """Reject fields that are not part of the workflow result model."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        WorkflowResult(
            workflow_name="test-workflow",
            steps=[],
            status=WorkflowStatus.SUCCEEDED,
            duration_seconds=0.0,
            unexpected_field="value",
        )


def test_workflow_result_accepts_rollback_results() -> None:
    """Accept a workflow result containing successful rollback results."""
    result = WorkflowResult(
        workflow_name="test-workflow",
        steps=[
            StepResult(
                step_name="deploy",
                status=StepStatus.FAILED,
                duration_seconds=1.0,
            )
        ],
        rollback_steps=[
            StepResult(
                step_name="rollback",
                status=StepStatus.SUCCEEDED,
                duration_seconds=0.5,
            )
        ],
        rollback_status=RollbackStatus.SUCCEEDED,
        status=WorkflowStatus.FAILED,
        duration_seconds=1.5,
        failure_reason="Deployment failed.",
    )

    assert result.status == WorkflowStatus.FAILED
    assert result.rollback_status == RollbackStatus.SUCCEEDED
    assert len(result.rollback_steps) == 1
    assert result.failure_reason == "Deployment failed."