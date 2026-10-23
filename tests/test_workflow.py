
"""Tests for sequential workflow execution."""

from unittest.mock import MagicMock

from deploypilot.models import DeploymentStep, StepType, WorkflowConfig
from deploypilot.results import StepResult, StepStatus
from deploypilot.workflow import WorkflowExecutor


def make_step(name: str, required: bool = True) -> DeploymentStep:
    """Create a command step for workflow tests."""
    return DeploymentStep(
        name=name,
        type=StepType.COMMAND,
        command=["python", "--version"],
        required=required,
    )


def make_result(
    name: str,
    status: StepStatus,
) -> StepResult:
    """Create a step result for workflow tests."""
    return StepResult(
        step_name=name,
        status=status,
        duration_seconds=0.1,
    )


def test_execute_runs_all_steps_after_success() -> None:
    """Execute every step when all previous steps succeed."""
    workflow = WorkflowConfig(
        name="test-workflow",
        steps=[make_step("step-one"), make_step("step-two")],
    )
    step_executor = MagicMock()
    step_executor.execute.side_effect = [
        make_result("step-one", StepStatus.SUCCEEDED),
        make_result("step-two", StepStatus.SUCCEEDED),
    ]

    results = WorkflowExecutor(step_executor).execute(workflow)

    assert [result.status for result in results] == [
        StepStatus.SUCCEEDED,
        StepStatus.SUCCEEDED,
    ]
    assert step_executor.execute.call_count == 2


def test_execute_skips_remaining_steps_after_required_failure() -> None:
    """Skip later steps after a required step fails."""
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

    results = WorkflowExecutor(step_executor).execute(workflow)

    assert [result.status for result in results] == [
        StepStatus.FAILED,
        StepStatus.SKIPPED,
        StepStatus.SKIPPED,
    ]
    assert step_executor.execute.call_count == 1


def test_execute_continues_after_optional_failure() -> None:
    """Continue when a non-required step fails."""
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

    results = WorkflowExecutor(step_executor).execute(workflow)

    assert [result.status for result in results] == [
        StepStatus.FAILED,
        StepStatus.SUCCEEDED,
    ]
    assert step_executor.execute.call_count == 2


def test_execute_returns_empty_results_for_empty_workflow_steps() -> None:
    """Return no results when there are no steps to execute."""
    # WorkflowConfig normally rejects empty steps, so this behavior is
    # tested only if an empty configuration can be constructed.
    workflow = WorkflowConfig.model_construct(
        name="empty-workflow",
        steps=[],
        rollback_steps=[],
    )

    results = WorkflowExecutor().execute(workflow)

    assert results == []
