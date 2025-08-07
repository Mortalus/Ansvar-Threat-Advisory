"""
STRIDE-focused data extraction service for threat modeling pipeline.
This service performs two-pass extraction:
1. STRIDE Expert Pass: Extract security-relevant information using STRIDE methodology
2. Quality Validator Pass: Enhance and validate the extracted data
"""

import json
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError

from app.core.llm.base import BaseLLMProvider
from app.utils.token_counter import TokenCounter

logger = logging.getLogger(__name__)

class SecurityAsset(BaseModel):
    """Security-focused asset definition"""
    name: str
    type: str = Field(description="Database, File Store, Cache, API, Service, etc.")
    sensitivity: str = Field(description="Public, Internal, Confidential, Restricted")
    data_types: list[str] = Field(description="Types of data stored/processed")
    security_controls: list[str] = Field(default_factory=list, description="Existing security measures")
    compliance_requirements: list[str] = Field(default_factory=list, description="Regulatory requirements")

class TrustZone(BaseModel):
    """Trust boundary definition"""
    name: str
    security_level: str = Field(description="Public, DMZ, Internal, Restricted")
    components: list[str] = Field(description="Components within this zone")
    access_controls: list[str] = Field(default_factory=list, description="Access control mechanisms")
    network_controls: list[str] = Field(default_factory=list, description="Network security controls")

class SecurityDataFlow(BaseModel):
    """Security-focused data flow definition"""
    source: str
    destination: str
    data_description: str
    data_classification: str = Field(description="Public, Internal, Confidential, Restricted")
    protocol: str = Field(description="HTTP, HTTPS, TLS, SSH, etc.")
    authentication: str = Field(description="Authentication mechanism")
    authorization: str = Field(description="Authorization mechanism")
    encryption: str = Field(description="Encryption method")
    stride_threats: list[str] = Field(default_factory=list, description="Potential STRIDE threats")

class AccessPattern(BaseModel):
    """User/system access pattern"""
    actor: str
    target_assets: list[str]
    access_type: str = Field(description="Read, Write, Execute, Admin")
    authentication_required: bool
    authorization_level: str
    typical_frequency: str = Field(description="Continuous, Frequent, Occasional, Rare")

class ExtractedSecurityData(BaseModel):
    """Complete extracted security data structure"""
    project_name: str
    project_description: str
    industry_context: str
    compliance_frameworks: list[str] = Field(default_factory=list)
    
    # Core components
    external_entities: list[str] = Field(description="External users, systems, services")
    security_assets: list[SecurityAsset] = Field(description="Security-focused asset inventory")
    processes: list[str] = Field(description="Services, applications, functions")
    trust_zones: list[TrustZone] = Field(description="Trust boundaries and zones")
    
    # Security-specific data
    security_data_flows: list[SecurityDataFlow] = Field(description="Security-annotated data flows")
    access_patterns: list[AccessPattern] = Field(description="User and system access patterns")
    
    # Risk context
    business_criticality: str = Field(description="High, Medium, Low")
    regulatory_environment: str = Field(description="Regulatory context")
    threat_landscape: list[str] = Field(default_factory=list, description="Known threat vectors")
    
    # Metadata
    extraction_method: str = "stride_focused"
    extracted_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    quality_score: Optional[float] = None
    completeness_indicators: Dict[str, bool] = Field(default_factory=dict)

