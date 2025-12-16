"""Temporal workflows for email processing."""
import asyncio
from datetime import timedelta
from typing import List
from temporalio import workflow

# Import activities
with workflow.unsafe.imports_passed_through():
    from app.temporal.activities import (
        send_email_activity,
        load_search_activity,
        process_email_activity,
        extract_data_activity,
        get_escalation_milestones_activity,
        update_load_activity,
    )


@workflow.defn(name="LoadProcessingWorkflow")
class LoadProcessingWorkflow:
    """
    Load processing workflow that orchestrates the complete load handling flow.

    Steps:
    1. Search for loads
    2. Send email
    3. Wait for 20 seconds
    4. Process email
    5. Extract data
    6. Update load
    """

    @workflow.run
    async def run(self) -> dict:
        """
        Execute the complete load processing workflow.

        Returns:
            Results from all stages of the workflow
        """
        # Get workflow execution information
        info = workflow.info()

        # Log workflow execution details
        workflow.logger.info(
            f"Workflow Execution Details - "
            f"Workflow ID: {info.workflow_id}, "
            f"Run ID: {info.run_id}, "
            f"Workflow Type: {info.workflow_type}, "
            f"Attempt: {info.attempt}"
        )

        workflow.logger.info("Starting LoadProcessingWorkflow")

        # Step 1: Search for loads
        workflow.logger.info("Executing activity: load_search")
        search_results = await workflow.execute_activity(
            load_search_activity,
            start_to_close_timeout=timedelta(seconds=30),
        )
        workflow.logger.info(f"Activity completed: load_search - Result: {search_results}")

        # Step 2: Send email
        workflow.logger.info("Executing activity: send_email")
        email_status = await workflow.execute_activity(
            send_email_activity,
            start_to_close_timeout=timedelta(seconds=30),
        )
        workflow.logger.info(f"Activity completed: send_email - Result: {email_status}")

        # Step 3: Wait for 20 seconds
        workflow.logger.info("Waiting for 20 seconds...")
        await asyncio.sleep(20)
        workflow.logger.info("Wait completed")

        # Step 4: Process email
        workflow.logger.info("Executing activity: process_email")
        classification = await workflow.execute_activity(
            process_email_activity,
            start_to_close_timeout=timedelta(seconds=30),
        )
        workflow.logger.info(f"Activity completed: process_email - Result: {classification}")

        # Step 5: Extract data
        workflow.logger.info("Executing activity: extract_data")
        extracted_data = await workflow.execute_activity(
            extract_data_activity,
            start_to_close_timeout=timedelta(seconds=30),
        )
        workflow.logger.info(f"Activity completed: extract_data - Result: {extracted_data}")

        # Step 6: Update load
        workflow.logger.info("Executing activity: update_load")
        update_status = await workflow.execute_activity(
            update_load_activity,
            start_to_close_timeout=timedelta(seconds=30),
        )
        workflow.logger.info(f"Activity completed: update_load - Result: {update_status}")

        # Log workflow completion
        workflow.logger.info(
            f"Workflow Completed Successfully - "
            f"Workflow ID: {info.workflow_id}, "
            f"Run ID: {info.run_id}"
        )

        return {
            "workflow_id": info.workflow_id,
            "run_id": info.run_id,
            "workflow_type": info.workflow_type,
            "attempt": info.attempt,
            "search_results": search_results,
            "email_status": email_status,
            "classification": classification,
            "extracted_data": extracted_data,
            "update_status": update_status,
            "workflow_status": "completed",
        }
