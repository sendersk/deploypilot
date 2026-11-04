"""Tests for deployment rollback behavior."""

from unittest.mock import MagicMock, patch

from deploypilot.models import DeploymentStep, StepType, WorkflowConfig
from deploypilot.results import (
    RollbackStatus,
    StepResult,
    StepStatus,
    WorkflowStatus,
)
from deploypilot.workflow import WorkflowExecutor


def make_step(name: str) -> DeploymentStep:
    """Create a command step for rollback tests."""
    return DeploymentStep(
        name=name,
        type=StepType.COMMAND,
        command=["python", "--version"],
    )


def make_result(name: str, status: StepStatus) -> StepResult:
    """Create a step result for rollback tests."""
    return StepResult(
        step_name=name,
        status=status,
        duration_seconds=0.1,
        message=f"Step {status.value}.",
    )


def test_rollback_runs_after_required_deployment_failure() -> None:
    """Run configured rollback steps after a deployment failure."""
    workflow = WorkflowConfig(
        name="test-workflow",
        steps=[make_step("deploy")],
        rollback_steps=[make_step("rollback")],
    )
    step_executor = MagicMock()
    step_executor.execute.side_effect = [
        make_result("deploy", StepStatus.FAILED),
        make_result("rollback", StepStatus.SUCCEEDED),
    ]

    result = WorkflowExecutor(step_executor).execute(workflow)

    assert result.status == WorkflowStatus.FAILED
    assert [step.step_name for step in result.steps] == ["deploy"]
    assert [step.step_name for step in result.rollback_steps] == ["rollback"]
    assert result.rollback_steps[0].status == StepStatus.SUCCEEDED
    assert step_executor.execute.call_count == 2


def test_rollback_does_not_run_after_successful_deployment() -> None:
    """Do not execute rollback steps when deployment succeeds."""
    workflow = WorkflowConfig(
        name="test-workflow",
        steps=[make_step("deploy")],
        rollback_steps=[make_step("rollback")],
    )
    step_executor = MagicMock()
    step_executor.execute.return_value = make_result(
        "deploy",
        StepStatus.SUCCEEDED,
    )

    result = WorkflowExecutor(step_executor).execute(workflow)

    assert result.status == WorkflowStatus.SUCCEEDED
    assert result.rollback_steps == []
    assert step_executor.execute.call_count == 1


def test_rollback_does_not_run_when_not_configured() -> None:
    """Do not attempt rollback when no rollback steps are configured."""
    workflow = WorkflowConfig(
        name="test-workflow",
        steps=[make_step("deploy")],
    )
    step_executor = MagicMock()
    step_executor.execute.return_value = make_result(
        "deploy",
        StepStatus.FAILED,
    )

    result = WorkflowExecutor(step_executor).execute(workflow)

    assert result.status == WorkflowStatus.FAILED
    assert result.rollback_steps == []
    assert step_executor.execute.call_count == 1


def test_rollback_stops_after_required_rollback_failure() -> None:
    """Skip remaining rollback steps after a required rollback failure."""
    workflow = WorkflowConfig(
        name="test-workflow",
        steps=[make_step("deploy")],
        rollback_steps=[
            make_step("rollback-one"),
            make_step("rollback-two"),
        ],
    )
    step_executor = MagicMock()
    step_executor.execute.side_effect = [
        make_result("deploy", StepStatus.FAILED),
        make_result("rollback-one", StepStatus.FAILED),
    ]

    result = WorkflowExecutor(step_executor).execute(workflow)

    assert result.status == WorkflowStatus.FAILED
    assert [step.status for step in result.rollback_steps] == [
        StepStatus.FAILED,
        StepStatus.SKIPPED,
    ]
    assert step_executor.execute.call_count == 2


def test_successful_rollback_has_succeeded_status() -> None:
    """Report a successful rollback while preserving deployment failure."""
    workflow = WorkflowConfig(
        name="test-workflow",
        steps=[make_step("deploy")],
        rollback_steps=[make_step("rollback")],
    )
    step_executor = MagicMock()
    step_executor.execute.side_effect = [
        make_result("deploy", StepStatus.FAILED),
        make_result("rollback", StepStatus.SUCCEEDED),
    ]

    result = WorkflowExecutor(step_executor).execute(workflow)

    assert result.status == WorkflowStatus.FAILED
    assert result.rollback_status == RollbackStatus.SUCCEEDED