# STRIDE Expert Prompt
STRIDE_EXPERT_PROMPT = """
You are a senior cybersecurity expert specializing in STRIDE threat modeling methodology. Your task is to analyze technical documentation and extract security-relevant information using STRIDE principles.

STRIDE Framework Focus:
- Spoofing: Identity and authentication vulnerabilities
- Tampering: Data integrity threats
- Repudiation: Non-repudiation and audit trails
- Information Disclosure: Confidentiality and privacy risks
- Denial of Service: Availability threats
- Elevation of Privilege: Authorization and access control issues

Extract ONLY the following JSON structure - no explanations or markdown:

{
  "project_name": "System/project name",
  "project_description": "Brief description of the system",
  "industry_context": "Industry domain (Healthcare, Finance, etc.)",
  "compliance_frameworks": ["GDPR", "HIPAA", "PCI-DSS", etc.],
  
  "external_entities": ["External users/systems that interact with the system"],
  "security_assets": [
    {
      "name": "Asset name",
      "type": "Database|FileStore|API|Service|Cache|etc.",
      "sensitivity": "Public|Internal|Confidential|Restricted",
      "data_types": ["Personal data", "Financial data", etc.],
      "security_controls": ["Encryption", "Access logging", etc.],
      "compliance_requirements": ["GDPR Article 32", etc.]
    }
  ],
  "processes": ["Services, APIs, applications that process data"],
  "trust_zones": [
    {
      "name": "Zone name",
      "security_level": "Public|DMZ|Internal|Restricted",
      "components": ["Components in this zone"],
      "access_controls": ["Authentication methods"],
      "network_controls": ["Firewall rules", "VPN", etc.]
    }
  ],
  "security_data_flows": [
    {
      "source": "Source component",
      "destination": "Destination component", 
      "data_description": "Data being transferred",
      "data_classification": "Public|Internal|Confidential|Restricted",
      "protocol": "HTTPS|TLS|SSH|etc.",
      "authentication": "OAuth2|API Key|Certificate|etc.",
      "authorization": "RBAC|ACL|etc.",
      "encryption": "TLS 1.3|AES-256|etc.",
      "stride_threats": ["Potential STRIDE threats for this flow"]
    }
  ],
  "access_patterns": [
    {
      "actor": "User/system type",
      "target_assets": ["Assets they access"],
      "access_type": "Read|Write|Execute|Admin",
      "authentication_required": true|false,
      "authorization_level": "User|Admin|System",
      "typical_frequency": "Continuous|Frequent|Occasional|Rare"
    }
  ],
  "business_criticality": "High|Medium|Low",
  "regulatory_environment": "Description of regulatory context",
  "threat_landscape": ["Known threats from document"]
}

Focus on:
1. Security-relevant components and their relationships
2. Data sensitivity and classification
3. Authentication/authorization mechanisms
4. Trust boundaries and access controls
5. Compliance requirements
6. Potential STRIDE threat vectors

Document to analyze:
"""

# Quality Validator Prompt
QUALITY_VALIDATOR_PROMPT = """
You are a security architecture quality assurance expert. Compare the original document with extracted security data and enhance it for completeness and accuracy.

Your task:
1. Verify all security-relevant information was captured
2. Identify missing components, trust boundaries, or data flows
3. Enhance data classifications and security controls
4. Validate STRIDE threat associations
5. Ensure compliance requirements are complete

Return enhanced JSON in the same format, adding:
- Missing components you find in the original document
- More precise security classifications
- Additional security controls mentioned
- More complete STRIDE threat mappings
- Quality indicators for completeness

Add these fields to the JSON:
- "quality_score": 0.0-1.0 (completeness score)
- "completeness_indicators": {
  "assets_complete": true|false,
  "data_flows_complete": true|false,
  "trust_zones_complete": true|false,
  "security_controls_complete": true|false,
  "stride_analysis_complete": true|false
}

Original document:
{document}

Extracted data to validate and enhance:
{extracted_data}

Return the enhanced JSON structure:
"""

