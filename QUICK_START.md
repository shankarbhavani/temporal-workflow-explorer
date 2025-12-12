# Quick Start Guide

## Installation

1. **Install dependencies:**
   ```bash
   pip install -e .
   # or with uv
   uv pip install -e .
   ```

2. **Verify Temporal server is running:**
   ```bash
   # Option 1: Docker
   docker run -p 7233:7233 -p 8080:8080 temporalio/auto-setup

   # Option 2: Check if already running
   curl http://localhost:7233
   ```

## Running the Application

### Terminal 1: Start FastAPI Server
```bash
python main.py
```

Server will start at: `http://localhost:8000`
API docs available at: `http://localhost:8000/docs`

### Terminal 2: Start Temporal Worker
```bash
python run_worker.py
```

You should see:
```
Connected to Temporal server successfully!
Worker started and listening on task queue: email-task-queue
```

## Testing the Endpoints

### Option 1: Direct Business Logic (No Temporal)

Fast, synchronous calls to business logic:

```bash
# Send email
curl -X POST http://localhost:8000/api/v1/email/send

# Load search
curl http://localhost:8000/api/v1/email/load-search

# Process email
curl -X POST http://localhost:8000/api/v1/email/process

# Extract data
curl -X POST http://localhost:8000/api/v1/email/extract-data

# Escalation milestones
curl http://localhost:8000/api/v1/email/escalation-milestones
```

### Option 2: Via Temporal Workflows (With Retry & Orchestration)

Calls that go through Temporal for reliability:

```bash
# Send email via workflow
curl -X POST http://localhost:8000/api/v1/tracy/send-email

# Load search via workflow
curl http://localhost:8000/api/v1/tracy/load-search

# Process email via workflow
curl -X POST http://localhost:8000/api/v1/tracy/process-email

# Extract data via workflow
curl -X POST http://localhost:8000/api/v1/tracy/extract-data

# Escalation milestones via workflow
curl http://localhost:8000/api/v1/tracy/escalation-milestones

# Run complete pipeline
curl -X POST http://localhost:8000/api/v1/tracy/pipeline
```

### Response Differences

**Direct Call Response:**
```json
{"message": "Email sent"}
```

**Workflow Call Response:**
```json
{
  "workflow_id": "send-email-abc-123",
  "message": "Email sent"
}
```

The workflow response includes a `workflow_id` that you can use to track execution in Temporal UI.

## Viewing Workflow Execution

Open Temporal UI: `http://localhost:8080`

You can:
- View all workflow executions
- See activity execution details
- Check workflow history
- Monitor worker status
- Debug failed workflows

## Common Commands

### Check if services are running
```bash
# Check FastAPI
curl http://localhost:8000/health

# Check Temporal (should connect without error)
curl http://localhost:7233

# Check Temporal UI
open http://localhost:8080
```

### View logs
- FastAPI logs: In Terminal 1
- Worker logs: In Terminal 2
- Temporal UI: http://localhost:8080

## Next Steps

1. **Customize business logic** in `app/controllers/email_business_logic.py`
2. **Modify activities** in `app/temporal/activities.py` to change HTTP behavior
3. **Create new workflows** in `app/temporal/workflows.py` for complex orchestrations
4. **Add request/response models** for typed APIs
5. **Implement authentication** for production use

## Troubleshooting

### "Connection refused" errors

**Problem**: Worker cannot connect to Temporal
**Solution**: Ensure Temporal server is running on port 7233

### "404 Not Found" when activities call business endpoints

**Problem**: Activities cannot reach business logic endpoints
**Solution**:
- Verify FastAPI server is running
- Check `API_BASE_URL` in `.env` is correct
- Ensure business logic endpoints are registered in `app/main.py`

### Worker shows no activity

**Problem**: Worker is not picking up tasks
**Solution**:
- Verify worker is running (`python run_worker.py`)
- Check task queue name matches in `.env` and worker
- Look for errors in worker logs

### Workflow times out

**Problem**: Workflow execution exceeds timeout
**Solution**:
- Check activity timeouts in `workflows.py`
- Verify activities complete successfully
- Check business logic endpoint response times

## Architecture Summary

```
┌──────────────┐
│     User     │
└──────┬───────┘
       │
       ├─────────────────────┐
       │                     │
       ▼                     ▼
┌─────────────┐      ┌──────────────┐
│   Direct    │      │   Workflow   │
│  Endpoint   │      │   Endpoint   │
│ /email/*    │      │  /tracy/*    │
└──────┬──────┘      └──────┬───────┘
       │                     │
       │                     ▼
       │             ┌───────────────┐
       │             │   Temporal    │
       │             │   Workflow    │
       │             └───────┬───────┘
       │                     │
       │                     ▼
       │             ┌───────────────┐
       │             │   Activity    │
       │             │ (HTTP Client) │
       │             └───────┬───────┘
       │                     │
       │                     │
       ▼                     ▼
┌─────────────────────────────────┐
│    Business Logic Endpoint      │
│    (Actual Implementation)      │
└─────────────────────────────────┘
```

## File Structure Quick Reference

```
temporal-workflow-explorer/
├── .env                                    # Configuration
├── main.py                                 # FastAPI entry point
├── run_worker.py                          # Temporal worker entry
├── app/
│   ├── main.py                            # FastAPI app setup
│   ├── controllers/
│   │   ├── email_business_logic.py        # Business logic endpoints
│   │   └── actions_controller.py          # Workflow trigger endpoints
│   └── temporal/
│       ├── activities.py                  # HTTP call activities
│       ├── workflows.py                   # Workflow definitions
│       ├── worker.py                      # Worker configuration
│       └── client.py                      # Temporal client utils
```
