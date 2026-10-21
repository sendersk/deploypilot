"""Tests for YAML workflow loading and validation."""

from pathlib import Path

import pytest

from deploypilot.loader import WorkflowLoadError, load_workflow


def test_load_valid_workflow(tmp_path: Path) -> None:
    """Load a valid workflow from a YAML file."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text(
        """
name: test-deployment
steps:
  - name: verify
    type: command
    command: ["python", "--version"]
""",
        encoding="utf-8",
    )

    workflow = load_workflow(workflow_file)

    assert workflow.name == "test-deployment"
    assert len(workflow.steps) == 1
    assert workflow.steps[0].name == "verify"


def test_missing_file_raises_load_error(tmp_path: Path) -> None:
    """Reject a workflow file that does not exist."""
    with pytest.raises(WorkflowLoadError, match="Unable to read"):
        load_workflow(tmp_path / "missing.yaml")


def test_invalid_yaml_raises_load_error(tmp_path: Path) -> None:
    """Reject a file containing malformed YAML."""
    workflow_file = tmp_path / "invalid.yaml"
    workflow_file.write_text("name: [invalid", encoding="utf-8")

    with pytest.raises(WorkflowLoadError, match="Invalid YAML syntax"):
        load_workflow(workflow_file)


@pytest.mark.parametrize("content", ["", "null", "- item"])
def test_non_mapping_yaml_raises_load_error(
    tmp_path: Path,
    content: str,
) -> None:
    """Reject YAML documents that are not mappings."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text(content, encoding="utf-8")

    with pytest.raises(WorkflowLoadError, match="YAML mapping"):
        load_workflow(workflow_file)


def test_invalid_workflow_data_raises_load_error(
    tmp_path: Path,
) -> None:
    """Reject YAML data that does not satisfy the workflow model."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text(
        "name: invalid-workflow\nsteps: []\n",
        encoding="utf-8",
    )

    with pytest.raises(
        WorkflowLoadError,
        match="failed validation",
    ):
        load_workflow(workflow_file)


def test_unknown_workflow_fields_are_rejected(
    tmp_path: Path,
) -> None:
    """Reject unexpected configuration fields."""
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text(
        """
name: test-deployment
unexpected: value
steps:
  - name: verify
    type: command
    command: ["python", "--version"]
""",
        encoding="utf-8",
    )

    with pytest.raises(
        WorkflowLoadError,
        match="failed validation",
    ):
        load_workflow(workflow_file)


def test_load_workflow_rejects_empty_yaml_file(tmp_path: Path) -> None:
    """Reject an empty YAML document."""
    workflow_file = tmp_path / "empty.yaml"
    workflow_file.write_text("", encoding="utf-8")

    with pytest.raises(WorkflowLoadError, match="YAML mapping"):
        load_workflow(workflow_file)


def test_load_workflow_rejects_yaml_list(tmp_path: Path) -> None:
    """Reject a YAML list instead of a workflow mapping."""
    workflow_file = tmp_path / "list.yaml"
    workflow_file.write_text("- item-one\n- item-two\n", encoding="utf-8")

    with pytest.raises(WorkflowLoadError, match="YAML mapping"):
        load_workflow(workflow_file)


def test_load_workflow_rejects_unknown_top_level_field(
    tmp_path: Path,
) -> None:
    """Reject unsupported fields in a workflow configuration."""
    workflow_file = tmp_path / "unknown-field.yaml"
    workflow_file.write_text(
        """
name: test-deployment
steps:
  - name: check-python
    type: command
    command:
      - python
      - --version
unexpected_field: true
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(WorkflowLoadError, match="failed validation"):
        load_workflow(workflow_file)
