"""
Core Network DevOps Agent

AI agent for managing core network infrastructure and DevOps operations on AWS.
Built with Amazon Bedrock's AgentCore framework patterns.
"""

from .core_agent import CoreNetworkDevOpsAgent
from .framework import Agent, AgentResponse, Tool, ToolResult, ConversationMemory
from .models.network_function import NetworkFunction, NetworkFunctionConfig, NetworkFunctionType
from .models.deployment import DeploymentRequest, DeploymentStatusModel
from .utils.aws_client import AWSClientManager
from .utils.k8s_client import KubernetesClientManager

__version__ = "1.0.0"
__author__ = "Core Network DevOps Team"
__description__ = "AI agent for core network and DevOps operations using Amazon Bedrock AgentCore"

__all__ = [
    'CoreNetworkDevOpsAgent',
    'Agent',
    'AgentResponse', 
    'Tool',
    'ToolResult',
    'ConversationMemory',
    'NetworkFunction',
    'NetworkFunctionConfig',
    'NetworkFunctionType',
    'DeploymentRequest',
    'DeploymentStatusModel',
    'AWSClientManager',
    'KubernetesClientManager'
]