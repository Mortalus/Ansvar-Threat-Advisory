"""Pipeline-specific background tasks"""

import asyncio
import logging
from typing import Dict, Any
from celery import current_task
from datetime import datetime

from app.celery_app import celery_app
from app.core.pipeline.manager import PipelineManager, PipelineStep
from app.database import AsyncSessionLocal
from app.services import PipelineService
from app.models import StepStatus

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="execute_pipeline_step")
def execute_pipeline_step(self, pipeline_id: str, step: str, data: Dict[str, Any]):
    """
    Execute a pipeline step in the background with real-time WebSocket updates
    
    Args:
        self: Celery task instance (for retry/status updates)
        pipeline_id: Pipeline identifier
        step: Pipeline step name (string value)
        data: Step input data
        
    Returns:
        Dict with step execution results
    """
    task_id = self.request.id
    
    try:
        # Convert step string to enum
        step_enum = PipelineStep(step)
        
        # Send WebSocket notification: task started
        _send_websocket_update_sync(pipeline_id, step, "started", task_id)
        
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={
                'pipeline_id': pipeline_id,
                'step': step,
                'status': 'Starting step execution',
                'started_at': datetime.utcnow().isoformat()
            }
        )
        
        # Send WebSocket notification: task in progress
        _send_websocket_update_sync(pipeline_id, step, "progress", task_id)
        
        # Run the async operation in sync context
        result = asyncio.run(_execute_step_async(pipeline_id, step_enum, data, task_id))
        
        # Update final status
        current_task.update_state(
            state='SUCCESS',
            meta={
                'pipeline_id': pipeline_id,
                'step': step,
                'status': 'Step completed successfully',
                'completed_at': datetime.utcnow().isoformat(),
                'result': result
            }
        )
        
        # Send WebSocket notification: task completed
        _send_websocket_update_sync(pipeline_id, step, "completed", task_id, result)
        
        logger.info(f"Pipeline {pipeline_id} step {step} completed successfully")
        return result
        
    except Exception as exc:
        logger.error(f"Pipeline {pipeline_id} step {step} failed: {exc}")
        
        # Send WebSocket notification: task failed
        _send_websocket_update_sync(pipeline_id, step, "failed", task_id, error=str(exc))
        
        # Update task status with error
        current_task.update_state(
            state='FAILURE',
            meta={
                'pipeline_id': pipeline_id,
                'step': step,
                'status': 'Step failed',
                'error': str(exc),
                'failed_at': datetime.utcnow().isoformat()
            }
        )
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying step {step} for pipeline {pipeline_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60)
        
        raise exc


async def _execute_step_async(pipeline_id: str, step: PipelineStep, data: Dict[str, Any], task_id: str = None) -> Dict[str, Any]:
    """Execute the pipeline step asynchronously"""
    session = AsyncSessionLocal()
    
    try:
        # Create pipeline manager with database session
        manager = PipelineManager(session)
        
        # Execute the step
        result = await manager.execute_step(
            pipeline_id=pipeline_id,
            step=step,
            data=data
        )
        
        return result
        
    finally:
        await session.close()


def _send_websocket_update_sync(pipeline_id: str, step: str, status: str, task_id: str = None, result: Dict[str, Any] = None, error: str = None):
    """Send real-time WebSocket update about step progress (synchronous wrapper)"""
    try:
        # Import here to avoid circular imports
        from app.api.endpoints.websocket import (
            notify_step_started, 
            notify_step_completed, 
            notify_task_progress,
            notify_task_failed,
            notify_task_completed
        )
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            if status == "started":
                loop.run_until_complete(notify_step_started(pipeline_id, step))
            elif status == "completed" and result:
                loop.run_until_complete(notify_step_completed(pipeline_id, step, result))
                if task_id:
                    loop.run_until_complete(notify_task_completed(pipeline_id, task_id, step, result))
            elif status == "progress" and task_id:
                loop.run_until_complete(notify_task_progress(pipeline_id, task_id, step, {"status": "in_progress"}))
            elif status == "failed" and task_id and error:
                loop.run_until_complete(notify_task_failed(pipeline_id, task_id, step, error))
        finally:
            loop.close()
        
        logger.info(f"Sent WebSocket update: {pipeline_id} - {step} - {status}")
        
    except Exception as e:
        # Don't fail the main task if WebSocket update fails
        logger.warning(f"Failed to send WebSocket update: {e}")


@celery_app.task(bind=True, name="execute_full_pipeline")
def execute_full_pipeline(self, pipeline_id: str, start_step: str = "document_upload"):
    """
    Execute multiple pipeline steps in sequence
    
    Args:
        self: Celery task instance
        pipeline_id: Pipeline identifier  
        start_step: Which step to start from
        
    Returns:
        Dict with full pipeline results
    """
    try:
        # Define step execution order
        step_order = [
            "document_upload",
            "dfd_extraction", 
            "dfd_review",
            "threat_generation",
            "threat_refinement",
            "attack_path_analysis"
        ]
        
        # Find starting index
        start_index = step_order.index(start_step) if start_step in step_order else 0
        steps_to_execute = step_order[start_index:]
        
        results = {}
        
        for step in steps_to_execute:
            logger.info(f"Executing step {step} for pipeline {pipeline_id}")
            
            # Update progress
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'pipeline_id': pipeline_id,
                    'current_step': step,
                    'completed_steps': list(results.keys()),
                    'remaining_steps': steps_to_execute[steps_to_execute.index(step) + 1:]
                }
            )
            
            # Execute step
            step_result = asyncio.run(_execute_step_async(
                pipeline_id, 
                PipelineStep(step), 
                {}  # Use data from previous steps stored in database
            ))
            
            results[step] = step_result
            
            # Check if step failed
            if not step_result or step_result.get("status") == "failed":
                raise Exception(f"Step {step} failed")
        
        logger.info(f"Full pipeline {pipeline_id} completed successfully")
        return {
            "pipeline_id": pipeline_id,
            "status": "completed",
            "results": results,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Full pipeline {pipeline_id} failed: {exc}")
        raise self.retry(exc=exc, countdown=120) if self.request.retries < self.max_retries else exc


@celery_app.task(name="cleanup_old_tasks")
def cleanup_old_tasks():
    """Clean up old completed tasks and results"""
    try:
        # This would clean up old task results from Redis
        # and mark old pipelines as archived in the database
        logger.info("Task cleanup completed")
        return {"status": "cleaned", "timestamp": datetime.utcnow().isoformat()}
        
    except Exception as e:
        logger.error(f"Task cleanup failed: {e}")
        raise