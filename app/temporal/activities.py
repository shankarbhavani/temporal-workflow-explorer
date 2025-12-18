"""Temporal activities for email processing."""
import asyncio
import os
from typing import List, Dict, Any
import httpx
from temporalio import activity
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API base URL from environment
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


@activity.defn(name="send_email")
async def send_email_activity(
    loads_by_scac: Dict[str, Any],
    load_objects: Dict[str, Any],
    shipper_id: str,
    agent_id: str,
    workflow_id: str,
    template_key: str,
    email_subject: str,
    batching_mode: str = "single",
    contact_levels: List[str] = None,
    template_type: str = "company",
    connect_from_role: str = "shipper",
    connect_to_role: str = "carrier",
    network_identifier_key: str = "scac"
) -> Dict[str, Any]:
    """
    Send email activity with carrier follow-up logic.
    Makes an HTTP POST call to the business logic endpoint with email configuration.

    Args:
        loads_by_scac: Loads grouped by SCAC code (from search results)
        load_objects: Full load details indexed by load_number (from search results)
        shipper_id: Shipper identifier
        agent_id: Agent identifier
        workflow_id: Workflow identifier
        template_key: Email template key
        email_subject: Email subject line
        batching_mode: Email batching mode (default: "single")
        contact_levels: Contact levels to target (default: ["is_level_1"])
        template_type: Template type (default: "company")
        connect_from_role: Role sending email (default: "shipper")
        connect_to_role: Role receiving email (default: "carrier")
        network_identifier_key: Network identifier key (default: "scac")

    Returns:
        Dictionary containing email sending results and status
    """
    # Set defaults for mutable arguments
    if contact_levels is None:
        contact_levels = ["is_level_1"]

    # Get activity execution information
    info = activity.info()
    activity.logger.info(
        f"Activity Execution Details - "
        f"Activity ID: {info.activity_id}, "
        f"Activity Type: {info.activity_type}, "
        f"Workflow ID: {info.workflow_id}, "
        f"Attempt: {info.attempt}"
    )

    activity.logger.info(
        f"Calling send email action block endpoint for {len(loads_by_scac)} carriers, "
        f"template: {template_key}, batching_mode: {batching_mode}"
    )

    url = f"{API_BASE_URL}/api/v1/tracy/send-email"

    # Prepare request payload
    payload = {
        "loads_by_scac": loads_by_scac,
        "load_objects": load_objects,
        "shipper_id": shipper_id,
        "agent_id": agent_id,
        "workflow_id": workflow_id,
        "template_key": template_key,
        "email_subject": email_subject,
        "batching_mode": batching_mode,
        "contact_levels": contact_levels,
        "template_type": template_type,
        "connect_from_role": connect_from_role,
        "connect_to_role": connect_to_role,
        "network_identifier_key": network_identifier_key
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=60.0)
            response.raise_for_status()
            data = response.json()

            activity.logger.info(
                f"Email sent successfully: {data.get('successful_emails', 0)} successful, "
                f"{data.get('failed_emails', 0)} failed, status: {data.get('workflow_status', 'unknown')}"
            )
            activity.logger.info(f"Activity returning result with keys: {list(data.keys())}")
            return data

        except httpx.HTTPError as e:
            activity.logger.error(f"HTTP error occurred: {e}")
            raise
        except Exception as e:
            activity.logger.error(f"Error calling send email endpoint: {e}")
            raise


