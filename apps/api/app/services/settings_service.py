"""Settings service for managing prompt templates"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
import logging

from app.models.settings import SystemPromptTemplate, SystemPromptTemplateCreate, SystemPromptTemplateUpdate

logger = logging.getLogger(__name__)

class SettingsService:
    """Service for managing system settings and prompt templates"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def list_prompt_templates(
        self,
        step_name: Optional[str] = None,
        agent_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[SystemPromptTemplate]:
        """List prompt templates with optional filtering"""
        query = select(SystemPromptTemplate)
        
        conditions = []
        if step_name:
            conditions.append(SystemPromptTemplate.step_name == step_name)
        if agent_type:
            conditions.append(SystemPromptTemplate.agent_type == agent_type)
        if active_only:
            conditions.append(SystemPromptTemplate.is_active == True)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(SystemPromptTemplate.step_name, SystemPromptTemplate.agent_type)
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def get_prompt_template(self, template_id: str) -> Optional[SystemPromptTemplate]:
        """Get a prompt template by ID"""
        query = select(SystemPromptTemplate).where(SystemPromptTemplate.id == template_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_active_prompt_template(
        self,
        step_name: str,
        agent_type: Optional[str] = None
    ) -> Optional[SystemPromptTemplate]:
        """Get the active prompt template for a step/agent combination"""
        query = select(SystemPromptTemplate).where(
            and_(
                SystemPromptTemplate.step_name == step_name,
                SystemPromptTemplate.agent_type == agent_type,
                SystemPromptTemplate.is_active == True
            )
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
    
    async def create_prompt_template(
        self,
        template_data: SystemPromptTemplateCreate
    ) -> SystemPromptTemplate:
        """Create a new prompt template"""
        
        # If this is being set as active, deactivate any existing active templates
        # for the same step/agent combination
        if template_data.is_active:
            await self._deactivate_existing_templates(
                template_data.step_name,
                template_data.agent_type
            )
        
        # Create new template
        template = SystemPromptTemplate(
            step_name=template_data.step_name,
            agent_type=template_data.agent_type,
            system_prompt=template_data.system_prompt,
            description=template_data.description,
            is_active=template_data.is_active
        )
        
        self.db_session.add(template)
        await self.db_session.commit()
        await self.db_session.refresh(template)
        
        logger.info(f"Created prompt template for {template_data.step_name}/{template_data.agent_type}")
        return template
    
    async def update_prompt_template(
        self,
        template_id: str,
        update_data: SystemPromptTemplateUpdate
    ) -> Optional[SystemPromptTemplate]:
        """Update an existing prompt template"""
        
        template = await self.get_prompt_template(template_id)
        if not template:
            return None
        
        # If being set to active, deactivate other templates for same step/agent
        if update_data.is_active is True:
            await self._deactivate_existing_templates(
                template.step_name,
                template.agent_type,
                exclude_id=template_id
            )
        
        # Apply updates
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(template, field, value)
        
        await self.db_session.commit()
        await self.db_session.refresh(template)
        
        logger.info(f"Updated prompt template {template_id}")
        return template
    
    async def delete_prompt_template(self, template_id: str) -> bool:
        """Delete a prompt template"""
        template = await self.get_prompt_template(template_id)
        if not template:
            return False
        
        await self.db_session.delete(template)
        await self.db_session.commit()
        
        logger.info(f"Deleted prompt template {template_id}")
        return True
    
    async def _deactivate_existing_templates(
        self,
        step_name: str,
        agent_type: Optional[str],
        exclude_id: Optional[str] = None
    ):
        """Deactivate existing active templates for a step/agent combination"""
        conditions = [
            SystemPromptTemplate.step_name == step_name,
            SystemPromptTemplate.agent_type == agent_type,
            SystemPromptTemplate.is_active == True
        ]
        
        if exclude_id:
            conditions.append(SystemPromptTemplate.id != exclude_id)
        
        query = select(SystemPromptTemplate).where(and_(*conditions))
        result = await self.db_session.execute(query)
        existing_templates = result.scalars().all()
        
        for template in existing_templates:
            template.is_active = False
        
        if existing_templates:
            await self.db_session.commit()
            logger.info(f"Deactivated {len(existing_templates)} existing templates for {step_name}/{agent_type}")

    async def get_system_prompt_for_step(
        self,
        step_name: str,
        agent_type: Optional[str] = None,
        fallback_prompt: Optional[str] = None
    ) -> str:
        """
        Get the system prompt for a specific step and agent.
        Returns custom prompt if available, otherwise returns fallback_prompt.
        """
        template = await self.get_active_prompt_template(step_name, agent_type)
        
        if template:
            logger.debug(f"Using custom prompt for {step_name}/{agent_type}")
            return template.system_prompt
        
        if fallback_prompt:
            logger.debug(f"Using fallback prompt for {step_name}/{agent_type}")
            return fallback_prompt
        
        # Default generic prompt as last resort
        logger.warning(f"No prompt found for {step_name}/{agent_type}, using generic default")
        return "You are a helpful AI assistant specialized in cybersecurity analysis."