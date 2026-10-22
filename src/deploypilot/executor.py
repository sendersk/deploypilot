"""Execute supported deployment workflow steps."""

from deploypilot.models import DeploymentStep, StepType
from deploypilot.results import StepResult
from deploypilot.runner import CommandRunner


class StepExecutor:
    """Execute individual workflow steps."""

    def __init__(self, command_runner: CommandRunner | None = None) -> None:
        """Initialize the executor with an optional command runner."""
        self._command_runner = command_runner or CommandRunner()

    def execute(self, step: DeploymentStep) -> StepResult:
        """Execute a command step and return its result."""
        if step.type != StepType.COMMAND:
            raise ValueError(
                f"Unsupported step type for execution: {step.type.value}"
            )

        if step.command is None:
            raise ValueError(
                f"Command step '{step.name}' has no command configured."
            )

        return self._command_runner.run(
            step_name=step.name,
            command=step.command,
            timeout=step.timeout,
        )
