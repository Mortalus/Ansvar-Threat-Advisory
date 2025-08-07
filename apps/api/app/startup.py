"""
Application startup tasks and initialization.
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.services.prompt_service import PromptService
from app.core.agents.registry import AgentRegistry

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
                    new_loop.close()
                
                thread = threading.Thread(target=run_in_thread)
                thread.start()
                thread.join()
            else:
                loop.run_until_complete(initialize_default_data())
        except RuntimeError:
            # No loop is running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(initialize_default_data())
            loop.close()
    except Exception as e:
        logger.error(f"Error running startup tasks: {str(e)}")
        # Don't raise to prevent startup failure