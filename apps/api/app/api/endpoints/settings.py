"""Settings management endpoints for customizable LLM prompts"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging
from datetime import datetime

from app.database import get_async_session
from app.models.settings import SystemPromptTemplate, SystemPromptTemplateCreate, SystemPromptTemplateUpdate
from app.services.settings_service import SettingsService
from app.services.feedback_learning_service import FeedbackLearningService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/settings", tags=["settings"])

# Pydantic models for API
class PromptTemplateResponse(BaseModel):
    id: str
    step_name: str
    agent_type: Optional[str]
    system_prompt: str
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class PromptTemplateRequest(BaseModel):
    step_name: str
    agent_type: Optional[str] = None
    system_prompt: str
    description: str
    is_active: bool = True

class PromptTemplateUpdate(BaseModel):
    system_prompt: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

# LLM step definitions with their default prompts
LLM_STEP_DEFINITIONS = {
    "dfd_extraction": {
        "description": "Data Flow Diagram extraction from documents",
        "default_prompt": "You are a cybersecurity expert extracting DFD components. Output only valid JSON.",
        "agents": []
    },
    "dfd_validation": {
        "description": "DFD validation and quality assessment",
        "default_prompt": "You are a STRIDE expert validating DFD components for completeness and accuracy.",
        "agents": []
    },
    "threat_generation": {
        "description": "Multi-agent threat generation (V3)",
        "default_prompt": "You are a cybersecurity expert generating comprehensive threat analysis.",
        "agents": [
            {
                "type": "architectural_risk",
                "description": "Architectural Risk Agent - systemic vulnerabilities",
                "default_prompt": "You are an expert Enterprise Architect specializing in identifying systemic architectural vulnerabilities that traditional security scans miss."
            },
            {
                "type": "business_financial",
                "description": "Business & Financial Risk Agent - business impact analysis", 
                "default_prompt": "You are a Chief Risk Officer and Business Continuity Expert with deep expertise in quantifying cybersecurity threats' impact on business operations and financial performance."
            },
            {
                "type": "compliance_governance",
                "description": "Compliance & Governance Agent - regulatory compliance",
                "default_prompt": "You are a Chief Compliance Officer and Regulatory Audit Expert with deep expertise in cybersecurity compliance frameworks (GDPR, PCI-DSS, HIPAA, SOX, ISO 27001) and governance standards."
            }
        ]
    },
    "threat_refinement": {
        "description": "Threat refinement and risk assessment",
        "default_prompt": "You are a cybersecurity analyst specializing in threat refinement and risk assessment.",
        "agents": []
    },
    "attack_path_analysis": {
        "description": "Attack path and vector analysis",
        "default_prompt": "You are a penetration tester and attack path analyst identifying potential attack vectors.",
        "agents": []
    }
}

@router.get("/llm-steps")
async def get_llm_steps():
    """Get available LLM steps and their descriptions"""
    return {
        "steps": LLM_STEP_DEFINITIONS,
        "total_steps": len(LLM_STEP_DEFINITIONS)
    }

@router.get("/prompts")
async def list_prompt_templates(
    step_name: Optional[str] = None,
    agent_type: Optional[str] = None,
    active_only: bool = True,
    db_session: AsyncSession = Depends(get_async_session)
) -> List[PromptTemplateResponse]:
    """List all prompt templates with optional filtering"""
    try:
        settings_service = SettingsService(db_session)
        templates = await settings_service.list_prompt_templates(
            step_name=step_name,
            agent_type=agent_type,
            active_only=active_only
        )
        
        return [
            PromptTemplateResponse(
                id=template.id,
                step_name=template.step_name,
                agent_type=template.agent_type,
                system_prompt=template.system_prompt,
                description=template.description,
                is_active=template.is_active,
                created_at=template.created_at,
                updated_at=template.updated_at
            )
            for template in templates
        ]
        
    except Exception as e:
        logger.error(f"Failed to list prompt templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prompts/{template_id}")
async def get_prompt_template(
    template_id: str,
    db_session: AsyncSession = Depends(get_async_session)
) -> PromptTemplateResponse:
    """Get a specific prompt template"""
    try:
        settings_service = SettingsService(db_session)
        template = await settings_service.get_prompt_template(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="Prompt template not found")
        
        return PromptTemplateResponse(
            id=template.id,
            step_name=template.step_name,
            agent_type=template.agent_type,
            system_prompt=template.system_prompt,
            description=template.description,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prompt template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prompts")
async def create_prompt_template(
    request: PromptTemplateRequest,
    db_session: AsyncSession = Depends(get_async_session)
) -> PromptTemplateResponse:
    """Create a new prompt template"""
    try:
        # Validate step_name
        if request.step_name not in LLM_STEP_DEFINITIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid step_name. Must be one of: {list(LLM_STEP_DEFINITIONS.keys())}"
            )
        
        # Validate agent_type if provided
        if request.agent_type:
            step_def = LLM_STEP_DEFINITIONS[request.step_name]
            if step_def["agents"]:
                valid_agents = [agent["type"] for agent in step_def["agents"]]
                if request.agent_type not in valid_agents:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid agent_type for {request.step_name}. Must be one of: {valid_agents}"
                    )
        
        settings_service = SettingsService(db_session)
        template_data = SystemPromptTemplateCreate(
            step_name=request.step_name,
            agent_type=request.agent_type,
            system_prompt=request.system_prompt,
            description=request.description,
            is_active=request.is_active
        )
        
        template = await settings_service.create_prompt_template(template_data)
        
        return PromptTemplateResponse(
            id=template.id,
            step_name=template.step_name,
            agent_type=template.agent_type,
            system_prompt=template.system_prompt,
            description=template.description,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create prompt template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/prompts/{template_id}")
async def update_prompt_template(
    template_id: str,
    request: PromptTemplateUpdate,
    db_session: AsyncSession = Depends(get_async_session)
) -> PromptTemplateResponse:
    """Update an existing prompt template"""
    try:
        settings_service = SettingsService(db_session)
        
        # Check if template exists
        existing = await settings_service.get_prompt_template(template_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Prompt template not found")
        
        # Create update data
        update_data = SystemPromptTemplateUpdate(**request.dict(exclude_unset=True))
        template = await settings_service.update_prompt_template(template_id, update_data)
        
        return PromptTemplateResponse(
            id=template.id,
            step_name=template.step_name,
            agent_type=template.agent_type,
            system_prompt=template.system_prompt,
            description=template.description,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update prompt template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/prompts/{template_id}")
async def delete_prompt_template(
    template_id: str,
    db_session: AsyncSession = Depends(get_async_session)
):
    """Delete a prompt template"""
    try:
        settings_service = SettingsService(db_session)
        
        success = await settings_service.delete_prompt_template(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Prompt template not found")
        
        return {"message": "Prompt template deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete prompt template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prompts/initialize-defaults")
async def initialize_default_prompts(
    db_session: AsyncSession = Depends(get_async_session)
):
    """Initialize default prompt templates for all steps"""
    try:
        settings_service = SettingsService(db_session)
        created_count = 0
        
        for step_name, step_def in LLM_STEP_DEFINITIONS.items():
            # Create main step prompt
            existing = await settings_service.get_active_prompt_template(step_name, None)
            if not existing:
                await settings_service.create_prompt_template(
                    SystemPromptTemplateCreate(
                        step_name=step_name,
                        agent_type=None,
                        system_prompt=step_def["default_prompt"],
                        description=f"Default system prompt for {step_def['description']}",
                        is_active=True
                    )
                )
                created_count += 1
            
            # Create agent-specific prompts
            for agent in step_def.get("agents", []):
                existing_agent = await settings_service.get_active_prompt_template(step_name, agent["type"])
                if not existing_agent:
                    await settings_service.create_prompt_template(
                        SystemPromptTemplateCreate(
                            step_name=step_name,
                            agent_type=agent["type"],
                            system_prompt=agent["default_prompt"],
                            description=f"Default prompt for {agent['description']}",
                            is_active=True
                        )
                    )
                    created_count += 1
        
        return {
            "message": f"Initialized {created_count} default prompt templates",
            "total_created": created_count
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize default prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prompts/active/{step_name}")
async def get_active_prompt_for_step(
    step_name: str,
    agent_type: Optional[str] = None,
    db_session: AsyncSession = Depends(get_async_session)
) -> PromptTemplateResponse:
    """Get the active prompt template for a specific step and agent"""
    try:
        settings_service = SettingsService(db_session)
        template = await settings_service.get_active_prompt_template(step_name, agent_type)
        
        if not template:
            # Return default if no custom template exists
            if step_name in LLM_STEP_DEFINITIONS:
                step_def = LLM_STEP_DEFINITIONS[step_name]
                
                if agent_type:
                    # Find agent default
                    agent_def = next((agent for agent in step_def.get("agents", []) if agent["type"] == agent_type), None)
                    if agent_def:
                        default_prompt = agent_def["default_prompt"]
                        description = f"Default prompt for {agent_def['description']}"
                    else:
                        raise HTTPException(status_code=404, detail=f"Agent type {agent_type} not found for step {step_name}")
                else:
                    default_prompt = step_def["default_prompt"]
                    description = f"Default prompt for {step_def['description']}"
                
                # Return virtual template (not saved in DB)
                return PromptTemplateResponse(
                    id="default",
                    step_name=step_name,
                    agent_type=agent_type,
                    system_prompt=default_prompt,
                    description=description,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            
            raise HTTPException(status_code=404, detail="No active prompt template found for this step")
        
        return PromptTemplateResponse(
            id=template.id,
            step_name=template.step_name,
            agent_type=template.agent_type,
            system_prompt=template.system_prompt,
            description=template.description,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get active prompt for {step_name}/{agent_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/learning/statistics")
async def get_learning_statistics(
    db_session: AsyncSession = Depends(get_async_session)
):
    """Get few-shot learning statistics from user feedback"""
    try:
        feedback_service = FeedbackLearningService(db_session)
        stats = await feedback_service.get_feedback_statistics()
        
        return {
            "learning_status": "enabled" if stats["learning_examples_available"] else "insufficient_data",
            "feedback_statistics": stats,
            "message": "Few-shot learning is active" if stats["learning_examples_available"] 
                      else "Need more user feedback to enable learning"
        }
        
    except Exception as e:
        logger.error(f"Failed to get learning statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/learning/examples/{step_name}")
async def get_learning_examples(
    step_name: str,
    agent_type: Optional[str] = None,
    example_type: str = "positive",
    db_session: AsyncSession = Depends(get_async_session)
):
    """Get few-shot learning examples for a specific step/agent"""
    try:
        feedback_service = FeedbackLearningService(db_session)
        examples = await feedback_service.get_few_shot_examples(
            step_name=step_name,
            agent_type=agent_type,
            example_type=example_type
        )
        
        return {
            "step_name": step_name,
            "agent_type": agent_type,
            "example_type": example_type,
            "examples_count": len(examples),
            "examples": examples
        }
        
    except Exception as e:
        logger.error(f"Failed to get learning examples: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/learning/preview-enhanced-prompt")
async def preview_enhanced_prompt(
    request: Dict[str, Any],
    db_session: AsyncSession = Depends(get_async_session)
):
    """Preview how a prompt would be enhanced with few-shot learning"""
    try:
        base_prompt = request.get("base_prompt", "")
        step_name = request.get("step_name", "")
        agent_type = request.get("agent_type")
        
        if not base_prompt or not step_name:
            raise HTTPException(status_code=400, detail="base_prompt and step_name are required")
        
        feedback_service = FeedbackLearningService(db_session)
        enhanced_prompt = await feedback_service.enhance_prompt_with_examples(
            base_prompt=base_prompt,
            step_name=step_name,
            agent_type=agent_type,
            include_positive=True,
            include_negative=request.get("include_negative", False)
        )
        
        return {
            "original_prompt": base_prompt,
            "enhanced_prompt": enhanced_prompt,
            "enhancement_applied": enhanced_prompt != base_prompt,
            "step_name": step_name,
            "agent_type": agent_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview enhanced prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))