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
