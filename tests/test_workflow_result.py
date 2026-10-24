"""Tests for workflow result summaries."""

import pytest
from pydantic import ValidationError

from deploypilot.results import (
    StepResult,
    StepStatus,
    WorkflowResult,
    WorkflowStatus,
)


def make_result(
    name: str,
    status: StepStatus,
    duration: float,
) -> StepResult:
    """Create a step result for summary tests."""
    return StepResult(
        step_name=name,
        status=status,
        duration_seconds=duration,
    )


def test_workflow_result_succeeds_when_all_steps_succeed() -> None:
    """Report success when all steps succeed."""
    steps = [
        make_result("step-one", StepStatus.SUCCEEDED, 1.2),
        make_result("step-two", StepStatus.SUCCEEDED, 0.8),
    ]

    result = WorkflowResult.from_step_results(
        "deployment",
        steps,
        {"step-one", "step-two"},
    )

    assert result.status == WorkflowStatus.SUCCEEDED
    assert result.duration_seconds == pytest.approx(2.0)
    assert len(result.steps) == 2


def test_workflow_result_fails_when_required_step_fails() -> None:
    """Report failure when a required step fails."""
    steps = [
        make_result("step-one", StepStatus.FAILED, 1.0),
        make_result("step-two", StepStatus.SKIPPED, 0.0),
    ]

    result = WorkflowResult.from_step_results(
        "deployment",
        steps,
        {"step-one", "step-two"},
    )

    assert result.status == WorkflowStatus.FAILED


def test_workflow_result_succeeds_when_only_optional_step_fails() -> None:
    """Do not fail the workflow for an optional step failure."""
    steps = [
        make_result("optional-step", StepStatus.FAILED, 0.5),
        make_result("required-step", StepStatus.SUCCEEDED, 1.0),
    ]

    result = WorkflowResult.from_step_results(
        "deployment",
        steps,
        {"required-step"},
    )

    assert result.status == WorkflowStatus.SUCCEEDED


def test_workflow_result_rejects_negative_duration() -> None:
    """Reject a negative workflow duration."""
    with pytest.raises(ValidationError):
        WorkflowResult(
            workflow_name="deployment",
            steps=[],
            status=WorkflowStatus.SUCCEEDED,
            duration_seconds=-1,
        )
