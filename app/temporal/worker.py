"""Temporal worker that executes workflows and activities."""
import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker
from dotenv import load_dotenv

from app.temporal.workflows import LoadProcessingWorkflow
from app.temporal.dsl_workflow import DSLWorkflow
from app.temporal.activities import (
    send_email_activity,
    load_search_activity,
    process_email_activity,
    extract_data_activity,
    get_escalation_milestones_activity,
    update_load_activity,
    send_escalation_email_activity,
    sleep_activity,
)

# Load environment variables
load_dotenv()


async def run_worker():
    """
    Start the Temporal worker that listens for workflow and activity tasks.
    """
    # Get configuration from environment variables
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "email-task-queue")

    print(f"Connecting to Temporal server at {temporal_host}")
    print(f"Namespace: {temporal_namespace}")
    print(f"Task Queue: {task_queue}")

    # Connect to Temporal server
    client = await Client.connect(
        temporal_host,
        namespace=temporal_namespace,
    )

    print("Connected to Temporal server successfully!")

    # Create worker
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[LoadProcessingWorkflow, DSLWorkflow],
        activities=[
            send_email_activity,
            load_search_activity,
            process_email_activity,
            extract_data_activity,
            get_escalation_milestones_activity,
            update_load_activity,
            send_escalation_email_activity,
            sleep_activity,
        ],
    )

    print(f"Worker started and listening on task queue: {task_queue}")
    print("Registered workflows:")
    print("  - LoadProcessingWorkflow (code-based)")
    print("  - DSLWorkflow (YAML-based)")
    print("\nRegistered activities:")
    print("  - send_email")
    print("  - load_search")
    print("  - process_email")
    print("  - extract_data")
    print("  - get_escalation_milestones")
    print("  - update_load")
    print("  - send_escalation_email")
    print("  - sleep_activity")
    print("\nWorker is ready to process tasks. Press Ctrl+C to stop.")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
