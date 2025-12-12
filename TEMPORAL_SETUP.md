# Temporal Integration Setup Guide

This guide explains how to use the Temporal workflow integration for email processing APIs.

## Overview

The email APIs have been integrated with Temporal to provide reliable, distributed workflow execution. Each API endpoint now triggers a Temporal workflow that executes activities on Temporal workers.

## Architecture

```
User Request → Workflow Endpoint → Temporal Workflow → Temporal Activity (HTTP Call) → Business Logic Endpoint
```

The application has a clean separation of concerns:

1. **Business Logic Endpoints** (`/api/v1/email/*`): Pure HTTP endpoints containing actual business logic
2. **Temporal Activities**: Make HTTP calls to business logic endpoints
3. **Temporal Workflows**: Orchestrate multiple activities in sequence or parallel
4. **Workflow Trigger Endpoints** (`/api/v1/tracy/*`): Start Temporal workflows
5. **Temporal Worker**: Polls for and executes workflows/activities

This architecture allows:
- Business logic to be tested independently without Temporal
- Activities can call any HTTP service (internal or external)
- Temporal provides orchestration, retry logic, and failure handling
- Clear separation between business logic and workflow orchestration

## Prerequisites

1. **Temporal Server**: Must be running at `localhost:7233`
   - Download from: https://github.com/temporalio/temporal
   - Or use Docker: `docker run -p 7233:7233 temporalio/auto-setup`

2. **Python Dependencies**: Install the required packages
   ```bash
   pip install -e .
   # or
   uv pip install -e .
   ```

## Configuration

Environment variables are stored in `.env` file:

```env
# Temporal Configuration
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=email-task-queue

# API Configuration (used by Temporal activities)
API_BASE_URL=http://localhost:8000
```

You can modify these values based on your Temporal and API setup.

## Running the Application

### Step 1: Start Temporal Server

If using Docker:
```bash
docker run -p 7233:7233 temporalio/auto-setup
```

### Step 2: Start the Temporal Worker

The worker must be running to process workflow and activity tasks:

```bash
python run_worker.py
```

You should see output like:
```
============================================================
Starting Temporal Worker
============================================================

Connecting to Temporal server at localhost:7233
Namespace: default
Task Queue: email-task-queue
Connected to Temporal server successfully!
Worker started and listening on task queue: email-task-queue
```

### Step 3: Start the FastAPI Server

In a separate terminal:

```bash
python main.py
```

The API server will start at `http://localhost:8000`

## API Endpoints

### Business Logic Endpoints (Direct - No Temporal)

These endpoints contain the actual business logic and can be called directly:

#### 1. Send Email
```bash
POST /api/v1/email/send
```
Response: `{"message": "Email sent"}`

#### 2. Load Search
```bash
GET /api/v1/email/load-search
```
Response: `[1, 2, 3, 4]`

#### 3. Process Email
```bash
POST /api/v1/email/process
```
Response: `{"result": "classified"}`

#### 4. Extract Data
```bash
POST /api/v1/email/extract-data
```
Response: `{"data": "extracted data"}`

#### 5. Escalation Milestones
```bash
GET /api/v1/email/escalation-milestones
```
Response: `{"status": "milestone check completed"}`

---

### Workflow Endpoints (Via Temporal)

These endpoints trigger Temporal workflows which then call the business logic endpoints via activities:

### 1. Send Email
```bash
POST /api/v1/tracy/send-email
```

Response:
```json
{
  "workflow_id": "send-email-xxxxx",
  "message": "Email sent"
}
```

### 2. Load Search
```bash
GET /api/v1/tracy/load-search
```

Response:
```json
{
  "workflow_id": "load-search-xxxxx",
  "data": [1, 2, 3, 4]
}
```

### 3. Process Email
```bash
POST /api/v1/tracy/process-email
```

Response:
```json
{
  "workflow_id": "process-email-xxxxx",
  "result": "classified"
}
```

### 4. Extract Data
```bash
POST /api/v1/tracy/extract-data
```

Response:
```json
{
  "workflow_id": "extract-data-xxxxx",
  "data": "extracted data"
}
```

### 5. Escalation Milestones
```bash
GET /api/v1/tracy/escalation-milestones
```

Response:
```json
{
  "workflow_id": "escalation-milestones-xxxxx",
  "status": "milestone check completed"
}
```

### 6. Email Processing Pipeline (Bonus)
```bash
POST /api/v1/tracy/pipeline
```

