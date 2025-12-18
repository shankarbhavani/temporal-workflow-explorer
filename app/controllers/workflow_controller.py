"""
Workflow controller for triggering Temporal workflows via HTTP endpoints.
"""
from datetime import timedelta
from uuid import uuid4
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from temporalio.client import (
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleSpec,
    ScheduleIntervalSpec,
    ScheduleState,
)

from app.temporal.client import get_temporal_client, get_task_queue
from app.temporal.workflows import LoadProcessingWorkflow
from app.temporal.dsl_workflow import DSLWorkflow
from app.temporal.dsl_loader import load_workflow_definition, get_default_workflow_path

router = APIRouter(prefix="/workflows")


# Pydantic Request Models
class ExecuteWorkflowRequest(BaseModel):
    """Request model for executing workflow with custom parameters."""
    shipper_id: str = Field(default="test-qa-demo-shipper", description="Shipper identifier")
    agent_id: str = Field(default="TRACY", description="Agent identifier")
    date_range_days: int = Field(default=30, description="Number of days to search back")
    email_subject: str = Field(
        default="FourKites Alert : Late Load Follow Up",
        description="Email subject line"
    )
    template_key: str = Field(default="test-wrapped-action-3", description="Email template key")
    scac_filter: List[str] = Field(default_factory=list, description="List of SCAC codes to filter")
    mode: List[str] = Field(default=["TL"], description="Transportation modes")
    batching_mode: str = Field(default="single", description="Email batching mode")
    contact_levels: List[str] = Field(default=["is_level_1"], description="Contact levels")

# Fixed schedule IDs
SCHEDULE_ID = "load-processing-pipeline-schedule"
WORKFLOW_1_SCHEDULE_ID = "workflow-1-schedule"


@router.post("/load-processing-pipeline")
async def trigger_load_processing_pipeline() -> dict:
    """
    Trigger the complete load processing workflow (code-based version).

    This endpoint executes the full load processing pipeline:
    1. Search for loads
    2. Send email
    3. Wait for 20 seconds
    4. Process email
    5. Extract data
    6. Update load

    Returns:
        Dictionary containing workflow_id and results from all stages
    """
    try:
        # Get Temporal client and task queue
        client = await get_temporal_client()
        task_queue = get_task_queue()

        # Generate unique workflow ID
        workflow_id = f"load-processing-pipeline-{uuid4()}"

        # Execute workflow
        result = await client.execute_workflow(
            LoadProcessingWorkflow.run,
            id=workflow_id,
            task_queue=task_queue,
        )

        return {
            "workflow_id": workflow_id,
            **result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute load processing workflow: {str(e)}"
        )


@router.post("/load-processing-pipeline-yaml")
async def trigger_load_processing_pipeline_yaml() -> dict:
    """
    Trigger the complete load processing workflow (YAML-based version).

    This endpoint executes the same load processing pipeline as the code-based version,
    but the workflow is defined in YAML (app/temporal/load_processing_workflow.yaml).

    The workflow steps are:
    1. Search for loads
    2. Send email
    3. Wait for 20 seconds
    4. Process email
    5. Extract data
    6. Update load

    Returns:
        Dictionary containing workflow_id and results from all stages
    """
    try:
        # Get Temporal client and task queue
        client = await get_temporal_client()
        task_queue = get_task_queue()

        # Load the YAML workflow definition
        yaml_path = get_default_workflow_path("load_processing_workflow")
        workflow_input = load_workflow_definition(yaml_path)

        # Generate unique workflow ID
        workflow_id = f"load-processing-pipeline-yaml-{uuid4()}"

        # Execute DSL workflow with YAML definition
        result = await client.execute_workflow(
            DSLWorkflow.run,
            workflow_input,
            id=workflow_id,
            task_queue=task_queue,
        )

        return {
            "workflow_id": workflow_id,
            "workflow_type": "YAML-based DSL",
            "yaml_definition": yaml_path,
            **result
        }

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"YAML workflow definition not found: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute YAML-based workflow: {str(e)}"
        )