def test_failed_rollback_has_failed_status() -> None:
    """Report a failed rollback separately from deployment status."""
    workflow = WorkflowConfig(
        name="test-workflow",
        steps=[make_step("deploy")],
        rollback_steps=[make_step("rollback")],
    )
    step_executor = MagicMock()
    step_executor.execute.side_effect = [
        make_result("deploy", StepStatus.FAILED),
        make_result("rollback", StepStatus.FAILED),
    ]

    result = WorkflowExecutor(step_executor).execute(workflow)

    assert result.status == WorkflowStatus.FAILED
    assert result.rollback_status == RollbackStatus.FAILED


def test_unconfigured_rollback_has_not_required_status() -> None:
    """Report that rollback was not required when no steps are configured."""
    workflow = WorkflowConfig(
        name="test-workflow",
        steps=[make_step("deploy")],
    )
    step_executor = MagicMock()
    step_executor.execute.return_value = make_result(
        "deploy",
        StepStatus.SUCCEEDED,
    )

    result = WorkflowExecutor(step_executor).execute(workflow)

    assert result.rollback_status == RollbackStatus.NOT_REQUIRED


def test_rollback_is_skipped_when_workflow_deadline_is_exceeded() -> None:
    """Skip rollback steps when the global workflow deadline has expired."""
    workflow = WorkflowConfig(
        name="timeout-rollback-workflow",
        steps=[make_step("deploy")],
        rollback_steps=[make_step("rollback")],
    )
    step_executor = MagicMock()
    step_executor.execute.return_value = make_result(
        "deploy",
        StepStatus.FAILED,
    )

    executor = WorkflowExecutor(step_executor, timeout=1.0)

    with patch(
        "deploypilot.workflow.time.monotonic",
        side_effect=[100.0, 100.5, 102.0, 102.0, 102.0],
    ):
        result = executor.execute(workflow)

    assert result.status == WorkflowStatus.FAILED
    assert len(result.steps) == 1
    assert result.steps[0].status == StepStatus.FAILED

    assert len(result.rollback_steps) == 1
    assert result.rollback_steps[0].step_name == "rollback"
    assert result.rollback_steps[0].status == StepStatus.FAILED

    assert result.rollback_status == RollbackStatus.FAILED
    assert step_executor.execute.call_count == 1


def test_rollback_timeout_sets_workflow_failure_reason() -> None:
    """Set a failure reason when the deadline prevents rollback execution."""
    workflow = WorkflowConfig(
        name="timeout-rollback-workflow",
        steps=[make_step("deploy")],
        rollback_steps=[make_step("rollback")],
    )
    step_executor = MagicMock()
    step_executor.execute.return_value = make_result(
        "deploy",
        StepStatus.FAILED,
    )

    executor = WorkflowExecutor(step_executor, timeout=1.0)

    with patch(
        "deploypilot.workflow.time.monotonic",
        side_effect=[100.0, 100.5, 102.0],
    ):
        result = executor.execute(workflow)

    assert result.status == WorkflowStatus.FAILED
    assert result.failure_reason == "Workflow timeout reached."
    assert len(result.rollback_steps) == 1
    assert result.rollback_steps[0].status == StepStatus.FAILED
    assert result.rollback_status == RollbackStatus.FAILED
    assert step_executor.execute.call_count == 1


def test_successful_rollback_does_not_change_workflow_failure_status() -> None:
    """Keep workflow failed when rollback succeeds after deployment failure."""
    workflow = WorkflowConfig(
        name="successful-rollback-workflow",
        steps=[make_step("deploy")],
        rollback_steps=[make_step("rollback")],
    )
    step_executor = MagicMock()
    step_executor.execute.side_effect = [
        make_result("deploy", StepStatus.FAILED),
        make_result("rollback", StepStatus.SUCCEEDED),
    ]

    result = WorkflowExecutor(step_executor).execute(workflow)

    assert result.status == WorkflowStatus.FAILED
    assert result.rollback_status == RollbackStatus.SUCCEEDED
    assert len(result.rollback_steps) == 1
    assert result.rollback_steps[0].status == StepStatus.SUCCEEDED
    assert result.failure_reason is None
    assert step_executor.execute.call_count == 2