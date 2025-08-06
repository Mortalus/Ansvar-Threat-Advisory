"""Pipeline database service layer"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update, delete
from datetime import datetime
import uuid

from ..models import Pipeline, PipelineStep, PipelineStepResult, PipelineStatus, StepStatus
from ..models.pipeline import PipelineStatus as PipelineStatusEnum, StepStatus as StepStatusEnum


class PipelineService:
    """Service for pipeline database operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_pipeline(
        self, 
        name: Optional[str] = None,
        description: Optional[str] = None,
        owner_id: Optional[int] = None
    ) -> Pipeline:
        """Create a new pipeline"""
        pipeline = Pipeline(
            pipeline_id=str(uuid.uuid4()),
            name=name,
            description=description,
            status=PipelineStatusEnum.CREATED,
            owner_id=owner_id,
            started_at=datetime.utcnow()
        )
        
        # Create initial pipeline steps
        steps_config = [
            {"step_name": "document_upload", "step_number": 1},
            {"step_name": "dfd_extraction", "step_number": 2},
            {"step_name": "dfd_review", "step_number": 3},
            {"step_name": "threat_generation", "step_number": 4},
            {"step_name": "threat_refinement", "step_number": 5},
            {"step_name": "attack_path_analysis", "step_number": 6},
        ]
        
        for step_config in steps_config:
            step = PipelineStep(
                pipeline=pipeline,
                step_name=step_config["step_name"],
                step_number=step_config["step_number"],
                status=StepStatusEnum.PENDING
            )
            self.session.add(step)
        
        self.session.add(pipeline)
        await self.session.commit()
        await self.session.refresh(pipeline)
        
        return pipeline
    
    async def get_pipeline(self, pipeline_id: str) -> Optional[Pipeline]:
        """Get pipeline by pipeline_id"""
        stmt = (
            select(Pipeline)
            .options(selectinload(Pipeline.steps).selectinload(PipelineStep.results))
            .where(Pipeline.pipeline_id == pipeline_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_pipeline_by_db_id(self, db_id: int) -> Optional[Pipeline]:
        """Get pipeline by database ID"""
        stmt = (
            select(Pipeline)
            .options(selectinload(Pipeline.steps).selectinload(PipelineStep.results))
            .where(Pipeline.id == db_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_pipeline_status(self, pipeline_id: str, status: PipelineStatusEnum) -> bool:
        """Update pipeline status"""
        stmt = (
            update(Pipeline)
            .where(Pipeline.pipeline_id == pipeline_id)
            .values(
                status=status,
                updated_at=datetime.utcnow(),
                completed_at=datetime.utcnow() if status == PipelineStatusEnum.COMPLETED else None
            )
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
    
    async def update_pipeline_data(
        self, 
        pipeline_id: str, 
        **data: Any
    ) -> bool:
        """Update pipeline data fields"""
        update_data = {k: v for k, v in data.items() if v is not None}
        update_data['updated_at'] = datetime.utcnow()
        
        stmt = (
            update(Pipeline)
            .where(Pipeline.pipeline_id == pipeline_id)
            .values(**update_data)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
    
    async def get_pipeline_step(self, pipeline_id: str, step_name: str) -> Optional[PipelineStep]:
        """Get specific pipeline step"""
        stmt = (
            select(PipelineStep)
            .join(Pipeline)
            .where(Pipeline.pipeline_id == pipeline_id)
            .where(PipelineStep.step_name == step_name)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_step_status(
        self, 
        pipeline_id: str, 
        step_name: str, 
        status: StepStatusEnum,
        error_message: Optional[str] = None
    ) -> bool:
        """Update step status"""
        now = datetime.utcnow()
        
        # Build update data
        update_data = {
            'status': status,
            'updated_at': now
        }
        
        if status == StepStatusEnum.IN_PROGRESS:
            update_data['started_at'] = now
        elif status in [StepStatusEnum.COMPLETED, StepStatusEnum.FAILED]:
            update_data['completed_at'] = now
        
        if error_message:
            update_data['error_message'] = error_message
        
        # Update the step
        stmt = (
            update(PipelineStep)
            .where(PipelineStep.pipeline_id == select(Pipeline.id).where(Pipeline.pipeline_id == pipeline_id).scalar_subquery())
            .where(PipelineStep.step_name == step_name)
            .values(**update_data)
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
    
    async def add_step_result(
        self,
        pipeline_id: str,
        step_name: str,
        result_type: str,
        result_data: Dict[str, Any],
        processing_time_seconds: Optional[int] = None,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None
    ) -> bool:
        """Add result data for a pipeline step"""
        
        # Get the step
        step = await self.get_pipeline_step(pipeline_id, step_name)
        if not step:
            return False
        
        result = PipelineStepResult(
            step_id=step.id,
            result_type=result_type,
            result_data=result_data,
            processing_time_seconds=processing_time_seconds,
            llm_provider=llm_provider,
            llm_model=llm_model
        )
        
        self.session.add(result)
        await self.session.commit()
        return True
    
    async def list_pipelines(
        self, 
        owner_id: Optional[int] = None, 
        limit: int = 50
    ) -> List[Pipeline]:
        """List pipelines with optional owner filter"""
        stmt = select(Pipeline)
        
        if owner_id:
            stmt = stmt.where(Pipeline.owner_id == owner_id)
        
        stmt = stmt.order_by(Pipeline.created_at.desc()).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def delete_pipeline(self, pipeline_id: str) -> bool:
        """Delete a pipeline and all its data"""
        stmt = delete(Pipeline).where(Pipeline.pipeline_id == pipeline_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0