@router.post("/execute-workflow")
async def execute_workflow_with_params(request: ExecuteWorkflowRequest) -> dict:
    """
    Execute workflow with custom parameters.

    This endpoint allows you to trigger the complete workflow cascade (Workflow 1 → 2 → 3)
    with custom parameters for load search and email configuration.

    The workflow steps are:
    1. Search for late loads with custom date range and filters
    2. Send carrier follow-up emails with custom template and subject
    3. Process email (Workflow 2)
    4. Extract data and update load (Workflow 3)

    Args:
        request: ExecuteWorkflowRequest containing custom parameters

    Returns:
        Dictionary containing workflow_id, parameters used, and results from all stages
    """
    try:
        # Get Temporal client and task queue
        client = await get_temporal_client()
        task_queue = get_task_queue()

        # Load the YAML workflow definition (workflow_1 which triggers the cascade)
        yaml_path = get_default_workflow_path("workflow_1_load_and_email")
        workflow_input = load_workflow_definition(yaml_path)

        # Override workflow variables with request parameters
        workflow_input.variables.update({
            "shipper_id": request.shipper_id,
            "agent_id": request.agent_id,
            "date_range_days": request.date_range_days,
            "scac_filter": request.scac_filter,
            "mode": request.mode,
            "template_key": request.template_key,
            "email_subject": request.email_subject,
            "batching_mode": request.batching_mode,
            "contact_levels": request.contact_levels,
        })

        # Generate unique workflow ID
        workflow_id = f"custom-workflow-{uuid4()}"

        # Execute DSL workflow with custom parameters
        result = await client.execute_workflow(
            DSLWorkflow.run,
            workflow_input,
            id=workflow_id,
            task_queue=task_queue,
        )

        return {
            "workflow_id": workflow_id,
            "workflow_name": "Custom Parameterized Workflow (Full Cascade)",
            "cascade": "Workflow 1 → Workflow 2 → Workflow 3",
            "parameters": {
                "shipper_id": request.shipper_id,
                "agent_id": request.agent_id,
                "date_range_days": request.date_range_days,
                "email_subject": request.email_subject,
                "template_key": request.template_key,
                "scac_filter": request.scac_filter,
                "mode": request.mode,
                "batching_mode": request.batching_mode,
                "contact_levels": request.contact_levels,
            },
            **result
        }

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"YAML workflow definition not found: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute workflow with custom parameters: {str(e)}"
        )


@router.post("/workflow-1")
async def trigger_workflow_1() -> dict:
    """
    Trigger Workflow 1: Load and Email

    This workflow executes:
    1. load_search - Search for loads
    2. send_email - Send notification email
    3. sleep_activity (10 sec) - Wait for processing
    4. Triggers Workflow 2 automatically

    Returns:
        Dictionary containing workflow_id and execution results
    """
    try:
        client = await get_temporal_client()
        task_queue = get_task_queue()

        yaml_path = get_default_workflow_path("workflow_1_load_and_email")
        workflow_input = load_workflow_definition(yaml_path)

        workflow_id = f"workflow-1-{uuid4()}"

        result = await client.execute_workflow(
            DSLWorkflow.run,
            workflow_input,
            id=workflow_id,
            task_queue=task_queue,
        )

        return {
            "workflow_id": workflow_id,
            "workflow_name": "Workflow 1: Load and Email",
            "yaml_definition": yaml_path,
            **result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute Workflow 1: {str(e)}"
        )


@router.post("/workflow-2")
async def trigger_workflow_2() -> dict:
    """
    Trigger Workflow 2: Process Email

    This workflow executes:
    1. process_email - Process and classify email
    2. sleep_activity (5 sec) - Wait before next workflow
    3. Triggers Workflow 3 automatically

    Returns:
        Dictionary containing workflow_id and execution results
    """
    try:
        client = await get_temporal_client()
        task_queue = get_task_queue()

        yaml_path = get_default_workflow_path("workflow_2_process")
        workflow_input = load_workflow_definition(yaml_path)

        workflow_id = f"workflow-2-{uuid4()}"

        result = await client.execute_workflow(
            DSLWorkflow.run,
            workflow_input,
            id=workflow_id,
            task_queue=task_queue,
        )

        return {
            "workflow_id": workflow_id,
            "workflow_name": "Workflow 2: Process Email",
            "yaml_definition": yaml_path,
            **result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute Workflow 2: {str(e)}"
        )