@activity.defn(name="load_search")
async def load_search_activity(
    shipper_id: str,
    agent_id: str,
    workflow_id: str,
    date_range_days: int = 30,
    scac_filter: List[str] = None,
    mode: List[str] = None
) -> Dict[str, Any]:
    """
    Load search results activity.
    Makes an HTTP POST call to the business logic endpoint with search parameters.

    Args:
        shipper_id: Shipper identifier
        agent_id: Agent identifier
        workflow_id: Workflow identifier
        date_range_days: Number of days to search back (default: 30)
        scac_filter: List of SCAC codes to filter by (default: [])
        mode: Transportation modes (default: ["TL"])

    Returns:
        Dictionary containing search results with loads_by_scac, load_objects, etc.
    """
    # Set defaults for mutable arguments
    if scac_filter is None:
        scac_filter = []
    if mode is None:
        mode = ["TL"]

    # Get activity execution information
    info = activity.info()
    activity.logger.info(
        f"Activity Execution Details - "
        f"Activity ID: {info.activity_id}, "
        f"Activity Type: {info.activity_type}, "
        f"Workflow ID: {info.workflow_id}, "
        f"Attempt: {info.attempt}"
    )

    activity.logger.info(
        f"Calling load search action block endpoint for shipper: {shipper_id}, "
        f"date_range_days: {date_range_days}"
    )

    url = f"{API_BASE_URL}/api/v1/tracy/load-search"

    # Prepare request payload
    payload = {
        "shipper_id": shipper_id,
        "agent_id": agent_id,
        "workflow_id": workflow_id,
        "date_range_days": date_range_days,
        "scac_filter": scac_filter,
        "mode": mode
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=60.0)
            response.raise_for_status()
            data = response.json()

            activity.logger.info(
                f"Search results loaded: Found {data.get('total_loads_found', 0)} loads "
                f"across {len(data.get('loads_by_scac', {}))} carriers"
            )
            activity.logger.info(f"Activity returning result with keys: {list(data.keys())}")
            return data

        except httpx.HTTPError as e:
            activity.logger.error(f"HTTP error occurred: {e}")
            raise
        except Exception as e:
            activity.logger.error(f"Error calling load search endpoint: {e}")
            raise


@activity.defn(name="process_email")
async def process_email_activity() -> str:
    """
    Process and classify an email activity.
    Makes an HTTP call to the business logic endpoint.

    Returns:
        The classification result
    """
    # Get activity execution information
    info = activity.info()
    activity.logger.info(
        f"Activity Execution Details - "
        f"Activity ID: {info.activity_id}, "
        f"Activity Type: {info.activity_type}, "
        f"Workflow ID: {info.workflow_id}, "
        f"Attempt: {info.attempt}"
    )

    activity.logger.info("Calling process email action block endpoint...")

    url = f"{API_BASE_URL}/api/v1/tracy/process-email"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            result = data.get("result", "classified")

            activity.logger.info(f"Email processed: {data}")
            activity.logger.info(f"Activity returning result: {result}")
            return result

        except httpx.HTTPError as e:
            activity.logger.error(f"HTTP error occurred: {e}")
            raise
        except Exception as e:
            activity.logger.error(f"Error calling process email endpoint: {e}")
            raise


@activity.defn(name="extract_data")
async def extract_data_activity() -> str:
    """
    Extract data from an email activity.
    Makes an HTTP call to the business logic endpoint.

    Returns:
        The extracted data
    """
    # Get activity execution information
    info = activity.info()
    activity.logger.info(
        f"Activity Execution Details - "
        f"Activity ID: {info.activity_id}, "
        f"Activity Type: {info.activity_type}, "
        f"Workflow ID: {info.workflow_id}, "
        f"Attempt: {info.attempt}"
    )

    activity.logger.info("Calling extract data action block endpoint...")

    url = f"{API_BASE_URL}/api/v1/tracy/extract-data"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            result = data.get("data", "extracted data")

            activity.logger.info(f"Data extracted: {data}")
            activity.logger.info(f"Activity returning result: {result}")
            return result

        except httpx.HTTPError as e:
            activity.logger.error(f"HTTP error occurred: {e}")
            raise
        except Exception as e:
            activity.logger.error(f"Error calling extract data endpoint: {e}")
            raise


@activity.defn(name="get_escalation_milestones")
async def get_escalation_milestones_activity() -> str:
    """
    Get escalation milestones status activity.
    Makes an HTTP call to the business logic endpoint.

    Returns:
        The milestone check status
    """
    activity.logger.info("Calling escalation milestones action block endpoint...")

    url = f"{API_BASE_URL}/api/v1/tracy/escalation-milestones"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            data = response.json()

            activity.logger.info(f"Escalation milestones checked: {data}")
            return data.get("status", "milestone check completed")

        except httpx.HTTPError as e:
            activity.logger.error(f"HTTP error occurred: {e}")
            raise
        except Exception as e:
            activity.logger.error(f"Error calling escalation milestones endpoint: {e}")
            raise


