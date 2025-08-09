#!/usr/bin/env python3
"""
Test script for Phase 2 workflow functionality.
Tests workflow creation and execution without authentication complications.
"""

import asyncio
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Add the API directory to the path
import sys
import os
sys.path.append('/app')

from app.database import get_async_session
from app.models import User
from app.models.workflow import WorkflowTemplate, WorkflowRun
from app.services.workflow_service import WorkflowService


async def test_phase2_workflow():
    """Test Phase 2 workflow functionality."""
    print("=" * 60)
    print("PHASE 2 WORKFLOW ENGINE TEST")
    print("=" * 60)
    
    # Initialize service
    workflow_service = WorkflowService()
    # Ensure agents are discovered
    workflow_service.agent_registry.discover_agents()
    print(f"✅ Discovered {len(workflow_service.agent_registry._agents)} agents")
    
    # Get database session
    async for db in get_async_session():
        try:
            # Get admin user for testing
            result = await db.execute(
                select(User).where(User.username == "admin")
            )
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                print("❌ Admin user not found. Please run RBAC initialization first.")
                return False
            
            print(f"✅ Using admin user: {admin_user.username}")
            
            # Test 1: Create workflow template
            print("\n📝 TEST 1: Creating workflow template...")
            
            workflow_def = {
                "steps": {
                    "analyze": {
                        "agent_type": "document_analysis",
                        "config": {"depth": "basic"},
                        "depends_on": []
                    },
                    "assess": {
                        "agent_type": "architectural_risk",
                        "config": {"threshold": 0.7},
                        "depends_on": ["analyze"]
                    },
                    "report": {
                        "agent_type": "compliance_governance",
                        "config": {"format": "json"},
                        "depends_on": ["assess"]
                    }
                }
            }
            
            template = await workflow_service.create_template(
                db=db,
                name="Phase 2 Test Workflow",
                description="Testing sequential execution",
                definition=workflow_def,
                user=admin_user,
                category="test"
            )
            
            print(f"✅ Created template: {template.name} (ID: {template.id})")
            
            # Test 2: Validate DAG
            print("\n🔍 TEST 2: Validating DAG structure...")
            is_valid, error = workflow_service.dag_validator.validate_dag(workflow_def)
            if is_valid:
                print("✅ DAG validation passed")
                execution_order = workflow_service.dag_validator.get_execution_order(workflow_def)
                print(f"   Execution order: {' → '.join(execution_order)}")
            else:
                print(f"❌ DAG validation failed: {error}")
                return False
            
            # Test 3: Start workflow run
            print("\n🚀 TEST 3: Starting workflow run...")
            run = await workflow_service.start_run(
                db=db,
                template_id=template.id,
                user=admin_user,
                initial_context={"test": True, "phase": 2}
            )
            
            print(f"✅ Started run: {run.run_id}")
            print(f"   Status: {run.status.value}")
            print(f"   Total steps: {run.total_steps}")
            
            # Test 4: Execute steps
            print("\n⚙️ TEST 4: Executing workflow steps...")
            
            for i in range(3):  # Execute 3 steps
                step = await workflow_service.execute_next_step(
                    db=db,
                    run_id=run.id
                )
                
                if step:
                    print(f"✅ Executed step '{step.step_id}'")
                    print(f"   Status: {step.status.value}")
                    print(f"   Execution time: {step.execution_time_ms}ms")
                else:
                    print("   No more steps to execute")
                    break
            
            # Test 5: Check final status
            print("\n📊 TEST 5: Checking workflow status...")
            status = await workflow_service.get_run_status(db, run.id)
            
            print(f"✅ Workflow status:")
            print(f"   Status: {status['status']}")
            print(f"   Progress: {status['progress']}%")
            print(f"   Completed steps: {status['completed_steps']}/{status['total_steps']}")
            print(f"   Artifacts created: {status['artifacts_count']}")
            
            # Test 6: Verify artifacts
            print("\n📦 TEST 6: Verifying artifacts...")
            from app.models.workflow import WorkflowArtifact
            artifact_result = await db.execute(
                select(WorkflowArtifact).where(WorkflowArtifact.run_id == run.id)
            )
            artifacts = list(artifact_result.scalars().all())
            
            print(f"✅ Found {len(artifacts)} artifacts")
            for artifact in artifacts:
                content = artifact.get_content()
                print(f"   - {artifact.name}: {artifact.artifact_type} (v{artifact.version})")
                if content:
                    print(f"     Content type: {type(content).__name__}")
            
            print("\n" + "=" * 60)
            print("🎉 PHASE 2 WORKFLOW TEST COMPLETE!")
            print("=" * 60)
            print("\nSUMMARY:")
            print(f"✅ Template created: {template.name}")
            print(f"✅ Workflow executed: {run.run_id}")
            print(f"✅ Steps completed: {status['completed_steps']}")
            print(f"✅ Artifacts created: {status['artifacts_count']}")
            print(f"✅ Final status: {status['status']}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await db.close()


if __name__ == "__main__":
    success = asyncio.run(test_phase2_workflow())
    sys.exit(0 if success else 1)