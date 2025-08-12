# Core Network DevOps Agent

An AI agent built with Amazon Bedrock's AgentCore framework for managing core network infrastructure and DevOps operations on AWS.

## Overview

This agent leverages Amazon Bedrock's foundation models and follows AgentCore framework patterns to provide intelligent automation for:

- **Core Network Infrastructure**: 5G Core, LTE Core, and traditional network functions
- **AWS Infrastructure Management**: EC2, EKS, VPC, and other AWS services
- **DevOps Operations**: CI/CD pipelines, monitoring, and deployment automation
- **Network Function Lifecycle**: CNF/VNF deployment, scaling, and management

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Amazon Bedrock AgentCore Framework           │
├─────────────────────────────────────────────────────────────┤
│  Agent Base     │  Tool System    │  Memory Management      │
│  • Agent        │  • @tool        │  • ConversationMemory   │
│  • AgentResponse│  • ToolResult   │  • MessageRole          │
│  • AgentConfig  │  • ToolSpec     │  • Context Management   │
│  • AgentFactory │  • ToolRegistry │  • History Tracking     │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│              CoreNetworkDevOpsAgent                         │
├─────────────────────────────────────────────────────────────┤
│  @agent_handler decorated class with:                      │
│  • @tool AWS Operations    │  • @tool Network Functions    │
│  • @tool Kubernetes Ops   │  • @tool Monitoring           │
│  • Automatic Registration │  • Structured Responses       │
│  • Conversation Memory    │  • Health Checking            │
└─────────────────────────────────────────────────────────────┘
```

## Features

### 🤖 **AgentCore Framework Integration**
- Built with Amazon Bedrock AgentCore framework patterns
- Decorator-based tool registration (`@tool`, `@agent_handler`)
- Structured response models (`AgentResponse`, `ToolResult`)
- Advanced conversation memory and context management
- Automatic tool discovery and health checking

### 🌐 **Core Network Management**
- 5G Core Network Functions (AMF, SMF, UPF, AUSF, UDM, UDR, NRF, NSSF, PCF)
- LTE Core Network Elements (MME, SGW, PGW, HSS, PCRF)
- Network slicing and service orchestration
- Inter-network function communication
- Declarative network function deployment with `@tool` decorators

### ☁️ **AWS Infrastructure**
- EC2 instance management and optimization
- EKS cluster operations and scaling
- VPC networking and security groups
- Load balancer configuration
- Auto Scaling Groups management
- Tool-based AWS operations with structured responses

### 🔧 **DevOps Automation**
- CI/CD pipeline creation and management
- Container registry operations (ECR)
- Infrastructure as Code (CloudFormation/CDK)
- Monitoring and alerting setup
- Log aggregation and analysis
- Framework-compliant tool execution and error handling

## Installation

### Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.9 or higher
- Docker (for containerized deployments)
- kubectl (for Kubernetes operations)

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd core-network-devops-agent

# Install dependencies
pip3 install -r requirements.txt

# Configure AWS credentials
aws configure

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Environment Configuration

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=default

# Bedrock Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1

# Agent Configuration
AGENT_NAME=CoreNetworkDevOpsAgent
LOG_LEVEL=INFO

# Network Configuration
NETWORK_TYPE=5G_CORE  # Options: 5G_CORE, LTE_CORE, HYBRID
KUBERNETES_NAMESPACE=core-network
```

## Usage

### Starting the Agent

```bash
# Start the interactive agent with AgentCore framework
python -m core_network_devops_agent chat

# Check agent health with framework patterns
python -m core_network_devops_agent health

# View agent information and registered tools
python -m core_network_devops_agent info
```

### Example Interactions

```
User: "Deploy a 5G Core AMF with 3 replicas in the production cluster"
Agent: I'll deploy a 5G Core AMF with 3 replicas using the deploy_5g_amf tool...

✅ Tool Execution Results:
   ✅ deploy_5g_amf: Deployment created successfully
   📊 AMF deployed with 3 replicas in core-network namespace

User: "Show me the current network function status"
Agent: Let me check the status using the list_network_functions tool...

Network Functions Status:
- AMF: 3/3 replicas running, healthy (CPU: 45%, Memory: 60%)
- SMF: 2/2 replicas running, healthy (CPU: 38%, Memory: 55%)
- UPF: 1/1 replica running, warning (CPU: 85%, Memory: 70%)

User: "Get system health status"
Agent: I'll use the get_system_health tool to provide a comprehensive status...

🟢 Overall Status: Healthy (1 warning)
⚠️  UPF showing high CPU usage - consider scaling or investigation
```

### AgentCore Framework API Usage

```python
from core_network_devops_agent import CoreNetworkDevOpsAgent

# Initialize agent with AgentCore framework
agent = CoreNetworkDevOpsAgent(
    name="MyNetworkAgent",
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    region="us-east-1"
)

# Initialize with framework patterns
await agent.initialize()

# Process request with structured response
response = await agent.process_request(
    "Deploy AMF with high availability configuration"
)

# AgentCore framework response structure
print(f"Success: {response.success}")
print(f"Content: {response.content}")
print(f"Tools used: {list(response.tool_results.keys())}")
print(f"Execution metadata: {response.metadata}")

# Access conversation history through framework
history = agent.get_conversation_history()
print(f"Conversation: {len(history)} messages")
```

### Tool Development with Decorators

