import json
import logging
from typing import Optional, Dict, Any
from app.core.llm.base import BaseLLMProvider, LLMResponse
from app.models.dfd import DFDComponents, DataFlow
from pydantic import ValidationError

logger = logging.getLogger(__name__)

# The comprehensive prompt for DFD extraction
EXTRACT_PROMPT_TEMPLATE = """
You are a senior cybersecurity analyst specializing in threat modeling and Data Flow Diagram (DFD) extraction. Your task is to analyze technical documentation and extract structured components for creating a DFD.

IMPORTANT: You must output ONLY valid JSON that matches the exact schema below. Do not include any explanatory text, markdown formatting, or comments.

Required JSON Schema:
{{
  "project_name": "string - Name of the system/project",
  "project_version": "string - Version number",
  "industry_context": "string - Industry or domain (e.g., Healthcare, Finance, E-commerce)",
  "external_entities": ["array of strings - External users, systems, or third-party services"],
  "assets": ["array of strings - Data stores, databases, file systems, caches"],
  "processes": ["array of strings - Services, applications, functions, APIs"],
  "trust_boundaries": ["array of strings - Network zones, security perimeters"],
  "data_flows": [
    {{
      "source": "string - Origin component",
      "destination": "string - Target component",
      "data_description": "string - What data is transferred",
      "data_classification": "string - Confidential/PII/Internal/Public",
      "protocol": "string - HTTPS/TLS/SSH/etc",
      "authentication_mechanism": "string - OAuth2/API Key/Certificate/etc"
    }}
  ]
}}

Analysis Guidelines:
1. External Entities: Identify users, external systems, third-party APIs, payment gateways, etc.
2. Assets: Find databases, file storage, caches, data warehouses, S3 buckets, etc.
3. Processes: Extract microservices, APIs, web servers, processing engines, Lambda functions, etc.
4. Trust Boundaries: Identify DMZs, VPCs, network segments, cloud boundaries, etc.
5. Data Flows: Map connections showing data movement between components

For data_classification, use:
- "Confidential" for passwords, keys, tokens, financial data
- "PII" for personal identifiable information
- "Internal" for business logic, internal communications
- "Public" for publicly accessible data

Extract information even if partially specified. Use reasonable defaults where information is unclear.

Input Documents:
---
{documents}
---

Output ONLY the JSON, with no additional commentary or formatting.
"""

async def extract_dfd_from_text(
    llm_provider: BaseLLMProvider,
    document_text: str,
    use_instructor: bool = True
) -> DFDComponents:
    """
    Extract DFD components from document text using an LLM provider.
    
    Args:
        llm_provider: The LLM provider instance to use
        document_text: The combined text from uploaded documents
        use_instructor: Whether to use instructor library for structured output
    
    Returns:
        DFDComponents model with extracted information
    """
    prompt = EXTRACT_PROMPT_TEMPLATE.format(documents=document_text[:15000])  # Limit context size
    
    logger.info(f"Extracting DFD components using {llm_provider.__class__.__name__}")
    
    try:
        if use_instructor and hasattr(llm_provider, 'client'):
            # Use instructor for structured output (if available)
            try:
                import instructor
                
                # Patch the client with instructor
                client = instructor.patch(llm_provider.client)
                
                response = client.chat.completions.create(
                    model=getattr(llm_provider, 'model', 'gpt-4'),
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a cybersecurity expert extracting DFD components. Output only valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    response_model=DFDComponents,
                    max_retries=3,
                    temperature=0.1  # Low temperature for consistent output
                )
                
                logger.info("Successfully extracted DFD components using instructor")
                return response
                
            except ImportError:
                logger.warning("Instructor library not available, falling back to standard extraction")
            except Exception as e:
                logger.info(f"Instructor extraction not available with {llm_provider.__class__.__name__}: {e}")
                logger.info("Using standard LLM provider interface for DFD extraction")
        
        # Fallback to standard LLM call with JSON parsing
        response = await llm_provider.generate(
            prompt=prompt,
            system_prompt="You are a cybersecurity expert. Output only valid JSON matching the schema provided."
        )
        
        # Parse the response
        return parse_llm_response(response.content)
        
    except Exception as e:
        logger.error(f"Failed to extract DFD components: {e}")
        # Return a default structure with error indication
        return DFDComponents(
            project_name="Extraction Failed",
            project_version="0.0",
            industry_context=f"Error: {str(e)[:100]}",
            external_entities=["Error during extraction"],
            assets=[],
            processes=[],
            trust_boundaries=[],
            data_flows=[]
        )

