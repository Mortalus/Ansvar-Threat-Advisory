"""
Base Agent Classes for Modular Threat Analysis System

Provides abstract base classes and data models that ensure all agents
maintain compatibility with the existing V3 threat analysis pipeline.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
import logging
import time

logger = logging.getLogger(__name__)


class AgentCategory(str, Enum):
    """Categories of threat analysis agents"""
    SECURITY = "security"
    ARCHITECTURE = "architecture" 
    BUSINESS = "business"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"


class AgentMetadata(BaseModel):
    """Metadata describing an agent's capabilities and requirements"""
    name: str = Field(..., description="Unique agent identifier")
    version: str = Field(..., description="Agent version (semver)")
    description: str = Field(..., description="Human-readable description")
    category: AgentCategory = Field(..., description="Agent category")
    priority: int = Field(default=100, description="Execution order (1-1000, lower = earlier)")
    requires_document: bool = Field(default=True, description="Needs document text")
    requires_components: bool = Field(default=True, description="Needs DFD components")
    estimated_tokens: int = Field(default=3000, description="Estimated token usage")
    enabled_by_default: bool = Field(default=True, description="Default enabled state")
    legacy_equivalent: Optional[str] = Field(default=None, description="Maps to old agent name")
    
    class Config:
        use_enum_values = True


class ThreatOutput(BaseModel):
    """
    Standardized threat output format
    Maintains exact compatibility with existing V3 system
    """
    # Core threat fields (exactly matching V3 format)
    threat_id: str = Field(..., description="Unique threat identifier")
    threat_name: str = Field(..., description="Threat Name from V3")
    description: str = Field(..., description="Description from V3")
    stride_category: str = Field(..., description="STRIDE Category from V3")
    affected_component: str = Field(..., description="Affected Component from V3")
    potential_impact: str = Field(..., description="Potential Impact from V3")
    likelihood: str = Field(..., description="Likelihood from V3")
    mitigation_strategy: str = Field(..., description="Suggested Mitigation from V3")
    
    # V2/V3 enhanced fields (preserved from existing system)
    residual_risk: Optional[str] = Field(default=None, description="After controls")
    controls_detected: Optional[List[str]] = Field(default=None, description="Applicable controls")
    threat_class: Optional[str] = Field(default=None, description="architectural/business/compliance")
    financial_exposure: Optional[str] = Field(default=None, description="Financial impact")
    regulatory_implications: Optional[List[str]] = Field(default=None, description="Compliance concerns")
    business_impact: Optional[str] = Field(default=None, description="Business context")
    priority_score: Optional[float] = Field(default=None, description="Risk priority")
    cwe_references: Optional[List[str]] = Field(default=None, description="CWE mappings")
    
    # Agent metadata
    agent_source: str = Field(..., description="Agent that generated this threat")
    confidence_score: float = Field(default=0.8, description="Agent confidence (0.0-1.0)")
    generation_time: float = Field(default_factory=time.time, description="When generated")
    
    def to_v3_format(self) -> Dict[str, Any]:
        """
        Convert to exact V3 output format for backward compatibility
        This ensures existing consumers continue to work unchanged
        """
        return {
            "Threat Name": self.threat_name,
            "Description": self.description,
            "STRIDE Category": self.stride_category,
            "Affected Component": self.affected_component,
            "Potential Impact": self.potential_impact,
            "Likelihood": self.likelihood,
            "Suggested Mitigation": self.mitigation_strategy,
            # V3 enhanced fields
            "residual_risk": self.residual_risk,
            "controls_detected": self.controls_detected,
            "threat_class": self.threat_class,
            "financial_exposure": self.financial_exposure,
            "regulatory_implications": self.regulatory_implications,
            "business_impact": self.business_impact,
            "priority_score": self.priority_score,
            "cwe_references": self.cwe_references,
            # Metadata
            "agent_source": self.agent_source,
            "confidence_score": self.confidence_score
        }


class AgentExecutionContext(BaseModel):
    """Context provided to agents during execution"""
    document_text: Optional[str] = None
    components: Optional[Dict[str, Any]] = None
    existing_threats: Optional[List[Dict]] = None
    pipeline_id: Optional[str] = None
    user_config: Optional[Dict[str, Any]] = None
    
    def validate_requirements(self, metadata: AgentMetadata) -> bool:
        """Check if context meets agent requirements"""
        if metadata.requires_document and not self.document_text:
            return False
        if metadata.requires_components and not self.components:
            return False
        return True


