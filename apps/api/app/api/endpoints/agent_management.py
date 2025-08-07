"""
Agent Management API Endpoints

Provides REST API for managing modular threat analysis agents,
including configuration, testing, and performance monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime, timedelta
import json
import logging
import uuid

from app.dependencies import get_db
from app.models.agent_config import AgentConfiguration, AgentPromptVersion, AgentExecutionLog
from app.core.agents import agent_registry
from app.core.agents.base import AgentExecutionContext
from app.core.llm.mock import MockLLMProvider
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agent-management"])


# Request/Response Models
class AgentConfigRequest(BaseModel):
    enabled: bool = True
    priority: int = Field(default=100, ge=1, le=1000)
    custom_prompt: Optional[str] = None
    max_tokens: int = Field(default=4000, ge=100, le=8000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    rate_limit_per_hour: Optional[int] = Field(default=None, ge=1)


class TestAgentRequest(BaseModel):
    sample_document: Optional[str] = None
    sample_components: Optional[Dict[str, Any]] = None
    use_mock_llm: bool = True
    custom_prompt: Optional[str] = None


class AgentInfoResponse(BaseModel):
    name: str
    version: str
    description: str
    category: str
    enabled: bool
    priority: int
    estimated_tokens: int
    metrics: Dict[str, Any]


class PromptVersionRequest(BaseModel):
    prompt: str
    description: Optional[str] = None
    activate: bool = False


# Main Endpoints
@router.get("/list", response_model=Dict[str, Any])
async def list_agents(
    include_disabled: bool = Query(False, description="Include disabled agents"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db)
):
    """List all available agents with their status and basic metrics"""
    
    try:
        agents = []
        
        # Get all agents from registry
        for agent_name, agent in agent_registry._instances.items():
            metadata = agent.get_metadata()
            
            # Apply category filter
            if category and metadata.category != category:
                continue
            
            # Get configuration from database
            stmt = select(AgentConfiguration).where(
                AgentConfiguration.agent_name == agent_name
            )
            result = await db.execute(stmt)
            config = result.scalar_one_or_none()
            
            # Check if should include disabled agents
            is_enabled = config.enabled if config else metadata.enabled_by_default
            if not is_enabled and not include_disabled:
                continue
            
            # Build agent info
            agent_info = {
                "name": metadata.name,
                "version": metadata.version,
                "description": metadata.description,
                "category": metadata.category,
                "enabled": is_enabled,
                "priority": config.priority if config else metadata.priority,
                "estimated_tokens": metadata.estimated_tokens,
                "requires_document": metadata.requires_document,
                "requires_components": metadata.requires_components,
                "metrics": {
                    "total_executions": config.total_executions if config else 0,
                    "success_rate": round(config.get_success_rate(), 1) if config else 0.0,
                    "avg_threats": round(config.get_average_threats(), 1) if config else 0.0,
                    "avg_execution_time": round(config.average_execution_time, 2) if config else 0.0,
                    "total_tokens_used": config.total_tokens_used if config else 0,
                    "last_executed": config.last_executed.isoformat() if config and config.last_executed else None
                }
            }
            
            agents.append(agent_info)
        
        # Sort by priority (then by name)
        agents.sort(key=lambda a: (a["priority"], a["name"]))
        
        return {
            "agents": agents,
            "total": len(agents),
            "categories": list(set(a["category"] for a in agents)),
            "enabled_count": sum(1 for a in agents if a["enabled"])
        }
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {e}")


@router.get("/{agent_name}", response_model=Dict[str, Any])
async def get_agent_details(
    agent_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific agent"""
    
    try:
        # Check if agent exists in registry
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        metadata = agent.get_metadata()
        
        # Get configuration from database
        stmt = select(AgentConfiguration).where(
            AgentConfiguration.agent_name == agent_name
        )
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()
        
        # Get prompt versions
        version_stmt = (
            select(AgentPromptVersion)
            .where(AgentPromptVersion.agent_name == agent_name)
            .order_by(AgentPromptVersion.version.desc())
            .limit(10)
        )
        version_result = await db.execute(version_stmt)
        versions = version_result.scalars().all()
        
        # Get recent execution logs
        log_stmt = (
            select(AgentExecutionLog)
            .where(AgentExecutionLog.agent_name == agent_name)
            .order_by(AgentExecutionLog.executed_at.desc())
            .limit(20)
        )
        log_result = await db.execute(log_stmt)
        recent_logs = log_result.scalars().all()
        
        # Calculate performance trends
        performance_trend = await _calculate_performance_trend(agent_name, db)
        
        return {
            "metadata": {
                "name": metadata.name,
                "version": metadata.version,
                "description": metadata.description,
                "category": metadata.category,
                "priority": metadata.priority,
                "requires_document": metadata.requires_document,
                "requires_components": metadata.requires_components,
                "estimated_tokens": metadata.estimated_tokens,
                "legacy_equivalent": metadata.legacy_equivalent
            },
            "configuration": {
                "enabled": config.enabled if config else metadata.enabled_by_default,
                "priority": config.priority if config else metadata.priority,
                "custom_prompt": config.custom_prompt if config else None,
                "max_tokens": config.max_tokens if config else 4000,
                "temperature": config.temperature if config else 0.7,
                "rate_limit_per_hour": config.rate_limit_per_hour if config else None
            },
            "prompt_versions": [
                {
                    "version": v.version,
                    "description": v.description,
                    "created_at": v.created_at.isoformat(),
                    "created_by": v.created_by,
                    "is_active": v.is_active,
                    "usage_count": v.usage_count,
                    "has_metrics": v.performance_metrics is not None
                }
                for v in versions
            ],
            "metrics": {
                "total_executions": config.total_executions if config else 0,
                "successful_executions": config.successful_executions if config else 0,
                "success_rate": round(config.get_success_rate(), 2) if config else 0.0,
                "total_threats_found": config.total_threats_found if config else 0,
                "avg_threats": round(config.get_average_threats(), 2) if config else 0.0,
                "total_tokens_used": config.total_tokens_used if config else 0,
                "avg_execution_time": round(config.average_execution_time, 2) if config else 0.0,
                "avg_confidence_score": round(config.average_confidence_score, 3) if config else 0.0,
                "last_executed": config.last_executed.isoformat() if config and config.last_executed else None,
                "performance_trend": performance_trend
            },
            "recent_executions": [
                {
                    "execution_id": log.execution_id,
                    "executed_at": log.executed_at.isoformat(),
                    "success": log.success,
                    "execution_time": log.execution_time,
                    "threats_found": log.threats_found,
                    "tokens_used": log.tokens_used,
                    "average_confidence": log.average_confidence,
                    "error_message": log.error_message if not log.success else None
                }
                for log in recent_logs
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent details: {e}")


@router.post("/{agent_name}/configure")
async def configure_agent(
    agent_name: str,
    config: AgentConfigRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Update agent configuration with hot reload"""
    
    try:
        # Verify agent exists
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        # Get or create configuration
        stmt = select(AgentConfiguration).where(
            AgentConfiguration.agent_name == agent_name
        )
        result = await db.execute(stmt)
        db_config = result.scalar_one_or_none()
        
        if not db_config:
            # Create new configuration
            db_config = AgentConfiguration(
                agent_name=agent_name,
                enabled=config.enabled,
                priority=config.priority,
                custom_prompt=config.custom_prompt,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                rate_limit_per_hour=config.rate_limit_per_hour
            )
            db.add(db_config)
        else:
            # Update existing configuration
            db_config.enabled = config.enabled
            db_config.priority = config.priority
            db_config.custom_prompt = config.custom_prompt
            db_config.max_tokens = config.max_tokens
            db_config.temperature = config.temperature
            db_config.rate_limit_per_hour = config.rate_limit_per_hour
            db_config.last_modified = datetime.utcnow()
        
        await db.commit()
        
        # Hot reload agent in background
        background_tasks.add_task(
            _hot_reload_agent,
            agent_name,
            config.dict()
        )
        
        logger.info(f"Agent {agent_name} configuration updated")
        
        return {
            "status": "success",
            "message": f"Agent {agent_name} configuration updated",
            "agent": agent_name,
            "hot_reload": "in_progress"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to configure agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration failed: {e}")


@router.post("/{agent_name}/test")
async def test_agent(
    agent_name: str,
    request: TestAgentRequest,
    db: AsyncSession = Depends(get_db)
):
    """Test an agent with sample data"""
    
    try:
        # Verify agent exists
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        metadata = agent.get_metadata()
        
        # Prepare test context
        context = AgentExecutionContext(
            document_text=request.sample_document or _get_sample_document(),
            components=request.sample_components or _get_sample_components(),
            existing_threats=[],  # Empty for testing
            pipeline_id=f"test_{uuid.uuid4().hex[:8]}"
        )
        
        # Validate context meets agent requirements
        if not agent.validate_context(context):
            return {
                "status": "error",
                "message": "Agent cannot execute with provided context",
                "requirements": {
                    "requires_document": metadata.requires_document,
                    "requires_components": metadata.requires_components
                },
                "context": {
                    "has_document": context.document_text is not None,
                    "has_components": context.components is not None
                }
            }
        
        # Setup LLM provider
        if request.use_mock_llm:
            llm_provider = MockLLMProvider()
        else:
            # Use real LLM provider (implement as needed)
            from app.core.llm import get_llm_provider
            llm_provider = await get_llm_provider("threat_generation")
        
        # Apply custom prompt if provided
        if request.custom_prompt:
            agent.update_configuration({"custom_prompt": request.custom_prompt})
        
        # Execute agent
        start_time = datetime.utcnow()
        try:
            threats = await agent.analyze(
                context=context,
                llm_provider=llm_provider,
                db_session=None,  # Don't save test results to pipeline
                settings_service=None
            )
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Calculate metrics
            confidence_scores = [t.confidence_score for t in threats if hasattr(t, 'confidence_score')]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            return {
                "status": "success",
                "agent": agent_name,
                "execution_time": round(execution_time, 2),
                "threats_found": len(threats),
                "average_confidence": round(avg_confidence, 3),
                "estimated_tokens": metadata.estimated_tokens,
                "threats_sample": [
                    {
                        "threat_name": t.threat_name,
                        "description": t.description[:200] + "..." if len(t.description) > 200 else t.description,
                        "severity": t.potential_impact,
                        "confidence": t.confidence_score
                    }
                    for t in threats[:5]  # Return first 5 for preview
                ],
                "context_info": {
                    "document_length": len(context.document_text) if context.document_text else 0,
                    "components_count": sum(len(v) for v in context.components.values() if isinstance(v, list)) if context.components else 0
                }
            }
            
        except Exception as agent_error:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Agent {agent_name} test execution failed: {agent_error}")
            
            return {
                "status": "error", 
                "agent": agent_name,
                "execution_time": round(execution_time, 2),
                "error": str(agent_error),
                "error_type": type(agent_error).__name__
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test execution failed: {e}")


@router.post("/{agent_name}/enable")
async def enable_agent(
    agent_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Enable an agent"""
    
    try:
        # Verify agent exists
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        # Get or create configuration
        stmt = select(AgentConfiguration).where(
            AgentConfiguration.agent_name == agent_name
        )
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()
        
        if not config:
            # Create enabled configuration
            config = AgentConfiguration(
                agent_name=agent_name,
                enabled=True
            )
            db.add(config)
        else:
            # Update existing
            config.enabled = True
            config.last_modified = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"Agent {agent_name} enabled")
        
        return {
            "status": "success",
            "message": f"Agent {agent_name} enabled",
            "agent": agent_name,
            "enabled": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enable agent: {e}")


@router.post("/{agent_name}/disable")
async def disable_agent(
    agent_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Disable an agent"""
    
    try:
        # Verify agent exists
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        # Get or create configuration
        stmt = select(AgentConfiguration).where(
            AgentConfiguration.agent_name == agent_name
        )
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()
        
        if not config:
            # Create disabled configuration
            config = AgentConfiguration(
                agent_name=agent_name,
                enabled=False
            )
            db.add(config)
        else:
            # Update existing
            config.enabled = False
            config.last_modified = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"Agent {agent_name} disabled")
        
        return {
            "status": "success",
            "message": f"Agent {agent_name} disabled",
            "agent": agent_name,
            "enabled": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disable agent: {e}")


# Helper Functions
async def _calculate_performance_trend(agent_name: str, db: AsyncSession) -> Dict[str, Any]:
    """Calculate performance trend over time"""
    try:
        # Get logs from last 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        stmt = (
            select(AgentExecutionLog)
            .where(
                AgentExecutionLog.agent_name == agent_name,
                AgentExecutionLog.executed_at >= cutoff_date
            )
            .order_by(AgentExecutionLog.executed_at.asc())
        )
        result = await db.execute(stmt)
        logs = result.scalars().all()
        
        if len(logs) < 2:
            return {"status": "insufficient_data", "data_points": len(logs)}
        
        # Calculate trends
        recent_logs = logs[-10:]  # Last 10 executions
        older_logs = logs[-20:-10] if len(logs) >= 20 else logs[:-10]
        
        def calc_avg_metric(log_list, metric_attr):
            values = [getattr(log, metric_attr) for log in log_list if hasattr(log, metric_attr) and getattr(log, metric_attr) is not None]
            return sum(values) / len(values) if values else 0
        
        recent_success_rate = (sum(1 for log in recent_logs if log.success) / len(recent_logs)) * 100
        older_success_rate = (sum(1 for log in older_logs if log.success) / len(older_logs)) * 100 if older_logs else recent_success_rate
        
        recent_avg_time = calc_avg_metric(recent_logs, 'execution_time')
        older_avg_time = calc_avg_metric(older_logs, 'execution_time')
        
        recent_avg_threats = calc_avg_metric(recent_logs, 'threats_found')
        older_avg_threats = calc_avg_metric(older_logs, 'threats_found')
        
        return {
            "status": "calculated",
            "data_points": len(logs),
            "period_days": 30,
            "success_rate": {
                "current": round(recent_success_rate, 1),
                "previous": round(older_success_rate, 1),
                "trend": "improving" if recent_success_rate > older_success_rate else "declining" if recent_success_rate < older_success_rate else "stable"
            },
            "execution_time": {
                "current": round(recent_avg_time, 2),
                "previous": round(older_avg_time, 2),
                "trend": "improving" if recent_avg_time < older_avg_time else "declining" if recent_avg_time > older_avg_time else "stable"
            },
            "threats_found": {
                "current": round(recent_avg_threats, 1),
                "previous": round(older_avg_threats, 1),
                "trend": "improving" if recent_avg_threats > older_avg_threats else "declining" if recent_avg_threats < older_avg_threats else "stable"
            }
        }
        
    except Exception as e:
        logger.warning(f"Failed to calculate performance trend: {e}")
        return {"status": "error", "message": str(e)}


async def _hot_reload_agent(agent_name: str, config: Dict[str, Any]) -> bool:
    """Hot reload agent configuration"""
    try:
        success = agent_registry.reload_agent(agent_name, config)
        if success:
            logger.info(f"✅ Hot reloaded agent: {agent_name}")
        else:
            logger.warning(f"⚠️ Failed to hot reload agent: {agent_name}")
        return success
    except Exception as e:
        logger.error(f"Hot reload failed for {agent_name}: {e}")
        return False


def _get_sample_document() -> str:
    """Get sample document for testing"""
    return """
    E-Commerce Platform Architecture
    
    This is a cloud-based e-commerce platform designed to handle high-volume transactions.
    The system consists of:
    
    - Frontend: React.js application served via CDN
    - API Gateway: NGINX load balancer with rate limiting
    - Authentication Service: JWT-based auth with Redis session store
    - Product Service: Manages product catalog and inventory
    - Order Service: Handles order processing and fulfillment
    - Payment Service: Processes payments via Stripe integration
    - User Database: PostgreSQL for user accounts and profiles
    - Product Database: MongoDB for product catalog
    - Order Database: PostgreSQL for order history
    - Cache Layer: Redis for session management and caching
    
    The system handles 10,000+ daily orders with 99.9% uptime SLA.
    PCI DSS compliance is required for payment processing.
    Customer data includes PII and payment information.
    """


def _get_sample_components() -> Dict[str, Any]:
    """Get sample DFD components for testing"""
    return {
        "processes": [
            {"name": "web-frontend", "type": "web_app", "description": "React.js e-commerce frontend"},
            {"name": "api-gateway", "type": "gateway", "description": "NGINX load balancer"},
            {"name": "auth-service", "type": "service", "description": "JWT authentication service"},
            {"name": "product-service", "type": "service", "description": "Product catalog API"},
            {"name": "order-service", "type": "service", "description": "Order processing API"},
            {"name": "payment-service", "type": "service", "description": "Payment processing via Stripe"}
        ],
        "assets": [
            {"name": "user-database", "type": "database", "description": "PostgreSQL user accounts"},
            {"name": "product-database", "type": "database", "description": "MongoDB product catalog"},
            {"name": "order-database", "type": "database", "description": "PostgreSQL order history"},
            {"name": "redis-cache", "type": "cache", "description": "Redis session and cache store"}
        ],
        "external_entities": [
            {"name": "customers", "type": "person", "description": "E-commerce customers"},
            {"name": "stripe-api", "type": "external_service", "description": "Payment processor"},
            {"name": "cdn-provider", "type": "external_service", "description": "Content delivery network"}
        ],
        "data_flows": [
            {"source": "customers", "destination": "web-frontend", "data": "HTTP requests"},
            {"source": "web-frontend", "destination": "api-gateway", "data": "API calls"},
            {"source": "api-gateway", "destination": "auth-service", "data": "Authentication requests"},
            {"source": "payment-service", "destination": "stripe-api", "data": "Payment data"}
        ]
    }