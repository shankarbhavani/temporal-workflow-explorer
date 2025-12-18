"""
Action controller for load processing operations.
These endpoints contain the actual business logic and are called by Temporal activities.
"""
import os
import logging
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tracy")

# Configuration
AI_AGENT_ACTIONS_BASE_URL = os.getenv(
    "AI_AGENT_ACTIONS_BASE_URL",
    "https://ai-agent-actions.fourkites.com"
)
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
WORKFLOW_TIMEOUT = int(os.getenv("WORKFLOW_TIMEOUT", "300"))

# API Endpoints
API_ENDPOINTS = {
    "load_search": "/api/v1/wrapped/triggers/load_search",
    "send_email": "/api/v1/wrapped/communications/send_email"
}


# Pydantic Models for Load Search
class LoadSearchRequest(BaseModel):
    """Request model for load search operation."""
    shipper_id: str = Field(..., description="Shipper identifier")
    agent_id: str = Field(..., description="Agent identifier")
    workflow_id: str = Field(..., description="Workflow identifier")
    date_range_days: int = Field(default=30, description="Number of days to search back")
    scac_filter: List[str] = Field(default_factory=list, description="List of SCAC codes to filter by")
    mode: List[str] = Field(default=["TL"], description="Transportation modes")


class LoadSearchMetadata(BaseModel):
    """Metadata for load search results."""
    search_params: Dict[str, Any] = Field(default_factory=dict)
    search_timestamp: str = Field(default="")


class LoadSearchResponse(BaseModel):
    """Response model for load search operation."""
    loads_by_scac: Dict[str, Any] = Field(default_factory=dict, description="Loads grouped by SCAC")
    load_objects: Dict[str, Any] = Field(default_factory=dict, description="Full load details indexed by load_number")
    load_numbers: List[str] = Field(default_factory=list, description="List of load numbers")
    total_loads_found: int = Field(default=0, description="Total number of loads found")
    metadata: LoadSearchMetadata = Field(default_factory=LoadSearchMetadata)
    audit: List[Dict[str, Any]] = Field(default_factory=list, description="Audit trail")
    current_step: str = Field(..., description="Current workflow step")
    timestamp: str = Field(..., description="Response timestamp")
    error_log: Optional[List[str]] = Field(default=None, description="Error messages if any")
    workflow_status: Optional[str] = Field(default=None, description="Workflow status")


# Pydantic Models for Send Email
class SendEmailRequest(BaseModel):
    """Request model for send email operation."""
    loads_by_scac: Dict[str, Any] = Field(..., description="Loads grouped by SCAC code")
    load_objects: Dict[str, Any] = Field(..., description="Full load details indexed by load_number")
    shipper_id: str = Field(..., description="Shipper identifier")
    agent_id: str = Field(..., description="Agent identifier")
    workflow_id: str = Field(..., description="Workflow identifier")
    template_key: str = Field(..., description="Email template key")
    email_subject: str = Field(..., description="Email subject line")
    batching_mode: str = Field(default="single", description="Email batching mode")
    contact_levels: List[str] = Field(default=["is_level_1"], description="Contact levels to target")
    template_type: str = Field(default="company", description="Template type")
    connect_from_role: str = Field(default="shipper", description="Role sending the email")
    connect_to_role: str = Field(default="carrier", description="Role receiving the email")
    network_identifier_key: str = Field(default="scac", description="Network identifier key")


class SendEmailResponse(BaseModel):
    """Response model for send email operation."""
    email_results: List[Dict[str, Any]] = Field(default_factory=list, description="Email sending results")
    successful_emails: int = Field(default=0, description="Number of emails sent successfully")
    failed_emails: int = Field(default=0, description="Number of emails that failed")
    current_step: str = Field(..., description="Current workflow step")
    timestamp: str = Field(..., description="Response timestamp")
    workflow_status: str = Field(..., description="Workflow status")
    error_log: Optional[List[str]] = Field(default=None, description="Error messages if any")