class BaseAgent(ABC):
    """
    Abstract base class for all threat analysis agents
    
    Ensures compatibility with existing V3 system while enabling
    modular agent development and deployment.
    """
    
    def __init__(self):
        self._config = {}
        self._custom_prompt = None
        
    @abstractmethod
    def get_metadata(self) -> AgentMetadata:
        """Return agent metadata and capabilities"""
        pass
    
    @abstractmethod
    async def analyze(
        self,
        context: AgentExecutionContext,
        llm_provider: Any,
        db_session: Any,
        settings_service: Optional[Any] = None
    ) -> List[ThreatOutput]:
        """
        Perform threat analysis
        
        Args:
            context: Execution context with document/components
            llm_provider: LLM provider instance
            db_session: Database session
            settings_service: For custom prompts and settings
            
        Returns:
            List of threats in standardized format
        """
        pass
    
    def validate_context(self, context: AgentExecutionContext) -> bool:
        """Check if agent has required context"""
        metadata = self.get_metadata()
        return context.validate_requirements(metadata)
    
    def update_configuration(self, config: Dict[str, Any]) -> None:
        """Update agent configuration (for hot reload)"""
        self._config.update(config)
        if 'custom_prompt' in config:
            self._custom_prompt = config['custom_prompt']
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current agent configuration"""
        return self._config.copy()
    
    async def get_prompt_template(self, settings_service: Optional[Any] = None) -> Optional[str]:
        """Get custom prompt if configured"""
        if self._custom_prompt:
            return self._custom_prompt
        
        if settings_service:
            try:
                metadata = self.get_metadata()
                return await settings_service.get_agent_prompt(metadata.name)
            except Exception as e:
                logger.warning(f"Failed to get custom prompt for {metadata.name}: {e}")
        
        return None
    
    def _parse_llm_response(self, response_content: str) -> List[Dict[str, Any]]:
        """
        Parse LLM JSON response into threat dictionaries
        Handles common parsing errors gracefully
        """
        import json
        import re
        
        try:
            # Try direct JSON parsing first
            if response_content.strip().startswith('['):
                return json.loads(response_content)
            elif response_content.strip().startswith('{'):
                return [json.loads(response_content)]
            
            # Extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Extract JSON from text
            json_match = re.search(r'(\[.*?\])', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            logger.warning(f"Could not parse LLM response as JSON: {response_content[:200]}...")
            return []
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing LLM response: {e}")
            return []
    
    def _create_threat_output(
        self,
        threat_dict: Dict[str, Any],
        agent_name: str,
        confidence: float = 0.8
    ) -> ThreatOutput:
        """Convert parsed threat dict to ThreatOutput"""
        
        # Generate unique ID
        threat_name = threat_dict.get('Threat Name', 'Unknown Threat')
        threat_id = f"{agent_name}_{hash(threat_name) & 0xFFFFFF:06x}"
        
        return ThreatOutput(
            threat_id=threat_id,
            threat_name=threat_name,
            description=threat_dict.get('Description', ''),
            stride_category=threat_dict.get('STRIDE Category', 'Unknown'),
            affected_component=threat_dict.get('Affected Component', ''),
            potential_impact=threat_dict.get('Potential Impact', 'Medium'),
            likelihood=threat_dict.get('Likelihood', 'Medium'),
            mitigation_strategy=threat_dict.get('Suggested Mitigation', ''),
            
            # Enhanced fields from V3
            residual_risk=threat_dict.get('residual_risk'),
            controls_detected=threat_dict.get('controls_detected'),
            threat_class=threat_dict.get('threat_class'),
            financial_exposure=threat_dict.get('financial_exposure'),
            regulatory_implications=threat_dict.get('regulatory_implications'),
            business_impact=threat_dict.get('business_impact'),
            priority_score=threat_dict.get('priority_score'),
            cwe_references=threat_dict.get('cwe_references'),
            
            # Agent metadata
            agent_source=agent_name,
            confidence_score=confidence
        )