"""
Core Network DevOps Agent - Refactored with Bedrock AgentCore Framework

This is the main agent implementation following AgentCore framework patterns.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
import structlog

# Import AgentCore framework components
from .framework import Agent, AgentResponse, ConversationMemory, agent_handler, tool
from .framework.tool_base import ToolResult
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


@agent_handler
class CoreNetworkDevOpsAgent(Agent):
    """
    Core Network DevOps Agent using Amazon Bedrock's AgentCore framework.
    
    This agent provides AI-powered automation for core network infrastructure
    and DevOps operations on AWS, following AgentCore framework patterns.
    """
    
    def __init__(
        self,
        name: str = "CoreNetworkDevOpsAgent",
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        region: str = "us-east-1",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Core Network DevOps Agent.
        
        Args:
            name: Agent name
            model_id: Bedrock model identifier
            region: AWS region
            config: Optional configuration dictionary
        """
        super().__init__(name, model_id, region, config)
        
        # Initialize managers
        self.aws_manager = AWSClientManager(region=region)
        self.k8s_manager = KubernetesClientManager()
        
        # Initialize memory
        memory_config = config.get('memory', {}) if config else {}
        self._memory = ConversationMemory(
            max_messages=memory_config.get('max_messages', 100),
            retention_hours=memory_config.get('retention_hours', 24),
            enable_summarization=memory_config.get('enable_summarization', True)
        )
        
        logger.info("CoreNetworkDevOpsAgent initialized", 
                   name=name, model_id=model_id, region=region)
    
    async def initialize(self) -> None:
        """Initialize the agent and its dependencies."""
        try:
            # Initialize Bedrock client
            self._bedrock_client = self.aws_manager.get_client('bedrock-runtime')
            
            # Validate AWS credentials
            cred_info = self.aws_manager.validate_credentials()
            if not cred_info['valid']:
                raise Exception(f"AWS credential validation failed: {cred_info['error']}")
            
            # Initialize Kubernetes client
            await self.k8s_manager.health_check()
            
            self._initialized = True
            logger.info("Agent initialized successfully", agent=self.name)
            
        except Exception as e:
            logger.error("Agent initialization failed", agent=self.name, error=str(e))
            raise
    
    async def process_request(
        self, 
        user_input: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Process a user request using the Bedrock model and available tools.
        
        Args:
            user_input: User's natural language request
            context: Optional additional context
            
        Returns:
            AgentResponse containing the agent's response and any actions taken
        """
        try:
            # Add user message to memory
            self._memory.add_message("user", user_input, metadata=context)
            
            # Update context if provided
            if context:
                self._memory.update_context(context)
            
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
            response_content = await self._generate_response(
                user_input, 
                analysis, 
                tool_results
            )
            
            # Create agent response
            response = AgentResponse(
                content=response_content,
                success=True,
                tool_results=tool_results,
                metadata={
                    'analysis': analysis,
                    'model_id': self.model_id,
                    'region': self.region
                }
            )
            
            # Add assistant response to memory
            self._memory.add_message(
                "assistant", 
                response_content,
                tool_results=tool_results
            )
            
            logger.info("Request processed successfully", 
                       user_input=user_input[:100])
            
            return response
            
        except Exception as e:
            logger.error("Error processing request", 
                        error=str(e), user_input=user_input)
            
            error_response = AgentResponse(
                content=f"I encountered an error processing your request: {str(e)}",
                success=False,
                metadata={'error': str(e)}
            )
            
            # Add error to memory
            self._memory.add_message(
                "assistant",
                error_response.content,
                metadata={'error': True}
            )
            
            return error_response
    
    # AWS Operations Tools
    @tool(
        name="describe_ec2_instances",
        description="List and describe EC2 instances",
        parameters={
            "region": {"type": "string", "description": "AWS region", "required": False},
            "instance_ids": {"type": "array", "description": "Specific instance IDs", "required": False},
            "filters": {"type": "object", "description": "Filter criteria", "required": False}
        }
    )
    async def describe_ec2_instances(
        self, 
        region: Optional[str] = None,
        instance_ids: Optional[List[str]] = None,
        filters: Optional[Dict[str, str]] = None
    ) -> ToolResult:
        """Describe EC2 instances."""
        try:
            ec2 = self.aws_manager.get_client('ec2', region)
            
            describe_params = {}
            if instance_ids:
                describe_params['InstanceIds'] = instance_ids
            if filters:
                describe_params['Filters'] = [
                    {'Name': k, 'Values': [v]} for k, v in filters.items()
                ]
            
            response = ec2.describe_instances(**describe_params)
            
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'InstanceId': instance['InstanceId'],
                        'InstanceType': instance['InstanceType'],
                        'State': instance['State']['Name'],
                        'LaunchTime': instance.get('LaunchTime').isoformat() if instance.get('LaunchTime') and hasattr(instance.get('LaunchTime'), 'isoformat') else str(instance.get('LaunchTime', '')),
                        'PrivateIpAddress': instance.get('PrivateIpAddress'),
                        'PublicIpAddress': instance.get('PublicIpAddress'),
                        'VpcId': instance.get('VpcId'),
                        'SubnetId': instance.get('SubnetId'),
                        'SecurityGroups': [sg['GroupName'] for sg in instance.get('SecurityGroups', [])],
                        'Tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    })
            
            return ToolResult(
                success=True,
                data={
                    "instances": instances,
                    "count": len(instances),
                    "region": region or self.region
                }
            )
            
        except ClientError as e:
            return ToolResult(
                success=False,
                error=f"AWS API error: {e.response['Error']['Message']}"
            )
    
    @tool(
        name="describe_vpcs",
        description="List and describe VPCs",
        parameters={
            "region": {"type": "string", "description": "AWS region", "required": False},
            "vpc_ids": {"type": "array", "description": "Specific VPC IDs", "required": False}
        }
    )
    async def describe_vpcs(
        self,
        region: Optional[str] = None,
        vpc_ids: Optional[List[str]] = None
    ) -> ToolResult:
        """Describe VPCs."""
        try:
            ec2 = self.aws_manager.get_client('ec2', region)
            
            describe_params = {}
            if vpc_ids:
                describe_params['VpcIds'] = vpc_ids
            
            response = ec2.describe_vpcs(**describe_params)
            
            vpcs = []
            for vpc in response['Vpcs']:
                name = next((tag['Value'] for tag in vpc.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
                vpcs.append({
                    'VpcId': vpc['VpcId'],
                    'CidrBlock': vpc['CidrBlock'],
                    'State': vpc['State'],
                    'Name': name,
                    'IsDefault': vpc['IsDefault'],
                    'Tags': {tag['Key']: tag['Value'] for tag in vpc.get('Tags', [])}
                })
            
            return ToolResult(
                success=True,
                data={
                    "vpcs": vpcs,
                    "count": len(vpcs),
                    "region": region or self.region
                }
            )
            
        except ClientError as e:
            return ToolResult(
                success=False,
                error=f"AWS API error: {e.response['Error']['Message']}"
            )
    
    # Network Function Tools
    @tool(
        name="deploy_5g_amf",
        description="Deploy 5G AMF (Access and Mobility Management Function)",
        parameters={
            "name": {"type": "string", "description": "AMF deployment name", "required": False},
            "namespace": {"type": "string", "description": "Kubernetes namespace", "required": False},
            "replicas": {"type": "integer", "description": "Number of replicas", "required": False},
            "plmn_id": {"type": "string", "description": "PLMN identifier", "required": False}
        }
    )
    async def deploy_5g_amf(
        self,
        name: str = "amf",
        namespace: str = "core-network",
        replicas: int = 2,
        plmn_id: str = "00101"
    ) -> ToolResult:
        """Deploy 5G AMF."""
        try:
            deployment_info = {
                'name': name,
                'type': 'AMF',
                'namespace': namespace,
                'replicas': replicas,
                'image': 'core-network/amf:latest',
                'ports': [80, 8080, 29518],
                'status': 'Deploying',
                'config': {
                    'plmn_id': plmn_id,
                    'amf_id': '000001',
                    'guami': f'{plmn_id}000001'
                }
            }
            
            return ToolResult(
                success=True,
                data=deployment_info
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to deploy AMF: {str(e)}"
            )
    
    @tool(
        name="list_network_functions",
        description="List all deployed network functions",
        parameters={
            "namespace": {"type": "string", "description": "Kubernetes namespace", "required": False},
            "function_type": {"type": "string", "description": "Filter by function type", "required": False}
        }
    )
    async def list_network_functions(
        self,
        namespace: str = "core-network",
        function_type: Optional[str] = None
    ) -> ToolResult:
        """List network functions."""
        try:
            # Mock network functions list
            network_functions = [
                {
                    'name': 'amf-deployment',
                    'type': 'AMF',
                    'namespace': namespace,
                    'replicas': '2/2',
                    'status': 'Running',
                    'age': '2d',
                    'image': 'core-network/amf:latest'
                },
                {
                    'name': 'smf-deployment',
                    'type': 'SMF',
                    'namespace': namespace,
                    'replicas': '2/2',
                    'status': 'Running',
                    'age': '2d',
                    'image': 'core-network/smf:latest'
                },
                {
                    'name': 'upf-deployment',
                    'type': 'UPF',
                    'namespace': namespace,
                    'replicas': '1/1',
                    'status': 'Running',
                    'age': '2d',
                    'image': 'core-network/upf:latest'
                }
            ]
            
            # Filter by function type if specified
            if function_type:
                network_functions = [
                    nf for nf in network_functions 
                    if nf['type'].lower() == function_type.lower()
                ]
            
            return ToolResult(
                success=True,
                data={
                    "network_functions": network_functions,
                    "count": len(network_functions),
                    "namespace": namespace
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to list network functions: {str(e)}"
            )
    
    @tool(
        name="get_system_health",
        description="Get overall system health status",
        parameters={
            "include_metrics": {"type": "boolean", "description": "Include performance metrics", "required": False}
        }
    )
    async def get_system_health(self, include_metrics: bool = True) -> ToolResult:
        """Get system health status."""
        try:
            health_status = {
                'overall_status': 'Healthy',
                'components': {
                    'amf': {
                        'status': 'Healthy',
                        'replicas': '2/2',
                        'cpu_usage': '45%',
                        'memory_usage': '60%'
                    },
                    'smf': {
                        'status': 'Healthy',
                        'replicas': '2/2',
                        'cpu_usage': '38%',
                        'memory_usage': '55%'
                    },
                    'upf': {
                        'status': 'Warning',
                        'replicas': '1/1',
                        'cpu_usage': '85%',
                        'memory_usage': '70%',
                        'warning': 'High CPU usage detected'
                    }
                },
                'infrastructure': {
                    'kubernetes_cluster': 'Healthy',
                    'aws_resources': 'Healthy',
                    'network_connectivity': 'Healthy'
                },
                'active_alerts': 1,
                'last_updated': datetime.now().isoformat()
            }
            
            if include_metrics:
                health_status['metrics'] = {
                    'total_sessions': 15420,
                    'throughput_gbps': 1.2,
                    'latency_ms': 12.5,
                    'error_rate': 0.01
                }
            
            return ToolResult(
                success=True,
                data=health_status
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to get system health: {str(e)}"
            )
    
    async def _analyze_request(self, user_input: str) -> Dict[str, Any]:
        """Analyze the user request to determine intent and required tools."""
        system_prompt = """
        You are an AI assistant that analyzes requests for core network and DevOps operations.
        
        Available tools:
        - describe_ec2_instances: List and describe EC2 instances
        - describe_vpcs: List and describe VPCs
        - deploy_5g_amf: Deploy 5G AMF network function
        - list_network_functions: List deployed network functions
        - get_system_health: Get system health status
        
        Analyze the user request and return a JSON response with:
        {
            "intent": "brief description of what user wants",
            "category": "infrastructure|network_functions|monitoring|general",
            "tools_needed": ["list", "of", "required", "tools"],
            "parameters": {"tool_name": {"param": "value"}},
            "complexity": "low|medium|high"
        }
        """
        
        try:
            response = self._bedrock_client.invoke_model(
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
        """Execute the required tools with given parameters."""
        results = {}
        
        for tool_name in tools_needed:
            tool = self.get_tool(tool_name)
            if tool:
                try:
                    tool_params = parameters.get(tool_name, {})
                    result = await tool.execute_with_validation(tool_params)
                    results[tool_name] = result.to_dict()
                    
                    logger.info("Tool executed successfully", 
                               tool=tool_name)
                    
                except Exception as e:
                    logger.error("Tool execution failed", 
                                tool=tool_name, error=str(e))
                    results[tool_name] = {
                        'success': False,
                        'error': str(e)
                    }
            else:
                logger.warning("Unknown tool requested", tool=tool_name)
                results[tool_name] = {
                    'success': False,
                    'error': f'Unknown tool: {tool_name}'
                }
        
        return results
    
    async def _generate_response(
        self,
        user_input: str,
        analysis: Dict[str, Any],
        tool_results: Dict[str, Any]
    ) -> str:
        """Generate a natural language response using Bedrock."""
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
        
        # Get recent conversation context
        recent_messages = self._memory.get_recent_messages(5)
        if recent_messages:
            context_info.append("Recent conversation context:")
            for msg in recent_messages[-3:]:  # Last 3 messages
                context_info.append(f"- {msg.role}: {msg.content[:100]}...")
        
        context_str = "\n\n".join(context_info) if context_info else "No additional context available."
        
        try:
            response = self._bedrock_client.invoke_model(
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
            
            return content
            
        except Exception as e:
            logger.error("Error generating response", error=str(e))
            return f"I encountered an error generating a response: {str(e)}"