# AgentCore Framework Developer Guide

## Overview

The Core Network DevOps Agent is built using Amazon Bedrock's AgentCore framework patterns, providing a robust, scalable, and maintainable architecture for AI-powered network infrastructure management.

## Framework Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                AgentCore Framework Layer                    │
├─────────────────────────────────────────────────────────────┤
│  Agent System   │  Tool System    │  Memory System          │
│  • Agent        │  • Tool         │  • ConversationMemory   │
│  • AgentResponse│  • ToolResult   │  • MessageRole          │
│  • AgentConfig  │  • ToolSpec     │  • ConversationMessage  │
│  • AgentFactory │  • ToolRegistry │  • Context Management   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│              Application Layer                              │
├─────────────────────────────────────────────────────────────┤
│  @agent_handler │  @tool Methods  │  Business Logic         │
│  • Auto Tool    │  • AWS Ops     │  • Network Functions    │
│    Registration │  • K8s Ops     │  • Infrastructure Mgmt  │
│  • Memory Mgmt  │  • NF Deploy   │  • DevOps Automation    │
│  • Health Check │  • Monitoring  │  • Error Handling       │
└─────────────────────────────────────────────────────────────┘
```

## Getting Started

### 1. Basic Agent Creation

```python
from core_network_devops_agent.framework import Agent, agent_handler, tool, ToolResult

@agent_handler
class MyNetworkAgent(Agent):
    def __init__(self):
        super().__init__(
            name="MyNetworkAgent",
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            region="us-east-1"
        )
    
    async def initialize(self):
        """Initialize the agent and its dependencies."""
        # Custom initialization logic
        self._initialized = True
    
    async def process_request(self, user_input, context=None):
        """Process user requests with framework patterns."""
        # Framework handles tool execution and response generation
        return await super().process_request(user_input, context)
```

### 2. Tool Development with Decorators

```python
@tool(
    name="deploy_network_function",
    description="Deploy a network function with specified configuration",
    parameters={
        "nf_type": {
            "type": "string", 
            "description": "Network function type (AMF, SMF, UPF)", 
            "required": True,
            "enum": ["AMF", "SMF", "UPF"]
        },
        "replicas": {
            "type": "integer", 
            "description": "Number of replicas", 
            "required": False, 
            "default": 1
        },
        "namespace": {
            "type": "string", 
            "description": "Kubernetes namespace", 
            "required": False, 
            "default": "core-network"
        }
    }
)
async def deploy_network_function(self, nf_type: str, replicas: int = 1, namespace: str = "core-network"):
    """Deploy a network function with the specified configuration."""
    try:
        # Implementation logic
        deployment_config = {
            "name": f"{nf_type.lower()}-deployment",
            "type": nf_type,
            "replicas": replicas,
            "namespace": namespace,
            "image": f"core-network/{nf_type.lower()}:latest",
            "status": "Deploying"
        }
        
        # Return structured result
        return ToolResult(
            success=True,
            data=deployment_config,
            metadata={"deployment_time": datetime.now().isoformat()}
        )
        
    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Failed to deploy {nf_type}: {str(e)}"
        )
```

### 3. Agent Factory Usage

```python
from core_network_devops_agent.framework import AgentFactory, AgentConfig

# Create agent from configuration
config = AgentConfig(
    name="ProductionNetworkAgent",
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    region="us-east-1",
    max_tokens=4000,
    enable_memory=True,
    memory_retention_hours=24
)

agent = AgentFactory.create_agent(MyNetworkAgent, config)

