"""
Comprehensive Agent Validation and Safety System

Provides multi-layer validation, safety checks, and quality assurance
for agent operations and outputs.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .base import BaseAgent, AgentExecutionContext, ThreatOutput

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation strictness levels"""
    MINIMAL = "minimal"      # Basic checks only
    STANDARD = "standard"    # Default validation
    STRICT = "strict"        # Comprehensive validation
    PARANOID = "paranoid"    # Maximum validation with redundancy


class ValidationResult:
    """Result of a validation check"""
    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.timestamp = datetime.utcnow()
    
    def add_error(self, error: str):
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        self.warnings.append(warning)
    
    def merge(self, other: 'ValidationResult'):
        """Merge another validation result into this one"""
        self.is_valid = self.is_valid and other.is_valid
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "timestamp": self.timestamp.isoformat()
        }


class AgentValidator:
    """
    Comprehensive validation system for agents
    Ensures safety, quality, and consistency of agent operations
    """
    
    def __init__(self, level: ValidationLevel = ValidationLevel.STANDARD):
        self.level = level
        self.validation_rules = self._initialize_rules()
        self.safety_patterns = self._initialize_safety_patterns()
        self.quality_thresholds = self._initialize_quality_thresholds()
        
    def _initialize_rules(self) -> Dict[str, callable]:
        """Initialize validation rules based on level"""
        rules = {
            "validate_context": self._validate_context,
            "validate_agent_metadata": self._validate_agent_metadata,
            "validate_output_structure": self._validate_output_structure,
            "validate_threat_quality": self._validate_threat_quality,
        }
        
        if self.level in [ValidationLevel.STRICT, ValidationLevel.PARANOID]:
            rules.update({
                "validate_security_compliance": self._validate_security_compliance,
                "validate_data_consistency": self._validate_data_consistency,
                "validate_performance_bounds": self._validate_performance_bounds,
            })
        
        if self.level == ValidationLevel.PARANOID:
            rules.update({
                "validate_redundant_checks": self._validate_redundant_checks,
                "validate_cross_references": self._validate_cross_references,
            })
        
        return rules
    
    def _initialize_safety_patterns(self) -> Dict[str, re.Pattern]:
        """Initialize patterns for safety validation"""
        return {
            # Security-sensitive patterns
            "api_key": re.compile(r'[a-zA-Z0-9]{32,}'),
            "private_key": re.compile(r'-----BEGIN [A-Z]+ PRIVATE KEY-----'),
            "password": re.compile(r'password["\']?\s*[:=]\s*["\'][^"\']+["\']', re.IGNORECASE),
            "token": re.compile(r'token["\']?\s*[:=]\s*["\'][^"\']+["\']', re.IGNORECASE),
            
            # Injection patterns
            "sql_injection": re.compile(r'(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE)\s+(TABLE|DATABASE)', re.IGNORECASE),
            "script_injection": re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
            "command_injection": re.compile(r'[;&|`$]|\$\(.*\)'),
            
            # Data quality patterns
            "excessive_length": re.compile(r'.{10000,}'),  # Strings over 10k chars
            "suspicious_encoding": re.compile(r'\\x[0-9a-f]{2}|\\u[0-9a-f]{4}'),
            "malformed_json": re.compile(r'[{}]\s*[{}]'),  # Adjacent braces without content
        }
    
    def _initialize_quality_thresholds(self) -> Dict[str, Any]:
        """Initialize quality thresholds based on validation level"""
        base_thresholds = {
            "min_threat_description_length": 20,
            "max_threat_description_length": 5000,
            "min_threats_per_component": 1,
            "max_threats_per_component": 50,
            "min_mitigation_length": 10,
            "max_mitigation_length": 2000,
            "max_execution_time_seconds": 60,
            "max_token_usage": 100000,
        }
        
        # Adjust based on level
        if self.level == ValidationLevel.MINIMAL:
            base_thresholds["min_threat_description_length"] = 10
            base_thresholds["max_threats_per_component"] = 100
        elif self.level == ValidationLevel.STRICT:
            base_thresholds["min_threat_description_length"] = 50
            base_thresholds["max_threats_per_component"] = 30
        elif self.level == ValidationLevel.PARANOID:
            base_thresholds["min_threat_description_length"] = 100
            base_thresholds["max_threats_per_component"] = 20
            base_thresholds["max_execution_time_seconds"] = 30
        
        return base_thresholds
    
    def validate_agent_input(self, agent: BaseAgent, context: AgentExecutionContext) -> ValidationResult:
        """
        Validate agent input before execution
        """
        result = ValidationResult(True)
        
        # Validate context
        context_result = self._validate_context(context)
        result.merge(context_result)
        
        # Validate agent readiness
        agent_result = self._validate_agent_metadata(agent)
        result.merge(agent_result)
        
        # Check for security issues in input
        if self.level != ValidationLevel.MINIMAL:
            security_result = self._validate_input_security(context)
            result.merge(security_result)
        
        return result
    
    def validate_agent_output(self, output: Any, agent_name: str) -> ValidationResult:
        """
        Validate agent output after execution
        """
        result = ValidationResult(True)
        
        # Validate output structure
        structure_result = self._validate_output_structure(output)
        result.merge(structure_result)
        
        # Validate threat quality
        if isinstance(output, (list, ThreatOutput)):
            quality_result = self._validate_threat_quality(output)
            result.merge(quality_result)
        
        # Security validation
        if self.level in [ValidationLevel.STANDARD, ValidationLevel.STRICT, ValidationLevel.PARANOID]:
            security_result = self._validate_output_security(output)
            result.merge(security_result)
        
        # Data consistency checks
        if self.level in [ValidationLevel.STRICT, ValidationLevel.PARANOID]:
            consistency_result = self._validate_data_consistency(output)
            result.merge(consistency_result)
        
        return result
    
    def _validate_context(self, context: AgentExecutionContext) -> ValidationResult:
        """Validate execution context"""
        result = ValidationResult(True)
        
        # Required fields
        if not context.pipeline_id:
            result.add_error("Pipeline ID is required")
        
        # Document validation
        if context.document_text:
            if len(context.document_text) > 1000000:  # 1MB limit
                result.add_error("Document content exceeds maximum size (1MB)")
            
            if len(context.document_text) < 10:
                result.add_warning("Document content is very short")
        
        # Component validation
        if context.components:
            if not isinstance(context.components, dict):
                result.add_error("Components must be a dictionary")
            elif len(context.components) > 1000:
                result.add_error("Too many components (max 1000)")
            else:
                for name, comp in context.components.items():
                    if not isinstance(comp, dict):
                        result.add_error(f"Component {name} must be a dictionary")
        
        return result
    
    def _validate_agent_metadata(self, agent: BaseAgent) -> ValidationResult:
        """Validate agent metadata and configuration"""
        result = ValidationResult(True)
        
        try:
            metadata = agent.get_metadata()
            
            # Required fields
            if not metadata.name:
                result.add_error("Agent name is required")
            
            if not metadata.version:
                result.add_warning("Agent version not specified")
            
            if metadata.priority < 0 or metadata.priority > 1000:
                result.add_error(f"Invalid agent priority: {metadata.priority}")
            
            # Category validation
            valid_categories = ['architecture', 'business', 'compliance', 'security', 'custom']
            if metadata.category not in valid_categories:
                result.add_warning(f"Non-standard agent category: {metadata.category}")
            
            # Token estimation
            if metadata.estimated_tokens <= 0:
                result.add_warning("Invalid token estimation")
            elif metadata.estimated_tokens > self.quality_thresholds["max_token_usage"]:
                result.add_warning(f"Agent may use excessive tokens: {metadata.estimated_tokens}")
            
        except Exception as e:
            result.add_error(f"Failed to validate agent metadata: {e}")
        
        return result
    
    def _validate_output_structure(self, output: Any) -> ValidationResult:
        """Validate output structure and format"""
        result = ValidationResult(True)
        
        if output is None:
            result.add_error("Agent returned null output")
            return result
        
        # Check for ThreatOutput or list of threats
        if isinstance(output, ThreatOutput):
            if not output.threats:
                result.add_warning("No threats generated")
            elif len(output.threats) > 500:
                result.add_error("Too many threats generated (max 500)")
        
        elif isinstance(output, list):
            if len(output) == 0:
                result.add_warning("Empty threat list")
            elif len(output) > 500:
                result.add_error("Too many threats in list (max 500)")
            
            # Validate each threat
            for i, threat in enumerate(output):
                if not isinstance(threat, dict):
                    result.add_error(f"Threat {i} is not a dictionary")
                elif 'description' not in threat:
                    result.add_error(f"Threat {i} missing description")
        
        elif isinstance(output, dict):
            # Validate dictionary structure
            if 'threats' not in output and 'results' not in output:
                result.add_warning("Output dictionary missing standard threat fields")
        
        else:
            result.add_error(f"Unexpected output type: {type(output)}")
        
        return result
    
    def _validate_threat_quality(self, output: Any) -> ValidationResult:
        """Validate threat quality and completeness"""
        result = ValidationResult(True)
        
        threats = []
        if isinstance(output, ThreatOutput):
            threats = output.threats
        elif isinstance(output, list):
            threats = output
        elif isinstance(output, dict) and 'threats' in output:
            threats = output['threats']
        
        for i, threat in enumerate(threats):
            if not isinstance(threat, dict):
                continue
            
            # Description validation
            desc = threat.get('description', '')
            if len(desc) < self.quality_thresholds["min_threat_description_length"]:
                result.add_warning(f"Threat {i}: Description too short")
            elif len(desc) > self.quality_thresholds["max_threat_description_length"]:
                result.add_warning(f"Threat {i}: Description too long")
            
            # Required fields
            if 'category' not in threat:
                result.add_warning(f"Threat {i}: Missing category")
            
            if 'severity' in threat:
                valid_severities = ['critical', 'high', 'medium', 'low', 'info']
                if threat['severity'].lower() not in valid_severities:
                    result.add_warning(f"Threat {i}: Invalid severity level")
            
            # Mitigation validation
            if 'mitigation' in threat:
                mit = threat['mitigation']
                if len(mit) < self.quality_thresholds["min_mitigation_length"]:
                    result.add_warning(f"Threat {i}: Mitigation too brief")
                elif len(mit) > self.quality_thresholds["max_mitigation_length"]:
                    result.add_warning(f"Threat {i}: Mitigation too verbose")
        
        return result
    
    def _validate_input_security(self, context: AgentExecutionContext) -> ValidationResult:
        """Validate input for security issues"""
        result = ValidationResult(True)
        
        # Check document content
        if context.document_text:
            for pattern_name, pattern in self.safety_patterns.items():
                if pattern.search(context.document_text):
                    if pattern_name in ['api_key', 'private_key', 'password', 'token']:
                        result.add_error(f"Potential sensitive data detected: {pattern_name}")
                    elif pattern_name in ['sql_injection', 'script_injection', 'command_injection']:
                        result.add_warning(f"Potential injection pattern detected: {pattern_name}")
        
        # Check component data
        if context.components:
            components_str = json.dumps(context.components)
            if self.safety_patterns['api_key'].search(components_str):
                result.add_error("Potential API key in component data")
        
        return result
    
    def _validate_output_security(self, output: Any) -> ValidationResult:
        """Validate output for security issues"""
        result = ValidationResult(True)
        
        try:
            output_str = json.dumps(output) if not isinstance(output, str) else output
            
            # Check for sensitive data exposure
            for pattern_name, pattern in self.safety_patterns.items():
                if pattern_name in ['api_key', 'private_key', 'password', 'token']:
                    if pattern.search(output_str):
                        result.add_error(f"Output contains potential {pattern_name}")
            
            # Check for excessive data
            if len(output_str) > 1000000:  # 1MB
                result.add_error("Output size exceeds safe limits")
            
        except Exception as e:
            result.add_warning(f"Could not perform security validation: {e}")
        
        return result
    
    def _validate_data_consistency(self, output: Any) -> ValidationResult:
        """Validate data consistency and integrity"""
        result = ValidationResult(True)
        
        threats = []
        if isinstance(output, ThreatOutput):
            threats = output.threats
        elif isinstance(output, list):
            threats = output
        elif isinstance(output, dict) and 'threats' in output:
            threats = output['threats']
        
        # Check for duplicates
        seen_descriptions = set()
        for threat in threats:
            if isinstance(threat, dict) and 'description' in threat:
                desc = threat['description']
                if desc in seen_descriptions:
                    result.add_warning(f"Duplicate threat detected: {desc[:50]}...")
                seen_descriptions.add(desc)
        
        # Check for data anomalies
        if len(threats) > 0:
            # All threats should have consistent structure
            first_keys = set(threats[0].keys()) if isinstance(threats[0], dict) else set()
            for i, threat in enumerate(threats[1:], 1):
                if isinstance(threat, dict):
                    if set(threat.keys()) != first_keys:
                        result.add_warning(f"Inconsistent threat structure at index {i}")
        
        return result
    
    def _validate_security_compliance(self, data: Any) -> ValidationResult:
        """Validate compliance with security standards"""
        result = ValidationResult(True)
        
        # Placeholder for compliance checks (OWASP, CWE, etc.)
        # This would be expanded based on specific compliance requirements
        
        return result
    
    def _validate_performance_bounds(self, metrics: Dict[str, Any]) -> ValidationResult:
        """Validate performance is within acceptable bounds"""
        result = ValidationResult(True)
        
        if 'execution_time' in metrics:
            if metrics['execution_time'] > self.quality_thresholds["max_execution_time_seconds"]:
                result.add_warning(f"Execution time exceeded threshold: {metrics['execution_time']}s")
        
        if 'token_usage' in metrics:
            if metrics['token_usage'] > self.quality_thresholds["max_token_usage"]:
                result.add_error(f"Token usage exceeded limit: {metrics['token_usage']}")
        
        return result
    
    def _validate_redundant_checks(self, data: Any) -> ValidationResult:
        """Perform redundant validation checks (paranoid mode)"""
        result = ValidationResult(True)
        
        # Double-check critical validations
        # This is intentionally redundant for maximum safety
        
        return result
    
    def _validate_cross_references(self, data: Any) -> ValidationResult:
        """Validate cross-references and relationships"""
        result = ValidationResult(True)
        
        # Validate that referenced components exist
        # Validate that threat categories match component types
        # etc.
        
        return result
    
    def sanitize_output(self, output: Any) -> Any:
        """
        Sanitize output to remove potential security issues
        Returns sanitized version of output
        """
        if isinstance(output, str):
            # Remove potential sensitive data
            for pattern_name, pattern in self.safety_patterns.items():
                if pattern_name in ['api_key', 'private_key', 'password', 'token']:
                    output = pattern.sub('[REDACTED]', output)
        
        elif isinstance(output, dict):
            # Recursively sanitize dictionary
            sanitized = {}
            for key, value in output.items():
                sanitized[key] = self.sanitize_output(value)
            return sanitized
        
        elif isinstance(output, list):
            # Recursively sanitize list
            return [self.sanitize_output(item) for item in output]
        
        return output


# Global validator instances for different levels
validators = {
    ValidationLevel.MINIMAL: AgentValidator(ValidationLevel.MINIMAL),
    ValidationLevel.STANDARD: AgentValidator(ValidationLevel.STANDARD),
    ValidationLevel.STRICT: AgentValidator(ValidationLevel.STRICT),
    ValidationLevel.PARANOID: AgentValidator(ValidationLevel.PARANOID),
}


def get_validator(level: ValidationLevel = ValidationLevel.STANDARD) -> AgentValidator:
    """Get validator instance for specified level"""
    return validators.get(level, validators[ValidationLevel.STANDARD])