@router.post("/workflow-3")
async def trigger_workflow_3() -> dict:
    """
    Trigger Workflow 3: Extract Data and Update Load

    This workflow executes:
    1. extract_data - Extract data from email
    2. update_load - Update load status

    This is the final workflow in the cascade chain.

    Returns:
        Dictionary containing workflow_id and execution results
    """
    try:
        client = await get_temporal_client()
        task_queue = get_task_queue()

        yaml_path = get_default_workflow_path("workflow_3_extract_and_update")
        workflow_input = load_workflow_definition(yaml_path)

        workflow_id = f"workflow-3-{uuid4()}"

        result = await client.execute_workflow(
            DSLWorkflow.run,
            workflow_input,
            id=workflow_id,
            task_queue=task_queue,
        )

        return {
            "workflow_id": workflow_id,
            "workflow_name": "Workflow 3: Extract and Update",
            "yaml_definition": yaml_path,
            **result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute Workflow 3: {str(e)}"
        )


@router.post("/workflow-1/schedule/start")
async def start_workflow_1_schedule() -> dict:
    """
    Start a scheduled workflow-1 that runs every 10 minutes.

    Creates a Temporal schedule that automatically triggers workflow-1
    every 10 minutes. This will execute the full cascade:
    - Workflow 1 → Workflow 2 → Workflow 3

    The workflow will continue running on this schedule until paused or deleted.

    Returns:
        Dictionary containing schedule_id and confirmation message
    """
    try:
        client = await get_temporal_client()
        task_queue = get_task_queue()

        # Load workflow definition
        yaml_path = get_default_workflow_path("workflow_1_load_and_email")
        workflow_input = load_workflow_definition(yaml_path)

        # Create the schedule
        await client.create_schedule(
            WORKFLOW_1_SCHEDULE_ID,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    DSLWorkflow.run,
                    workflow_input,
                    id=f"workflow-1-scheduled-{uuid4()}",
                    task_queue=task_queue,
                ),
                spec=ScheduleSpec(
                    intervals=[ScheduleIntervalSpec(every=timedelta(minutes=10))]
                ),
                state=ScheduleState(
                    note="Workflow-1 cascade - runs every 10 minutes"
                ),
            ),
        )

        return {
            "schedule_id": WORKFLOW_1_SCHEDULE_ID,
            "status": "started",
            "interval": "10 minutes",
            "message": "Schedule created successfully. Workflow-1 (and cascade) will run every 10 minutes.",
            "cascade": "Workflow 1 → Workflow 2 → Workflow 3"
        }

    except Exception as e:
        # Check if schedule already exists
        if "already exists" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail=f"Schedule already exists. Use the pause/resume endpoints to manage it, or delete it first."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create schedule: {str(e)}"
        )


@router.post("/workflow-1/schedule/pause")
async def pause_workflow_1_schedule() -> dict:
    """
    Pause the scheduled workflow-1.

    The schedule will stop triggering new workflow executions until resumed.
    Any currently running workflow execution will complete normally.

    Returns:
        Dictionary containing schedule_id and confirmation message
    """
    try:
        client = await get_temporal_client()
        handle = client.get_schedule_handle(WORKFLOW_1_SCHEDULE_ID)

        await handle.pause(note="Paused via API")

        return {
            "schedule_id": WORKFLOW_1_SCHEDULE_ID,
            "status": "paused",
            "message": "Schedule paused successfully. No new workflow-1 executions will be triggered.",
        }

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Schedule not found. Create a schedule first using the start endpoint."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to pause schedule: {str(e)}"
        )


@router.post("/workflow-1/schedule/resume")
async def resume_workflow_1_schedule() -> dict:
    """
    Resume a paused scheduled workflow-1.

    The schedule will resume triggering workflow executions every 10 minutes.

    Returns:
        Dictionary containing schedule_id and confirmation message
    """
    try:
        client = await get_temporal_client()
        handle = client.get_schedule_handle(WORKFLOW_1_SCHEDULE_ID)

        await handle.unpause(note="Resumed via API")

        return {
            "schedule_id": WORKFLOW_1_SCHEDULE_ID,
            "status": "resumed",
            "message": "Schedule resumed successfully. Workflow-1 will continue running every 10 minutes.",
        }

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Schedule not found. Create a schedule first using the start endpoint."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume schedule: {str(e)}"
        )


