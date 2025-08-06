"""
Application startup tasks and initialization.
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.services.prompt_service import PromptService

logger = logging.getLogger(__name__)


async def initialize_default_data():
    """
    Initialize default data for the application.
    This includes default prompt templates.
    """
    try:
        async with AsyncSessionLocal() as session:
            # Initialize default prompts
            prompt_service = PromptService(session)
            await prompt_service.initialize_default_prompts()
            
            logger.info("Default data initialization completed successfully")
            
    except Exception as e:
        logger.error(f"Error during startup initialization: {str(e)}")
        # Don't raise the exception to prevent startup failure
        # The application should start even if default data initialization fails


def run_startup_tasks():
    """
    Run startup tasks synchronously.
    This can be called from the FastAPI lifespan context.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(initialize_default_data())
    except Exception as e:
        logger.error(f"Error running startup tasks: {str(e)}")
    finally:
        loop.close()