@activity.defn(name="update_load")
async def update_load_activity() -> str:
    """
    Update load information activity.
    Makes an HTTP call to the action block endpoint.

    Returns:
        A message indicating the load was updated
    """
    # Get activity execution information
    info = activity.info()
    activity.logger.info(
        f"Activity Execution Details - "
        f"Activity ID: {info.activity_id}, "
        f"Activity Type: {info.activity_type}, "
        f"Workflow ID: {info.workflow_id}, "
        f"Attempt: {info.attempt}"
    )

    activity.logger.info("Calling update load action block endpoint...")

    url = f"{API_BASE_URL}/api/v1/tracy/update-load"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            result = data.get("message", "load updated")

            activity.logger.info(f"Load updated successfully: {data}")
            activity.logger.info(f"Activity returning result: {result}")
            return result

        except httpx.HTTPError as e:
            activity.logger.error(f"HTTP error occurred: {e}")
            raise
        except Exception as e:
            activity.logger.error(f"Error calling update load endpoint: {e}")
            raise


@activity.defn(name="send_escalation_email")
async def send_escalation_email_activity() -> str:
    """
    Send escalation email to carrier activity.
    Makes an HTTP call to the action block endpoint.

    Returns:
        A message indicating escalation email was sent
    """
    activity.logger.info("Calling send escalation email action block endpoint...")

    url = f"{API_BASE_URL}/api/v1/tracy/send-escalation-email"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, timeout=30.0)
            response.raise_for_status()
            data = response.json()

            activity.logger.info(f"Escalation email sent successfully: {data}")
            return data.get("message", "escalation email to carrier")

        except httpx.HTTPError as e:
            activity.logger.error(f"HTTP error occurred: {e}")
            raise
        except Exception as e:
            activity.logger.error(f"Error calling send escalation email endpoint: {e}")
            raise


@activity.defn(name="sleep_activity")
async def sleep_activity(seconds: str) -> str:
    """
    Sleep activity for workflow delays.

    Args:
        seconds: Number of seconds to sleep (as string)

    Returns:
        A message indicating the sleep completed
    """
    sleep_time = int(seconds)
    activity.logger.info(f"Sleeping for {sleep_time} seconds...")
    await asyncio.sleep(sleep_time)
    activity.logger.info(f"Sleep completed after {sleep_time} seconds")
    return f"slept for {sleep_time} seconds"


@activity.defn(name="start_child_workflow")
async def start_child_workflow_activity(yaml_workflow_name: str) -> dict:
    """
    Start a child workflow from a YAML definition.

    This activity triggers another DSL workflow, allowing workflow composition
    where one workflow can start another workflow.

    Args:
        yaml_workflow_name: Name of the YAML file (without .yaml extension)
                          e.g., "workflow_2_process"

    Returns:
        Dictionary containing the child workflow execution result
    """
    from uuid import uuid4
    from temporalio.client import Client
    from app.temporal.dsl_loader import load_workflow_definition, get_default_workflow_path
    from app.temporal.dsl_workflow import DSLWorkflow

    info = activity.info()

    activity.logger.info(
        f"Starting child workflow from YAML: {yaml_workflow_name} - "
        f"Parent Workflow ID: {info.workflow_id}"
    )

    try:
        # Get Temporal configuration
        temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
        temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
        task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "email-task-queue")

        # Connect to Temporal
        client = await Client.connect(
            temporal_host,
            namespace=temporal_namespace,
        )

        # Load the YAML workflow definition
        yaml_path = get_default_workflow_path(yaml_workflow_name)
        activity.logger.info(f"Loading workflow from: {yaml_path}")

        workflow_input = load_workflow_definition(yaml_path)

        # Generate unique workflow ID
        child_workflow_id = f"{yaml_workflow_name}-{uuid4()}"

        activity.logger.info(f"Executing child workflow with ID: {child_workflow_id}")

        # Execute the child workflow
        result = await client.execute_workflow(
            DSLWorkflow.run,
            workflow_input,
            id=child_workflow_id,
            task_queue=task_queue,
        )

        activity.logger.info(
            f"Child workflow completed successfully - "
            f"Workflow ID: {child_workflow_id}, "
            f"Result keys: {list(result.keys())}"
        )

        return {
            "child_workflow_id": child_workflow_id,
            "child_workflow_name": yaml_workflow_name,
            "child_result": result,
            "status": "completed"
        }

    except FileNotFoundError as e:
        activity.logger.error(f"Workflow YAML file not found: {e}")
        raise
    except Exception as e:
        activity.logger.error(f"Error starting child workflow: {e}")
        raise
