# Cascading Workflows Guide

This guide explains how to use the 3 cascading workflows that automatically trigger each other.

## 🔄 Workflow Cascade Overview

```
Workflow 1: Load and Email
├── load_search
├── send_email
├── sleep_activity (10 seconds)
└── start_child_workflow → triggers Workflow 2
                            ↓
                    Workflow 2: Process Email
                    ├── process_email
                    ├── sleep_activity (5 seconds)
                    └── start_child_workflow → triggers Workflow 3
                                                ↓
                                        Workflow 3: Extract and Update
                                        ├── extract_data
                                        └── update_load
```

## 📁 Workflow Files

### 1. Workflow 1: `workflow_1_load_and_email.yaml`
**Purpose:** Initial data loading and email sending

**Activities:**
- `load_search` - Search for loads
- `send_email` - Send notification email
- `sleep_activity(10)` - Wait 10 seconds
- `start_child_workflow("workflow_2_process")` - Trigger Workflow 2

### 2. Workflow 2: `workflow_2_process.yaml`
**Purpose:** Email processing

**Activities:**
- `process_email` - Process and classify email
- `sleep_activity(5)` - Wait 5 seconds
- `start_child_workflow("workflow_3_extract_and_update")` - Trigger Workflow 3

### 3. Workflow 3: `workflow_3_extract_and_update.yaml`
**Purpose:** Data extraction and load updating (final step)

**Activities:**
- `extract_data` - Extract data from email
- `update_load` - Update load status

## 🚀 API Endpoints

### Start the Cascade
```bash
POST /api/v1/workflows/workflow-1
```

This will:
1. Execute Workflow 1
2. Automatically trigger Workflow 2 after 10 seconds
3. Automatically trigger Workflow 3 after 5 more seconds

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/workflows/workflow-1
```

**Response:**
```json
{
  "workflow_id": "workflow-1-abc-123",
  "workflow_name": "Workflow 1: Load and Email",
  "yaml_definition": "/path/to/workflow_1_load_and_email.yaml",
  "search_results": [1, 2, 3, 4],
  "email_status": "Email sent",
  "sleep_result": "slept for 10 seconds",
  "workflow_2_result": {
    "child_workflow_id": "workflow_2_process-def-456",
    "child_workflow_name": "workflow_2_process",
    "child_result": {
      "classification": "classified",
      "sleep_result": "slept for 5 seconds",
      "workflow_3_result": {
        "child_workflow_id": "workflow_3_extract_and_update-ghi-789",
        "child_workflow_name": "workflow_3_extract_and_update",
        "child_result": {
          "extracted_data": "extracted data",
          "update_status": "load updated"
        },
        "status": "completed"
      }
    },
    "status": "completed"
  },
  "workflow_status": "completed"
}
```

### Run Individual Workflows

You can also trigger each workflow independently:

#### Workflow 2 Only
```bash
curl -X POST http://localhost:8000/api/v1/workflows/workflow-2
```

#### Workflow 3 Only
```bash
curl -X POST http://localhost:8000/api/v1/workflows/workflow-3
```

## ⏱️ Execution Timeline

```
Time    Workflow        Activity
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
00:00   Workflow 1      load_search
00:01   Workflow 1      send_email
00:02   Workflow 1      sleep_activity (10s)
        ↓               ⏳ waiting...
00:12   Workflow 1      start_child_workflow
00:12   Workflow 2      process_email
00:13   Workflow 2      sleep_activity (5s)
        ↓               ⏳ waiting...
