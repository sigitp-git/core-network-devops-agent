"""
Core Network DevOps Agent

Main agent implementation using Amazon Bedrock's AgentCore framework.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
import structlog

from .models.network_function import NetworkFunction, NetworkFunctionConfig
from .models.deployment import DeploymentRequest, DeploymentStatus
from .tools.aws_operations import AWSOperationsTool
from .tools.kubernetes_ops import KubernetesTool
from .tools.network_functions import NetworkFunctionsTool
from .tools.monitoring import MonitoringTool
from .utils.aws_client import AWSClientManager
from .utils.k8s_client import KubernetesClientManager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class CoreNetworkAgent:
    """
    Core Network DevOps Agent using Amazon Bedrock's AgentCore framework.
    
    This agent provides AI-powered automation for core network infrastructure
    and DevOps operations on AWS.
    """
    
    def __init__(
        self,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        region: str = "us-east-1",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Core Network DevOps Agent.
        
        Args:
            model_id: Bedrock model identifier
            region: AWS region
            config: Optional configuration dictionary
        """
        self.model_id = model_id
        self.region = region
        self.config = config or {}
        
        # Initialize AWS clients
        self.aws_manager = AWSClientManager(region=region)
        self.k8s_manager = KubernetesClientManager()
        
        # Initialize Bedrock client
        self.bedrock_client = self.aws_manager.get_client('bedrock-runtime')
        
        # Initialize tools
        self.tools = {
            'aws_operations': AWSOperationsTool(self.aws_manager),
            'kubernetes_ops': KubernetesTool(self.k8s_manager),
            'network_functions': NetworkFunctionsTool(self.k8s_manager),
            'monitoring': MonitoringTool(self.aws_manager, self.k8s_manager)
        }
        
        # Agent state
        self.conversation_history: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        
        logger.info("CoreNetworkAgent initialized", 
                   model_id=model_id, region=region)
    
    async def process_request(
        self, 
        user_input: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user request using the Bedrock model and available tools.
        
        Args:
            user_input: User's natural language request
            context: Optional additional context
            
        Returns:
            Dictionary containing the agent's response and any actions taken
        """
        try:
            # Update context
            if context:
                self.context.update(context)
            
            # Add to conversation history
            self.conversation_history.append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now().isoformat()
            })
            
            # Analyze the request and determine required tools
            analysis = await self._analyze_request(user_input)
            
            # Execute tools if needed
            tool_results = {}
            if analysis.get('tools_needed'):
                tool_results = await self._execute_tools(
                    analysis['tools_needed'], 
                    analysis.get('parameters', {})
                )
            
            # Generate response using Bedrock
            response = await self._generate_response(
                user_input, 
                analysis, 
                tool_results
            )
            
            # Add response to conversation history
            self.conversation_history.append({
                'role': 'assistant',
                'content': response['content'],
                'timestamp': datetime.now().isoformat(),
                'tool_results': tool_results
            })
            
            logger.info("Request processed successfully", 
                       user_input=user_input[:100])
            
            return response
            
        except Exception as e:
            logger.error("Error processing request", 
                        error=str(e), user_input=user_input)
            return {
                'content': f"I encountered an error processing your request: {str(e)}",
                'error': True,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _analyze_request(self, user_input: str) -> Dict[str, Any]:
        """
        Analyze the user request to determine intent and required tools.
        
        Args:
            user_input: User's request
            
        Returns:
            Analysis results including intent and required tools
        """
        # System prompt for request analysis
        system_prompt = """
        You are an AI assistant that analyzes requests for core network and DevOps operations.
        
        Available tools:
        - aws_operations: EC2, EKS, VPC, CloudFormation operations
        - kubernetes_ops: Kubernetes cluster and resource management
        - network_functions: 5G/LTE core network function management
        - monitoring: Monitoring, alerting, and observability
        
        Analyze the user request and return a JSON response with:
        {
            "intent": "brief description of what user wants",
            "category": "infrastructure|network_functions|devops|monitoring|general",
            "tools_needed": ["list", "of", "required", "tools"],
            "parameters": {"key": "value pairs for tool execution"},
            "complexity": "low|medium|high"
        }
        """
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "system": system_prompt,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Analyze this request: {user_input}"
                        }
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            analysis_text = response_body['content'][0]['text']
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                # Fallback analysis
                analysis = {
                    "intent": "General request",
                    "category": "general",
                    "tools_needed": [],
                    "parameters": {},
                    "complexity": "medium"
                }
            
            return analysis
            
        except Exception as e:
            logger.error("Error analyzing request", error=str(e))
            return {
                "intent": "Unknown request",
                "category": "general", 
                "tools_needed": [],
                "parameters": {},
                "complexity": "medium"
            }
    
    async def _execute_tools(
        self, 
        tools_needed: List[str], 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the required tools with given parameters.
        
        Args:
            tools_needed: List of tool names to execute
            parameters: Parameters for tool execution
            
        Returns:
            Dictionary of tool execution results
        """
        results = {}
        
        for tool_name in tools_needed:
            if tool_name in self.tools:
                try:
                    tool = self.tools[tool_name]
                    result = await tool.execute(parameters.get(tool_name, {}))
                    results[tool_name] = result
                    
                    logger.info("Tool executed successfully", 
                               tool=tool_name, result_keys=list(result.keys()))
                    
                except Exception as e:
                    logger.error("Tool execution failed", 
                                tool=tool_name, error=str(e))
                    results[tool_name] = {
                        'error': str(e),
                        'success': False
                    }
            else:
                logger.warning("Unknown tool requested", tool=tool_name)
                results[tool_name] = {
                    'error': f'Unknown tool: {tool_name}',
                    'success': False
                }
        
        return results
    
    async def _generate_response(
        self,
        user_input: str,
        analysis: Dict[str, Any],
        tool_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a natural language response using Bedrock.
        
        Args:
            user_input: Original user request
            analysis: Request analysis results
            tool_results: Results from tool execution
            
        Returns:
            Generated response dictionary
        """
        # System prompt for response generation
        system_prompt = """
        You are a Core Network DevOps AI Agent specializing in:
        - 5G and LTE core network functions (AMF, SMF, UPF, MME, SGW, PGW, etc.)
        - AWS infrastructure management (EC2, EKS, VPC, etc.)
        - Kubernetes operations and container orchestration
        - DevOps automation and CI/CD pipelines
        - Network monitoring and observability
        
        Provide helpful, accurate, and actionable responses. When tool results are available,
        incorporate them into your response. Be specific about what actions were taken or
        what information was found.
        
        If errors occurred, explain them clearly and suggest next steps.
        """
        
        # Prepare context for the model
        context_info = []
        if tool_results:
            context_info.append(f"Tool execution results: {json.dumps(tool_results, indent=2)}")
        
        if self.context:
            context_info.append(f"Current context: {json.dumps(self.context, indent=2)}")
        
        context_str = "\n\n".join(context_info) if context_info else "No additional context available."
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "system": system_prompt,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"""
                            User request: {user_input}
                            
                            Request analysis: {json.dumps(analysis, indent=2)}
                            
                            Context and tool results:
                            {context_str}
                            
                            Please provide a comprehensive response to the user's request.
                            """
                        }
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            return {
                'content': content,
                'analysis': analysis,
                'tool_results': tool_results,
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
            
        except Exception as e:
            logger.error("Error generating response", error=str(e))
            return {
                'content': f"I encountered an error generating a response: {str(e)}",
                'error': True,
                'timestamp': datetime.now().isoformat(),
                'success': False
            }
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history."""
        return self.conversation_history.copy()
    
    def clear_conversation_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history.clear()
        logger.info("Conversation history cleared")
    
    def update_context(self, context: Dict[str, Any]) -> None:
        """Update the agent context."""
        self.context.update(context)
        logger.info("Context updated", new_keys=list(context.keys()))
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return list(self.tools.keys())
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the agent and its dependencies."""
        health_status = {
            'agent': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }
        
        # Check Bedrock connectivity
        try:
            self.bedrock_client.list_foundation_models()
            health_status['components']['bedrock'] = 'healthy'
        except Exception as e:
            health_status['components']['bedrock'] = f'unhealthy: {str(e)}'
            health_status['agent'] = 'degraded'
        
        # Check AWS connectivity
        try:
            self.aws_manager.get_client('sts').get_caller_identity()
            health_status['components']['aws'] = 'healthy'
        except Exception as e:
            health_status['components']['aws'] = f'unhealthy: {str(e)}'
            health_status['agent'] = 'degraded'
        
        # Check Kubernetes connectivity
        try:
            await self.k8s_manager.health_check()
            health_status['components']['kubernetes'] = 'healthy'
        except Exception as e:
            health_status['components']['kubernetes'] = f'unhealthy: {str(e)}'
            health_status['agent'] = 'degraded'
        
        return health_status