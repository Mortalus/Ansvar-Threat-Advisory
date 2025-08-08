"""
Comprehensive Unit Tests for Modular Agent System

Tests agent registry, health monitoring, validation, and execution
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json

# Import components to test
from app.core.agents.base import BaseAgent, AgentMetadata, AgentExecutionContext, ThreatOutput
from app.core.agents.registry import AgentRegistry, agent_registry
from app.core.agents.health_monitor import AgentHealthMonitor, AgentHealthMetrics
from app.core.agents.validator import AgentValidator, ValidationLevel, ValidationResult


# Test fixtures
@pytest.fixture
def mock_agent():
    """Create a mock agent for testing"""
    agent = Mock(spec=BaseAgent)
    agent.get_metadata.return_value = AgentMetadata(
        name="test_agent",
        version="1.0.0",
        description="Test agent for unit tests",
        category="architecture",
        priority=10,
        requires_document=True,
        requires_components=True,
        estimated_tokens=5000,
        enabled_by_default=True
    )
    agent.validate_context.return_value = True
    agent.update_configuration = Mock()
    return agent


@pytest.fixture
def test_context():
    """Create a test execution context"""
    return AgentExecutionContext(
        pipeline_id="test-pipeline-123",
        step_num=3,
        document_content="Test document content",
        components=[
            {"name": "web_server", "type": "process"},
            {"name": "database", "type": "datastore"}
        ],
        extracted_data={"test": "data"},
        previous_results={}
    )


@pytest.fixture
def test_registry():
    """Create a clean test registry"""
    registry = AgentRegistry()
    registry.clear_registry()
    return registry


@pytest.fixture
def health_monitor():
    """Create a health monitor instance"""
    monitor = AgentHealthMonitor()
    monitor.health_check_interval = 1  # Fast checks for testing
    return monitor


@pytest.fixture
def validator():
    """Create a validator instance"""
    return AgentValidator(ValidationLevel.STANDARD)


class TestAgentForTesting(BaseAgent):
    """Concrete test agent implementation"""
    
    def __init__(self, name="test_agent"):
        self.name = name
        self.execution_count = 0
        self.should_fail = False
    
    def get_metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name=self.name,
            version="1.0.0",
            description="Test agent",
            category="architecture",
            priority=10,
            requires_document=True,
            requires_components=True,
            estimated_tokens=5000,
            enabled_by_default=True
        )
    
    def validate_context(self, context: AgentExecutionContext) -> bool:
        return not self.should_fail
    
    async def execute(self, context: AgentExecutionContext) -> ThreatOutput:
        self.execution_count += 1
        
        if self.should_fail:
            raise Exception("Test failure")
        
        return ThreatOutput(
            threats=[
                {
                    "description": "Test threat",
                    "category": "authentication",
                    "severity": "high",
                    "mitigation": "Test mitigation"
                }
            ],
            metadata={
                "agent": self.name,
                "execution_count": self.execution_count
            }
        )


# Test Agent Registry
class TestAgentRegistry:
    """Test agent registry functionality"""
    
    def test_register_agent_class(self, test_registry):
        """Test registering an agent class"""
        agent_class = TestAgentForTesting
        
        result = test_registry.register_class(agent_class)
        
        assert result is True
        assert "test_agent" in test_registry._agents
        assert test_registry.get_agent("test_agent") is not None
    
    def test_register_duplicate_agent(self, test_registry):
        """Test that duplicate registration is prevented"""
        agent_class = TestAgentForTesting
        
        test_registry.register_class(agent_class)
        result = test_registry.register_class(agent_class)
        
        assert result is False
    
    def test_legacy_mapping(self, test_registry):
        """Test legacy agent name mapping"""
        test_registry._legacy_mapping["old_name"] = "new_name"
        
        agent = TestAgentForTesting(name="new_name")
        test_registry.register_instance(agent)
        
        # Should find agent by both old and new name
        assert test_registry.get_agent("new_name") is not None
        assert test_registry.get_agent("old_name") is not None
        assert test_registry.get_agent("old_name") == test_registry.get_agent("new_name")
    
    def test_get_enabled_agents(self, test_registry):
        """Test getting enabled agents with configuration"""
        agent1 = TestAgentForTesting(name="agent1")
        agent2 = TestAgentForTesting(name="agent2")
        agent3 = TestAgentForTesting(name="agent3")
        
        test_registry.register_instance(agent1)
        test_registry.register_instance(agent2)
        test_registry.register_instance(agent3)
        
        config = {
            "enabled_agents": ["agent1", "agent3"]
        }
        
        enabled = test_registry.get_enabled_agents(config)
        
        assert len(enabled) == 2
        assert enabled[0].get_metadata().name == "agent1"
        assert enabled[1].get_metadata().name == "agent3"
    
    def test_get_agents_by_category(self, test_registry):
        """Test filtering agents by category"""
        agent1 = TestAgentForTesting(name="arch_agent")
        agent2 = Mock(spec=BaseAgent)
        agent2.get_metadata.return_value = AgentMetadata(
            name="biz_agent",
            version="1.0",
            description="Business agent",
            category="business"
        )
        
        test_registry.register_instance(agent1)
        test_registry.register_instance(agent2)
        
        arch_agents = test_registry.get_agents_by_category("architecture")
        biz_agents = test_registry.get_agents_by_category("business")
        
        assert len(arch_agents) == 1
        assert len(biz_agents) == 1
        assert arch_agents[0].get_metadata().name == "arch_agent"
        assert biz_agents[0].get_metadata().name == "biz_agent"
    
    def test_validate_agents_with_context(self, test_registry, test_context):
        """Test agent validation with context"""
        agent1 = TestAgentForTesting(name="valid_agent")
        agent2 = TestAgentForTesting(name="invalid_agent")
        agent2.should_fail = True
        
        test_registry.register_instance(agent1)
        test_registry.register_instance(agent2)
        
        valid_agents = test_registry.validate_agents(test_context)
        
        assert len(valid_agents) == 1
        assert valid_agents[0].get_metadata().name == "valid_agent"
    
    @pytest.mark.asyncio
    async def test_hot_reload_agent(self, test_registry):
        """Test hot reloading agent configuration"""
        agent = TestAgentForTesting()
        test_registry.register_instance(agent)
        
        new_config = {"test_setting": "new_value"}
        result = await test_registry.reload_agent("test_agent", new_config)
        
        assert result is True
        assert test_registry._configurations["test_agent"] == new_config
    
    def test_get_registry_stats(self, test_registry):
        """Test registry statistics"""
        agent1 = TestAgentForTesting(name="agent1")
        agent2 = TestAgentForTesting(name="agent2")
        
        test_registry.register_instance(agent1)
        test_registry.register_instance(agent2)
        
        stats = test_registry.get_registry_stats()
        
        assert stats["total_agents"] == 2
        assert stats["total_classes"] == 2
        assert "architecture" in stats["agents_by_category"]
        assert stats["agents_by_category"]["architecture"] == 2


# Test Health Monitor
class TestHealthMonitor:
    """Test health monitoring functionality"""
    
    @pytest.mark.asyncio
    async def test_check_agent_health(self, health_monitor, mock_agent):
        """Test basic health check"""
        result = await health_monitor.check_agent_health(mock_agent)
        
        assert result is True
        assert "test_agent" in health_monitor.metrics
        assert health_monitor.metrics["test_agent"].is_healthy is True
    
    @pytest.mark.asyncio
    async def test_monitor_successful_execution(self, health_monitor):
        """Test monitoring successful execution"""
        agent_name = "test_agent"
        
        async def successful_execution():
            await asyncio.sleep(0.1)
            return {"result": "success"}
        
        result = await health_monitor.monitor_execution(
            agent_name, 
            successful_execution()
        )
        
        assert result == {"result": "success"}
        
        metrics = health_monitor.get_or_create_metrics(agent_name)
        assert metrics.total_executions == 1
        assert metrics.successful_executions == 1
        assert metrics.consecutive_failures == 0
    
    @pytest.mark.asyncio
    async def test_monitor_failed_execution(self, health_monitor):
        """Test monitoring failed execution"""
        agent_name = "test_agent"
        
        async def failed_execution():
            raise Exception("Test failure")
        
        with pytest.raises(Exception) as exc_info:
            await health_monitor.monitor_execution(
                agent_name,
                failed_execution()
            )
        
        assert "Test failure" in str(exc_info.value)
        
        metrics = health_monitor.get_or_create_metrics(agent_name)
        assert metrics.total_executions == 1
        assert metrics.failed_executions == 1
        assert metrics.consecutive_failures == 1
        assert metrics.last_error is not None
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self, health_monitor):
        """Test circuit breaker functionality"""
        agent_name = "test_agent"
        
        async def failing_execution():
            raise Exception("Test failure")
        
        # Fail 3 times to open circuit
        for _ in range(3):
            try:
                await health_monitor.monitor_execution(
                    agent_name,
                    failing_execution()
                )
            except:
                pass
        
        metrics = health_monitor.get_or_create_metrics(agent_name)
        assert metrics.circuit_breaker_state == "open"
        assert metrics.consecutive_failures >= 3
        
        # Circuit should be open, preventing execution
        with pytest.raises(Exception) as exc_info:
            await health_monitor.monitor_execution(
                agent_name,
                failing_execution()
            )
        
        assert "Circuit breaker open" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, health_monitor):
        """Test execution timeout"""
        agent_name = "test_agent"
        
        async def slow_execution():
            await asyncio.sleep(100)  # Will timeout
        
        with pytest.raises(Exception) as exc_info:
            await health_monitor.monitor_execution(
                agent_name,
                slow_execution()
            )
        
        assert "timed out" in str(exc_info.value)
        
        metrics = health_monitor.get_or_create_metrics(agent_name)
        assert metrics.failed_executions == 1
    
    def test_health_metrics_calculation(self):
        """Test health metrics calculations"""
        metrics = AgentHealthMetrics(agent_name="test")
        
        # Record some executions
        metrics.record_execution(True, 2.0)
        metrics.record_execution(True, 3.0)
        metrics.record_execution(False, 1.0, "Test error")
        metrics.record_execution(True, 2.5)
        
        assert metrics.success_rate == 75.0
        assert metrics.total_executions == 4
        assert metrics.successful_executions == 3
        assert metrics.failed_executions == 1
        assert metrics.average_execution_time == pytest.approx(2.125, 0.01)
    
    def test_health_report_generation(self, health_monitor):
        """Test health report generation"""
        # Create some metrics
        metrics1 = health_monitor.get_or_create_metrics("agent1")
        metrics1.is_healthy = True
        metrics1.record_execution(True, 1.0)
        
        metrics2 = health_monitor.get_or_create_metrics("agent2")
        metrics2.is_healthy = False
        metrics2.record_execution(False, 2.0, "Error")
        
        report = health_monitor.get_health_report()
        
        assert report["total_agents"] == 2
        assert report["healthy_agents"] == 1
        assert report["unhealthy_agents"] == 1
        assert "agent1" in report["agents"]
        assert "agent2" in report["agents"]
        assert report["agents"]["agent1"]["is_healthy"] is True
        assert report["agents"]["agent2"]["is_healthy"] is False


# Test Validator
class TestAgentValidator:
    """Test validation functionality"""
    
    def test_validate_valid_context(self, validator, test_context):
        """Test validation of valid context"""
        result = validator._validate_context(test_context)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_invalid_context(self, validator):
        """Test validation of invalid context"""
        invalid_context = AgentExecutionContext(
            pipeline_id="",  # Empty pipeline ID
            step_num=-1,  # Negative step
            document_content="x" * 2000000,  # Too large
            components=[{"invalid": "component"}]  # Missing name
        )
        
        result = validator._validate_context(invalid_context)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    def test_validate_agent_metadata(self, validator, mock_agent):
        """Test agent metadata validation"""
        result = validator._validate_agent_metadata(mock_agent)
        
        assert result.is_valid is True
    
    def test_validate_threat_output(self, validator):
        """Test threat output validation"""
        valid_output = ThreatOutput(
            threats=[
                {
                    "description": "This is a valid threat description",
                    "category": "authentication",
                    "severity": "high",
                    "mitigation": "Implement proper authentication"
                }
            ],
            metadata={"test": "data"}
        )
        
        result = validator._validate_output_structure(valid_output)
        assert result.is_valid is True
        
        quality_result = validator._validate_threat_quality(valid_output)
        assert quality_result.is_valid is True
    
    def test_validate_invalid_threats(self, validator):
        """Test validation of invalid threats"""
        invalid_output = [
            {"description": "Too short"},  # Too short
            {"no_description": "here"},  # Missing description
            {
                "description": "x" * 10000,  # Too long
                "severity": "invalid_level"  # Invalid severity
            }
        ]
        
        result = validator._validate_threat_quality(invalid_output)
        
        assert len(result.warnings) > 0
    
    def test_security_validation(self, validator):
        """Test security validation"""
        # Context with potential sensitive data
        sensitive_context = AgentExecutionContext(
            pipeline_id="test",
            step_num=0,
            document_content="password: 'secretpass123'",
            components=[]
        )
        
        result = validator._validate_input_security(sensitive_context)
        
        assert result.is_valid is False
        assert any("password" in error.lower() for error in result.errors)
    
    def test_output_sanitization(self, validator):
        """Test output sanitization"""
        sensitive_output = {
            "threat": "SQL injection risk",
            "details": "API key: abc123def456ghi789jkl012mno345pqr678",
            "password": "password: 'secretpass'"
        }
        
        sanitized = validator.sanitize_output(sensitive_output)
        
        assert "[REDACTED]" in str(sanitized)
        assert "abc123def456" not in str(sanitized)
        assert "secretpass" not in str(sanitized)
    
    def test_validation_levels(self):
        """Test different validation levels"""
        minimal = AgentValidator(ValidationLevel.MINIMAL)
        strict = AgentValidator(ValidationLevel.STRICT)
        paranoid = AgentValidator(ValidationLevel.PARANOID)
        
        # Minimal should have fewer rules
        assert len(minimal.validation_rules) < len(strict.validation_rules)
        assert len(strict.validation_rules) < len(paranoid.validation_rules)
        
        # Thresholds should be different
        assert minimal.quality_thresholds["min_threat_description_length"] < \
               strict.quality_thresholds["min_threat_description_length"]


# Integration Tests
class TestAgentSystemIntegration:
    """Integration tests for the complete agent system"""
    
    @pytest.mark.asyncio
    async def test_full_agent_lifecycle(self, test_registry, health_monitor, validator):
        """Test complete agent lifecycle"""
        # Create and register agent
        agent = TestAgentForTesting(name="lifecycle_agent")
        test_registry.register_instance(agent)
        
        # Create context
        context = AgentExecutionContext(
            pipeline_id="test-123",
            step_num=1,
            document_content="Test document",
            components=[{"name": "component1", "type": "process"}]
        )
        
        # Validate input
        input_validation = validator.validate_agent_input(agent, context)
        assert input_validation.is_valid is True
        
        # Execute with monitoring
        async def agent_execution():
            return await agent.execute(context)
        
        result = await health_monitor.monitor_execution(
            "lifecycle_agent",
            agent_execution()
        )
        
        # Validate output
        output_validation = validator.validate_agent_output(result, "lifecycle_agent")
        assert output_validation.is_valid is True
        
        # Check metrics
        metrics = health_monitor.get_agent_metrics("lifecycle_agent")
        assert metrics["total_executions"] == 1
        assert metrics["successful_executions"] == 1
        assert metrics["success_rate"] == 100.0
    
    @pytest.mark.asyncio
    async def test_agent_recovery(self, test_registry, health_monitor):
        """Test agent recovery after failures"""
        agent = TestAgentForTesting(name="recovery_agent")
        test_registry.register_instance(agent)
        
        # Make agent fail
        agent.should_fail = True
        
        # Register recovery strategy
        async def recovery_strategy(failed_agent):
            # Fix the agent
            if hasattr(failed_agent, 'should_fail'):
                failed_agent.should_fail = False
        
        health_monitor.register_recovery_strategy("recovery_agent", recovery_strategy)
        
        # Attempt recovery
        await health_monitor.attempt_recovery("recovery_agent")
        
        # Agent should be fixed
        assert agent.should_fail is False
        
        # Should be able to execute now
        context = AgentExecutionContext(
            pipeline_id="test",
            step_num=0,
            document_content="",
            components=[]
        )
        
        result = await agent.execute(context)
        assert result is not None


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])