00:18   Workflow 2      start_child_workflow
00:18   Workflow 3      extract_data
00:19   Workflow 3      update_load
00:20   ✅ Complete     All workflows done
```

**Total Duration:** ~20 seconds

## 🔍 View in Temporal UI

Open http://localhost:8080 to see:

1. **Main Workflow:**
   - ID: `workflow-1-{uuid}`
   - Type: `DSLWorkflow`
   - Shows all activities including child workflow triggers

2. **Child Workflow 2:**
   - ID: `workflow_2_process-{uuid}`
   - Parent: `workflow-1-{uuid}`
   - Shows process_email and next trigger

3. **Child Workflow 3:**
   - ID: `workflow_3_extract_and_update-{uuid}`
   - Parent: `workflow_2_process-{uuid}`
   - Shows final data extraction and update

## 🛠️ How Child Workflow Triggering Works

### The Magic Activity: `start_child_workflow`

**In YAML:**
```yaml
- activity:
    name: start_child_workflow
    arguments:
      - "workflow_2_process"    # Name of YAML file (without .yaml)
    result: workflow_2_result
```

**What happens:**
1. Activity receives workflow name: `"workflow_2_process"`
2. Loads YAML: `app/temporal/workflow_2_process.yaml`
3. Parses YAML into DSL workflow input
4. Creates new Temporal client
5. Executes child workflow with unique ID
6. Waits for child workflow to complete
7. Returns child workflow result

**Implementation:**
```python
@activity.defn(name="start_child_workflow")
async def start_child_workflow_activity(yaml_workflow_name: str) -> dict:
    # Load YAML workflow definition
    yaml_path = get_default_workflow_path(yaml_workflow_name)
    workflow_input = load_workflow_definition(yaml_path)

    # Execute child workflow
    result = await client.execute_workflow(
        DSLWorkflow.run,
        workflow_input,
        id=f"{yaml_workflow_name}-{uuid4()}",
        task_queue=task_queue,
    )

    return {
        "child_workflow_id": workflow_id,
        "child_workflow_name": yaml_workflow_name,
        "child_result": result,
        "status": "completed"
    }
```

## 📊 Result Structure

When Workflow 1 completes, the result contains nested child workflow results:

```json
{
  "workflow_id": "workflow-1-xxx",
  "search_results": [...],      // From Workflow 1
  "email_status": "...",         // From Workflow 1
  "sleep_result": "...",         // From Workflow 1
  "workflow_2_result": {         // From child workflow 2
    "child_workflow_id": "workflow_2_process-yyy",
    "child_result": {
      "classification": "...",    // From Workflow 2
      "sleep_result": "...",      // From Workflow 2
      "workflow_3_result": {      // From child workflow 3
        "child_workflow_id": "workflow_3_extract_and_update-zzz",
        "child_result": {
          "extracted_data": "...", // From Workflow 3
          "update_status": "..."   // From Workflow 3
        }
      }
    }
  }
}
```

## 🎯 Use Cases

### Sequential Data Pipeline
```yaml
# Workflow 1: Fetch data
- activity: { name: fetch_data, result: raw_data }
- activity: { name: start_child_workflow, arguments: ["workflow_2_transform"] }

# Workflow 2: Transform data
- activity: { name: transform_data, result: clean_data }
- activity: { name: start_child_workflow, arguments: ["workflow_3_load"] }

# Workflow 3: Load to database
- activity: { name: load_to_db, result: load_status }
```

### Long-Running Process with Checkpoints
```yaml
# Workflow 1: Initial processing (fast)
- activity: { name: quick_validation }
- activity: { name: start_child_workflow, arguments: ["workflow_2_processing"] }

# Workflow 2: Heavy processing (slow)
- activity: { name: heavy_computation }
- activity: { name: start_child_workflow, arguments: ["workflow_3_finalize"] }

# Workflow 3: Finalization (fast)
- activity: { name: cleanup }
- activity: { name: notify_completion }
```

### Error Isolation
Each workflow is independent, so:
- If Workflow 1 fails, Workflow 2 never starts
- If Workflow 2 fails, Workflow 3 never starts
- Each workflow has its own retry policy
- Failed workflows don't affect completed parent workflows

## 🧪 Testing

### Test the Full Cascade
```bash
# Start Workflow 1 (will trigger all 3)
curl -X POST http://localhost:8000/api/v1/workflows/workflow-1