# Or create from YAML file
agent = AgentFactory.from_yaml_config(MyNetworkAgent, "config/agent_config.yaml")
```

## Framework Components

### Agent System

#### Agent Base Class

```python
class Agent(ABC):
    """Base agent class following AgentCore patterns."""
    
    def __init__(self, name: str, model_id: str, region: str, config: Dict[str, Any]):
        self.name = name
        self.model_id = model_id
        self.region = region
        self._tools: Dict[str, Tool] = {}
        self._memory: ConversationMemory = None
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent and its dependencies."""
        pass
    
    @abstractmethod
    async def process_request(self, user_input: str, context: Dict[str, Any] = None) -> AgentResponse:
        """Process a user request and return a structured response."""
        pass
    
    def register_tool(self, tool_name: str, tool_instance: Tool) -> None:
        """Register a tool with the agent."""
        self._tools[tool_name] = tool_instance
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        # Returns health status for agent and all tools
```

#### AgentResponse Model

```python
@dataclass
class AgentResponse:
    """Structured response from agent operations."""
    content: str                                    # Response content
    success: bool = True                           # Success indicator
    tool_results: Optional[Dict[str, Any]] = None  # Tool execution results
    metadata: Optional[Dict[str, Any]] = None      # Additional metadata
    timestamp: Optional[datetime] = None           # Response timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization."""
```

### Tool System

#### Tool Base Class

```python
class Tool(ABC):
    """Base tool class for framework compliance."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    @abstractmethod
    def get_spec(self) -> ToolSpec:
        """Get the tool specification for Bedrock compatibility."""
        pass
    
    async def execute_with_validation(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute with parameter validation and error handling."""
        # Validates parameters against spec and handles errors
```

#### ToolResult Model

```python
@dataclass
class ToolResult:
    """Structured result from tool execution."""
    success: bool                                   # Success indicator
    data: Optional[Dict[str, Any]] = None          # Result data
    error: Optional[str] = None                    # Error message
    metadata: Optional[Dict[str, Any]] = None      # Additional metadata
    execution_time_ms: Optional[float] = None      # Execution time
    timestamp: Optional[datetime] = None           # Execution timestamp
```

#### Tool Registry

```python
class ToolRegistry:
    """Registry for managing multiple tools."""
    
    def register(self, tool: Tool) -> None:
        """Register a tool in the registry."""
    
    def get_tool_specs(self) -> List[Dict[str, Any]]:
        """Get Bedrock-compatible tool specifications."""
    
    async def initialize_all(self) -> None:
        """Initialize all registered tools."""
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Health check all registered tools."""
```

### Memory System

#### Conversation Memory

```python
class ConversationMemory:
    """Advanced conversation memory management."""
    
    def __init__(self, max_messages: int = 100, retention_hours: int = 24):
        self.max_messages = max_messages
        self.retention_hours = retention_hours
    
    def add_message(self, role: MessageRole, content: str, metadata: Dict[str, Any] = None):
        """Add a message to conversation history."""
    
    def get_messages(self, limit: int = None, role_filter: MessageRole = None) -> List[ConversationMessage]:
        """Retrieve messages with optional filtering."""
    
    def update_context(self, context: Dict[str, Any]) -> None:
        """Update conversation context."""
    
    def to_bedrock_format(self) -> List[Dict[str, Any]]:
        """Convert to Bedrock API format."""
```

#### Message Models

```python
class MessageRole(str, Enum):
    """Message roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

@dataclass
class ConversationMessage:
    """Individual conversation message."""
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    tool_results: Optional[Dict[str, Any]] = None
```

## Advanced Features

### Decorator System

#### @agent_handler Decorator

```python
@agent_handler
class MyAgent(Agent):
    """Automatically registers all @tool decorated methods."""
    
    @tool(name="my_tool", description="Example tool")
    async def my_tool_method(self, param: str):
        return ToolResult(success=True, data={"result": param})
```

The `@agent_handler` decorator:
- Discovers all `@tool` decorated methods
- Automatically registers them as tools
- Sets up tool registry and management
- Provides tool health checking

#### @tool Decorator

```python
@tool(
    name="tool_name",
    description="Tool description",
    parameters={
        "param1": {"type": "string", "description": "Parameter 1", "required": True},
        "param2": {"type": "integer", "description": "Parameter 2", "required": False, "default": 10}
    }
)
async def my_tool(self, param1: str, param2: int = 10):
    """Tool implementation with automatic wrapping."""
    # Return value automatically wrapped in ToolResult
    return {"processed": param1, "count": param2}
