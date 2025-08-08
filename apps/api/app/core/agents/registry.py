"""
Agent Registry for Dynamic Discovery and Management

Provides centralized registration and discovery of threat analysis agents,
enabling dynamic loading and hot-reloading capabilities.
"""

import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Type, Optional, Any, Tuple
import logging
import asyncio
from datetime import datetime

from .base import BaseAgent, AgentMetadata, AgentExecutionContext

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Central registry for threat analysis agents
    Handles discovery, registration, and lifecycle management
    """
    
    def __init__(self):
        self._agents: Dict[str, Type[BaseAgent]] = {}
        self._instances: Dict[str, BaseAgent] = {}
        self._configurations: Dict[str, Dict] = {}
        # Lightweight in-process cache for agent catalog
        self._catalog_cache: Optional[List[Dict[str, Any]] ] = None
        self._catalog_cached_at: Optional[float] = None
        self._last_refresh: Optional[datetime] = None
        self._refresh_in_progress: bool = False
        self._refresh_lock: asyncio.Lock = asyncio.Lock()
        self._legacy_mapping = {
            # Map old V3 agent names to new modular agents
            "architectural_risk_agent": "architectural_risk",
            "business_financial_agent": "business_financial", 
            "compliance_governance_agent": "compliance_governance"
        }
        self._discovery_paths = [
            "app.core.agents.impl"
        ]
        
    def add_discovery_path(self, path: str) -> None:
        """Add additional path for agent discovery"""
        if path not in self._discovery_paths:
            self._discovery_paths.append(path)
    
    def discover_agents(self) -> int:
        """
        Auto-discover agent implementations from configured paths
        Returns number of agents discovered
        """
        discovered_count = 0
        
        for package_path in self._discovery_paths:
            try:
                discovered_count += self._discover_from_path(package_path)
            except Exception as e:
                logger.error(f"Failed to discover agents from {package_path}: {e}")
        
        logger.info(f"Agent discovery complete: {discovered_count} agents found")
        return discovered_count
    
    def _discover_from_path(self, package_path: str) -> int:
        """Discover agents from a specific package path"""
        discovered_count = 0
        
        # Convert package path to file system path
        try:
            # For app.core.agents.impl, use relative path from current file location
            if package_path == "app.core.agents.impl":
                impl_path = Path(__file__).parent / "impl"
            else:
                # Fallback to generic path resolution
                module_parts = package_path.split('.')
                impl_path = Path(__file__).parent
                for part in module_parts[module_parts.index("agents")+1:]:
                    impl_path = impl_path / part
                
            if not impl_path.exists():
                logger.warning(f"Agent discovery path does not exist: {impl_path}")
                return 0
            
            # Scan for Python files
            for py_file in impl_path.glob("*_agent.py"):
                try:
                    # Import module
                    module_name = f"{package_path}.{py_file.stem}"
                    logger.debug(f"Attempting to import {module_name}")
                    
                    module = importlib.import_module(module_name)
                    
                    # Find BaseAgent subclasses
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseAgent) and 
                            obj != BaseAgent):
                            
                            self.register_class(obj)
                            discovered_count += 1
                            logger.info(f"✅ Discovered agent: {obj.__name__} from {py_file.name}")
                            
                except Exception as e:
                    logger.error(f"Failed to load agent from {py_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Error during agent discovery: {e}")
            
        return discovered_count
    
    def register_class(self, agent_class: Type[BaseAgent]) -> bool:
        """
        Register an agent class
        Returns True if successful, False if already registered
        """
        try:
            # Create temporary instance to get metadata
            temp_instance = agent_class()
            metadata = temp_instance.get_metadata()
            
            if metadata.name in self._agents:
                logger.warning(f"Agent {metadata.name} already registered, skipping")
                return False
            
            # Register class and create instance
            self._agents[metadata.name] = agent_class
            self._instances[metadata.name] = temp_instance
            
            # Register legacy mapping if specified
            if metadata.legacy_equivalent:
                self._legacy_mapping[metadata.legacy_equivalent] = metadata.name
                logger.debug(f"Registered legacy mapping: {metadata.legacy_equivalent} -> {metadata.name}")
            
            logger.info(f"✅ Registered agent: {metadata.name} v{metadata.version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent class {agent_class.__name__}: {e}")
            return False
    
    def register_instance(self, agent: BaseAgent) -> bool:
        """Register a pre-configured agent instance"""
        try:
            metadata = agent.get_metadata()
            self._instances[metadata.name] = agent
            self._agents[metadata.name] = type(agent)
            logger.info(f"✅ Registered agent instance: {metadata.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register agent instance: {e}")
            return False
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        Get agent by name (supports legacy names)
        """
        # Check for legacy name mapping first
        if name in self._legacy_mapping:
            name = self._legacy_mapping[name]
        
        return self._instances.get(name)
    
    def get_agent_class(self, name: str) -> Optional[Type[BaseAgent]]:
        """Get agent class by name"""
        if name in self._legacy_mapping:
            name = self._legacy_mapping[name]
        return self._agents.get(name)
    
    def list_all_agents(self) -> List[BaseAgent]:
        """Get list of all registered agents"""
        return list(self._instances.values())
    
    def get_enabled_agents(self, config: Optional[Dict] = None) -> List[BaseAgent]:
        """
        Get list of enabled agents based on configuration
        Defaults to V3 compatibility agents if no config provided
        """
        if not config:
            # Default to V3 agents for backward compatibility
            config = {
                "enabled_agents": [
                    "architectural_risk",
                    "business_financial",
                    "compliance_governance"
                ]
            }
        
        enabled_names = config.get("enabled_agents", [])
        agents = []
        
        for name in enabled_names:
            agent = self.get_agent(name)
            if agent:
                agents.append(agent)
            else:
                logger.warning(f"Requested agent {name} not found in registry")
        
        # Sort by priority (lower priority = earlier execution)
        agents.sort(key=lambda a: a.get_metadata().priority)
        
        logger.debug(f"Retrieved {len(agents)} enabled agents")
        return agents
    
    def get_agents_by_category(self, category: str) -> List[BaseAgent]:
        """Get agents filtered by category"""
        return [
            agent for agent in self._instances.values()
            if agent.get_metadata().category == category
        ]
    
    def validate_agents(self, context: AgentExecutionContext) -> List[BaseAgent]:
        """Get agents that can execute with given context"""
        valid_agents = []
        
        for agent in self._instances.values():
            if agent.validate_context(context):
                valid_agents.append(agent)
            else:
                logger.debug(f"Agent {agent.get_metadata().name} cannot execute with current context")
        
        return valid_agents
    
    async def reload_agent(self, agent_name: str, config: Dict[str, Any]) -> bool:
        """
        Hot reload agent with new configuration
        Returns True if successful
        """
        try:
            agent = self.get_agent(agent_name)
            if not agent:
                logger.error(f"Agent {agent_name} not found for reload")
                return False
            
            # Update configuration
            agent.update_configuration(config)
            
            # Store configuration for persistence
            self._configurations[agent_name] = config
            
            logger.info(f"✅ Hot reloaded agent: {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload agent {agent_name}: {e}")
            return False
    
    def get_agent_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive information about an agent"""
        agent = self.get_agent(name)
        if not agent:
            return None
        
        metadata = agent.get_metadata()
        config = self._configurations.get(name, {})
        
        return {
            "name": metadata.name,
            "version": metadata.version,
            "description": metadata.description,
            "category": metadata.category,
            "priority": metadata.priority,
            "requires_document": metadata.requires_document,
            "requires_components": metadata.requires_components,
            "estimated_tokens": metadata.estimated_tokens,
            "enabled_by_default": metadata.enabled_by_default,
            "legacy_equivalent": metadata.legacy_equivalent,
            "current_config": config,
            "class_name": type(agent).__name__
        }
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the registry"""
        agents_by_category = {}
        for agent in self._instances.values():
            category = agent.get_metadata().category
            if category not in agents_by_category:
                agents_by_category[category] = 0
            agents_by_category[category] += 1
        
        return {
            "total_agents": len(self._instances),
            "total_classes": len(self._agents),
            "agents_by_category": agents_by_category,
            "legacy_mappings": len(self._legacy_mapping),
            "discovery_paths": self._discovery_paths,
            "last_discovery": datetime.now().isoformat()
        }
    
    def clear_registry(self) -> None:
        """Clear all registered agents (for testing)"""
        self._agents.clear()
        self._instances.clear()
        self._configurations.clear()
        logger.info("Agent registry cleared")
    
    async def update_database_registry(self, db_session) -> None:
        """Update database registry with discovered agents"""
        try:
            from sqlalchemy import select
            from app.models.agent_config import AgentRegistry as DBAgentRegistry
            
            for agent_name, agent in self._instances.items():
                metadata = agent.get_metadata()
                
                # Check if agent already exists in database
                stmt = select(DBAgentRegistry).where(DBAgentRegistry.agent_name == agent_name)
                result = await db_session.execute(stmt)
                db_agent = result.scalar_one_or_none()
                
                if db_agent:
                    # Update existing record
                    db_agent.version = metadata.version
                    db_agent.description = metadata.description
                    db_agent.category = metadata.category
                    db_agent.priority = metadata.priority
                    db_agent.requires_document = metadata.requires_document
                    db_agent.requires_components = metadata.requires_components
                    db_agent.estimated_tokens = metadata.estimated_tokens
                    db_agent.enabled_by_default = metadata.enabled_by_default
                    db_agent.legacy_equivalent = metadata.legacy_equivalent
                    db_agent.last_seen = datetime.utcnow()
                    db_agent.is_available = True
                    db_agent.load_error = None
                else:
                    # Create new record
                    db_agent = DBAgentRegistry(
                        agent_name=agent_name,
                        agent_class=f"{type(agent).__module__}.{type(agent).__name__}",
                        version=metadata.version,
                        description=metadata.description,
                        category=metadata.category,
                        priority=metadata.priority,
                        requires_document=metadata.requires_document,
                        requires_components=metadata.requires_components,
                        estimated_tokens=metadata.estimated_tokens,
                        enabled_by_default=metadata.enabled_by_default,
                        legacy_equivalent=metadata.legacy_equivalent,
                        discovered_at=datetime.utcnow(),
                        last_seen=datetime.utcnow(),
                        is_available=True
                    )
                    db_session.add(db_agent)
            
            await db_session.commit()
            logger.info(f"✅ Updated database registry for {len(self._instances)} agents")
            self._last_refresh = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to update database registry: {e}")
            await db_session.rollback()

    async def _load_catalog_from_db(self, db_session) -> Tuple[List[Dict[str, Any]], Optional[datetime]]:
        """
        Load agent catalog from database snapshot.
        Returns (agents_list, last_refreshed_timestamp)
        """
        try:
            from sqlalchemy import select
            from app.models.agent_config import AgentRegistry as DBAgentRegistry
            result = await db_session.execute(select(DBAgentRegistry))
            rows = result.scalars().all()
            agents: List[Dict[str, Any]] = []
            last_seen_values: List[datetime] = []
            for r in rows:
                if getattr(r, 'last_seen', None):
                    last_seen_values.append(r.last_seen)
                agents.append({
                    "name": r.agent_name,
                    "version": r.version,
                    "description": r.description,
                    "category": r.category,
                    "enabled": r.enabled_by_default,
                    "priority": r.priority,
                    "estimated_tokens": r.estimated_tokens,
                    "requires_document": r.requires_document,
                    "requires_components": r.requires_components,
                    "metrics": {
                        "total_executions": 0,
                        "success_rate": 0.0,
                        "avg_threats": 0.0,
                        "avg_execution_time": 0.0,
                        "total_tokens_used": 0,
                        "last_executed": None
                    }
                })
            last_refreshed = max(last_seen_values) if last_seen_values else None
            return agents, last_refreshed
        except Exception as e:
            logger.warning(f"Failed to load catalog from DB: {e}")
            return [], None

    async def get_cached_catalog(self, db_session, max_age_seconds: int = 30) -> Dict[str, Any]:
        """
        Return cached agent catalog if fresh, otherwise load from DB snapshot.
        Includes metadata: last_refreshed and refresh_in_progress.
        """
        now = asyncio.get_event_loop().time()
        use_cache = (
            self._catalog_cache is not None and 
            self._catalog_cached_at is not None and 
            (now - self._catalog_cached_at) < max_age_seconds
        )
        if use_cache:
            categories = sorted({a["category"] for a in self._catalog_cache})
            enabled_count = sum(1 for a in self._catalog_cache if a.get("enabled"))
            return {
                "agents": self._catalog_cache,
                "total": len(self._catalog_cache),
                "categories": categories,
                "enabled_count": enabled_count,
                "source": "cache",
                "last_refreshed": (self._last_refresh.isoformat() if self._last_refresh else None),
                "refresh_in_progress": self._refresh_in_progress,
            }

        # Load from DB and populate cache
        agents, last_refreshed = await self._load_catalog_from_db(db_session)
        if agents:
            self._catalog_cache = agents
            self._catalog_cached_at = asyncio.get_event_loop().time()
            self._last_refresh = last_refreshed or datetime.utcnow()
            categories = sorted({a["category"] for a in agents})
            enabled_count = sum(1 for a in agents if a.get("enabled"))
            return {
                "agents": agents,
                "total": len(agents),
                "categories": categories,
                "enabled_count": enabled_count,
                "source": "db",
                "last_refreshed": (self._last_refresh.isoformat() if self._last_refresh else None),
                "refresh_in_progress": self._refresh_in_progress,
            }
        else:
            return {
                "agents": [],
                "total": 0,
                "categories": [],
                "enabled_count": 0,
                "source": "empty",
                "last_refreshed": None,
                "refresh_in_progress": self._refresh_in_progress,
            }

    async def refresh_and_sync(self, db_session) -> None:
        """Perform discovery and sync results to the database and cache (non-blocking)."""
        if self._refresh_in_progress:
            logger.debug("Agent registry refresh already in progress; skipping")
            return
        async with self._refresh_lock:
            self._refresh_in_progress = True
            try:
                logger.info("Refreshing agent registry via discovery and syncing to DB...")
                self.discover_agents()
                await self.update_database_registry(db_session)
                # Update cache from DB snapshot
                agents, last_refreshed = await self._load_catalog_from_db(db_session)
                if agents:
                    self._catalog_cache = agents
                    self._catalog_cached_at = asyncio.get_event_loop().time()
                    self._last_refresh = last_refreshed or datetime.utcnow()
                logger.info("Agent registry refresh complete")
            except Exception as e:
                logger.error(f"Agent registry refresh failed: {e}")
            finally:
                self._refresh_in_progress = False


# Global registry instance
agent_registry = AgentRegistry()


async def initialize_agent_registry() -> AgentRegistry:
    """
    Initialize the global agent registry
    Discovers and registers all available agents
    """
    logger.info("Initializing agent registry...")
    
    try:
        # Discover agents from configured paths
        discovered = agent_registry.discover_agents()
        
        if discovered == 0:
            logger.warning("No agents discovered during initialization")
        else:
            logger.info(f"Agent registry initialized with {discovered} agents")
        
        # Log registry stats
        stats = agent_registry.get_registry_stats()
        logger.info(f"Registry stats: {stats}")
        
        return agent_registry
        
    except Exception as e:
        logger.error(f"Failed to initialize agent registry: {e}")
        raise