@router.delete("/workflow-1/schedule")
async def delete_workflow_1_schedule() -> dict:
    """
    Delete the scheduled workflow-1 permanently.

    This will stop all future workflow executions. Any currently running
    workflow execution will complete normally.

    Returns:
        Dictionary containing schedule_id and confirmation message
    """
    try:
        client = await get_temporal_client()
        handle = client.get_schedule_handle(WORKFLOW_1_SCHEDULE_ID)

        await handle.delete()

        return {
            "schedule_id": WORKFLOW_1_SCHEDULE_ID,
            "status": "deleted",
            "message": "Schedule deleted successfully. No more workflow-1 executions will be triggered.",
        }

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Schedule not found. It may have already been deleted."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete schedule: {str(e)}"
        )


@router.get("/workflow-1/schedule")
async def get_workflow_1_schedule_status() -> dict:
    """
    Get the current status and details of the scheduled workflow-1.

    Returns:
        Dictionary containing schedule details, state, and configuration
    """
    try:
        client = await get_temporal_client()
        handle = client.get_schedule_handle(WORKFLOW_1_SCHEDULE_ID)

        description = await handle.describe()

        return {
            "schedule_id": WORKFLOW_1_SCHEDULE_ID,
            "paused": description.schedule.state.paused,
            "note": description.schedule.state.note,
            "interval_minutes": 10,
            "num_actions": description.info.num_actions,
            "recent_actions": [
                {
                    "start_time": action.start_time.isoformat() if action.start_time else None,
                    "workflow_id": action.action.workflow_id if hasattr(action.action, 'workflow_id') else None,
                }
                for action in description.info.recent_actions[:5]
            ] if description.info.recent_actions else [],
            "next_action_times": [
                time.isoformat() for time in description.info.next_action_times[:3]
            ] if description.info.next_action_times else [],
            "cascade": "Workflow 1 → Workflow 2 → Workflow 3"
        }

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Schedule not found. Create a schedule first using the start endpoint."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get schedule status: {str(e)}"
        )


@router.post("/workflow-1/schedule/trigger")
async def trigger_workflow_1_schedule_manually() -> dict:
    """
    Manually trigger one workflow-1 execution outside the regular schedule.

    This does not affect the regular scheduled executions. Use this to run
    the workflow immediately without waiting for the next scheduled time.

    Returns:
        Dictionary containing schedule_id and confirmation message
    """
    try:
        client = await get_temporal_client()
        handle = client.get_schedule_handle(WORKFLOW_1_SCHEDULE_ID)

        await handle.trigger()

        return {
            "schedule_id": WORKFLOW_1_SCHEDULE_ID,
            "status": "triggered",
            "message": "Workflow-1 triggered manually. Check Temporal UI for execution details.",
            "cascade": "Workflow 1 → Workflow 2 → Workflow 3"
        }

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Schedule not found. Create a schedule first using the start endpoint."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger schedule: {str(e)}"
        )


@router.post("/load-processing-pipeline/schedule/start")
async def start_load_processing_schedule() -> dict:
    """
    Start a scheduled workflow that runs every 5 minutes.

    Creates a Temporal schedule that automatically triggers the load processing
    workflow every 5 minutes. The workflow will continue running on this schedule
    until paused or deleted.

    Returns:
        Dictionary containing schedule_id and confirmation message
    """
    try:
        client = await get_temporal_client()
        task_queue = get_task_queue()

        # Create the schedule
        await client.create_schedule(
            SCHEDULE_ID,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    LoadProcessingWorkflow.run,
                    id=f"load-processing-{uuid4()}",  # Unique ID for each workflow run
                    task_queue=task_queue,
                ),
                spec=ScheduleSpec(
                    intervals=[ScheduleIntervalSpec(every=timedelta(minutes=5))]
                ),
                state=ScheduleState(
                    note="Load processing pipeline - runs every 5 minutes"
                ),
            ),
        )

        return {
            "schedule_id": SCHEDULE_ID,
            "status": "started",
            "interval": "5 minutes",
            "message": "Schedule created successfully. Workflow will run every 5 minutes.",
        }

    except Exception as e:
        # Check if schedule already exists
        if "already exists" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail=f"Schedule already exists. Use the pause/resume endpoints to manage it, or delete it first."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create schedule: {str(e)}"
        )


