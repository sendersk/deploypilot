"""Tests for HTTP health checks."""

from unittest.mock import MagicMock, patch
from urllib.error import URLError

from deploypilot.health import HttpHealthChecker
from deploypilot.results import StepStatus


def test_check_succeeds_for_http_200() -> None:
    """Treat an HTTP 200 response as success."""
    response = MagicMock()
    response.status = 200

    with patch("deploypilot.health.urlopen") as mocked_urlopen:
        mocked_urlopen.return_value.__enter__.return_value = response

        result = HttpHealthChecker().check("service-health", "https://example.com/", 5)

    assert result.status == StepStatus.SUCCEEDED
    assert "200" in (result.message or "")
    mocked_urlopen.assert_called_once_with("https://example.com/", timeout=5)


def test_check_succeeds_for_http_204() -> None:
    """Treat an HTTP 204 response as success."""
    response = MagicMock()
    response.status = 204

    with patch("deploypilot.health.urlopen") as mocked_urlopen:
        mocked_urlopen.return_value.__enter__.return_value = response

        result = HttpHealthChecker().check("service-health", "https://example.com/", 5)

    assert result.status == StepStatus.SUCCEEDED


def test_check_fails_for_http_503() -> None:
    """Treat an HTTP 503 response as failure."""
    response = MagicMock()
    response.status = 503

    with patch("deploypilot.health.urlopen") as mocked_urlopen:
        mocked_urlopen.return_value.__enter__.return_value = response

        result = HttpHealthChecker().check("service-health", "https://example.com/", 5)

    assert result.status == StepStatus.FAILED
    assert "503" in (result.message or "")


def test_check_handles_connection_error() -> None:
    """Return a failed result when the connection cannot be established."""
    with patch(
        "deploypilot.health.urlopen",
        side_effect=URLError("Connection refused"),
    ):
        result = HttpHealthChecker().check("service-health", "https://example.com/", 5)

    assert result.status == StepStatus.FAILED
    assert "HTTP health check failed" in (result.message or "")
