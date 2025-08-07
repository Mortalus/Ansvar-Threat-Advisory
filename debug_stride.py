#!/usr/bin/env python3
"""
Debug script to find exactly where the JSON error is thrown
"""
import json
import sys
from pathlib import Path

# Test the specific problematic JSON
problematic_json = '"\n  {"project_name": "Test", "project_description": "Test", "industry_context": "Test", "completeness_indicators": {"assets_complete": true}}"'

print("🔍 Testing problematic JSON string:")
print(f"Raw: {repr(problematic_json)}")

try:
    # Try to parse as-is
    result = json.loads(problematic_json)
    print("✅ Parsed as-is successfully!")
    print(result)
except json.JSONDecodeError as e:
    print(f"❌ Initial parse failed: {e}")
    print(f"Error message: {e.msg}")
    print(f"Error args: {e.args}")
    
    # Try the cleaning approach
    cleaned = problematic_json.replace('\\n', '').replace('\\"', '"')
    print(f"\n🔧 After escape cleaning: {repr(cleaned)}")
    
    try:
        result = json.loads(cleaned)
        print("✅ Cleaned version parsed successfully!")
    except json.JSONDecodeError as e2:
        print(f"❌ Cleaned version failed: {e2}")
        
        # Try removing outer quotes
        if cleaned.startswith('"') and cleaned.endswith('"'):
            inner = cleaned[1:-1]
            print(f"\n🔧 After removing outer quotes: {repr(inner)}")
            
            try:
                result = json.loads(inner)
                print("✅ Inner content parsed successfully!")
                print(result)
            except json.JSONDecodeError as e3:
                print(f"❌ Inner content failed: {e3}")
                print(f"This is the exact error we see: {repr(str(e3))}")