@router.post("/send-email")
async def send_email(request: SendEmailRequest) -> SendEmailResponse:
    """
    Send follow-up emails to carrier contacts using native send_email batching.

    Uses the send_email action with native batching support:
    - batching_mode to control email batching (default: "single" for one email per load)
    - connect_to_role to automatically retrieve carrier contacts
    - to_levels to target specific contact levels

    Args:
        request: SendEmailRequest containing email configuration and load data

    Returns:
        SendEmailResponse with email sending results and status
    """
    logger.info("Sending carrier follow-up emails using native batching")

    loads_by_scac = request.loads_by_scac
    load_objects = request.load_objects

    if not loads_by_scac:
        logger.warning("No loads found to send emails")
        return SendEmailResponse(
            email_results=[],
            successful_emails=0,
            failed_emails=0,
            current_step="emails_skipped_no_loads",
            timestamp=datetime.utcnow().isoformat(),
            workflow_status="completed_no_loads"
        )

    logger.info(f"Preparing to send emails with {len(loads_by_scac)} SCACs and {len(load_objects)} load objects")

    try:
        # Prepare event_data
        event_data = {
            "shipper_id": request.shipper_id,
            "agent_id": request.agent_id,
            "workflow_id": request.workflow_id
        }

        # Prepare configurations
        configurations = {
            "use_template_service": True,
            "template_key": request.template_key,
            "template_type": request.template_type,
            "batching_mode": request.batching_mode,
            "email_subject": request.email_subject,
            "is_smart_action": True,
            "connect_from_role": request.connect_from_role,
            "connect_to_role": request.connect_to_role,
            "network_identifier_key": request.network_identifier_key,
            "to_levels": request.contact_levels,
            "track_milestone": True
        }

        # Prepare request payload with both scac_load_dict and load_objects
        payload = {
            "event_data": event_data,
            "configurations": configurations,
            "data": {
                "scac_load_dict": loads_by_scac,
                "load_objects": load_objects  # Required for template service
            }
        }

        logger.info(f"Sending emails for {len(loads_by_scac)} carriers with batching_mode={request.batching_mode}")

        # Make API call
        async with httpx.AsyncClient(timeout=WORKFLOW_TIMEOUT) as client:
            response = await client.post(
                f"{AI_AGENT_ACTIONS_BASE_URL}{API_ENDPOINTS['send_email']}",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": AUTH_TOKEN
                }
            )
            response.raise_for_status()
            result = response.json()

        logger.info(f"Successfully sent emails. Response: {result.get('status', 'unknown')}")

        return SendEmailResponse(
            email_results=[result],
            successful_emails=len(loads_by_scac),
            failed_emails=0,
            current_step="emails_sent",
            timestamp=datetime.utcnow().isoformat(),
            workflow_status="completed_successfully"
        )

    except httpx.TimeoutException as e:
        error_msg = f"Timeout sending emails: {str(e)}"
        logger.error(error_msg)
        return SendEmailResponse(
            email_results=[],
            successful_emails=0,
            failed_emails=len(loads_by_scac),
            error_log=[error_msg],
            current_step="email_sending_failed",
            timestamp=datetime.utcnow().isoformat(),
            workflow_status="completed_with_errors"
        )

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error {e.response.status_code} sending emails: {str(e)}"
        logger.error(error_msg)
        return SendEmailResponse(
            email_results=[],
            successful_emails=0,
            failed_emails=len(loads_by_scac),
            error_log=[error_msg],
            current_step="email_sending_failed",
            timestamp=datetime.utcnow().isoformat(),
            workflow_status="completed_with_errors"
        )

    except Exception as e:
        error_msg = f"Unexpected error sending emails: {str(e)}"
        logger.error(error_msg)
        return SendEmailResponse(
            email_results=[],
            successful_emails=0,
            failed_emails=len(loads_by_scac),
            error_log=[error_msg],
            current_step="email_sending_failed",
            timestamp=datetime.utcnow().isoformat(),
            workflow_status="completed_with_errors"
        )


