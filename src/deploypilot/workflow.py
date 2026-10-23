"""Execute deployment workflows sequentially."""

from deploypilot.executor import StepExecutor
from deploypilot.models import DeploymentStep, WorkflowConfig
from deploypilot.results import StepResult, StepStatus


class WorkflowExecutor:
    """Execute workflow steps in order and collect their results."""

    def __init__(self, step_executor: StepExecutor | None = None) -> None:
        """Initialize the workflow executor."""
        self._step_executor = step_executor or StepExecutor()

    def execute(self, workflow: WorkflowConfig) -> list[StepResult]:
        """Execute steps sequentially, stopping after a required failure."""
        results: list[StepResult] = []
        stop_execution = False

        for step in workflow.steps:
            if stop_execution:
                results.append(self._skipped_result(step))
                continue

            result = self._step_executor.execute(step)
            results.append(result)

            if (
                result.status == StepStatus.FAILED
                and step.required
            ):
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
