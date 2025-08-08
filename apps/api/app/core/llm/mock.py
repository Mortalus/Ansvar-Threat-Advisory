"""
Mock LLM Provider for testing threat generation.
"""
import json
from typing import Optional
from app.core.llm.base import BaseLLMProvider, LLMResponse


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider that returns realistic test threats."""
    
    def __init__(self):
        self.model = "mock-llm-v1"
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate mock threats based on the component in the prompt."""
        
        # Parse component info from prompt
        component_type = "process"
        component_name = "Unknown Component"
        
        if "Authentication Service" in prompt:
            component_name = "Authentication Service"
            threats = [
                {
                    "Threat Category": "Spoofing",
                    "Threat Name": "Credential Bypass Attack",
                    "Description": "Attacker could bypass authentication by exploiting SQL injection vulnerabilities in login queries, allowing unauthorized access to user accounts.",
                    "Potential Impact": "High",
                    "Likelihood": "Medium",
                    "Suggested Mitigation": "Implement parameterized queries and input validation for all authentication endpoints"
                },
                {
                    "Threat Category": "Information Disclosure", 
                    "Threat Name": "Database Credential Exposure",
                    "Description": "Authentication service database credentials could be exposed through configuration files or environment variables, allowing attackers to access sensitive user data.",
                    "Potential Impact": "High",
                    "Likelihood": "Low",
                    "Suggested Mitigation": "Use secure credential management systems and encrypt sensitive configuration data"
                }
            ]
        elif "Payment Processor" in prompt:
            component_name = "Payment Processor"
            threats = [
                {
                    "Threat Category": "Tampering",
                    "Threat Name": "Payment Amount Manipulation",
                    "Description": "Buffer overflow vulnerabilities in payment processing could allow attackers to manipulate transaction amounts or redirect payments.",
                    "Potential Impact": "High", 
                    "Likelihood": "Medium",
                    "Suggested Mitigation": "Apply security patches and implement robust input validation for payment data"
                },
                {
                    "Threat Category": "Denial of Service",
                    "Threat Name": "Payment Service Disruption", 
                    "Description": "Attackers could exploit buffer overflow vulnerabilities to crash the payment processing service, disrupting business operations.",
                    "Potential Impact": "Medium",
                    "Likelihood": "High",
                    "Suggested Mitigation": "Implement proper error handling and resource limits for payment processing"
                }
            ]
        elif "Database" in prompt:
            component_name = "User Database"
            threats = [
                {
                    "Threat Category": "Information Disclosure",
                    "Threat Name": "Unauthorized Data Access",
                    "Description": "SQL injection vulnerabilities could allow attackers to access sensitive user data stored in the database.",
                    "Potential Impact": "High",
                    "Likelihood": "Medium", 
                    "Suggested Mitigation": "Implement database access controls and audit logging"
                }
            ]
        else:
            # Generic threats
            threats = [
                {
                    "Threat Category": "Elevation of Privilege",
                    "Threat Name": "Unauthorized Access",
                    "Description": "Component may be vulnerable to privilege escalation attacks.",
                    "Potential Impact": "Medium",
                    "Likelihood": "Low",
                    "Suggested Mitigation": "Implement proper access controls and authentication"
                }
            ]
        
        # Return JSON response
        response_json = json.dumps(threats, indent=2)
        
        return LLMResponse(
            content=response_json,
            model=self.model,
            usage={"prompt_tokens": len(prompt), "completion_tokens": len(response_json)}
        )
    
    async def validate_connection(self) -> bool:
        """Always return True for mock provider."""
        return True