class StrideDataExtractor:
    """STRIDE-focused data extraction with quality validation"""
    
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm_provider = llm_provider
    
    async def extract_security_data(
        self,
        document_text: str,
        enable_quality_validation: bool = True
    ) -> Tuple[ExtractedSecurityData, Dict[str, Any]]:
        """
        Resilient STRIDE-focused data extraction with multiple fallback layers
        
        Args:
            document_text: Raw document content
            enable_quality_validation: Whether to attempt quality validation pass
            
        Returns:
            Tuple of (extracted_data, metadata) - ALWAYS succeeds with valid data
        """
        metadata = {
            "extraction_method": "stride_focused",
            "passes_performed": [],
            "token_usage": {},
            "quality_validation_enabled": enable_quality_validation,
            "fallback_used": None,
            "errors": []
        }
        
        logger.info("🛡️ Starting resilient STRIDE-focused data extraction")
        logger.info(f"📄 Document length: {len(document_text)} characters")
        
        # Layer 1: Try STRIDE Expert Extraction
        try:
            logger.info("🔍 Layer 1: STRIDE Expert Analysis")
            stride_result, stride_tokens = await self._stride_expert_pass(document_text)
            metadata["passes_performed"].append("stride_expert")
            metadata["token_usage"]["stride_expert"] = stride_tokens
            
            # Ensure we have basic quality metrics
            if not hasattr(stride_result, 'quality_score') or stride_result.quality_score is None:
                stride_result.quality_score = 0.7
            if not hasattr(stride_result, 'completeness_indicators') or not stride_result.completeness_indicators:
                stride_result.completeness_indicators = {
                    "assets_complete": len(stride_result.security_assets) > 0,
                    "data_flows_complete": len(stride_result.security_data_flows) > 0,
                    "trust_zones_complete": len(stride_result.trust_zones) > 0,
                    "security_controls_complete": False,
                    "stride_analysis_complete": False
                }
            
            logger.info("✅ STRIDE expert extraction successful")
            
            # Layer 2: Try Quality Validation (completely optional)
            if enable_quality_validation:
                enhanced_result = await self._safe_quality_validation(document_text, stride_result, metadata)
                if enhanced_result:
                    return enhanced_result, metadata
            
            # Return STRIDE expert results (guaranteed success)
            metadata["token_usage"]["total"] = stride_tokens
            return stride_result, metadata
            
        except Exception as e:
            logger.error(f"❌ STRIDE expert pass failed: {e}")
            metadata["errors"].append(f"stride_expert_failed: {str(e)}")
            
        # Layer 3: Minimal extraction fallback
        logger.warning("🆘 Using minimal extraction fallback")
        return await self._minimal_extraction_fallback(document_text, metadata)
    
    async def _stride_expert_pass(
        self, 
        document_text: str
    ) -> Tuple[ExtractedSecurityData, int]:
        """First pass: STRIDE expert analysis"""
        
        prompt = STRIDE_EXPERT_PROMPT + document_text
        
        logger.info("🤖 Sending document to STRIDE expert...")
        response = await self.llm_provider.generate(
            prompt=prompt,
            system_prompt="You are a STRIDE cybersecurity expert specializing in extracting security-relevant information from system architecture documents. Output only valid JSON.",
            max_tokens=4000,
            temperature=0.1
        )
        
        token_usage = response.usage.get("total_tokens", 0) if response.usage else 0
        logger.info(f"🪙 STRIDE expert tokens: {token_usage}")
        
        try:
            # Parse JSON response with resilient cleaning
            extracted_json = self._parse_llm_json_response(response.content, "STRIDE expert")
            
            # Convert to Pydantic model for validation
            extracted_data = ExtractedSecurityData(**extracted_json)
            
            logger.info("✅ STRIDE expert extraction successful")
            logger.info(f"📊 Extracted: {len(extracted_data.security_assets)} assets, "
                       f"{len(extracted_data.security_data_flows)} data flows, "
                       f"{len(extracted_data.trust_zones)} trust zones")
            
            return extracted_data, token_usage
            
        except Exception as e:
            logger.error(f"❌ STRIDE expert extraction failed: {e}")
            logger.error(f"Raw response: {response.content[:500]}...")
            
            # Don't return fallback here - let the main method handle it
            raise e
    
    async def _quality_validator_pass(
        self,
        document_text: str,
        stride_data: ExtractedSecurityData
    ) -> Tuple[ExtractedSecurityData, int]:
        """Second pass: Quality validation and enhancement"""
        
        # Prepare validation prompt
        stride_json = stride_data.model_dump_json(indent=2)
        prompt = QUALITY_VALIDATOR_PROMPT.format(
            document=document_text[:3000],  # Truncate for token limits
            extracted_data=stride_json
        )
        
        logger.info("🔍 Sending to quality validator...")
        response = await self.llm_provider.generate(
            prompt=prompt,
            system_prompt="You are a cybersecurity quality validator. Your role is to enhance and validate security data extraction results. Output only valid JSON.",
            max_tokens=4000,
            temperature=0.1
        )
        
        token_usage = response.usage.get("total_tokens", 0) if response.usage else 0
        logger.info(f"🪙 Quality validator tokens: {token_usage}")
        
        try:
            # Parse JSON response with resilient cleaning
            enhanced_json = self._parse_llm_json_response(response.content, "Quality validator")
            
            # Convert to Pydantic model
            enhanced_data = ExtractedSecurityData(**enhanced_json)
            
            logger.info("✅ Quality validation successful")
            
            # Log quality improvements
            if enhanced_data.quality_score:
                logger.info(f"📈 Quality score: {enhanced_data.quality_score:.2f}")
            
            if enhanced_data.completeness_indicators:
                complete_areas = sum(enhanced_data.completeness_indicators.values())
                total_areas = len(enhanced_data.completeness_indicators)
                logger.info(f"📊 Completeness: {complete_areas}/{total_areas} areas complete")
            
            return enhanced_data, token_usage
            
        except Exception as e:
            logger.warning(f"⚠️ Quality validation JSON parsing failed: {e}")
            
            # Re-raise to be handled by _safe_quality_validation
            raise e
    
    async def _safe_quality_validation(
        self,
        document_text: str,
        stride_data: ExtractedSecurityData,
        metadata: Dict[str, Any]
    ) -> Optional[ExtractedSecurityData]:
        """
        Safe quality validation with comprehensive error handling
        Returns enhanced result on success, None on any failure
        """
        try:
            logger.info("🔍 Layer 2: Safe Quality Validation")
            
            # Pre-flight check: ensure stride_data can be serialized
            try:
                test_json = stride_data.model_dump_json(indent=2)
                logger.info("✅ Stride data serialization check passed")
            except Exception as serialize_e:
                logger.warning(f"⚠️ Stride data cannot be serialized, skipping quality validation: {serialize_e}")
                metadata["errors"].append(f"serialization_failed: {str(serialize_e)}")
                return None
            
            # Attempt quality validation
            enhanced_result, quality_tokens = await self._quality_validator_pass(
                document_text, stride_data
            )
            
            metadata["passes_performed"].append("quality_validator")
            metadata["token_usage"]["quality_validator"] = quality_tokens
            metadata["token_usage"]["total"] = metadata["token_usage"]["stride_expert"] + quality_tokens
            
            logger.info("✅ Quality validation successful")
            logger.info(f"🎯 Quality Score: {enhanced_result.quality_score}")
            
            return enhanced_result
            
        except Exception as e:
            logger.warning(f"⚠️ Quality validation failed safely: {e}")
            metadata["errors"].append(f"quality_validation_failed: {str(e)}")
            metadata["passes_performed"].append("quality_validator_failed")
            return None
    
    async def _minimal_extraction_fallback(
        self,
        document_text: str,
        metadata: Dict[str, Any]
    ) -> Tuple[ExtractedSecurityData, Dict[str, Any]]:
        """
        Minimal fallback that always succeeds - extracts basic info from document
        """
        logger.info("🆘 Creating minimal security data from document analysis")
        
        # Basic document analysis without LLM
        words = document_text.lower().split()
        word_count = len(words)
        
        # Extract potential asset names (simple heuristics)
        potential_assets = []
        asset_keywords = ['database', 'server', 'api', 'service', 'cache', 'queue', 'storage', 'file']
        for word in words:
            if any(keyword in word for keyword in asset_keywords):
                if word not in potential_assets and len(potential_assets) < 5:
                    potential_assets.append(word.title())
        
        # Create minimal security data
        minimal_data = ExtractedSecurityData(
            project_name="Document Analysis",
            project_description="Extracted from document content",
            industry_context="Technology",
            compliance_frameworks=[],
            external_entities=["Users", "External Services"],
            security_assets=[
                SecurityAsset(
                    name=asset,
                    type="Component",
                    sensitivity="Internal",
                    data_types=["Application Data"],
                    security_controls=[],
                    compliance_requirements=[]
                ) for asset in potential_assets[:3]  # Limit to 3 assets
            ],
            processes=["Data Processing", "User Authentication"],
            trust_zones=[
                TrustZone(
                    name="Internal Network",
                    security_level="Internal",
                    components=["Application Components"],
                    access_controls=[],
                    network_controls=[]
                )
            ],
            security_data_flows=[],
            access_patterns=[
                AccessPattern(
                    actor="User",
                    target_assets=potential_assets[:1] if potential_assets else ["System"],
                    access_type="Read",
                    authentication_required=True,
                    authorization_level="User",
                    typical_frequency="Frequent"
                )
            ],
            business_criticality="Medium",
            regulatory_environment="Standard",
            threat_landscape=["Data Breach", "Unauthorized Access"],
            quality_score=0.3,  # Low score for fallback
            completeness_indicators={
                "assets_complete": len(potential_assets) > 0,
                "data_flows_complete": False,
                "trust_zones_complete": True,
                "security_controls_complete": False,
                "stride_analysis_complete": False
            }
        )
        
        metadata["fallback_used"] = "minimal_extraction"
        metadata["token_usage"]["stride_expert"] = 0
        metadata["token_usage"]["total"] = 0
        metadata["passes_performed"].append("minimal_fallback")
        
        logger.info("✅ Minimal extraction fallback completed")
        return minimal_data, metadata
    
    def _parse_llm_json_response(self, raw_response: str, context: str = "LLM") -> Dict[str, Any]:
        """
        Resilient JSON parsing with multiple repair strategies
        """
        logger.info(f"🔍 Parsing {context} JSON response ({len(raw_response)} chars)")
        
        # Strategy 1: Try parsing as-is
        try:
            return json.loads(raw_response.strip())
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract from markdown wrapper
        try:
            if "```json" in raw_response:
                json_start = raw_response.find('{')
                json_end = raw_response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    content = raw_response[json_start:json_end]
                    logger.info("🔧 Extracted JSON from markdown")
                    return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Remove outer quotes and escaping
        try:
            content = raw_response.strip()
            content = content.replace('\\n', '').replace('\\"', '"')
            
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1]
                logger.info("🔧 Removed outer quotes")
                
            # Try to find JSON boundaries
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                content = content[json_start:json_end]
                logger.info("🔧 Extracted JSON boundaries")
                return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Strategy 4: Last resort - regex extraction
        try:
            import re
            json_pattern = r'\{.*\}'
            matches = re.findall(json_pattern, raw_response, re.DOTALL)
            if matches:
                logger.info("🔧 Found JSON via regex")
                return json.loads(matches[0])
        except json.JSONDecodeError:
            pass
        
        # All strategies failed
        logger.error(f"❌ All JSON parsing strategies failed for {context}")
        logger.error(f"Raw response sample: {raw_response[:200]}...")
        raise json.JSONDecodeError(f"Unable to parse {context} JSON response", raw_response, 0)

async def extract_stride_security_data(
    llm_provider: BaseLLMProvider,
    document_text: str,
    enable_quality_validation: bool = True
) -> Tuple[ExtractedSecurityData, Dict[str, Any]]:
    """
    Convenience function for STRIDE-focused security data extraction
    
    Args:
        llm_provider: LLM provider instance
        document_text: Raw document content
        enable_quality_validation: Whether to run quality validation
        
    Returns:
        Tuple of (extracted_security_data, extraction_metadata)
    """
    extractor = StrideDataExtractor(llm_provider)
    return await extractor.extract_security_data(
        document_text=document_text,
        enable_quality_validation=enable_quality_validation
    )