@router.post("/load-processing-pipeline/schedule/pause")
async def pause_load_processing_schedule() -> dict:
    """
    Pause the scheduled workflow.

    The schedule will stop triggering new workflow executions until resumed.
    Any currently running workflow execution will complete normally.

    Returns:
        Dictionary containing schedule_id and confirmation message
    """
    try:
        client = await get_temporal_client()
        handle = client.get_schedule_handle(SCHEDULE_ID)

        await handle.pause(note="Paused via API")

        return {
            "schedule_id": SCHEDULE_ID,
            "status": "paused",
            "message": "Schedule paused successfully. No new workflows will be triggered.",
        }

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Schedule not found. Create a schedule first using the start endpoint."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to pause schedule: {str(e)}"
        )


@router.post("/load-processing-pipeline/schedule/resume")
async def resume_load_processing_schedule() -> dict:
    """
    Resume a paused scheduled workflow.

    The schedule will resume triggering workflow executions every 5 minutes.

    Returns:
        Dictionary containing schedule_id and confirmation message
    """
    try:
        client = await get_temporal_client()
        handle = client.get_schedule_handle(SCHEDULE_ID)

        await handle.unpause(note="Resumed via API")

        return {
            "schedule_id": SCHEDULE_ID,
            "status": "resumed",
            "message": "Schedule resumed successfully. Workflows will continue running every 5 minutes.",
        }

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Schedule not found. Create a schedule first using the start endpoint."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume schedule: {str(e)}"
        )


@router.delete("/load-processing-pipeline/schedule")
async def delete_load_processing_schedule() -> dict:
    """
    Delete the scheduled workflow permanently.

    This will stop all future workflow executions. Any currently running
    workflow execution will complete normally.

    Returns:
        Dictionary containing schedule_id and confirmation message
    """
    try:
        client = await get_temporal_client()
        handle = client.get_schedule_handle(SCHEDULE_ID)

        await handle.delete()

        return {
            "schedule_id": SCHEDULE_ID,
            "status": "deleted",
            "message": "Schedule deleted successfully. No more workflows will be triggered.",
        }

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Schedule not found. It may have already been deleted."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete schedule: {str(e)}"
        )


@router.get("/load-processing-pipeline/schedule")
async def get_load_processing_schedule_status() -> dict:
    """
    Get the current status and details of the scheduled workflow.

    Returns:
        Dictionary containing schedule details, state, and configuration
    """
    try:
        client = await get_temporal_client()
        handle = client.get_schedule_handle(SCHEDULE_ID)

        description = await handle.describe()

        return {
            "schedule_id": SCHEDULE_ID,
            "paused": description.schedule.state.paused,
            "note": description.schedule.state.note,
            "interval_minutes": 5,
            "num_actions": description.info.num_actions,
            "recent_actions": [
                {
                    "start_time": action.start_time.isoformat() if action.start_time else None,
                    "workflow_id": action.action.workflow_id if hasattr(action.action, 'workflow_id') else None,
                }
                for action in description.info.recent_actions[:5]
            ] if description.info.recent_actions else [],
            "next_action_times": [
                time.isoformat() for time in description.info.next_action_times[:3]
            ] if description.info.next_action_times else [],
        }

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Schedule not found. Create a schedule first using the start endpoint."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get schedule status: {str(e)}"
        )


@router.post("/load-processing-pipeline/schedule/trigger")
async def trigger_load_processing_schedule_manually() -> dict:
    """
    Manually trigger one workflow execution outside the regular schedule.

    This does not affect the regular scheduled executions. Use this to run
    the workflow immediately without waiting for the next scheduled time.

    Returns:
        Dictionary containing schedule_id and confirmation message
    """
    try:
        client = await get_temporal_client()
        handle = client.get_schedule_handle(SCHEDULE_ID)

        await handle.trigger()

        return {
            "schedule_id": SCHEDULE_ID,
            "status": "triggered",
            "message": "Workflow triggered manually. Check Temporal UI for execution details.",
        }

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail=f"Schedule not found. Create a schedule first using the start endpoint."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger schedule: {str(e)}"
        )
