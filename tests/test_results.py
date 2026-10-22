"""Tests for deployment execution result models."""

import pytest
from pydantic import ValidationError

from deploypilot.results import StepResult, StepStatus


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