# Watch logs to see cascade happen
# Check Temporal UI at http://localhost:8080
```

### Test Individual Workflows
```bash
# Test Workflow 2 only
curl -X POST http://localhost:8000/api/v1/workflows/workflow-2

# Test Workflow 3 only
curl -X POST http://localhost:8000/api/v1/workflows/workflow-3
```

### Verify Results
```bash
# Get workflow result
curl http://localhost:8000/api/v1/workflows/{workflow-id}/result
```

## 🔧 Modifying the Cascade

### Change Wait Times
Edit the YAML files:

**Workflow 1:**
```yaml
- activity:
    name: sleep_activity
    arguments:
      - "20"  # Change from 10 to 20 seconds
```

**Workflow 2:**
```yaml
- activity:
    name: sleep_activity
    arguments:
      - "10"  # Change from 5 to 10 seconds
```

### Add More Steps
```yaml
# In workflow_1_load_and_email.yaml
elements:
  - activity: { name: load_search, result: search_results }
  - activity: { name: send_email, result: email_status }
  - activity: { name: validate_data, result: validation }  # New step!
  - activity: { name: sleep_activity, arguments: ["10"] }
  - activity: { name: start_child_workflow, arguments: ["workflow_2_process"] }
```

### Chain More Workflows
Create `workflow_4_notification.yaml`:
```yaml
variables:
  final_status: ""

root:
  sequence:
    elements:
      - activity:
          name: send_notification
          result: final_status
```

Update Workflow 3:
```yaml
# In workflow_3_extract_and_update.yaml
elements:
  - activity: { name: extract_data, result: extracted_data }
  - activity: { name: update_load, result: update_status }
  - activity: { name: start_child_workflow, arguments: ["workflow_4_notification"] }  # Add this!
```

## 🚨 Important Notes

### Activity Timeout
The `start_child_workflow` activity has a 1-minute timeout by default. If child workflows take longer, increase the timeout in `dsl_workflow.py`:

```python
result = await workflow.execute_activity(
    activity_name,
    args=args,
    start_to_close_timeout=timedelta(minutes=5),  # Increase from 1 to 5 minutes
)
```

### Circular Dependencies
⚠️ **Don't create circular workflows:**
```yaml
# ❌ BAD: Workflow 1 triggers 2, which triggers 1 again
# This creates an infinite loop!

# Workflow 1
- activity: { name: start_child_workflow, arguments: ["workflow_2"] }

# Workflow 2
- activity: { name: start_child_workflow, arguments: ["workflow_1"] }  # Don't do this!
```

### Nested Depth
Keep cascades reasonable (3-5 levels max). Deeply nested workflows are hard to debug and monitor.

## 📚 Advanced Patterns

### Conditional Cascade
```yaml
# Workflow 1: Validate and route
- activity: { name: validate_data, result: is_valid }
- activity: { name: route_based_on_validation, arguments: ["is_valid"], result: next_workflow }
- activity: { name: start_child_workflow, arguments: ["next_workflow"] }
```

### Parallel Child Workflows
```yaml
# Start multiple workflows at once
- parallel:
    branches:
      - activity: { name: start_child_workflow, arguments: ["workflow_2a"] }
      - activity: { name: start_child_workflow, arguments: ["workflow_2b"] }
      - activity: { name: start_child_workflow, arguments: ["workflow_2c"] }
```

## 📖 Related Documentation

- [YAML_WORKFLOWS.md](YAML_WORKFLOWS.md) - YAML workflow structure
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Implementation details
- [README.md](README.md) - Project overview

---

## 🎉 Ready to Test!

1. **Start the worker:** `python run_worker.py`
2. **Start the API:** `python main.py`
3. **Trigger the cascade:** `curl -X POST http://localhost:8000/api/v1/workflows/workflow-1`
4. **Watch it flow:** Open http://localhost:8080 to see all 3 workflows execute!
