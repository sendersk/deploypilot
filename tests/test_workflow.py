"""Tests for sequential workflow execution."""

from unittest.mock import MagicMock, patch

from deploypilot.models import DeploymentStep, StepType, WorkflowConfig
from deploypilot.results import (
    StepResult,
    StepStatus,
    WorkflowStatus,
)
from deploypilot.workflow import WorkflowExecutor


def make_step(name: str, required: bool = True) -> DeploymentStep:
    """Create a command step for workflow tests."""
    return DeploymentStep(
        name=name,
        type=StepType.COMMAND,
        command=["python", "--version"],
        required=required,
    )


def make_result(name: str, status: StepStatus) -> StepResult:
    """Create a step result for workflow tests."""
    return StepResult(
        step_name=name,
        status=status,
        duration_seconds=0.1,
    )


def test_execute_runs_all_steps_after_success() -> None:
    workflow = WorkflowConfig(
        name="test-workflow",
        steps=[make_step("step-one"), make_step("step-two")],
    )
    step_executor = MagicMock()
    step_executor.execute.side_effect = [
        make_result("step-one", StepStatus.SUCCEEDED),
        make_result("step-two", StepStatus.SUCCEEDED),
    ]

    result = WorkflowExecutor(step_executor).execute(workflow)

    assert result.workflow_name == "test-workflow"
    assert result.status == WorkflowStatus.SUCCEEDED
    assert [step.status for step in result.steps] == [
        StepStatus.SUCCEEDED,
        StepStatus.SUCCEEDED,
    ]
    assert step_executor.execute.call_count == 2


def test_execute_skips_remaining_steps_after_required_failure() -> None:
    workflow = WorkflowConfig(
        name="test-workflow",
        steps=[
            make_step("step-one"),
            make_step("step-two"),
            make_step("step-three"),
        ],
    )
    step_executor = MagicMock()
    step_executor.execute.side_effect = [
        make_result("step-one", StepStatus.FAILED),
    ]

    result = WorkflowExecutor(step_executor).execute(workflow)

    assert result.status == WorkflowStatus.FAILED
    assert [step.status for step in result.steps] == [
        StepStatus.FAILED,
        StepStatus.SKIPPED,
        StepStatus.SKIPPED,
    ]
    assert step_executor.execute.call_count == 1


def test_execute_continues_after_optional_failure() -> None:
    workflow = WorkflowConfig(
        name="test-workflow",
        steps=[
            make_step("optional-step", required=False),
            make_step("required-step"),
        ],
    )
    step_executor = MagicMock()
    step_executor.execute.side_effect = [
        make_result("optional-step", StepStatus.FAILED),
        make_result("required-step", StepStatus.SUCCEEDED),
    ]

    result = WorkflowExecutor(step_executor).execute(workflow)

    assert result.status == WorkflowStatus.SUCCEEDED
    assert [step.status for step in result.steps] == [
        StepStatus.FAILED,
        StepStatus.SUCCEEDED,
    ]
    assert step_executor.execute.call_count == 2


def test_execute_returns_summary_for_empty_workflow_steps() -> None:
    # WorkflowConfig normally rejects empty steps, so this behavior is
    # tested only if an empty configuration can be constructed.
    workflow = WorkflowConfig.model_construct(
        name="empty-workflow",
        steps=[],
        rollback_steps=[],
    )

    result = WorkflowExecutor().execute(workflow)

    assert result.workflow_name == "empty-workflow"
    assert result.status == WorkflowStatus.SUCCEEDED
    assert result.steps == []



def test_workflow_timeout_prevents_starting_later_steps() -> None:
    """Skip steps that have not started before the deadline."""
    workflow = WorkflowConfig(
        name="timeout-workflow",
        steps=[make_step("step-one"), make_step("step-two")],
    )
    step_executor = MagicMock()
    step_executor.execute.return_value = make_result(
        "step-one",
        StepStatus.SUCCEEDED,
    )
    executor = WorkflowExecutor(step_executor, timeout=1.0)

    with patch(
        "deploypilot.workflow.time.monotonic",
        side_effect=[100.0, 100.5, 102.0],
    ):
        result = executor.execute(workflow)

    assert result.status == WorkflowStatus.FAILED
    assert [step.status for step in result.steps] == [
        StepStatus.SUCCEEDED,
        StepStatus.FAILED,
    ]
    assert step_executor.execute.call_count == 1



def test_workflow_rejects_non_positive_timeout() -> None:
    """Reject a zero or negative workflow timeout."""
    import pytest

    with pytest.raises(ValueError, match="greater than zero"):
        WorkflowExecutor(timeout=0)
