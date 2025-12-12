from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TERMINATED = "terminated"


class WorkflowCreateRequest(BaseModel):
    workflow_id: str = Field(..., description="Unique identifier for the workflow")
    workflow_type: str = Field(..., description="Type of workflow to execute")
    input_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Input parameters for the workflow"
    )
    task_queue: str = Field(
        default="default", description="Task queue to use for the workflow"
    )


class WorkflowResponse(BaseModel):
    workflow_id: str
    workflow_type: str
    status: WorkflowStatus
    run_id: str
    created_at: datetime
    updated_at: datetime
    input_data: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class WorkflowListResponse(BaseModel):
    workflows: list[WorkflowResponse]
    total: int
    page: int
    page_size: int
