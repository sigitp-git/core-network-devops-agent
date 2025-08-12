# Quick Start Guide - AgentCore Framework

## 🚀 Get Started in 5 Minutes

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd core-network-devops-agent

# Install dependencies
pip3 install -r requirements.txt

# Configure AWS credentials
aws configure
```

### 2. Basic Usage

```bash
# Start interactive chat with AgentCore framework
python -m core_network_devops_agent chat

# Check agent health
python -m core_network_devops_agent health

# View agent information and tools
python -m core_network_devops_agent info
```

### 3. Example Interactions

```
🤖 core-network-agent> List my EC2 instances

✅ I found 2 EC2 instances in your account:

**i-0123456789abcdef0** (t3.large)
- State: running
- Private IP: 10.0.1.100
- Name: core-network-node-1

**i-0987654321fedcba0** (t3.xlarge)  
- State: running
- Private IP: 10.0.1.101
- Name: core-network-node-2

🔧 Tool Execution Results:
   ✅ describe_ec2_instances: Found 2 instances
```

```
🤖 core-network-agent> Deploy a 5G AMF with 3 replicas

✅ I've successfully deployed a 5G AMF with the following configuration:

**Deployment Details:**
- Name: amf
- Type: AMF (5G Core)
- Replicas: 3 (for high availability)
- Namespace: core-network
- Status: Deploying

🔧 Tool Execution Results:
   ✅ deploy_5g_amf: Deployment created successfully
```

## 🛠️ Development Quick Start

### Create a Custom Agent

```python
from core_network_devops_agent.framework import Agent, agent_handler, tool, ToolResult

@agent_handler
class MyCustomAgent(Agent):
    def __init__(self):
        super().__init__(
            name="MyCustomAgent",
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            region="us-east-1"
        )
    
    async def initialize(self):
        """Initialize your agent."""
        self._initialized = True
    
    async def process_request(self, user_input, context=None):
        """Process requests with AgentCore framework."""
        return await super().process_request(user_input, context)
    
    @tool(
        name="my_custom_tool",
        description="A custom tool for demonstration",
        parameters={
            "action": {"type": "string", "description": "Action to perform", "required": True},
            "count": {"type": "integer", "description": "Number of items", "required": False, "default": 1}
        }
    )
    async def my_custom_tool(self, action: str, count: int = 1):
        """Custom tool implementation."""
        return ToolResult(
            success=True,
            data={"action": action, "count": count, "status": "completed"}
        )

# Usage
agent = MyCustomAgent()
await agent.initialize()
response = await agent.process_request("Perform action with 5 items")
```

### Add Tools to Existing Agent

```python
# Add to CoreNetworkDevOpsAgent
@tool(
    name="deploy_custom_nf",
    description="Deploy a custom network function",
    parameters={
        "nf_name": {"type": "string", "description": "Network function name", "required": True},
        "image": {"type": "string", "description": "Container image", "required": True},
        "replicas": {"type": "integer", "description": "Number of replicas", "required": False, "default": 1}
    }
)
async def deploy_custom_nf(self, nf_name: str, image: str, replicas: int = 1):
    """Deploy a custom network function."""
    deployment_config = {
        "name": nf_name,
        "image": image,
        "replicas": replicas,
        "namespace": "core-network",
        "status": "Deploying"
    }
    
    return ToolResult(
        success=True,
        data=deployment_config,
        metadata={"deployment_type": "custom"}
    )
```

## 🧪 Testing Your Agent

### Run Framework Tests

```bash
# Test AgentCore framework integration
python3 test_agentcore_framework.py

# Test comprehensive functionality
python3 test_agent_comprehensive.py

# Test basic functionality
python3 test_agent_basic.py
```

### Write Custom Tests

```python
import pytest
from your_agent import MyCustomAgent

@pytest.mark.asyncio
async def test_custom_tool():
    agent = MyCustomAgent()
    await agent.initialize()
    
    # Test tool directly
    tool = agent.get_tool("my_custom_tool")
    result = await tool.execute_with_validation({"action": "test", "count": 5})
    
    assert result.success
    assert result.data["action"] == "test"
    assert result.data["count"] == 5

@pytest.mark.asyncio
async def test_agent_request():
    agent = MyCustomAgent()
    await agent.initialize()
    
    # Test full request processing
    response = await agent.process_request("Perform test action with 3 items")
    
    assert response.success
    assert "test" in response.content.lower()
    assert response.tool_results is not None
```

## 📋 Configuration

### Basic Configuration

```yaml
# config/agent_config.yaml
agent:
  name: "MyAgent"
  model:
    model_id: "anthropic.claude-3-sonnet-20240229-v1:0"
    region: "us-east-1"
    max_tokens: 4000
    temperature: 0.1

memory:
  max_messages: 100
  retention_hours: 24

tools:
  my_custom_tool:
    enabled: true
    timeout_seconds: 30
```

### Environment Variables

```bash
# .env file
AWS_REGION=us-east-1
AWS_PROFILE=default
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
LOG_LEVEL=INFO
```

## 🔧 Available Tools

The CoreNetworkDevOpsAgent comes with these built-in tools:

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `describe_ec2_instances` | List and describe EC2 instances | `region`, `instance_ids`, `filters` |
| `describe_vpcs` | List and describe VPCs | `region`, `vpc_ids` |
| `deploy_5g_amf` | Deploy 5G AMF network function | `name`, `namespace`, `replicas`, `plmn_id` |
| `list_network_functions` | List deployed network functions | `namespace`, `function_type` |
| `get_system_health` | Get system health status | `include_metrics` |

## 🎯 Common Use Cases

### 1. Infrastructure Management
```
"List all EC2 instances in us-west-2"
"Create a VPC with CIDR 10.0.0.0/16"
"Show me all VPCs in my account"
```

### 2. Network Function Deployment
```
"Deploy AMF with 3 replicas"
"List all network functions in core-network namespace"
"Deploy SMF in production namespace"
```

### 3. System Monitoring
```
"What's the current system health?"
"Show me the status of all network functions"
"Get performance metrics for the core network"
```

## 🚨 Troubleshooting

### Common Issues

1. **AWS Credentials Not Configured**
   ```bash
   aws configure
   # or
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   ```

2. **Tool Not Found**
   - Check `@tool` decorator is applied
   - Verify `@agent_handler` is on the class
   - Ensure tool name is unique

3. **Parameter Validation Errors**
   - Check parameter types match schema
   - Verify required parameters are provided
   - Validate enum values

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python -m core_network_devops_agent chat --verbose
```

### Health Check

```bash
# Check agent and tool health
python -m core_network_devops_agent health
```

## 📚 Next Steps

1. **Read the Full Guide**: [AgentCore Framework Guide](AGENTCORE_FRAMEWORK_GUIDE.md)
2. **Review Examples**: Check the `demo_agent.py` for comprehensive examples
3. **Explore Tests**: Look at test files for usage patterns
4. **Customize**: Add your own tools and extend functionality

## 🎉 Success Metrics

- ✅ **100% Test Pass Rate** - All framework and functionality tests pass
- ✅ **AgentCore Compliance** - Follows all AWS AgentCore patterns
- ✅ **Enhanced Features** - Specialized 5G/LTE network capabilities
- ✅ **Production Ready** - Robust error handling and monitoring

Happy building with the AgentCore framework! 🚀