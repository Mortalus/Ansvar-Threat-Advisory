"""
Phase 2: Workflow Execution Celery Tasks (Refactored)
Handles synchronous workflow execution with comprehensive logging and defensive programming.
"""

import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from celery import Task
from sqlalchemy import select

from app.celery_app import celery_app
from app.database import get_async_session
from app.models.workflow import WorkflowRun, WorkflowStatus
from app.services.workflow_service import WorkflowService
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def run_async_in_celery(coro):
    """
    Helper function to run async coroutines in Celery tasks.
    Creates a new event loop for each task execution with proper cleanup.
    """
    logger.debug("🔄 Creating event loop for async operation in Celery task")
    
    try:
        # Create a new event loop for this task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(coro)
            logger.debug("✅ Successfully completed async operation in Celery task")
            return result
        except Exception as e:
            logger.error(f"❌ Async operation failed in Celery task: {str(e)}", exc_info=True)
            raise
        finally:
            loop.close()
            logger.debug("🧹 Cleaned up event loop")
            
    except Exception as e:
        logger.error(f"💥 Fatal error in async wrapper: {str(e)}", exc_info=True)
        raise


class DefensiveWorkflowTask(Task):
    """Base task class with comprehensive logging, error handling, and defensive programming."""
    
    def __init__(self):
        super().__init__()
        self.workflow_service = None
    
    def __call__(self, *args, **kwargs):
        task_id = getattr(self.request, 'id', 'unknown')
        task_name = getattr(self, 'name', 'unknown')
        
        logger.info(f"🚀 CELERY TASK START: {task_name} (ID: {task_id})")
        logger.info(f"📝 Task arguments: {args}")
        logger.info(f"🔧 Task kwargs: {kwargs}")
        
        start_time = datetime.utcnow()
        
        try:
            # Initialize service if needed
            if not self.workflow_service:
                logger.debug("🏗️ Initializing WorkflowService")
                self.workflow_service = WorkflowService()
            
            # Execute the task
            logger.info(f"⚡ Executing task logic for {task_name}")
            result = self.run(*args, **kwargs)
            
            # Log successful completion
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"✅ CELERY TASK SUCCESS: {task_name} completed in {duration:.2f}s")
            logger.debug(f"📊 Task result: {result}")
            
            return result
            
        except Exception as e:
            # Log detailed error information
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"❌ CELERY TASK FAILED: {task_name} after {duration:.2f}s")
            logger.error(f"💥 Error type: {type(e).__name__}")
            logger.error(f"📜 Error message: {str(e)}")
            logger.error(f"🔍 Full traceback:", exc_info=True)
            
            # Re-raise the exception to let Celery handle retries
            raise


