"""
Application startup tasks and initialization.
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.services.prompt_service import PromptService
from app.core.agents.registry import AgentRegistry
from app.services.workflow_manager import WorkflowManager

logger = logging.getLogger(__name__)


async def initialize_default_data():
    """
    Initialize default data for the application.
    This includes default prompt templates and agent registry.
    """
    try:
        async with AsyncSessionLocal() as session:
            # Initialize default prompts
            prompt_service = PromptService(session)
            await prompt_service.initialize_default_prompts()
            
            # Initialize agent registry
            await initialize_agent_registry()

            # Seed default Threat Modeling workflow template if missing
            try:
                from sqlalchemy import select
                # Import the correct model (our unified workflow model is in app.models.workflow)
                from app.models.workflow import WorkflowTemplate
                from app.services.llm_service import LLMService

                # Check if a default template exists by name
                result = await session.execute(select(WorkflowTemplate).where(WorkflowTemplate.name == "Threat Modeling (Standard)"))
                existing = result.scalar_one_or_none()
                if not existing:
                    workflow_manager = WorkflowManager(session, LLMService())
                    await workflow_manager.create_template(
                        name="Threat Modeling (Standard)",
                        description="End-to-end threat modeling with DFD, minimum three agents (Architectural, Business, Compliance), refinement, and optional attack paths.",
                        steps=[
                            {
                                "id": "document_upload",
                                "name": "Document Upload",
                                "description": "Upload and register documents; compute token estimates",
                                "agent_type": "document_analysis",
                                "required_inputs": ["document_text"],
                                "optional_parameters": {"max_document_chars": 20000},
                                "automation_enabled": True,
                                "confidence_threshold": 0.9,
                                "review_required": False,
                                "timeout_minutes": 10,
                                "retry_limit": 1
                            },
                            {
                                "id": "dfd_extraction",
                                "name": "DFD Extraction (Enhanced)",
                                "description": "Extract DFD components with STRIDE expert review and confidence scoring",
                                "agent_type": "data_flow_analysis",
                                "required_inputs": ["components"],
                                "optional_parameters": {"enable_stride_review": True, "confidence_scoring": True},
                                "automation_enabled": False,
                                "confidence_threshold": 0.9,
                                "review_required": True,
                                "timeout_minutes": 30,
                                "retry_limit": 2
                            },
                            {
                                "id": "architectural_agent",
                                "name": "Architectural Risk Agent",
                                "description": "System-level architectural vulnerabilities (SPOF, segmentation, DR)",
                                "agent_type": "architectural_risk",
                                "required_inputs": ["document_text", "components"],
                                "optional_parameters": {"existing_threats_limit": 50},
                                "automation_enabled": False,
                                "confidence_threshold": 0.9,
                                "review_required": True,
                                "timeout_minutes": 20,
                                "retry_limit": 2
                            },
                            {
                                "id": "business_agent",
                                "name": "Business & Financial Risk Agent",
                                "description": "Quantify business impact; connect threats to operations and cost",
                                "agent_type": "business_financial",
                                "required_inputs": ["document_text", "components"],
                                "optional_parameters": {"existing_threats_limit": 50},
                                "automation_enabled": False,
                                "confidence_threshold": 0.9,
                                "review_required": True,
                                "timeout_minutes": 20,
                                "retry_limit": 2
                            },
                            {
                                "id": "compliance_agent",
                                "name": "Compliance & Governance Agent",
                                "description": "Regulatory gaps, audit trails, data protection obligations",
                                "agent_type": "compliance_governance",
                                "required_inputs": ["document_text", "components"],
                                "optional_parameters": {"existing_threats_limit": 50},
                                "automation_enabled": False,
                                "confidence_threshold": 0.9,
                                "review_required": True,
                                "timeout_minutes": 20,
                                "retry_limit": 2
                            },
                            {
                                "id": "threat_refinement",
                                "name": "Threat Refinement",
                                "description": "Deduplicate, risk score, and add business statements; consolidate",
                                "agent_type": "threat_refinement",
                                "required_inputs": ["threats"],
                                "optional_parameters": {"batch_size": 50},
                                "automation_enabled": False,
                                "confidence_threshold": 0.9,
                                "review_required": True,
                                "timeout_minutes": 25,
                                "retry_limit": 2
                            },
                            {
                                "id": "attack_path_analysis",
                                "name": "Attack Path Analysis (Optional)",
                                "description": "Discover attack chains and critical scenarios",
                                "agent_type": "attack_path_analyzer",
                                "required_inputs": ["threats", "components"],
                                "optional_parameters": {"max_paths": 25},
                                "automation_enabled": True,
                                "confidence_threshold": 0.9,
                                "review_required": False,
                                "timeout_minutes": 15,
                                "retry_limit": 1
                            }
                        ],
                        automation_settings={
                            "enabled": False,  # review-by-default
                            "confidence_threshold": 0.9,
                            "max_auto_approvals_per_day": 0,
                            "business_hours_only": False,
                            "notification_level": "summary",
                            "fallback_to_manual": True
                        },
                        client_access_rules={
                            "authentication_method": "token",
                            "token_expiry_days": 30,
                            "ip_restrictions": [],
                            "allowed_actions": ["view", "edit", "export"],
                            "data_retention_days": 90,
                            "requires_approval": False
                        },
                        created_by=None
                    )
                    logger.info("Seeded default workflow template: Threat Modeling (Standard)")
                else:
                    logger.info("Default workflow template already present")
            except Exception as wf_err:
                logger.warning(f"Failed to seed default workflow template: {wf_err}")
            
            logger.info("Default data initialization completed successfully")
            
    except Exception as e:
        logger.error(f"Error during startup initialization: {str(e)}")
        # Don't raise the exception to prevent startup failure
        # The application should start even if default data initialization fails


async def initialize_agent_registry():
    """Initialize the global agent registry with discovered agents"""
    try:
        from app.core.agents import agent_registry
        
        # Discover and register available agents
        discovered_count = agent_registry.discover_agents()
        logger.info(f"🤖 Agent registry initialized: {discovered_count} agents discovered")
        
        # Optionally, save agent metadata to database for the management interface
        async with AsyncSessionLocal() as session:
            await agent_registry.update_database_registry(session)
            # Warm the cache from DB snapshot for fast list responses
            await agent_registry.get_cached_catalog(session)
            
        logger.info("✅ Agent registry database updated")
        
    except Exception as e:
        logger.error(f"Failed to initialize agent registry: {e}")
        # Don't raise to prevent startup failure


def run_startup_tasks():
    """
    Run startup tasks synchronously.
    This can be called from the FastAPI lifespan context.
    """
    try:
        # Check if there's already a running event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, schedule the task instead
                import threading
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(initialize_default_data())
                    # Schedule periodic registry refresh every 60 seconds (non-blocking)
                    async def periodic_refresh():
                        from app.core.agents import agent_registry
                        while True:
                            try:
                                async with AsyncSessionLocal() as session:
                                    await agent_registry.refresh_and_sync(session)
                            except Exception as e:
                                logger.warning(f"Agent registry periodic refresh failed: {e}")
                            await asyncio.sleep(60)
                    new_loop.create_task(periodic_refresh())
                    new_loop.close()
                
                thread = threading.Thread(target=run_in_thread)
                thread.start()
                thread.join()
            else:
                loop.run_until_complete(initialize_default_data())
                # Schedule periodic registry refresh in this loop
                async def periodic_refresh():
                    from app.core.agents import agent_registry
                    while True:
                        try:
                            async with AsyncSessionLocal() as session:
                                await agent_registry.refresh_and_sync(session)
                        except Exception as e:
                            logger.warning(f"Agent registry periodic refresh failed: {e}")
                        await asyncio.sleep(60)
                loop.create_task(periodic_refresh())
        except RuntimeError:
            # No loop is running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(initialize_default_data())
            # Schedule periodic registry refresh in this loop
            async def periodic_refresh():
                from app.core.agents import agent_registry
                while True:
                    try:
                        async with AsyncSessionLocal() as session:
                            await agent_registry.refresh_and_sync(session)
                    except Exception as e:
                        logger.warning(f"Agent registry periodic refresh failed: {e}")
                    await asyncio.sleep(60)
            loop.create_task(periodic_refresh())
            loop.close()
    except Exception as e:
        logger.error(f"Error running startup tasks: {str(e)}")
        # Don't raise to prevent startup failure


async def initialize_default_data_robust():
    """
    Initialize default data with robust connection handling.
    Uses the new connection manager to avoid event loop issues.
    """
    from app.core.db_connection_manager import get_robust_session
    
    try:
        async with get_robust_session() as session:
            # Initialize default prompts
            prompt_service = PromptService(session)
            await prompt_service.initialize_default_prompts()
            
            # Initialize agent registry
            await initialize_agent_registry()

            # Seed default Threat Modeling workflow template if missing
            try:
                from sqlalchemy import select
                from app.models.workflow import WorkflowTemplate
                from app.services.llm_service import LLMService

                # Check if a default template exists by name
                result = await session.execute(select(WorkflowTemplate).where(WorkflowTemplate.name == "Threat Modeling (Standard)"))
                existing = result.scalar_one_or_none()
                if not existing:
                    workflow_manager = WorkflowManager(session, LLMService())
                    await workflow_manager.create_template(
                        name="Threat Modeling (Standard)",
                        description="End-to-end threat modeling with DFD, minimum three agents (Architectural, Business, Compliance), refinement, and optional attack paths.",
                        steps=[
                            {
                                "id": "document_upload",
                                "name": "Document Upload",
                                "description": "Upload and register documents; compute token estimates",
                                "agent_type": "document_analysis",
                                "required_inputs": ["document_text"],
                                "optional_parameters": {"max_document_chars": 20000},
                                "automation_enabled": True,
                                "confidence_threshold": 0.9,
                                "review_required": False,
                                "timeout_minutes": 10,
                                "retry_limit": 1
                            },
                            {
                                "id": "dfd_extraction",
                                "name": "DFD Extraction (Enhanced)",
                                "description": "Extract DFD components with STRIDE expert review and confidence scoring",
                                "agent_type": "data_flow_analysis",
                                "required_inputs": ["components"],
                                "optional_parameters": {"enable_stride_review": True, "confidence_scoring": True},
                                "automation_enabled": False,
                                "confidence_threshold": 0.9,
                                "review_required": True,
                                "timeout_minutes": 30,
                                "retry_limit": 2
                            },
                            {
                                "id": "architectural_agent",
                                "name": "Architectural Risk Agent",
                                "description": "System-level architectural vulnerabilities (SPOF, segmentation, DR)",
                                "agent_type": "architectural_risk",
                                "required_inputs": ["document_text", "components"],
                                "optional_parameters": {"existing_threats_limit": 50},
                                "automation_enabled": False,
                                "confidence_threshold": 0.9,
                                "review_required": True,
                                "timeout_minutes": 20,
                                "retry_limit": 2
                            },
                            {
                                "id": "business_agent",
                                "name": "Business & Financial Risk Agent",
                                "description": "Quantify business impact; connect threats to operations and cost",
                                "agent_type": "business_financial",
                                "required_inputs": ["document_text", "components"],
                                "optional_parameters": {"existing_threats_limit": 50},
                                "automation_enabled": False,
                                "confidence_threshold": 0.9,
                                "review_required": True,
                                "timeout_minutes": 20,
                                "retry_limit": 2
                            },
                            {
                                "id": "compliance_agent",
                                "name": "Compliance & Governance Agent",
                                "description": "Regulatory gaps, audit trails, data protection obligations",
                                "agent_type": "compliance_governance",
                                "required_inputs": ["document_text", "components"],
                                "optional_parameters": {"existing_threats_limit": 50},
                                "automation_enabled": False,
                                "confidence_threshold": 0.9,
                                "review_required": True,
                                "timeout_minutes": 20,
                                "retry_limit": 2
                            },
                            {
                                "id": "threat_refinement",
                                "name": "Threat Refinement",
                                "description": "Deduplicate, risk score, and add business statements; consolidate",
                                "agent_type": "threat_refinement",
                                "required_inputs": ["threats"],
                                "optional_parameters": {"batch_size": 50},
                                "automation_enabled": False,
                                "confidence_threshold": 0.9,
                                "review_required": True,
                                "timeout_minutes": 25,
                                "retry_limit": 2
                            },
                            {
                                "id": "attack_path_analysis",
                                "name": "Attack Path Analysis (Optional)",
                                "description": "Discover attack chains and critical scenarios",
                                "agent_type": "attack_path_analyzer",
                                "required_inputs": ["threats", "components"],
                                "optional_parameters": {"max_paths": 25},
                                "automation_enabled": True,
                                "confidence_threshold": 0.9,
                                "review_required": False,
                                "timeout_minutes": 15,
                                "retry_limit": 1
                            }
                        ],
                        automation_settings={
                            "enabled": False,  # review-by-default
                            "confidence_threshold": 0.9,
                            "max_auto_approvals_per_day": 0,
                            "business_hours_only": False,
                            "notification_level": "summary",
                            "fallback_to_manual": True
                        },
                        client_access_rules={
                            "authentication_method": "token",
                            "token_expiry_days": 30,
                            "ip_restrictions": [],
                            "allowed_actions": ["view", "edit", "export"],
                            "data_retention_days": 90,
                            "require_mfa": False
                        },
                        created_by="system"
                    )
                    logger.info("✅ Default Threat Modeling workflow template created")
            except Exception as e:
                logger.warning(f"Could not seed default workflow template: {e}")
        
        logger.info("Default data initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize default data: {e}")
        # Do not raise to prevent startup failure
