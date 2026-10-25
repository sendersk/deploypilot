"""Models representing deployment step execution results."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class StepStatus(StrEnum):
    """Represent the possible outcomes of a deployment step."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepResult(BaseModel):
    """Represent the execution result of a single workflow step."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    step_name: str = Field(min_length=1)
    status: StepStatus
    duration_seconds: float = Field(ge=0)
    message: str | None = None
    exit_code: int | None = None



class WorkflowStatus(StrEnum):
    """Represent the overall outcome of a workflow."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"


class WorkflowResult(BaseModel):
    """Represent the overall result of a deployment workflow."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    workflow_name: str = Field(min_length=1)
    steps: list[StepResult]
    rollback_steps: list[StepResult] = Field(default_factory=list)
    status: WorkflowStatus
    duration_seconds: float = Field(ge=0)


    @classmethod
    def from_step_results(
        cls,
        workflow_name: str,
        steps: list[StepResult],
        required_step_names: set[str],
    ) -> "WorkflowResult":
        """Build a workflow result using required step names."""
        failed_required_step = any(
            result.status == StepStatus.FAILED
            and result.step_name in required_step_names
            for result in steps
        )

        return cls(
            workflow_name=workflow_name,
            steps=steps,
            status=(
                WorkflowStatus.FAILED
                if failed_required_step
                else WorkflowStatus.SUCCEEDED
            ),
            duration_seconds=sum(
                result.duration_seconds for result in steps
            ),
        )
