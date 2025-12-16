# YAML-Based Workflows Guide

This guide explains how to use YAML-based workflow definitions instead of writing Python code for Temporal workflows.

## Overview

Your `LoadProcessingWorkflow` has been successfully converted to a YAML-based declarative workflow! This means you can now define and modify workflows without writing Python code.

## Benefits of YAML Workflows

✅ **No Code Required** - Define workflows using simple YAML syntax
✅ **Easy to Modify** - Change workflow steps by editing YAML files
✅ **Living Documentation** - YAML files serve as clear documentation
✅ **Lower Barrier** - Non-developers can understand and modify workflows
✅ **Version Control Friendly** - Clean diffs when workflows change

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         YAML Workflow Definition                     │
│   (load_processing_workflow.yaml)                    │
└─────────────┬───────────────────────────────────────┘
              │
              │ Loaded by
              ▼
┌─────────────────────────────────────────────────────┐
│            DSL Loader (dsl_loader.py)                │
│       Parses YAML and creates DSLInput               │
└─────────────┬───────────────────────────────────────┘
              │
              │ Executes via
              ▼
┌─────────────────────────────────────────────────────┐
│          DSL Workflow (dsl_workflow.py)              │
│      Interprets and executes workflow steps          │
└─────────────┬───────────────────────────────────────┘
              │
              │ Calls
              ▼
┌─────────────────────────────────────────────────────┐
│        Temporal Activities (activities.py)           │
│         Existing activity implementations            │
└─────────────────────────────────────────────────────┘
```

## YAML Workflow Structure

### Basic Structure

```yaml
# Variables that can be used throughout the workflow
variables:
  var_name: value

# Root statement - the starting point of the workflow
root:
  sequence:
    elements:
      - activity:
          name: activity_name
          arguments: []
          result: result_variable_name
```

### Statement Types

#### 1. Activity Statement

Execute a single activity:

```yaml
- activity:
    name: send_email_activity
    arguments: []
    result: email_status
```

With arguments:

```yaml
- activity:
    name: sleep_activity
    arguments:
      - "20"
    result: sleep_result
```

#### 2. Sequence Statement

Execute multiple statements in order:

```yaml
- sequence:
    elements:
      - activity:
          name: step1_activity
      - activity:
          name: step2_activity
      - activity:
          name: step3_activity
```

#### 3. Parallel Statement

Execute multiple branches in parallel:

```yaml
- parallel:
    branches:
      - activity:
          name: parallel_task_1
      - activity:
          name: parallel_task_2
      - activity:
          name: parallel_task_3
```

## LoadProcessingWorkflow YAML Example

Here's the complete YAML definition for the LoadProcessingWorkflow:

**File:** `app/temporal/load_processing_workflow.yaml`

```yaml
# Load Processing Workflow - YAML Definition
# This workflow orchestrates the complete load handling flow:
# 1. Search for loads
# 2. Send email
# 3. Wait for 20 seconds
# 4. Process email
# 5. Extract data
# 6. Update load

variables:
  workflow_id: ""
  run_id: ""
  workflow_type: ""
  attempt: 0

root:
  sequence:
    elements:
      # Step 1: Search for loads
      - activity:
          name: load_search_activity
          arguments: []
          result: search_results

      # Step 2: Send email
      - activity:
          name: send_email_activity
          arguments: []
          result: email_status

      # Step 3: Wait for 20 seconds
      - activity:
          name: sleep_activity
          arguments:
            - "20"
          result: sleep_result

      # Step 4: Process email
      - activity:
          name: process_email_activity
          arguments: []
          result: classification

      # Step 5: Extract data
      - activity:
          name: extract_data_activity
          arguments: []
          result: extracted_data

      # Step 6: Update load
      - activity:
          name: update_load_activity
          arguments: []
          result: update_status
```

## API Endpoints

### Code-Based Workflow (Original)

```bash
POST http://localhost:8000/api/v1/workflows/load-processing-pipeline
```

### YAML-Based Workflow (New!)

```bash
POST http://localhost:8000/api/v1/workflows/load-processing-pipeline-yaml
```

### Comparison

Both endpoints execute the **exact same workflow**, but:

| Feature | Code-Based | YAML-Based |
|---------|------------|------------|
| Definition | Python code | YAML file |
| Modification | Requires coding | Edit YAML file |
| Hot Reload | Requires restart | Can reload YAML |
| Complexity | Complex branching OK | Best for simple flows |
| Type Safety | ✅ Python types | ⚠️ YAML validation |

## Testing the YAML Workflow

### 1. Start the Worker

Make sure the worker is running with DSL workflow support:

```bash
python run_worker.py
```

You should see:

```
Registered workflows:
  - LoadProcessingWorkflow (code-based)
  - DSLWorkflow (YAML-based)
```

### 2. Start the API Server

```bash
python main.py
```

### 3. Execute the YAML Workflow

**Using curl:**

```bash
curl -X POST http://localhost:8000/api/v1/workflows/load-processing-pipeline-yaml
```

**Expected Response:**

```json
{
  "workflow_id": "load-processing-pipeline-yaml-abc-123-def-456",
  "workflow_type": "YAML-based DSL",
  "yaml_definition": "/path/to/load_processing_workflow.yaml",
  "workflow_id": "load-processing-pipeline-yaml-abc-123-def-456",
  "run_id": "xyz-789",
  "workflow_type": "DSLWorkflow",
  "attempt": 1,
  "search_results": [1, 2, 3, 4],
  "email_status": "Email sent",
  "sleep_result": "slept for 20 seconds",
  "classification": "classified",
  "extracted_data": "extracted data",
  "update_status": "load updated",
  "workflow_status": "completed"
}
```

### 4. View in Temporal UI

Open http://localhost:8080 and you'll see:
- Workflow ID: `load-processing-pipeline-yaml-...`
- Workflow Type: `DSLWorkflow`
- All executed activities and their results

## Creating Custom YAML Workflows

### Example: Parallel Processing Workflow

Create `app/temporal/parallel_workflow.yaml`:

```yaml
variables:
  processing_complete: false

