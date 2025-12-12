from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter
import platform

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint to verify the service is running.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "temporal-workflow-explorer",
    }


@router.get("/status")
async def system_status() -> Dict[str, Any]:
    """
    Detailed system status including runtime information.
    """
    return {
        "service": "temporal-workflow-explorer",
        "status": "running",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat(),
        "system": {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "machine": platform.machine(),
        },
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness probe for container orchestration systems (K8s, etc.).
    """
    # In a real application, you would check dependencies like:
    # - Database connectivity
    # - Temporal server connection
    # - Any other critical dependencies

    return {
        "ready": True,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness probe for container orchestration systems (K8s, etc.).
    """
    return {
        "alive": True,
        "timestamp": datetime.now().isoformat(),
    }
