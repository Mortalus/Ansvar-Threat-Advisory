"""
Service for managing prompt templates and versions.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging

from app.models.prompt import Prompt

logger = logging.getLogger(__name__)


class PromptService:
    """Service for managing prompt templates and versions."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_active_prompt(self, name: str) -> Optional[Prompt]:
        """
        Get the active prompt template for a given name.
        
        Args:
            name: Unique identifier for the prompt (e.g., 'threat_generation')
            
        Returns:
            Active Prompt object or None if not found
        """
        stmt = select(Prompt).where(
            and_(
                Prompt.name == name,
                Prompt.is_active == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_prompt(
        self,
        name: str,
        template_text: str,
        activate: bool = False
    ) -> Prompt:
        """
        Create a new prompt template version.
        
        Args:
            name: Unique identifier for the prompt
            template_text: The prompt template text
            activate: Whether to make this the active version
            
        Returns:
            Created Prompt object
        """
        # Get the latest version number for this prompt name
        stmt = select(Prompt.version).where(
            Prompt.name == name
        ).order_by(Prompt.version.desc()).limit(1)
        
        result = await self.session.execute(stmt)
        latest_version = result.scalar_one_or_none()
        
        # Calculate new version number
        new_version = (latest_version or 0) + 1
        
        # If activating, deactivate all other versions
        if activate:
            await self.deactivate_all_versions(name)
        
        # Create new prompt
        prompt = Prompt(
            name=name,
            version=new_version,
            template_text=template_text,
            is_active=activate
        )
        
        self.session.add(prompt)
        await self.session.commit()
        await self.session.refresh(prompt)
        
        logger.info(f"Created prompt '{name}' version {new_version} (active={activate})")
        return prompt
    
    async def update_prompt(
        self,
        prompt_id: int,
        template_text: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Prompt:
        """
        Update an existing prompt.
        
        Args:
            prompt_id: ID of the prompt to update
            template_text: New template text (optional)
            is_active: New active status (optional)
            
        Returns:
            Updated Prompt object
        """
        stmt = select(Prompt).where(Prompt.id == prompt_id)
        result = await self.session.execute(stmt)
        prompt = result.scalar_one_or_none()
        
        if not prompt:
            raise ValueError(f"Prompt with id {prompt_id} not found")
        
        if template_text is not None:
            prompt.template_text = template_text
        
        if is_active is not None:
            # If activating, deactivate all other versions
            if is_active:
                await self.deactivate_all_versions(prompt.name)
            prompt.is_active = is_active
        
        await self.session.commit()
        await self.session.refresh(prompt)
        
        logger.info(f"Updated prompt {prompt_id}")
        return prompt
    
    async def activate_version(self, name: str, version: int) -> Prompt:
        """
        Activate a specific version of a prompt.
        
        Args:
            name: Prompt name
            version: Version number to activate
            
        Returns:
            Activated Prompt object
        """
        # Deactivate all versions
        await self.deactivate_all_versions(name)
        
        # Activate the specified version
        stmt = select(Prompt).where(
            and_(
                Prompt.name == name,
                Prompt.version == version
            )
        )
        result = await self.session.execute(stmt)
        prompt = result.scalar_one_or_none()
        
        if not prompt:
            raise ValueError(f"Prompt '{name}' version {version} not found")
        
        prompt.is_active = True
        await self.session.commit()
        await self.session.refresh(prompt)
        
        logger.info(f"Activated prompt '{name}' version {version}")
        return prompt
    
    async def deactivate_all_versions(self, name: str) -> None:
        """
        Deactivate all versions of a prompt.
        
        Args:
            name: Prompt name
        """
        stmt = select(Prompt).where(Prompt.name == name)
        result = await self.session.execute(stmt)
        prompts = result.scalars().all()
        
        for prompt in prompts:
            prompt.is_active = False
        
        await self.session.commit()
        logger.info(f"Deactivated all versions of prompt '{name}'")
    
    async def get_prompt_by_id(self, prompt_id: int) -> Optional[Prompt]:
        """
        Get a prompt by its ID.
        
        Args:
            prompt_id: Prompt ID
            
        Returns:
            Prompt object or None if not found
        """
        stmt = select(Prompt).where(Prompt.id == prompt_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_prompt_by_version(self, name: str, version: int) -> Optional[Prompt]:
        """
        Get a specific version of a prompt.
        
        Args:
            name: Prompt name
            version: Version number
            
        Returns:
            Prompt object or None if not found
        """
        stmt = select(Prompt).where(
            and_(
                Prompt.name == name,
                Prompt.version == version
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_prompts(self, name: Optional[str] = None) -> List[Prompt]:
        """
        List all prompts, optionally filtered by name.
        
        Args:
            name: Optional prompt name to filter by
            
        Returns:
            List of Prompt objects
        """
        stmt = select(Prompt).order_by(Prompt.name, Prompt.version.desc())
        
        if name:
            stmt = stmt.where(Prompt.name == name)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_latest_version(self, name: str) -> Optional[Prompt]:
        """
        Get the latest version of a prompt (regardless of active status).
        
        Args:
            name: Prompt name
            
        Returns:
            Latest Prompt object or None if not found
        """
        stmt = select(Prompt).where(
            Prompt.name == name
        ).order_by(Prompt.version.desc()).limit(1)
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def initialize_default_prompts(self) -> None:
        """
        Initialize default prompt templates for the application.
        This should be called during application startup.
        """
        default_prompts = {
            "threat_generation": """Analyze the following component and generate specific threats using the STRIDE methodology.

Component Information:
{component_info}

Relevant Threat Intelligence Context:
{threat_context}

Generate 3-5 specific threats for this component. For each threat, provide:
1. Threat Category (STRIDE: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege)
2. Threat Name
3. Description
4. Potential Impact
5. Likelihood (Low/Medium/High)
6. Suggested Mitigation

Format the response as a JSON array of threat objects.""",
            
            "dfd_extraction": """Extract Data Flow Diagram (DFD) components from the following system documentation.

Document Content:
{document_content}

Identify and extract:
1. Processes (services, applications, functions)
2. External Entities (users, third-party systems)
3. Data Stores (databases, file systems, caches)
4. Data Flows (communication channels, APIs, data transfers)

For each component, provide:
- Name
- Type
- Description
- Trust boundaries (if applicable)

Format the response as structured JSON.""",
            
            "attack_path_analysis": """Analyze the following threats and generate potential attack paths.

Threats:
{threats}

System Components:
{components}

For each significant threat, identify:
1. Attack vector
2. Prerequisites
3. Step-by-step attack path
4. Potential impact
5. Detection opportunities
6. Mitigation strategies

Format the response as structured JSON with clear attack chains."""
        }
        
        for name, template in default_prompts.items():
            # Check if this prompt already exists
            existing = await self.get_active_prompt(name)
            if not existing:
                # Create and activate the default prompt
                await self.create_prompt(
                    name=name,
                    template_text=template,
                    activate=True
                )
                logger.info(f"Initialized default prompt for '{name}'")
            else:
                logger.info(f"Prompt '{name}' already exists, skipping initialization")