Executes all email processing steps in sequence. Response:
```json
{
  "workflow_id": "email-pipeline-xxxxx",
  "search_results": [1, 2, 3, 4],
  "classification": "classified",
  "extracted_data": "extracted data",
  "milestone_status": "milestone check completed",
  "send_status": "Email sent",
  "pipeline_status": "completed"
}
```

## Testing the Integration

### Using cURL

```bash
# Send email
curl -X POST http://localhost:8000/api/v1/tracy/send-email

# Load search
curl http://localhost:8000/api/v1/tracy/load-search

# Process email
curl -X POST http://localhost:8000/api/v1/tracy/process-email

# Extract data
curl -X POST http://localhost:8000/api/v1/tracy/extract-data

# Get escalation milestones
curl http://localhost:8000/api/v1/tracy/escalation-milestones

# Run complete pipeline
curl -X POST http://localhost:8000/api/v1/tracy/pipeline
```

### Using the Swagger UI

Navigate to `http://localhost:8000/docs` for interactive API documentation.

## Viewing Workflow Execution

### Temporal Web UI

If you have Temporal UI running (default port 8080):
```
http://localhost:8080
```

You can view:
- Workflow execution history
- Activity results
- Task queue metrics
- Worker status

### Using Temporal CLI

```bash
# List workflows
temporal workflow list

# Describe a specific workflow
temporal workflow describe --workflow-id send-email-xxxxx

# Show workflow history
temporal workflow show --workflow-id send-email-xxxxx
```

## Project Structure

```
temporal-workflow-explorer/
├── .env                          # Environment variables
├── run_worker.py                 # Worker startup script
├── app/
│   ├── controllers/
│   │   └── actions_controller.py # FastAPI endpoints
│   └── temporal/
│       ├── __init__.py
│       ├── activities.py         # Temporal activities
│       ├── workflows.py          # Temporal workflows
│       ├── worker.py            # Worker configuration
│       └── client.py            # Temporal client utilities
```

## How It Works

### Direct Business Logic Flow
1. User calls business logic endpoint (e.g., `/api/v1/email/send`)
2. Endpoint executes business logic and returns response
3. No Temporal involvement - fast, synchronous response

### Temporal Workflow Flow
1. **Client Request**: User sends HTTP request to workflow endpoint (e.g., `/api/v1/tracy/send-email`)
2. **Workflow Creation**: Endpoint creates a unique workflow ID and starts a Temporal workflow
3. **Worker Polling**: The Temporal worker polls the task queue for new tasks
4. **Activity Execution**: Worker executes the activity which makes an HTTP call to the business logic endpoint
5. **Business Logic**: The business logic endpoint processes the request and returns data
6. **Activity Completion**: Activity receives the HTTP response and returns it to the workflow
7. **Result Return**: Workflow completes and returns result to the workflow endpoint
8. **HTTP Response**: FastAPI returns the result along with the workflow ID for tracking

### Benefits of This Architecture

**Business Logic Endpoints**:
- Can be tested independently
- Can be called directly without Temporal overhead
- Can be reused by different workflows
- Easy to mock for testing

**Temporal Activities**:
- Make HTTP calls to decouple from business logic
- Benefit from Temporal's retry policies
- Can call any HTTP service (internal or external APIs)
- Provide observability through Temporal UI

**Temporal Workflows**:
- Orchestrate multiple activities
- Provide reliability and fault tolerance
- Enable complex workflows with branching, loops, etc.
- Maintain workflow state across failures

## Troubleshooting

### Worker not connecting to Temporal

- Verify Temporal server is running: `docker ps` or check `localhost:7233`
- Check `.env` file configuration
- Ensure no firewall blocking port 7233

### Workflow execution timeout

- Check if worker is running
- Verify worker is listening on the correct task queue
- Check worker logs for errors

### Import errors

- Install dependencies: `pip install -e .`
- Verify Python version >= 3.10

## Next Steps

To customize the activities with real business logic:

1. Edit `app/temporal/activities.py` to implement actual email sending, data extraction, etc.
2. Add error handling and retry policies to activities
3. Implement more complex workflow orchestration in `app/temporal/workflows.py`
4. Add workflow input parameters for dynamic behavior
5. Configure Temporal retry policies and timeouts

## Benefits of Using Temporal

- **Reliability**: Automatic retries and failure handling
- **Durability**: Workflow state persisted across restarts
- **Visibility**: Full execution history and debugging
- **Scalability**: Horizontal scaling of workers
- **Versioning**: Safe workflow code updates