```

The `@tool` decorator:
- Generates tool specifications automatically
- Handles parameter validation
- Wraps return values in ToolResult
- Provides execution timing and error handling
- Integrates with tool registry

### Parameter Validation

```python
@tool(
    name="validated_tool",
    parameters={
        "region": {"type": "string", "enum": ["us-east-1", "us-west-2"], "required": True},
        "count": {"type": "integer", "minimum": 1, "maximum": 100, "required": False, "default": 10}
    }
)
async def validated_tool(self, region: str, count: int = 10):
    """Tool with automatic parameter validation."""
    # Parameters are validated before execution
    return {"region": region, "count": count}
```

### Error Handling and Retry

```python
from core_network_devops_agent.framework.decorators import retry_on_failure

@retry_on_failure(max_retries=3, delay_seconds=1.0)
@tool(name="resilient_tool", description="Tool with retry logic")
async def resilient_tool(self, operation: str):
    """Tool with automatic retry on failure."""
    # Automatically retries on exceptions
    if operation == "fail":
        raise Exception("Simulated failure")
    return {"operation": operation, "status": "success"}
```

## Configuration Management

### YAML Configuration

```yaml
# config/agent_config.yaml
agent:
  name: "MyNetworkAgent"
  model:
    model_id: "anthropic.claude-3-sonnet-20240229-v1:0"
    region: "us-east-1"
    max_tokens: 4000
    temperature: 0.1
  
  behavior:
    max_conversation_turns: 50
    enable_memory: true
    memory_retention_hours: 24
    enable_tool_chaining: true
    max_tool_calls_per_turn: 5

memory:
  max_messages: 100
  retention_hours: 24
  enable_summarization: true

tools:
  deploy_network_function:
    enabled: true
    timeout_seconds: 60
    retry_attempts: 3
  
  get_system_health:
    enabled: true
    timeout_seconds: 30
    retry_attempts: 2
```

### Programmatic Configuration

```python
from core_network_devops_agent.framework import AgentConfig

config = AgentConfig(
    name="MyAgent",
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    region="us-east-1",
    max_tokens=4000,
    temperature=0.1,
    max_conversation_turns=50,
    enable_memory=True,
    memory_retention_hours=24,
    enable_tool_chaining=True,
    max_tool_calls_per_turn=5
)
```

## Testing Framework

### Unit Testing Tools

```python
import pytest
from core_network_devops_agent.framework import Agent, tool, ToolResult

class TestAgent(Agent):
    @tool(name="test_tool", description="Test tool")
    async def test_tool(self, value: str):
        return ToolResult(success=True, data={"value": value})

@pytest.mark.asyncio
async def test_tool_execution():
    agent = TestAgent()
    await agent.initialize()
    
    tool = agent.get_tool("test_tool")
    result = await tool.execute_with_validation({"value": "test"})
    
    assert result.success
    assert result.data["value"] == "test"
    assert result.execution_time_ms is not None
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_agent_request_processing():
    agent = MyNetworkAgent()
    await agent.initialize()
    
    response = await agent.process_request("Deploy AMF with 3 replicas")
    
    assert response.success
    assert "AMF" in response.content
    assert response.tool_results is not None
    assert len(agent.get_conversation_history()) == 2  # User + Assistant
```

## Best Practices

### 1. Tool Design

- **Single Responsibility**: Each tool should have a single, well-defined purpose
- **Parameter Validation**: Always define comprehensive parameter schemas
- **Error Handling**: Return structured ToolResult with clear error messages
- **Documentation**: Provide clear descriptions and examples

```python
@tool(
    name="deploy_amf",
    description="Deploy 5G AMF (Access and Mobility Management Function) with high availability",
    parameters={
        "replicas": {
            "type": "integer",
            "description": "Number of AMF replicas for high availability",
            "required": False,
            "default": 2,
            "minimum": 1,
            "maximum": 10
        },
        "namespace": {
            "type": "string",
            "description": "Kubernetes namespace for deployment",
            "required": False,
            "default": "core-network",
            "pattern": "^[a-z0-9-]+$"
        }
    },
    examples=[
        {
            "description": "Deploy AMF with default settings",
            "parameters": {},
            "expected_result": {"name": "amf", "replicas": 2, "namespace": "core-network"}
        },
        {
            "description": "Deploy AMF with custom configuration",
            "parameters": {"replicas": 3, "namespace": "production"},
            "expected_result": {"name": "amf", "replicas": 3, "namespace": "production"}
        }
    ]
)
async def deploy_amf(self, replicas: int = 2, namespace: str = "core-network"):
    """Deploy 5G AMF with specified configuration."""
    # Implementation
