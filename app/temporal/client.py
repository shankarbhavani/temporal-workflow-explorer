"""Temporal client utilities for connecting to Temporal server."""
import os
from temporalio.client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def get_temporal_client() -> Client:
    """
    Get a connected Temporal client instance.

    Returns:
        Connected Temporal client
    """
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")

    client = await Client.connect(
        temporal_host,
        namespace=temporal_namespace,
    )

    return client


def get_task_queue() -> str:
    """
    Get the task queue name from environment variables.

    Returns:
        Task queue name
    """
    return os.getenv("TEMPORAL_TASK_QUEUE", "email-task-queue")