def parse_llm_response(response_text: str) -> DFDComponents:
    """
    Parse LLM response text into DFDComponents model.
    Handles various response formats and cleans up the text.
    """
    try:
        # Clean up the response text
        cleaned_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        
        cleaned_text = cleaned_text.strip()
        
        # Try to find JSON in the response
        json_start = cleaned_text.find('{')
        json_end = cleaned_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_text = cleaned_text[json_start:json_end]
        else:
            json_text = cleaned_text
        
        # Parse JSON
        data = json.loads(json_text)
        
        # Validate and create DFDComponents
        return DFDComponents(**data)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from LLM response: {e}")
        logger.debug(f"Response text: {response_text[:500]}")
        
        # Try to extract at least some information
        return extract_fallback_components(response_text)
        
    except ValidationError as e:
        logger.error(f"Validation error creating DFDComponents: {e}")
        
        # Try to fix common issues
        if isinstance(data, dict):
            # Ensure all required fields exist
            data.setdefault('project_name', 'Unknown Project')
            data.setdefault('project_version', '1.0')
            data.setdefault('industry_context', 'Unknown')
            data.setdefault('external_entities', [])
            data.setdefault('assets', [])
            data.setdefault('processes', [])
            data.setdefault('trust_boundaries', [])
            data.setdefault('data_flows', [])
            
            # Try again with defaults
            try:
                return DFDComponents(**data)
            except:
                pass
        
        return DFDComponents()

def extract_fallback_components(text: str) -> DFDComponents:
    """
    Fallback extraction using simple pattern matching.
    Used when JSON parsing fails.
    """
    components = DFDComponents()
    
    # Try to extract project name
    if "project" in text.lower() or "system" in text.lower():
        lines = text.split('\n')
        for line in lines:
            if "project" in line.lower() or "system" in line.lower():
                # Take the first meaningful line as project name
                components.project_name = line.strip()[:100]
                break
    
    # Look for common component patterns
    text_lower = text.lower()
    
    # External entities patterns
    if "user" in text_lower or "customer" in text_lower:
        components.external_entities.append("User")
    if "admin" in text_lower:
        components.external_entities.append("Administrator")
    if "api" in text_lower or "third-party" in text_lower:
        components.external_entities.append("External API")
    
    # Assets patterns
    if "database" in text_lower or "db" in text_lower:
        components.assets.append("Database")
    if "storage" in text_lower or "s3" in text_lower:
        components.assets.append("File Storage")
    if "cache" in text_lower or "redis" in text_lower:
        components.assets.append("Cache")
    
    # Processes patterns
    if "server" in text_lower:
        components.processes.append("Web Server")
    if "service" in text_lower:
        components.processes.append("Backend Service")
    if "api" in text_lower:
        components.processes.append("API Gateway")
    
    # Trust boundaries
    if "dmz" in text_lower or "internet" in text_lower:
        components.trust_boundaries.append("Internet Boundary")
    if "internal" in text_lower or "private" in text_lower:
        components.trust_boundaries.append("Internal Network")
    
    return components

async def validate_dfd_components(components: DFDComponents) -> Dict[str, Any]:
    """
    Validate and enrich DFD components with quality metrics.
    
    Returns:
        Dictionary with validation results and quality scores
    """
    validation_result = {
        "is_valid": True,
        "warnings": [],
        "quality_score": 100,
        "component_counts": {
            "external_entities": len(components.external_entities),
            "assets": len(components.assets),
            "processes": len(components.processes),
            "trust_boundaries": len(components.trust_boundaries),
            "data_flows": len(components.data_flows)
        }
    }
    
    # Check for minimum components
    if len(components.external_entities) == 0:
        validation_result["warnings"].append("No external entities identified")
        validation_result["quality_score"] -= 20
    
    if len(components.processes) == 0:
        validation_result["warnings"].append("No processes identified")
        validation_result["quality_score"] -= 20
    
    if len(components.data_flows) == 0:
        validation_result["warnings"].append("No data flows identified")
        validation_result["quality_score"] -= 30
    
    # Check data flow validity
    all_components = set(components.external_entities + components.assets + components.processes)
    for flow in components.data_flows:
        if flow.source not in all_components:
            validation_result["warnings"].append(f"Data flow source '{flow.source}' not in component list")
        if flow.destination not in all_components:
            validation_result["warnings"].append(f"Data flow destination '{flow.destination}' not in component list")
    
    validation_result["is_valid"] = validation_result["quality_score"] >= 50
    
    return validation_result