```

### 2. Memory Management

- **Context Updates**: Regularly update conversation context with relevant information
- **Message Filtering**: Use role-based filtering for specific conversation analysis
- **Cleanup**: Implement proper message retention and cleanup policies

```python
# Update context with deployment information
self._memory.update_context({
    "last_deployment": "AMF",
    "current_namespace": namespace,
    "deployment_count": deployment_count
})

# Filter for user questions only
user_questions = self._memory.get_user_messages(limit=5)
```

### 3. Error Handling

- **Graceful Degradation**: Handle tool failures gracefully
- **Informative Errors**: Provide actionable error messages
- **Retry Logic**: Implement appropriate retry strategies

```python
try:
    result = await self.deploy_network_function(nf_type="AMF", replicas=3)
    if not result.success:
        return ToolResult(
            success=False,
            error=f"Deployment failed: {result.error}. Please check cluster resources and try again."
        )
except Exception as e:
    return ToolResult(
        success=False,
        error=f"Unexpected error during deployment: {str(e)}. Contact support if issue persists."
    )
```

### 4. Performance Optimization

- **Async Operations**: Use async/await for all I/O operations
- **Connection Pooling**: Reuse connections for external services
- **Caching**: Cache frequently accessed data appropriately

```python
# Use connection pooling
self.aws_client = self.aws_manager.get_client('ec2')  # Cached client

# Async operations
async def deploy_multiple_nfs(self, nf_configs: List[Dict]):
    """Deploy multiple network functions concurrently."""
    tasks = [
        self.deploy_network_function(**config)
        for config in nf_configs
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

## Troubleshooting

### Common Issues

1. **Tool Not Registered**
   - Ensure `@tool` decorator is applied
   - Verify `@agent_handler` is on the class
   - Check tool name uniqueness

2. **Parameter Validation Errors**
   - Verify parameter types match schema
   - Check required parameters are provided
   - Validate enum values and constraints

3. **Memory Issues**
   - Monitor conversation history size
   - Implement appropriate cleanup policies
   - Check memory retention settings

4. **Performance Issues**
   - Profile tool execution times
   - Optimize database queries
   - Use appropriate async patterns

### Debugging Tools

```python
# Enable debug logging
import structlog
structlog.configure(level="DEBUG")

# Tool execution profiling
@tool(name="profiled_tool")
async def profiled_tool(self, param: str):
    start_time = time.time()
    # Tool implementation
    execution_time = (time.time() - start_time) * 1000
    logger.debug("Tool execution time", tool="profiled_tool", time_ms=execution_time)
    return result

# Health check debugging
health = await agent.health_check()
for component, status in health.get('tool_health', {}).items():
    if 'error' in str(status):
        logger.error("Tool health issue", tool=component, status=status)
```

## Migration Guide

### From Custom Implementation to AgentCore

1. **Update Agent Class**
   ```python
   # Before
   class MyAgent:
       def __init__(self):
           self.tools = {}
   
   # After
   @agent_handler
   class MyAgent(Agent):
       def __init__(self):
           super().__init__(name="MyAgent")
   ```

2. **Convert Tools to Decorators**
   ```python
   # Before
   class MyTool:
       async def execute(self, params):
           return {"result": "success"}
   
   # After
   @tool(name="my_tool", description="My tool")
   async def my_tool(self, param: str):
       return ToolResult(success=True, data={"result": "success"})
   ```

3. **Update Response Handling**
   ```python
   # Before
   return {"content": "Response", "success": True}
   
   # After
   return AgentResponse(content="Response", success=True)
   ```

This guide provides comprehensive coverage of the AgentCore framework implementation. For additional examples and advanced usage patterns, refer to the test files and example implementations in the repository.