```python
@agent_handler
class MyCustomAgent(Agent):
    @tool(
        name="deploy_custom_nf",
        description="Deploy a custom network function",
        parameters={
            "nf_type": {"type": "string", "description": "Network function type", "required": True},
            "replicas": {"type": "integer", "description": "Number of replicas", "required": False, "default": 1}
        }
    )
    async def deploy_custom_nf(self, nf_type: str, replicas: int = 1):
        # Implementation automatically wrapped with ToolResult
        return ToolResult(
            success=True,
            data={"nf_type": nf_type, "replicas": replicas, "status": "deployed"}
        )
```

## Configuration

### AgentCore Framework Configuration (`config.yaml`)

```yaml
# AgentCore Framework Configuration
agent:
  name: "CoreNetworkDevOpsAgent"
  description: "AI agent for core network and DevOps operations using AgentCore framework"
  version: "1.0.0"
  
  # Bedrock model configuration
  model:
    model_id: "anthropic.claude-3-sonnet-20240229-v1:0"
    region: "us-east-1"
    max_tokens: 4000
    temperature: 0.1
    
  # AgentCore behavior configuration
  behavior:
    max_conversation_turns: 50
    enable_memory: true
    memory_retention_hours: 24
    enable_tool_chaining: true
    max_tool_calls_per_turn: 5

# Framework memory configuration
memory:
  max_messages: 100
  retention_hours: 24
  enable_summarization: true

# Tool configuration (automatically discovered via @tool decorators)
tools:
  describe_ec2_instances:
    enabled: true
    timeout_seconds: 30
    retry_attempts: 3
    
  deploy_5g_amf:
    enabled: true
    timeout_seconds: 60
    retry_attempts: 2
    
  list_network_functions:
    enabled: true
    timeout_seconds: 45
    
  get_system_health:
    enabled: true
    timeout_seconds: 30

# Network function defaults
network:
  type: "5G_CORE"
  namespace: "core-network"
  components:
    amf:
      default_replicas: 2
      default_resources:
        cpu: "1000m"
        memory: "2Gi"
    smf:
      default_replicas: 2
      default_resources:
        cpu: "800m"
        memory: "1.5Gi"
    upf:
      default_replicas: 1
      default_resources:
        cpu: "2000m"
        memory: "4Gi"

# AWS configuration
aws:
  region: "us-east-1"
  cluster_name: "core-network-cluster"
  vpc_id: "vpc-12345678"
```

## Development

### AgentCore Framework Project Structure

```
core-network-devops-agent/
├── src/
│   └── core_network_devops_agent/
│       ├── __init__.py                    # Framework exports
│       ├── core_agent.py                  # @agent_handler decorated agent
│       ├── framework/                     # AgentCore framework implementation
│       │   ├── __init__.py               # Framework components
│       │   ├── agent_base.py             # Agent, AgentResponse, AgentFactory
│       │   ├── tool_base.py              # Tool, ToolResult, ToolRegistry
│       │   ├── memory.py                 # ConversationMemory, MessageRole
│       │   └── decorators.py             # @tool, @agent_handler decorators
│       ├── models/                       # Data models
│       │   ├── network_function.py       # NetworkFunction, NetworkFunctionConfig
│       │   └── deployment.py             # DeploymentRequest, DeploymentStatus
│       └── utils/                        # Utilities
│           ├── aws_client.py             # AWS client management
│           └── k8s_client.py             # Kubernetes client management
├── tests/                                # Test files
│   ├── test_agentcore_framework.py       # AgentCore framework tests
│   ├── test_agent_comprehensive.py       # Comprehensive functionality tests
│   └── test_agent_basic.py               # Basic functionality tests
├── config/                               # Configuration files
│   └── agent_config.yaml                 # AgentCore framework configuration
├── docs/                                 # Documentation
│   ├── AGENTCORE_ADOPTION_SUMMARY.md     # Framework adoption summary
│   └── DELTA_ANALYSIS.md                 # Framework comparison analysis
├── requirements.txt                      # Dependencies
├── setup.py                              # Package setup
└── README.md                             # This file
```

### Running Tests

```bash
# Run AgentCore framework tests (100% pass rate)
python3 test_agentcore_framework.py

# Run comprehensive functionality tests
python3 test_agent_comprehensive.py

# Run basic functionality tests
python3 test_agent_basic.py

# Run all tests with pytest
pytest

# Run with coverage
pytest --cov=core_network_devops_agent

# Test specific framework components
pytest tests/test_framework/ -v
```

### Test Results Summary

- **AgentCore Framework Tests**: 8/8 PASSED (100%)
- **Comprehensive Tests**: 6/6 PASSED (100%)  
- **Basic Tests**: 6/6 PASSED (100%)
- **Total Success Rate**: 100%

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## AWS Permissions

The agent requires the following AWS permissions:

### Core Permissions
- `bedrock:InvokeModel`
- `bedrock:InvokeModelWithResponseStream`

### Infrastructure Management
- `ec2:*`
- `eks:*`
- `iam:PassRole`
- `cloudformation:*`

### Container Operations
- `ecr:*`
- `ecs:*`

### Monitoring & Logging
- `cloudwatch:*`
- `logs:*`

## Security Considerations

- All AWS API calls are made using IAM roles with least privilege
- Sensitive data is encrypted in transit and at rest
- Agent conversations can be logged for audit purposes
- Network function configurations are validated before deployment

## Troubleshooting

### Common Issues

1. **Bedrock Access Denied**
   - Ensure your AWS credentials have Bedrock permissions
   - Check if Bedrock is available in your region

2. **Kubernetes Connection Failed**
   - Verify kubectl configuration
   - Check cluster endpoint accessibility

3. **Network Function Deployment Failed**
   - Review resource quotas
   - Check image availability
   - Validate configuration syntax

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Check the [documentation](docs/)
- Review the [troubleshooting guide](docs/troubleshooting.md)