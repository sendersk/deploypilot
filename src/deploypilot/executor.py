"""Execute supported deployment workflow steps."""

from deploypilot.health import HttpHealthChecker
from deploypilot.models import DeploymentStep, StepType
from deploypilot.results import StepResult
from deploypilot.runner import CommandRunner


class StepExecutor:
    """Execute individual workflow steps."""

    def __init__(
        self,
        command_runner: CommandRunner | None = None,
        health_checker: HttpHealthChecker | None = None,
    ) -> None:
        """Initialize the executor with optional execution components."""
        self._command_runner = command_runner or CommandRunner()
        self._health_checker = health_checker or HttpHealthChecker()

    def execute(self, step: DeploymentStep) -> StepResult:
        """Execute a supported step and return its result."""
        if step.type == StepType.COMMAND:
            if step.command is None:
                raise ValueError(
                    f"Command step '{step.name}' has no command configured."
                )

            return self._command_runner.run(
                step_name=step.name,
                command=step.command,
                timeout=step.timeout,
            )

        if step.type == StepType.HTTP_HEALTH_CHECK:
            if step.url is None:
                raise ValueError(
                    f"HTTP health check '{step.name}' has no URL configured."
                )

            return self._health_checker.check(
                step_name=step.name,
                url=str(step.url),
                timeout=step.timeout,
            )

        raise ValueError(
            f"Unsupported step type for execution: {step.type.value}"
        )
