# Core Network DevOps Agent

An AI agent built with Amazon Bedrock's AgentCore framework for managing core network infrastructure and DevOps operations on AWS.

## Overview

This agent leverages Amazon Bedrock's foundation models and AgentCore framework to provide intelligent automation for:

- **Core Network Infrastructure**: 5G Core, LTE Core, and traditional network functions
- **AWS Infrastructure Management**: EC2, EKS, VPC, and other AWS services
- **DevOps Operations**: CI/CD pipelines, monitoring, and deployment automation
- **Network Function Lifecycle**: CNF/VNF deployment, scaling, and management

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Amazon Bedrock AgentCore                     │
├─────────────────────────────────────────────────────────────┤
│  Foundation Model  │  Agent Runtime  │  Tool Integration   │
│  • Claude 3        │  • Conversation │  • AWS APIs        │
│  • Titan          │  • Memory       │  • Kubernetes      │
│  • Custom Models  │  • Planning     │  • Network Tools   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Core Network DevOps Agent                    │
├─────────────────────────────────────────────────────────────┤
│  Network Functions │  Infrastructure │  DevOps Automation │
│  • 5G Core (AMF,   │  • AWS Services │  • CI/CD Pipelines │
│    SMF, UPF)       │  • Kubernetes   │  • Monitoring      │
│  • LTE Core (MME,  │  • Networking   │  • Deployment      │
│    SGW, PGW)       │  • Storage      │  • Observability   │
└─────────────────────────────────────────────────────────────┘
```

## Features

### 🤖 **AI-Powered Operations**
- Natural language interaction with network infrastructure
- Intelligent troubleshooting and root cause analysis
- Automated remediation suggestions
- Context-aware decision making

### 🌐 **Core Network Management**
- 5G Core Network Functions (AMF, SMF, UPF, AUSF, UDM, UDR, NRF, NSSF, PCF)
- LTE Core Network Elements (MME, SGW, PGW, HSS, PCRF)
- Network slicing and service orchestration
- Inter-network function communication

### ☁️ **AWS Infrastructure**
- EC2 instance management and optimization
- EKS cluster operations and scaling
- VPC networking and security groups
- Load balancer configuration
- Auto Scaling Groups management

### 🔧 **DevOps Automation**
- CI/CD pipeline creation and management
- Container registry operations (ECR)
- Infrastructure as Code (CloudFormation/CDK)
- Monitoring and alerting setup
- Log aggregation and analysis

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
pip install -r requirements.txt

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
# Start the interactive agent
python -m core_network_devops_agent

# Or run with specific configuration
python -m core_network_devops_agent --config config.yaml
```

### Example Interactions

```
User: "Deploy a 5G Core AMF with 3 replicas in the production cluster"
Agent: I'll deploy a 5G Core AMF with 3 replicas. Let me check the production cluster status and create the deployment configuration...

User: "Show me the current network function status"
Agent: Here's the current status of your core network functions:
- AMF: 3/3 replicas running, healthy
- SMF: 2/2 replicas running, healthy  
- UPF: 1/1 replica running, healthy
...

User: "The UPF is showing high CPU usage, what should I do?"
Agent: I see the UPF CPU usage is at 85%. Based on the current traffic patterns, I recommend:
1. Scale the UPF to 2 replicas
2. Check for any memory leaks in the application
3. Review the traffic routing configuration
Would you like me to proceed with scaling?
```

### API Usage

```python
from core_network_devops_agent import CoreNetworkAgent

# Initialize the agent
agent = CoreNetworkAgent(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    region="us-east-1"
)

# Send a request
response = agent.process_request(
    "Deploy AMF with high availability configuration"
)

print(response.content)
```

## Configuration

### Agent Configuration (`config.yaml`)

```yaml
agent:
  name: "CoreNetworkDevOpsAgent"
  description: "AI agent for core network and DevOps operations"
  model_id: "anthropic.claude-3-sonnet-20240229-v1:0"
  region: "us-east-1"
  
tools:
  - name: "aws_operations"
    enabled: true
  - name: "kubernetes_operations" 
    enabled: true
  - name: "network_functions"
    enabled: true
  - name: "monitoring"
    enabled: true

network:
  type: "5G_CORE"
  namespace: "core-network"
  components:
    amf:
      replicas: 2
      resources:
        cpu: "1000m"
        memory: "2Gi"
    smf:
      replicas: 2
      resources:
        cpu: "800m"
        memory: "1.5Gi"
    upf:
      replicas: 1
      resources:
        cpu: "2000m"
        memory: "4Gi"

aws:
  region: "us-east-1"
  cluster_name: "core-network-cluster"
  vpc_id: "vpc-12345678"
```

## Development

### Project Structure

```
core-network-devops-agent/
├── src/
│   └── core_network_devops_agent/
│       ├── __init__.py
│       ├── agent.py              # Main agent implementation
│       ├── tools/                # Agent tools
│       │   ├── aws_operations.py
│       │   ├── kubernetes_ops.py
│       │   ├── network_functions.py
│       │   └── monitoring.py
│       ├── models/               # Data models
│       │   ├── network_function.py
│       │   └── deployment.py
│       └── utils/                # Utilities
│           ├── aws_client.py
│           └── k8s_client.py
├── tests/                        # Test files
├── config/                       # Configuration files
├── docs/                         # Documentation
├── requirements.txt
├── setup.py
└── README.md
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core_network_devops_agent

# Run specific test category
pytest tests/test_network_functions.py
```

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