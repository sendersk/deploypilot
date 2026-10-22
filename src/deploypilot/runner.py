"""Execute individual system commands safely."""

import subprocess
import time

from deploypilot.results import StepResult, StepStatus


class CommandRunner:
    """Execute commands and capture their results."""

    def run(
        self,
        step_name: str,
        command: list[str],
        timeout: float,
    ) -> StepResult:
        """Run a command with a timeout and return its result."""
        start_time = time.monotonic()

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            duration = time.monotonic() - start_time
            return StepResult(
                step_name=step_name,
                status=StepStatus.FAILED,
                duration_seconds=duration,
                message=f"Command timed out after {timeout} seconds.",
            )
        except OSError as exc:
            duration = time.monotonic() - start_time
            return StepResult(
                step_name=step_name,
                status=StepStatus.FAILED,
                duration_seconds=duration,
                message=f"Unable to execute command: {exc}",
            )

        duration = time.monotonic() - start_time

        if completed.returncode == 0:
            return StepResult(
                step_name=step_name,
                status=StepStatus.SUCCEEDED,
                duration_seconds=duration,
                message="Command completed successfully.",
                exit_code=completed.returncode,
            )

        return StepResult(
            step_name=step_name,
            status=StepStatus.FAILED,
            duration_seconds=duration,
            message="Command returned a non-zero exit code.",
            exit_code=completed.returncode,
        )
