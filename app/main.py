from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers import health_controller, workflow_controller, action_controller

app = FastAPI(
    title="Temporal Workflow Explorer",
    description="API for exploring and managing Temporal workflows",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_controller.router, tags=["Health"])
app.include_router(workflow_controller.router, prefix="/api/v1", tags=["Workflows"])

# Action endpoints (called by Temporal activities)
app.include_router(action_controller.router, prefix="/api/v1", tags=["Actions"])


@app.get("/")
async def root():
    return {
        "message": "Welcome to Temporal Workflow Explorer API",
        "version": "0.1.0",
        "docs": "/docs",
    }
