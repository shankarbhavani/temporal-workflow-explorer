"""DSL Workflow - YAML-based workflow interpreter for Temporal."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List, Optional, Union

from temporalio import workflow
from temporalio.common import RetryPolicy


@dataclass
class DSLInput:
    """Input for DSL workflow containing the root statement and variables."""
    root: Statement
    variables: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclass
class ActivityStatement:
    """Statement representing a single activity execution."""
    activity: ActivityInvocation


@dataclass
class ActivityInvocation:
    """Details of an activity to be invoked."""
    name: str
    arguments: List[str] = dataclasses.field(default_factory=list)
    result: Optional[str] = None


@dataclass
class SequenceStatement:
    """Statement representing a sequence of statements to execute in order."""
    sequence: Sequence


@dataclass
class Sequence:
    """A sequence of statements."""
    elements: List[Statement]


@dataclass
class ParallelStatement:
    """Statement representing parallel execution of branches."""
    parallel: Parallel


@dataclass
class Parallel:
    """Parallel execution branches."""
    branches: List[Statement]


Statement = Union[ActivityStatement, SequenceStatement, ParallelStatement]


@workflow.defn(name="DSLWorkflow")
class DSLWorkflow:
    """
    DSL Workflow that executes steps defined in a YAML file.

    This workflow interprets YAML-defined workflow definitions and executes
    them using Temporal's workflow and activity APIs. It supports:
    - Sequential execution
    - Parallel execution
    - Activity invocation with arguments and result storage
    - Variable management
    """

    @workflow.run
    async def run(self, input: DSLInput) -> Dict[str, Any]:
        """
        Execute the DSL workflow.

        Args:
            input: DSL input containing the workflow definition and variables

        Returns:
            Dictionary containing all variables and execution results
        """
        # Initialize variables from input
        self.variables = dict(input.variables)

        # Get workflow execution information
        info = workflow.info()

        # Update variables with workflow metadata
        self.variables["workflow_id"] = info.workflow_id
        self.variables["run_id"] = info.run_id
        self.variables["workflow_type"] = info.workflow_type
        self.variables["attempt"] = info.attempt

        workflow.logger.info(
            f"Starting DSL workflow - "
            f"Workflow ID: {info.workflow_id}, "
            f"Run ID: {info.run_id}"
        )

        # Execute the root statement
        await self.execute_statement(input.root)

        workflow.logger.info(
            f"DSL workflow completed successfully - "
            f"Workflow ID: {info.workflow_id}, "
            f"Run ID: {info.run_id}"
        )

        # Add completion status
        self.variables["workflow_status"] = "completed"

        return self.variables

    async def execute_statement(self, stmt: Statement) -> None:
        """
        Execute a single statement.

        Args:
            stmt: Statement to execute (Activity, Sequence, or Parallel)
        """
        if isinstance(stmt, ActivityStatement):
            await self.execute_activity(stmt)
        elif isinstance(stmt, SequenceStatement):
            await self.execute_sequence(stmt)
        elif isinstance(stmt, ParallelStatement):
            await self.execute_parallel(stmt)

    def resolve_argument(self, arg: str) -> Any:
        """
        Resolve argument value, supporting dot notation for nested dictionary access.

        This method handles both simple variable lookups and nested dictionary access
        using dot notation (e.g., "search_results.loads_by_scac").

        Args:
            arg: Argument string, either a simple variable name or dot-notated path

        Returns:
            The resolved value from variables, or the original argument if not found

        Examples:
            - "shipper_id" -> self.variables["shipper_id"]
            - "search_results.loads_by_scac" -> self.variables["search_results"]["loads_by_scac"]
        """
        # If no dot, do simple variable lookup
        if "." not in arg:
            return self.variables.get(arg, arg)

        # Handle nested dictionary access with dot notation
        keys = arg.split(".")
        value = self.variables

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    workflow.logger.warning(f"Could not resolve nested path: {arg} (failed at key: {key})")
                    return arg  # Fallback to original string if path not found
            else:
                workflow.logger.warning(f"Could not resolve nested path: {arg} (value at {key} is not a dict)")
                return arg  # Fallback if intermediate value is not a dict

        return value

    async def execute_activity(self, stmt: ActivityStatement) -> None:
        """
        Execute an activity statement.

        Args:
            stmt: Activity statement to execute
        """
        activity_name = stmt.activity.name

        workflow.logger.info(f"Executing activity: {activity_name}")

        # Resolve arguments from variables (supports dot notation for nested access)
        args = [self.resolve_argument(arg) for arg in stmt.activity.arguments]

        workflow.logger.info(f"Activity arguments resolved: {len(args)} arguments")

        # Execute the activity with extended timeout for external API calls
        result = await workflow.execute_activity(
            activity_name,
            args=args,
            start_to_close_timeout=timedelta(minutes=5),  # Extended for external API calls
            retry_policy=RetryPolicy(
                maximum_attempts=3,  # Limit retries to prevent excessive attempts
            ),
        )

        workflow.logger.info(f"Activity completed: {activity_name} - Result type: {type(result).__name__}")

        # Store result in variables if specified
        if stmt.activity.result:
            self.variables[stmt.activity.result] = result
            workflow.logger.info(f"Stored result in variable: {stmt.activity.result}")

    async def execute_sequence(self, stmt: SequenceStatement) -> None:
        """
        Execute a sequence of statements in order.

        Args:
            stmt: Sequence statement containing elements to execute
        """
        workflow.logger.info(f"Executing sequence with {len(stmt.sequence.elements)} elements")

        for i, elem in enumerate(stmt.sequence.elements, 1):
            workflow.logger.info(f"Executing sequence element {i}/{len(stmt.sequence.elements)}")
            await self.execute_statement(elem)

    async def execute_parallel(self, stmt: ParallelStatement) -> None:
        """
        Execute multiple branches in parallel.

        Args:
            stmt: Parallel statement containing branches to execute
        """
        workflow.logger.info(f"Executing {len(stmt.parallel.branches)} branches in parallel")

        # Create tasks for each branch
        import asyncio
        tasks = [
            asyncio.create_task(self.execute_statement(branch))
            for branch in stmt.parallel.branches
        ]

        # Wait for all branches to complete
        await asyncio.gather(*tasks)

        workflow.logger.info("All parallel branches completed")
