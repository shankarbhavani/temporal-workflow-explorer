"""Temporal activities for email processing."""
import asyncio
import os
from typing import List
import httpx
from temporalio import activity
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API base URL from environment
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


@activity.defn(name="send_email")
async def send_email_activity() -> str:
    """
    Send an email activity.
    Makes an HTTP call to the business logic endpoint.

    Returns:
        A message indicating the email was sent
    """
    # Get activity execution information
    info = activity.info()

    # Log activity execution details
    activity.logger.info(
        f"Activity Execution Details - "
        f"Activity ID: {info.activity_id}, "
        f"Activity Type: {info.activity_type}, "
        f"Workflow ID: {info.workflow_id}, "
        f"Attempt: {info.attempt}"
    )

    activity.logger.info("Calling send email action block endpoint...")

    url = f"{API_BASE_URL}/api/v1/tracy/send-email"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            result = data.get("message", "Email sent")

            activity.logger.info(f"Email sent successfully: {data}")
            activity.logger.info(f"Activity returning result: {result}")
            return result

        except httpx.HTTPError as e:
            activity.logger.error(f"HTTP error occurred: {e}")
            raise
        except Exception as e:
            activity.logger.error(f"Error calling send email endpoint: {e}")
            raise


@activity.defn(name="load_search")
async def load_search_activity() -> List[int]:
    """
    Load search results activity.
    Makes an HTTP call to the business logic endpoint.

    Returns:
        An array of search result IDs
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

    activity.logger.info("Calling load search action block endpoint...")

    url = f"{API_BASE_URL}/api/v1/tracy/load-search"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            data = response.json()

            activity.logger.info(f"Search results loaded: {data}")
            activity.logger.info(f"Activity returning result: {data}")
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