@router.post("/load-search")
async def load_search(request: LoadSearchRequest) -> LoadSearchResponse:
    """
    Search for loads with "late" or "very_late" status.

    This endpoint makes an HTTP POST request to the AI Agent Actions service
    to search for late loads based on the provided criteria.

    Args:
        request: LoadSearchRequest containing search parameters

    Returns:
        LoadSearchResponse with search results, loads grouped by SCAC, and metadata
    """
    logger.info(f"Searching for late loads for shipper: {request.shipper_id}")

    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=request.date_range_days)

        # Prepare request payload matching the exact API format
        # IMPORTANT: include_flat_list MUST be True to get load_objects for template service
        payload = {
            "configurations": {
                "date_range": {
                    "from": start_date.strftime("%Y-%m-%d"),
                    "to": end_date.strftime("%Y-%m-%d")
                },
                "tracking_status": ["late", "very_late"],
                "carrier_filter": request.scac_filter,
                "mode_filter": request.mode,
                "include_scac_grouped": True,
                "include_flat_list": True  # Must be True for template service
            },
            "data": {},
            "event_data": {
                "shipper_id": request.shipper_id,
                "agent_id": request.agent_id
            }
        }

        # Make API call
        async with httpx.AsyncClient(timeout=WORKFLOW_TIMEOUT) as client:
            response = await client.post(
                f"{AI_AGENT_ACTIONS_BASE_URL}{API_ENDPOINTS['load_search']}",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": AUTH_TOKEN
                }
            )
            response.raise_for_status()
            result = response.json()

        # Extract results - the API returns scac_load_dict, loads, and load_objects at top level
        loads_by_scac = result.get("scac_load_dict") or {}
        load_objects = result.get("load_objects") or {}  # Already keyed by load_number (correct format)
        load_numbers = result.get("load_numbers") or []

        # Calculate total loads from scac_load_dict structure
        total_loads = 0
        if loads_by_scac:
            for scac, scac_data in loads_by_scac.items():
                if scac_data is None:
                    continue  # Skip None values
                elif isinstance(scac_data, dict):
                    # scac_data is dict with load_id as keys
                    total_loads += len(scac_data)
                elif isinstance(scac_data, list):
                    # scac_data is list of loads
                    total_loads += len(scac_data)

        logger.info(f"Found {total_loads} late loads across {len(loads_by_scac)} carriers")
        logger.info(f"Extracted {len(load_objects)} load objects (keyed by load_number) for template service")

        # Return optimized response with no duplicates
        return LoadSearchResponse(
            loads_by_scac=loads_by_scac,
            load_objects=load_objects,
            load_numbers=load_numbers,
            total_loads_found=total_loads,
            metadata=LoadSearchMetadata(
                search_params=result.get("metadata", {}).get("search_params", {}),
                search_timestamp=result.get("metadata", {}).get("search_timestamp", "")
            ),
            audit=result.get("audit", []),
            current_step="search_complete",
            timestamp=datetime.utcnow().isoformat()
        )

    except httpx.TimeoutException as e:
        error_msg = f"Timeout searching for late loads: {str(e)}"
        logger.error(error_msg)
        return LoadSearchResponse(
            loads_by_scac={},
            load_objects={},
            load_numbers=[],
            total_loads_found=0,
            metadata=LoadSearchMetadata(),
            audit=[],
            error_log=[error_msg],
            current_step="search_failed",
            timestamp=datetime.utcnow().isoformat()
        )

    except httpx.HTTPStatusError as e:
        # Log the response body for 422 errors to see validation details
        response_body = e.response.text if hasattr(e.response, 'text') else str(e)
        error_msg = f"HTTP error {e.response.status_code} searching loads: {str(e)}"
        logger.error(f"{error_msg}\nResponse body: {response_body}")
        return LoadSearchResponse(
            loads_by_scac={},
            load_objects={},
            load_numbers=[],
            total_loads_found=0,
            metadata=LoadSearchMetadata(),
            audit=[],
            error_log=[error_msg],
            current_step="search_failed",
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        error_msg = f"Unexpected error searching loads: {str(e)}"
        logger.error(error_msg)
        return LoadSearchResponse(
            loads_by_scac={},
            load_objects={},
            load_numbers=[],
            total_loads_found=0,
            metadata=LoadSearchMetadata(),
            audit=[],
            error_log=[error_msg],
            current_step="search_failed",
            timestamp=datetime.utcnow().isoformat()
        )


@router.post("/process-email")
async def process_email() -> dict:
    """
    Process and classify an email - Action endpoint.

    This endpoint contains the actual email processing/classification logic.
    Called by Temporal activities.

    Returns:
        The classification result
    """
    # Business logic for email classification
    # In production, this would use ML models or rule-based classification
    return {"result": "classified"}


@router.post("/extract-data")
async def extract_data() -> dict:
    """
    Extract data from an email - Action endpoint.

    This endpoint contains the actual data extraction logic.
    Called by Temporal activities.

    Returns:
        The extracted data
    """
    # Business logic for data extraction
    # In production, this would parse email content, extract entities, etc.
    return {"data": "extracted data"}


@router.get("/escalation-milestones")
async def get_escalation_milestones() -> dict:
    """
    Get escalation milestones status - Action endpoint.

    This endpoint contains the actual escalation milestone checking logic.
    Called by Temporal activities.

    Returns:
        The milestone check status
    """
    # Business logic for checking escalation milestones
    # In production, this would check SLA rules, escalation policies, etc.
    return {"status": "milestone check completed"}


@router.post("/update-load")
async def update_load() -> dict:
    """
    Update load information - Action endpoint.

    This endpoint contains the actual load update logic.
    Called by Temporal activities.

    Returns:
        A message indicating the load was updated
    """
    # Business logic for updating load
    # In production, this would update load status in database/TMS
    return {"message": "load updated"}


@router.post("/send-escalation-email")
async def send_escalation_email() -> dict:
    """
    Send escalation email to carrier - Action endpoint.

    This endpoint contains the actual escalation email sending logic.
    Called by Temporal activities.

    Returns:
        A message indicating escalation email was sent
    """
    # Business logic for sending escalation emails
    # In production, this would send email to carrier with escalation details
    return {"message": "escalation email to carrier"}
