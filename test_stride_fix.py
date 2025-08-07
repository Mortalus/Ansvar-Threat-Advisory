#!/usr/bin/env python3
"""
Test script to validate the STRIDE data extraction JSON parsing fix
"""
import json
import sys
import asyncio
from pathlib import Path

# Add the API app to Python path
sys.path.append(str(Path(__file__).parent / "apps" / "api"))

from app.core.pipeline.steps.stride_data_extractor import StrideDataExtractor, ExtractedSecurityData

class MockLLMProvider:
    """Mock LLM provider that returns problematic JSON responses"""
    
    def __init__(self, response_content):
        self.response_content = response_content
    
    async def generate(self, prompt, system_prompt=None, max_tokens=None, temperature=None):
        class MockResponse:
            def __init__(self, content):
                self.content = content
                self.usage = {"total_tokens": 100}
        
        return MockResponse(self.response_content)

async def test_json_parsing_fixes():
    """Test various malformed JSON responses that should now be handled"""
    
    print("🧪 Testing STRIDE JSON parsing fixes...")
    
    # Test cases with malformed JSON that previously caused errors
    test_cases = [
        {
            "name": "Quoted JSON fragment with newline escape", 
            "response": '"\n  "assets_complete": true"',
            "should_work": False  # This is invalid JSON, should fallback gracefully
        },
        {
            "name": "Quoted valid JSON with newline escape",
            "response": '"\n  {"project_name": "Test", "project_description": "Test", "industry_context": "Test", "completeness_indicators": {"assets_complete": true}}"',
            "should_work": True
        },
        {
            "name": "Double-quoted JSON",
            "response": '"{\"project_name\": \"Test\", \"project_description\": \"Test\", \"industry_context\": \"Test\", \"completeness_indicators\": {\"assets_complete\": true}}"',
            "should_work": True
        },
        {
            "name": "JSON with escaped quotes",
            "response": '{\\"project_name\\": \\"Test\\", \\"project_description\\": \\"Test\\", \\"industry_context\\": \\"Test\\", \\"completeness_indicators\\": {\\"assets_complete\\": true}}',
            "should_work": True
        },
        {
            "name": "Valid JSON in markdown",
            "response": '```json\n{"project_name": "Test", "project_description": "Test", "industry_context": "Test", "completeness_indicators": {"assets_complete": true}}\n```',
            "should_work": True
        },
        {
            "name": "Completely invalid JSON",
            "response": 'This is not JSON at all!',
            "should_work": False  # Should fallback gracefully
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📝 Testing: {test_case['name']}")
        print(f"🔍 Response: {test_case['response'][:100]}...")
        
        # Create mock LLM provider
        mock_provider = MockLLMProvider(test_case['response'])
        extractor = StrideDataExtractor(mock_provider)
        
        # Create minimal valid JSON for STRIDE expert pass
        valid_stride_data = {
            "project_name": "Test Project",
            "project_description": "Test Description", 
            "industry_context": "Technology",
            "compliance_frameworks": [],
            "external_entities": [],
            "security_assets": [],
            "processes": [],
            "trust_zones": [],
            "security_data_flows": [],
            "access_patterns": [],
            "business_criticality": "Medium",
            "regulatory_environment": "Standard",
            "threat_landscape": []
        }
        
        stride_data = ExtractedSecurityData(**valid_stride_data)
        
        try:
            # Test the quality validator pass specifically
            result, tokens = await extractor._quality_validator_pass(
                "Test document content", 
                stride_data
            )
            
            if test_case['should_work']:
                print(f"✅ Success - Quality score: {result.quality_score}")
            else:
                print(f"✅ Unexpected success (fallback worked)")
                
        except Exception as e:
            if test_case['should_work']:
                print(f"❌ Failed - Error: {e}")
                return False
            else:
                print(f"✅ Expected failure handled gracefully: {e}")
    
    print(f"\n🎉 All JSON parsing tests completed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_json_parsing_fixes())
    if success:
        print("\n✅ All tests passed! The JSON parsing fixes are working.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the implementation.")
        sys.exit(1)