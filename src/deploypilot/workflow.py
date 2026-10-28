"""Execute deployment workflows sequentially."""

import logging

from deploypilot.executor import StepExecutor
from deploypilot.models import DeploymentStep, WorkflowConfig
from deploypilot.results import (
    RollbackStatus,
    StepResult,
    StepStatus,
    WorkflowResult,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """Execute deployment workflows and handle configured rollback steps."""

    def __init__(self, step_executor: StepExecutor | None = None) -> None:
        """Initialize the workflow executor."""
        self._step_executor = step_executor or StepExecutor()

    def execute(self, workflow: WorkflowConfig) -> WorkflowResult:
        """Execute a workflow and roll back after a required failure."""
        logger.info("Starting workflow '%s'.", workflow.name)

        deployment_results = self._execute_steps(workflow.steps)
        required_step_names = {step.name for step in workflow.steps if step.required}
        deployment_result = WorkflowResult.from_step_results(
            workflow_name=workflow.name,
            steps=deployment_results,
            required_step_names=required_step_names,
        )

        rollback_results: list[StepResult] = []
        if (
            deployment_result.status == WorkflowStatus.FAILED
            and workflow.rollback_steps
        ):
            logger.warning(
                "Deployment failed for workflow '%s'; starting rollback.",
                workflow.name,
            )
            rollback_results = self._execute_steps(workflow.rollback_steps)

        rollback_status = RollbackStatus.NOT_REQUIRED
        if rollback_results:
            rollback_status = (
                RollbackStatus.FAILED
                if any(step.status != StepStatus.SUCCEEDED for step in rollback_results)
                else RollbackStatus.SUCCEEDED
            )

        total_duration = sum(
            result.duration_seconds
            for result in [*deployment_results, *rollback_results]
        )

        result = WorkflowResult(
            workflow_name=workflow.name,
            steps=deployment_results,
            rollback_steps=rollback_results,
            rollback_status=rollback_status,
            status=deployment_result.status,
            duration_seconds=total_duration,
        )

        logger.info(
            "Workflow '%s' finished with status '%s' in %.2f seconds.",
            result.workflow_name,
            result.status.value,
            result.duration_seconds,
        )

        return result

    def _execute_steps(
        self,
        steps: list[DeploymentStep],
    ) -> list[StepResult]:
        """Execute steps sequentially, stopping after a required failure."""
        results: list[StepResult] = []
        stop_execution = False

        for step in steps:
            if stop_execution:
                skipped_result = self._skipped_result(step)
                results.append(skipped_result)
                logger.info(
                    "Skipping step '%s' because a previous required step failed.",
                    step.name,
                )
                continue

            logger.info("Starting step '%s'.", step.name)
            result = self._step_executor.execute(step)
            results.append(result)

            if result.status == StepStatus.FAILED:
                logger.error(
                    "Step '%s' failed: %s",
                    step.name,
                    result.message or "No error details available.",
                )
            else:
                logger.info(
                    "Step '%s' finished with status '%s' in %.2f seconds.",
                    step.name,
                    result.status.value,
                    result.duration_seconds,
                )

            if result.status == StepStatus.FAILED and step.required:
                stop_execution = True

        return results

    @staticmethod
    def _skipped_result(step: DeploymentStep) -> StepResult:
        """Create a result for a step skipped after a required failure."""
        return StepResult(
            step_name=step.name,
            status=StepStatus.SKIPPED,
            duration_seconds=0,
            message="Skipped because a previous required step failed.",
        )