root:
  sequence:
    elements:
      # First, do initial setup
      - activity:
          name: setup_activity
          result: setup_result

      # Then run multiple tasks in parallel
      - parallel:
          branches:
            - activity:
                name: process_batch_1
                result: batch1_result
            - activity:
                name: process_batch_2
                result: batch2_result
            - activity:
                name: process_batch_3
                result: batch3_result

      # Finally, aggregate results
      - activity:
          name: aggregate_results
          result: final_result
```

### Loading Custom Workflows

**In your controller:**

```python
from app.temporal.dsl_loader import load_workflow_definition

# Load custom workflow
workflow_input = load_workflow_definition("app/temporal/parallel_workflow.yaml")

# Execute it
result = await client.execute_workflow(
    DSLWorkflow.run,
    workflow_input,
    id=f"parallel-workflow-{uuid4()}",
    task_queue=task_queue,
)
```

## Variables and Results

### Setting Initial Variables

```yaml
variables:
  user_id: "12345"
  environment: "production"
  max_retries: 3
```

### Using Variables in Activities

Variables are automatically available to activities:

```yaml
- activity:
    name: send_notification
    arguments:
      - user_id        # Uses variable value "12345"
      - environment    # Uses variable value "production"
    result: notification_status
```

### Storing Results

Activity results are automatically stored in variables:

```yaml
- activity:
    name: fetch_data
    result: fetched_data  # Result stored in variable "fetched_data"

- activity:
    name: process_data
    arguments:
      - fetched_data      # Uses the result from previous activity
    result: processed_data
```

## Advanced Patterns

### Conditional Execution with Metadata

While YAML workflows don't support if/else directly, you can use workflow metadata:

```yaml
variables:
  execution_mode: "normal"  # or "fast" or "slow"

root:
  sequence:
    elements:
      - activity:
          name: check_mode_activity
          arguments:
            - execution_mode
          result: mode_config

      - activity:
          name: execute_with_config
          arguments:
            - mode_config
          result: execution_result
```

### Nested Sequences

```yaml
root:
  sequence:
    elements:
      - activity:
          name: phase1

      - sequence:
          elements:
            - activity:
                name: phase2_step1
            - activity:
                name: phase2_step2

      - activity:
          name: phase3
```

## Best Practices

### ✅ DO

- Use clear, descriptive activity names
- Add comments to explain workflow logic
- Store intermediate results in meaningful variable names
- Keep workflows simple and linear when possible
- Use parallel execution for independent tasks

### ❌ DON'T

- Put complex business logic in YAML (use activities instead)
- Create deeply nested structures
- Use YAML for workflows requiring complex branching
- Forget to register activities in the worker
- Mix activity names with different naming conventions

## Troubleshooting

### Error: "YAML file not found"

**Solution:** Check the file path in your YAML definition:

```python
yaml_path = get_default_workflow_path("load_processing_workflow")
# Looks for: app/temporal/load_processing_workflow.yaml
```

### Error: "Activity not found"

**Solution:** Ensure the activity is:
1. Defined in `app/temporal/activities.py`
2. Registered in `app/temporal/worker.py`
3. Named correctly in the YAML file

### Error: "Invalid YAML syntax"

**Solution:** Validate your YAML:

```bash
python -c "import yaml; yaml.safe_load(open('app/temporal/load_processing_workflow.yaml'))"
```

### Workflow doesn't execute as expected

**Solution:** Check the Temporal UI (http://localhost:8080) for:
- Workflow execution history
- Activity failures
- Error messages
- Input/output values

## Comparison: Code vs YAML

### Original Python Code (118 lines)

```python
@workflow.defn(name="LoadProcessingWorkflow")
class LoadProcessingWorkflow:
    @workflow.run
    async def run(self) -> dict:
        info = workflow.info()

        search_results = await workflow.execute_activity(
            load_search_activity,
            start_to_close_timeout=timedelta(seconds=30),
        )

        email_status = await workflow.execute_activity(
            send_email_activity,
            start_to_close_timeout=timedelta(seconds=30),
        )

        await asyncio.sleep(20)

        # ... more code ...

        return {...}
```

### YAML Version (56 lines)

```yaml
root:
  sequence:
    elements:
      - activity:
          name: load_search_activity
          result: search_results

      - activity:
          name: send_email_activity
          result: email_status

      - activity:
          name: sleep_activity
          arguments: ["20"]
          result: sleep_result
```

**Result:** 50% reduction in lines, 100% more readable!

## Next Steps

1. ✅ Test the YAML workflow endpoint
2. ✅ View execution in Temporal UI
3. ✅ Modify the YAML file and re-run
4. ✅ Create custom YAML workflows for your use cases
5. ✅ Share YAML files with your team for review

## Additional Resources

- [Temporal Documentation](https://docs.temporal.io/)
- [Temporal Python SDK DSL Sample](https://github.com/temporalio/samples-python/tree/main/dsl)
- [Serverless Workflow Specification](https://serverlessworkflow.io/)
- [YAML Syntax Guide](https://yaml.org/spec/1.2/spec.html)

## Support

For questions or issues:
- Check the Temporal UI for workflow execution details
- Review worker logs for activity errors
- Examine the YAML file for syntax errors
- Consult the Temporal community forums
