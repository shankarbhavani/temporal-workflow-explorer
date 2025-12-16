"""YAML loader for DSL workflows."""
import os
from pathlib import Path
from typing import Any, Dict, List, Union

import yaml

from app.temporal.dsl_workflow import (
    DSLInput,
    ActivityStatement,
    ActivityInvocation,
    SequenceStatement,
    Sequence,
    ParallelStatement,
    Parallel,
)


def load_yaml_file(yaml_path: str) -> Dict[str, Any]:
    """
    Load a YAML file and return its contents.

    Args:
        yaml_path: Path to the YAML file

    Returns:
        Dictionary containing the YAML contents
    """
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"YAML file not found: {yaml_path}")

    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)


def parse_statement(stmt_dict: Dict[str, Any]) -> Union[ActivityStatement, SequenceStatement, ParallelStatement]:
    """
    Parse a statement dictionary into a Statement object.

    Args:
        stmt_dict: Dictionary representing a statement

    Returns:
        Statement object (Activity, Sequence, or Parallel)
    """
    if "activity" in stmt_dict:
        return parse_activity_statement(stmt_dict)
    elif "sequence" in stmt_dict:
        return parse_sequence_statement(stmt_dict)
    elif "parallel" in stmt_dict:
        return parse_parallel_statement(stmt_dict)
    else:
        raise ValueError(f"Unknown statement type: {stmt_dict}")


def parse_activity_statement(stmt_dict: Dict[str, Any]) -> ActivityStatement:
    """
    Parse an activity statement.

    Args:
        stmt_dict: Dictionary with 'activity' key

    Returns:
        ActivityStatement object
    """
    activity_dict = stmt_dict["activity"]

    # Handle arguments - can be a list or empty
    arguments = activity_dict.get("arguments", [])
    if arguments is None:
        arguments = []

    activity_invocation = ActivityInvocation(
        name=activity_dict["name"],
        arguments=arguments,
        result=activity_dict.get("result"),
    )

    return ActivityStatement(activity=activity_invocation)


def parse_sequence_statement(stmt_dict: Dict[str, Any]) -> SequenceStatement:
    """
    Parse a sequence statement.

    Args:
        stmt_dict: Dictionary with 'sequence' key

    Returns:
        SequenceStatement object
    """
    sequence_dict = stmt_dict["sequence"]
    elements = [parse_statement(elem) for elem in sequence_dict["elements"]]

    sequence = Sequence(elements=elements)
    return SequenceStatement(sequence=sequence)


def parse_parallel_statement(stmt_dict: Dict[str, Any]) -> ParallelStatement:
    """
    Parse a parallel statement.

    Args:
        stmt_dict: Dictionary with 'parallel' key

    Returns:
        ParallelStatement object
    """
    parallel_dict = stmt_dict["parallel"]
    branches = [parse_statement(branch) for branch in parallel_dict["branches"]]

    parallel = Parallel(branches=branches)
    return ParallelStatement(parallel=parallel)


def load_workflow_definition(yaml_path: str) -> DSLInput:
    """
    Load a workflow definition from a YAML file.

    Args:
        yaml_path: Path to the YAML workflow definition file

    Returns:
        DSLInput object ready for workflow execution
    """
    # Load YAML contents
    workflow_dict = load_yaml_file(yaml_path)

    # Extract variables (default to empty dict if not present)
    variables = workflow_dict.get("variables", {})

    # Parse the root statement
    root_dict = workflow_dict["root"]
    root_statement = parse_statement(root_dict)

    # Create and return DSLInput
    return DSLInput(root=root_statement, variables=variables)


def get_default_workflow_path(workflow_name: str = "load_processing_workflow") -> str:
    """
    Get the default path for a workflow YAML file.

    Args:
        workflow_name: Name of the workflow (without .yaml extension)

    Returns:
        Absolute path to the workflow YAML file
    """
    # Get the directory of this file
    current_dir = Path(__file__).parent

    # Construct path to YAML file
    yaml_path = current_dir / f"{workflow_name}.yaml"

    return str(yaml_path)
