#!/usr/bin/env python3
"""
Debug script to find where security_controls is referenced
"""

import ast
import os

def find_security_controls_usage(filepath):
    """Find all usages of security_controls in a Python file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check for direct string occurrences
        if 'security_controls' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if 'security_controls' in line:
                    # Exclude imports and constant definitions
                    if 'SECURITY_CONTROLS' not in line and 'import' not in line.lower():
                        print(f"{filepath}:{i}: {line.strip()}")
                    
    except Exception as e:
        print(f"Error reading {filepath}: {e}")

# Search in threat generator
threat_gen_file = "/Users/jeffreyvonrotz/SynologyDrive/Projects/ThreatModelingPipeline/apps/api/app/core/pipeline/steps/threat_generator_v3.py"
print("=== Searching in threat_generator_v3.py ===")
find_security_controls_usage(threat_gen_file)

# Search all py files in steps directory
steps_dir = "/Users/jeffreyvonrotz/SynologyDrive/Projects/ThreatModelingPipeline/apps/api/app/core/pipeline/steps/"
print("\n=== Searching all Python files in steps/ ===")
for root, dirs, files in os.walk(steps_dir):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            find_security_controls_usage(filepath)