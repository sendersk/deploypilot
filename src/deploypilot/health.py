"""Perform HTTP health checks for deployment workflows."""

import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from deploypilot.results import StepResult, StepStatus


class HttpHealthChecker:
    """Check service availability through HTTP requests."""

    def check(
        self,
        step_name: str,
        url: str,
        timeout: float,
    ) -> StepResult:
        """Return a result based on the HTTP response or connection error."""
        start_time = time.monotonic()

        try:
            with urlopen(url, timeout=timeout) as response:
                status_code = response.status
        except HTTPError as exc:
            status_code = exc.code
        except (URLError, TimeoutError, OSError) as exc:
            duration = time.monotonic() - start_time
            return StepResult(
                step_name=step_name,
                status=StepStatus.FAILED,
                duration_seconds=duration,
                message=f"HTTP health check failed: {exc}",
            )

        duration = time.monotonic() - start_time
        succeeded = 200 <= status_code < 300

        return StepResult(
            step_name=step_name,
            status=(
                StepStatus.SUCCEEDED if succeeded else StepStatus.FAILED
            ),
            duration_seconds=duration,
            message=f"HTTP health check returned status {status_code}.",
        )
