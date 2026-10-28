"""Load and validate deployment workflows from YAML files."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from deploypilot.models import WorkflowConfig


class WorkflowLoadError(Exception):
    """Represent an error while loading a workflow configuration."""


def load_workflow(path: Path) -> WorkflowConfig:
    """Load a YAML file and validate its workflow configuration."""
    try:
        with path.open("r", encoding="utf-8") as file:
            data: Any = yaml.safe_load(file)
    except OSError as exc:
        raise WorkflowLoadError(f"Unable to read workflow file: {path}") from exc
    except yaml.YAMLError as exc:
        raise WorkflowLoadError(
            f"Invalid YAML syntax in workflow file: {path}"
        ) from exc

    if not isinstance(data, dict):
        raise WorkflowLoadError("Workflow configuration must contain a YAML mapping.")

    try:
        return WorkflowConfig.model_validate(data)
    except ValidationError as exc:
        raise WorkflowLoadError(
            f"Workflow configuration failed validation: {exc}"
        ) from exc
