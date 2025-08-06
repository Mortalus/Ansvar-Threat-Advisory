"""
API endpoints for threat management and feedback.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List
import json
import logging

from app.database import get_async_session
from app.models import ThreatFeedback, ValidationAction, Pipeline
from app.services import PipelineService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/threats", tags=["threats"])


class ThreatFeedbackRequest(BaseModel):
    """Request model for submitting threat feedback."""
    action: ValidationAction
    edited_content: Optional[str] = None
    feedback_reason: Optional[str] = None
    confidence_rating: Optional[int] = Field(None, ge=1, le=5)
    original_threat: dict  # The original threat object


class ThreatFeedbackResponse(BaseModel):
    """Response model for threat feedback."""
    id: int
    threat_id: str
    pipeline_id: int
    action: ValidationAction
    edited_content: Optional[str]
    feedback_reason: Optional[str]
    confidence_rating: Optional[int]
    
    class Config:
        from_attributes = True


@router.post("/{threat_id}/feedback", response_model=ThreatFeedbackResponse)
async def submit_threat_feedback(
    threat_id: str,
    pipeline_id: int,
    feedback: ThreatFeedbackRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Submit feedback for a generated threat.
    
    Args:
        threat_id: ID of the threat being validated
        pipeline_id: ID of the pipeline this threat belongs to
        feedback: Feedback data
        session: Database session
        
    Returns:
        Created feedback record
    """
    try:
        # Verify pipeline exists
        pipeline = await session.get(Pipeline, pipeline_id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pipeline {pipeline_id} not found"
            )
        
        # Create feedback record
        threat_feedback = ThreatFeedback(
            threat_id=threat_id,
            pipeline_id=pipeline_id,
            action=feedback.action,
            edited_content=feedback.edited_content,
            original_threat=json.dumps(feedback.original_threat),
            feedback_reason=feedback.feedback_reason,
            confidence_rating=feedback.confidence_rating,
            user_id=None  # Will be populated when auth is implemented
        )
        
        session.add(threat_feedback)
        await session.commit()
        await session.refresh(threat_feedback)
        
        logger.info(f"Feedback submitted for threat {threat_id}: action={feedback.action}")
        
        return ThreatFeedbackResponse.model_validate(threat_feedback)
        
    except Exception as e:
        logger.error(f"Error submitting threat feedback: {str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/{threat_id}/feedback", response_model=List[ThreatFeedbackResponse])
async def get_threat_feedback(
    threat_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get all feedback for a specific threat.
    
    Args:
        threat_id: ID of the threat
        session: Database session
        
    Returns:
        List of feedback records for the threat
    """
    try:
        from sqlalchemy import select
        
        stmt = select(ThreatFeedback).where(ThreatFeedback.threat_id == threat_id)
        result = await session.execute(stmt)
        feedback_records = result.scalars().all()
        
        return [ThreatFeedbackResponse.model_validate(f) for f in feedback_records]
        
    except Exception as e:
        logger.error(f"Error fetching threat feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch feedback: {str(e)}"
        )


@router.get("/pipeline/{pipeline_id}/feedback", response_model=List[ThreatFeedbackResponse])
async def get_pipeline_threat_feedback(
    pipeline_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get all threat feedback for a pipeline.
    
    Args:
        pipeline_id: ID of the pipeline
        session: Database session
        
    Returns:
        List of all feedback records for the pipeline
    """
    try:
        from sqlalchemy import select
        
        # Verify pipeline exists
        pipeline = await session.get(Pipeline, pipeline_id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pipeline {pipeline_id} not found"
            )
        
        stmt = select(ThreatFeedback).where(ThreatFeedback.pipeline_id == pipeline_id)
        result = await session.execute(stmt)
        feedback_records = result.scalars().all()
        
        return [ThreatFeedbackResponse.model_validate(f) for f in feedback_records]
        
    except Exception as e:
        logger.error(f"Error fetching pipeline threat feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch feedback: {str(e)}"
        )


@router.get("/feedback/stats")
async def get_feedback_statistics(
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get statistics about threat feedback across all pipelines.
    
    Returns:
        Aggregated statistics about threat feedback
    """
    try:
        from sqlalchemy import select, func
        
        # Count by action type
        stmt = select(
            ThreatFeedback.action,
            func.count(ThreatFeedback.id).label('count')
        ).group_by(ThreatFeedback.action)
        
        result = await session.execute(stmt)
        action_counts = {row.action: row.count for row in result}
        
        # Average confidence rating
        stmt = select(func.avg(ThreatFeedback.confidence_rating))
        result = await session.execute(stmt)
        avg_confidence = result.scalar() or 0
        
        # Total feedback count
        stmt = select(func.count(ThreatFeedback.id))
        result = await session.execute(stmt)
        total_feedback = result.scalar() or 0
        
        return {
            "total_feedback": total_feedback,
            "action_counts": action_counts,
            "average_confidence": round(avg_confidence, 2),
            "message": f"Collected {total_feedback} feedback entries for continuous improvement"
        }
        
    except Exception as e:
        logger.error(f"Error calculating feedback statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate statistics: {str(e)}"
        )