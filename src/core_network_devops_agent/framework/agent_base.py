"""
Agent Base Classes for Bedrock AgentCore Framework Compatibility
"""

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class AgentResponse:
    """Response from an agent operation."""
    content: str
    success: bool = True
    tool_results: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'content': self.content,
            'success': self.success,
            'tool_results': self.tool_results or {},
            'metadata': self.metadata or {},
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class Agent(ABC):
    """
    Base Agent class following Bedrock AgentCore framework patterns.
    
    This provides the foundation for building AI agents that can:
    - Process natural language requests
    - Execute tools and operations
    - Maintain conversation context
    - Generate structured responses
    """
    
    def __init__(
        self,
        name: str,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        region: str = "us-east-1",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the agent.
        
        Args:
            name: Agent name
            model_id: Bedrock model identifier
            region: AWS region
            config: Optional configuration dictionary
        """
        self.name = name
        self.model_id = model_id
        self.region = region
        self.config = config or {}
        
        # Initialize components
        self._tools: Dict[str, Any] = {}
        self._memory = None
        self._bedrock_client = None
        
        # Agent state
        self._initialized = False
        
        logger.info("Agent initialized", 
                   name=name, model_id=model_id, region=region)
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent and its dependencies."""
        pass
    
    @abstractmethod
    async def process_request(
        self, 
        user_input: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Process a user request and return a response.
        
        Args:
            user_input: User's natural language request
            context: Optional additional context
            
        Returns:
            AgentResponse with the agent's response
        """
        pass
    
    def register_tool(self, tool_name: str, tool_instance: Any) -> None:
        """Register a tool with the agent."""
        self._tools[tool_name] = tool_instance
        logger.info("Tool registered", tool=tool_name, agent=self.name)
    
    def get_tools(self) -> Dict[str, Any]:
        """Get all registered tools."""
        return self._tools.copy()
    
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """Get a specific tool by name."""
        return self._tools.get(tool_name)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the agent."""
        health_status = {
            'agent': self.name,
            'status': 'healthy' if self._initialized else 'not_initialized',
            'model_id': self.model_id,
            'region': self.region,
            'tools': list(self._tools.keys()),
            'timestamp': datetime.now().isoformat()
        }
        
        # Check tool health
        tool_health = {}
        for tool_name, tool in self._tools.items():
            try:
                if hasattr(tool, 'health_check'):
                    tool_health[tool_name] = await tool.health_check()
                else:
                    tool_health[tool_name] = 'available'
            except Exception as e:
                tool_health[tool_name] = f'error: {str(e)}'
        
        health_status['tool_health'] = tool_health
        return health_status
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history from memory."""
        if self._memory:
            return self._memory.get_history()
        return []
    
    def clear_conversation_history(self) -> None:
        """Clear conversation history."""
        if self._memory:
            self._memory.clear()
            logger.info("Conversation history cleared", agent=self.name)


class AgentConfig(BaseModel):
    """Configuration model for agents."""
    
    name: str
    model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    region: str = "us-east-1"
    max_tokens: int = 4000
    temperature: float = 0.1
    
    # Behavior settings
    max_conversation_turns: int = 50
    enable_memory: bool = True
    memory_retention_hours: int = 24
    enable_tool_chaining: bool = True
    max_tool_calls_per_turn: int = 5
    
    # Tool settings
    tool_timeout_seconds: int = 30
    tool_retry_attempts: int = 3
    
    class Config:
        """Pydantic configuration."""
        extra = "allow"  # Allow additional fields


class AgentFactory:
    """Factory for creating agents with proper configuration."""
    
    @staticmethod
    def create_agent(
        agent_class: type,
        config: Union[Dict[str, Any], AgentConfig],
        **kwargs
    ) -> Agent:
        """
        Create an agent instance with the given configuration.
        
        Args:
            agent_class: Agent class to instantiate
            config: Configuration dictionary or AgentConfig instance
            **kwargs: Additional arguments
            
        Returns:
            Configured agent instance
        """
        if isinstance(config, dict):
            config = AgentConfig(**config)
        
        return agent_class(
            name=config.name,
            model_id=config.model_id,
            region=config.region,
            config=config.dict(),
            **kwargs
        )
    
    @staticmethod
    def from_yaml_config(
        agent_class: type,
        config_path: str,
        **kwargs
    ) -> Agent:
        """Create an agent from a YAML configuration file."""
        import yaml
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        agent_config = config_data.get('agent', {})
        return AgentFactory.create_agent(agent_class, agent_config, **kwargs)