@celery_app.task(base=DefensiveWorkflowTask, bind=True, name='workflow.execute_run')
def execute_workflow_run(self, run_id: str) -> Dict[str, Any]:
    """
    Execute an entire workflow run with comprehensive logging and error handling.
    
    Args:
        run_id: Database ID (integer) of the workflow run
    
    Returns:
        Status of workflow execution start
    """
    logger.info(f"🏃 WORKFLOW EXECUTION START: Run ID {run_id}")
    
    async def _execute_workflow_async():
        """Inner async function to handle workflow execution."""
        logger.debug("🔍 Getting database session for workflow execution")
        
        async for db in get_async_session():
            try:
                logger.info(f"📊 Fetching workflow run from database: ID {run_id}")
                
                # Get the run by database ID (integer)
                result = await db.execute(
                    select(WorkflowRun).where(WorkflowRun.id == int(run_id))
                )
                run = result.scalar_one_or_none()
                
                if not run:
                    logger.error(f"❌ Workflow run not found: ID {run_id}")
                    raise ValueError(f"Run {run_id} not found")
                
                logger.info(f"✅ Found workflow run: {run.run_id} (Status: {run.status})")
                
                # Check run status
                if run.status != WorkflowStatus.CREATED:
                    logger.warning(f"⚠️ Run is not in CREATED state: {run.status}")
                    return {
                        'status': 'skipped',
                        'reason': f'Run already in {run.status} state',
                        'run_id': str(run.run_id)
                    }
                
                # Update status to RUNNING
                logger.info("🔄 Updating run status to RUNNING")
                run.status = WorkflowStatus.RUNNING
                run.started_at = datetime.utcnow()
                await db.commit()
                
                logger.info("📤 Triggering individual step execution")
                
                # Use the workflow service to execute ALL steps in a loop
                workflow_service = WorkflowService()
                executed_steps = []
                
                # CRITICAL FIX: Loop until all steps are executed or run is terminal
                while True:
                    logger.info(f"🔄 Attempting to execute next step for run {run.run_id}")
                    
                    executed_step = await workflow_service.execute_next_step(
                        db=db, 
                        run_id=run.run_id,  # Use UUID for the service
                        user_prompt_override=None
                    )
                    
                    if executed_step:
                        logger.info(f"✅ Successfully executed step: {executed_step.step_id}")
                        executed_steps.append({
                            'step_id': executed_step.step_id,
                            'status': executed_step.status.value if hasattr(executed_step.status, 'value') else str(executed_step.status)
                        })
                        
                        # Continue to next step
                        continue
                    else:
                        # No more steps to execute - check if run is complete
                        await db.refresh(run)
                        logger.info(f"📊 Run status after execution: {run.status}")
                        
                        if run.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
                            logger.info(f"🎉 Workflow run {run.run_id} reached terminal state: {run.status}")
                            return {
                                'status': 'completed',
                                'run_id': str(run.run_id),
                                'final_status': run.status.value if hasattr(run.status, 'value') else str(run.status),
                                'executed_steps': executed_steps,
                                'total_steps_executed': len(executed_steps)
                            }
                        else:
                            logger.warning(f"⚠️ No more steps but run is still {run.status}")
                            # Try one more time to complete the run
                            await workflow_service.execute_next_step(db=db, run_id=run.run_id, user_prompt_override=None)
                            await db.refresh(run)
                            
                            return {
                                'status': 'execution_complete',
                                'run_id': str(run.run_id),
                                'final_status': run.status.value if hasattr(run.status, 'value') else str(run.status),
                                'executed_steps': executed_steps,
                                'total_steps_executed': len(executed_steps)
                            }
                
            except Exception as e:
                logger.error(f"💥 Database error in workflow execution: {str(e)}", exc_info=True)
                await db.rollback()
                raise
            finally:
                await db.close()
                logger.debug("🧹 Database session closed")
    
    # Execute the async function using our helper
    try:
        return run_async_in_celery(_execute_workflow_async())
    except Exception as e:
        logger.error(f"💥 Workflow execution completely failed: {str(e)}", exc_info=True)
        return {
            'status': 'failed',
            'error': str(e),
            'run_id': run_id
        }


@celery_app.task(base=DefensiveWorkflowTask, bind=True, name='workflow.execute_step')
def execute_workflow_step(
    self,
    run_id: str,
    step_id: str,
    prompt_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a single workflow step with comprehensive logging.
    
    Args:
        run_id: UUID string of the workflow run
        step_id: ID of the step to execute
        prompt_override: Optional user prompt override
    
    Returns:
        Execution result with status and artifacts
    """
    logger.info(f"🔧 STEP EXECUTION START: Run {run_id}, Step {step_id}")
    
    async def _execute_step_async():
        """Inner async function to handle step execution."""
        async for db in get_async_session():
            try:
                logger.info(f"🔍 Using workflow service for step execution")
                
                workflow_service = WorkflowService()
                result = await workflow_service.execute_next_step(
                    db=db,
                    run_id=uuid.UUID(run_id),
                    user_prompt_override=prompt_override
                )
                
                if result:
                    logger.info(f"✅ Step executed successfully: {result.step_id}")
                    return {
                        'status': 'success',
                        'step_id': result.step_id,
                        'step_status': result.status.value,
                        'execution_time_ms': result.execution_time_ms
                    }
                else:
                    logger.warning("⚠️ No step was executed")
                    return {
                        'status': 'no_steps_ready',
                        'message': 'No steps are ready for execution'
                    }
                    
            except Exception as e:
                logger.error(f"💥 Step execution error: {str(e)}", exc_info=True)
                await db.rollback()
                raise
            finally:
                await db.close()
    
    try:
        return run_async_in_celery(_execute_step_async())
    except Exception as e:
        logger.error(f"💥 Step execution completely failed: {str(e)}", exc_info=True)
        return {
            'status': 'failed',
            'error': str(e),
            'run_id': run_id,
            'step_id': step_id
        }


# Export the tasks for import
__all__ = ['execute_workflow_run', 'execute_workflow_step']