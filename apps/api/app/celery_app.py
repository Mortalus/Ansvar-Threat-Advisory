"""Celery application configuration for background task processing"""

from celery import Celery
from app.config import settings

# Create Celery application
celery_app = Celery(
    "threat_modeling_pipeline",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.pipeline_tasks",
        "app.tasks.llm_tasks",
        "app.tasks.knowledge_base_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing - use default queue for now
    # task_routes={
    #     "app.tasks.pipeline_tasks.*": {"queue": "pipeline"},
    #     "app.tasks.llm_tasks.*": {"queue": "llm"},
    # },
    
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Task retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
    },
    
    # Worker settings
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=True,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Task result settings
    task_track_started=True,
    task_publish_retry=True,
)

# Configure task queues - simplified for now, use default queue
# celery_app.conf.task_queues can be added later if needed

# Celery Beat schedule for periodic tasks
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'update-knowledge-bases-daily': {
        'task': 'tasks.update_all_knowledge_bases',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
}

# Task annotations for specific configuration per task
celery_app.conf.task_annotations = {
    "app.tasks.llm_tasks.extract_dfd_task": {
        "rate_limit": "5/m",  # Max 5 DFD extractions per minute
        "time_limit": 300,    # 5 minutes max
        "soft_time_limit": 240,  # 4 minutes soft limit
    },
    "app.tasks.llm_tasks.generate_threats_task": {
        "rate_limit": "3/m",  # Max 3 threat generations per minute  
        "time_limit": 600,    # 10 minutes max
        "soft_time_limit": 540,  # 9 minutes soft limit
    },
    "app.tasks.pipeline_tasks.execute_pipeline_step": {
        "time_limit": 900,    # 15 minutes max
        "soft_time_limit": 840,  # 14 minutes soft limit
    }
}

# Health check task
@celery_app.task
def health_check():
    """Simple health check task"""
    return {"status": "healthy", "message": "Celery worker is running"}

if __name__ == "__main__":
    celery_app.start()