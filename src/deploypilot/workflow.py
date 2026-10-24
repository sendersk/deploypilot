"""Execute deployment workflows sequentially."""

from deploypilot.executor import StepExecutor
from deploypilot.models import DeploymentStep, WorkflowConfig
from deploypilot.results import (
    StepResult,
    StepStatus,
    WorkflowResult,
)


class WorkflowExecutor:
    """Execute workflow steps sequentially and summarize the results."""

    def __init__(self, step_executor: StepExecutor | None = None) -> None:
        """Initialize the workflow executor."""
        self._step_executor = step_executor or StepExecutor()

    def execute(self, workflow: WorkflowConfig) -> WorkflowResult:
        """Execute a workflow and return its overall result."""
        step_results: list[StepResult] = []
        required_step_names = {
            step.name for step in workflow.steps if step.required
        }
        stop_execution = False

        for step in workflow.steps:
            if stop_execution:
                step_results.append(self._skipped_result(step))
                continue

            result = self._step_executor.execute(step)
            step_results.append(result)

            if result.status == StepStatus.FAILED and step.required:
                stop_execution = True

        return WorkflowResult.from_step_results(
            workflow_name=workflow.name,
            steps=step_results,
            required_step_names=required_step_names,
        )

    @staticmethod
    def _skipped_result(step: DeploymentStep) -> StepResult:
        """Create a result for a step skipped after a required failure."""
        return StepResult(
            step_name=step.name,
            status=StepStatus.SKIPPED,
            duration_seconds=0,
            message="Skipped because a previous required step failed.",
        )
