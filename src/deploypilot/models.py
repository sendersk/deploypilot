"""Validated data models for deployment workflows."""

from enum import StrEnum
from typing import Self

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, model_validator


class StepType(StrEnum):
    """Supported deployment step types."""

    COMMAND = "command"
    HTTP_HEALTH_CHECK = "http_health_check"
    VERIFICATION = "verification"


class DeploymentStep(BaseModel):
    """Represent a single validated deployment step."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1)
    type: StepType
    command: list[str] | None = None
    url: AnyHttpUrl | None = None
    timeout: float = Field(default=30.0, gt=0, le=300)
    required: bool = True

    @model_validator(mode="after")
    def validate_step_configuration(self) -> Self:
        """Ensure each step contains the fields required by its type."""
        if self.type == StepType.HTTP_HEALTH_CHECK:
            if self.url is None:
                raise ValueError("HTTP health checks require a URL.")
            if self.command is not None:
                raise ValueError("HTTP health checks cannot define a command.")
        else:
            if not self.command:
                raise ValueError(f"{self.type.value} steps require a command.")
            if any(not argument.strip() for argument in self.command):
                raise ValueError("Command arguments cannot be empty.")
            if self.url is not None:
                raise ValueError(f"{self.type.value} steps cannot define a URL.")

        return self


class WorkflowConfig(BaseModel):
    """Represent a validated deployment workflow."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1)
    steps: list[DeploymentStep] = Field(min_length=1)
    rollback_steps: list[DeploymentStep] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_step_names(self) -> Self:
        """Ensure step names are unique within each workflow phase."""
        for phase_name, phase_steps in (
            ("deployment", self.steps),
            ("rollback", self.rollback_steps),
        ):
            names = [step.name for step in phase_steps]
            if len(names) != len(set(names)):
                raise ValueError(
                    f"Step names must be unique within the {phase_name} phase."
                )

        return self
