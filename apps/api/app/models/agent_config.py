"""
Database Models for Agent Configuration Management

Provides persistent storage for agent configurations, prompt versions,
and execution metrics to enable the modular agent system.
"""

from sqlalchemy import Column, String, JSON, Boolean, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import BaseModel


class AgentConfiguration(BaseModel):
    """
    Agent configuration and settings
    Stores per-agent settings including custom prompts and execution parameters
    """
    __tablename__ = "agent_configurations"
    
    agent_name = Column(String(100), unique=True, nullable=False, index=True)
    enabled = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=100, nullable=False)
    
    # Configuration settings
    configuration = Column(JSON)  # Agent-specific settings
    custom_prompt = Column(Text)  # Override default prompt
    max_tokens = Column(Integer, default=4000)
    temperature = Column(Float, default=0.7)
    
    # Rate limiting and resource management
    rate_limit_per_hour = Column(Integer)
    concurrent_limit = Column(Integer, default=1)
    
    # Customer-specific configuration
    customer_id = Column(String(100))  # For multi-tenant deployments
    organization_id = Column(String(100))  # Organization-specific configs
    
    # Execution metrics (updated during runtime)
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    total_threats_found = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    average_execution_time = Column(Float, default=0.0)
    average_confidence_score = Column(Float, default=0.0)
    
    # Timestamps
    last_executed = Column(DateTime)
    last_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    prompt_versions = relationship(
        "AgentPromptVersion", 
        back_populates="agent_config",
        cascade="all, delete-orphan",
        order_by="desc(AgentPromptVersion.version)"
    )
    
    execution_logs = relationship(
        "AgentExecutionLog",
        back_populates="agent_config", 
        cascade="all, delete-orphan",
        order_by="desc(AgentExecutionLog.executed_at)"
    )
    
    def __repr__(self):
        return f"<AgentConfiguration(agent_name='{self.agent_name}', enabled={self.enabled})>"
    
    def get_success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100
    
    def get_average_threats(self) -> float:
        """Calculate average threats found per execution"""
        if self.successful_executions == 0:
            return 0.0
        return self.total_threats_found / self.successful_executions
    
    def update_metrics(
        self,
        execution_time: float,
        threats_found: int,
        tokens_used: int,
        success: bool,
        confidence_score: float = None
    ) -> None:
        """Update execution metrics"""
        self.total_executions += 1
        
        if success:
            self.successful_executions += 1
            self.total_threats_found += threats_found
            self.total_tokens_used += tokens_used
            
            # Update running averages
            if self.successful_executions == 1:
                self.average_execution_time = execution_time
                if confidence_score is not None:
                    self.average_confidence_score = confidence_score
            else:
                # Running average calculation
                n = self.successful_executions
                self.average_execution_time = (
                    (self.average_execution_time * (n - 1) + execution_time) / n
                )
                if confidence_score is not None:
                    self.average_confidence_score = (
                        (self.average_confidence_score * (n - 1) + confidence_score) / n
                    )
        
        self.last_executed = datetime.utcnow()


class AgentPromptVersion(BaseModel):
    """
    Version control for agent prompts
    Enables A/B testing and rollback capabilities
    """
    __tablename__ = "agent_prompt_versions"
    
    agent_name = Column(String(100), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    prompt = Column(Text, nullable=False)
    
    # Metadata
    description = Column(String(500))  # Description of changes
    created_by = Column(String(100))   # User who created this version
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    
    # Performance tracking for this version
    performance_metrics = Column(JSON)  # Track how this version performs
    usage_count = Column(Integer, default=0)
    average_confidence = Column(Float)
    average_threats = Column(Float)
    
    # Foreign key relationship
    agent_config_id = Column(Integer, ForeignKey("agent_configurations.id"))
    agent_config = relationship("AgentConfiguration", back_populates="prompt_versions")
    
    def __repr__(self):
        return f"<AgentPromptVersion(agent='{self.agent_name}', version={self.version}, active={self.is_active})>"


class AgentExecutionLog(BaseModel):
    """
    Detailed execution logs for agents
    Useful for monitoring, debugging, and performance analysis
    """
    __tablename__ = "agent_execution_logs"
    
    agent_name = Column(String(100), nullable=False, index=True)
    execution_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Execution details
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    execution_time = Column(Float, nullable=False)  # seconds
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)  # If execution failed
    
    # Input context summary
    had_document = Column(Boolean, default=False)
    had_components = Column(Boolean, default=False)
    context_size = Column(Integer, default=0)  # rough context size
    
    # Results summary
    threats_found = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    confidence_scores = Column(JSON)  # Array of confidence scores
    average_confidence = Column(Float)
    
    # Configuration used
    prompt_version = Column(Integer)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=4000)
    configuration_snapshot = Column(JSON)  # Snapshot of config used
    
    # Environment info
    pipeline_id = Column(String(100))  # If part of a pipeline
    user_id = Column(String(100))      # If user-specific
    execution_mode = Column(String(50)) # legacy, shadow, modular, etc.
    
    # Foreign key relationship
    agent_config_id = Column(Integer, ForeignKey("agent_configurations.id"))
    agent_config = relationship("AgentConfiguration", back_populates="execution_logs")
    
    def __repr__(self):
        return f"<AgentExecutionLog(agent='{self.agent_name}', success={self.success}, threats={self.threats_found})>"


class AgentRegistry(BaseModel):
    """
    Registry of discovered agents and their metadata
    Tracks which agents are available in the system
    """
    __tablename__ = "agent_registry"
    
    agent_name = Column(String(100), unique=True, nullable=False, index=True)
    agent_class = Column(String(200), nullable=False)  # Full class name
    version = Column(String(50), nullable=False)
    
    # Metadata from AgentMetadata
    description = Column(String(1000))
    category = Column(String(50))  # architecture, business, compliance, etc.
    priority = Column(Integer, default=100)
    requires_document = Column(Boolean, default=True)
    requires_components = Column(Boolean, default=True)
    estimated_tokens = Column(Integer, default=3000)
    enabled_by_default = Column(Boolean, default=True)
    legacy_equivalent = Column(String(100))  # Maps to old agent name
    
    # Discovery metadata
    discovered_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String(500))  # Where the agent was found
    
    # Status
    is_available = Column(Boolean, default=True)
    load_error = Column(Text)  # If agent failed to load
    
    def __repr__(self):
        return f"<AgentRegistry(name='{self.agent_name}', version='{self.version}', available={self.is_available})>"