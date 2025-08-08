"""
AWS Operations Tool for Core Network DevOps Agent

This tool provides AWS infrastructure operations following the AgentCore framework pattern.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
import boto3
from botocore.exceptions import ClientError
import structlog

logger = structlog.get_logger(__name__)


class AWSOperationsTool:
    """
    AWS Operations tool for managing AWS infrastructure.
    
    This tool follows the Amazon Bedrock AgentCore framework patterns
    for tool implementation and provides comprehensive AWS operations.
    """
    
    def __init__(self, aws_manager):
        """Initialize the AWS Operations tool."""
        self.aws_manager = aws_manager
        self.tool_name = "aws_operations"
        self.description = "Comprehensive AWS infrastructure operations"
        
        # Tool metadata following AgentCore patterns
        self.tool_spec = {
            "toolSpec": {
                "name": self.tool_name,
                "description": self.description,
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "description": "AWS operation to perform",
                                "enum": [
                                    "describe_instances",
                                    "create_instance", 
                                    "terminate_instance",
                                    "describe_vpcs",
                                    "create_vpc",
                                    "describe_subnets",
                                    "create_subnet",
                                    "describe_security_groups",
                                    "create_security_group",
                                    "describe_eks_clusters",
                                    "create_eks_cluster",
                                    "describe_load_balancers",
                                    "create_load_balancer"
                                ]
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Parameters for the AWS operation"
                            }
                        },
                        "required": ["action"]
                    }
                }
            }
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute AWS operations based on the action and parameters.
        
        Args:
            parameters: Dictionary containing action and operation parameters
            
        Returns:
            Dictionary containing operation results
        """
        action = parameters.get("action")
        action_params = parameters.get("parameters", {})
        
        logger.info("Executing AWS operation", action=action, params=action_params)
        
        try:
            # Route to appropriate handler
            if action == "describe_instances":
                return await self._describe_instances(action_params)
            elif action == "create_instance":
                return await self._create_instance(action_params)
            elif action == "terminate_instance":
                return await self._terminate_instance(action_params)
            elif action == "describe_vpcs":
                return await self._describe_vpcs(action_params)
            elif action == "create_vpc":
                return await self._create_vpc(action_params)
            elif action == "describe_subnets":
                return await self._describe_subnets(action_params)
            elif action == "create_subnet":
                return await self._create_subnet(action_params)
            elif action == "describe_security_groups":
                return await self._describe_security_groups(action_params)
            elif action == "create_security_group":
                return await self._create_security_group(action_params)
            elif action == "describe_eks_clusters":
                return await self._describe_eks_clusters(action_params)
            elif action == "create_eks_cluster":
                return await self._create_eks_cluster(action_params)
            elif action == "describe_load_balancers":
                return await self._describe_load_balancers(action_params)
            elif action == "create_load_balancer":
                return await self._create_load_balancer(action_params)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": list(self.tool_spec["toolSpec"]["inputSchema"]["json"]["properties"]["action"]["enum"])
                }
                
        except Exception as e:
            logger.error("AWS operation failed", action=action, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "action": action
            }
    
    async def _describe_instances(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Describe EC2 instances."""
        try:
            ec2 = self.aws_manager.get_client('ec2', params.get('region'))
            
            describe_params = {}
            if params.get('instance_ids'):
                describe_params['InstanceIds'] = params['instance_ids']
            if params.get('filters'):
                describe_params['Filters'] = [
                    {'Name': k, 'Values': [v]} for k, v in params['filters'].items()
                ]
            
            response = ec2.describe_instances(**describe_params)
            
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'InstanceId': instance['InstanceId'],
                        'InstanceType': instance['InstanceType'],
                        'State': instance['State']['Name'],
                        'LaunchTime': instance.get('LaunchTime', '').isoformat() if instance.get('LaunchTime') else None,
                        'PrivateIpAddress': instance.get('PrivateIpAddress'),
                        'PublicIpAddress': instance.get('PublicIpAddress'),
                        'VpcId': instance.get('VpcId'),
                        'SubnetId': instance.get('SubnetId'),
                        'SecurityGroups': [sg['GroupName'] for sg in instance.get('SecurityGroups', [])],
                        'Tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    })
            
            return {
                "success": True,
                "action": "describe_instances",
                "data": {
                    "instances": instances,
                    "count": len(instances)
                }
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": f"AWS API error: {e.response['Error']['Message']}",
                "error_code": e.response['Error']['Code']
            }
    
    async def _create_instance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an EC2 instance."""
        try:
            ec2 = self.aws_manager.get_client('ec2', params.get('region'))
            
            # Required parameters
            image_id = params.get('image_id')
            instance_type = params.get('instance_type', 't3.micro')
            
            if not image_id:
                return {
                    "success": False,
                    "error": "image_id is required for creating an instance"
                }
            
            run_params = {
                'ImageId': image_id,
                'InstanceType': instance_type,
                'MinCount': 1,
                'MaxCount': 1
            }
            
            # Optional parameters
            if params.get('key_name'):
                run_params['KeyName'] = params['key_name']
            if params.get('security_group_ids'):
                run_params['SecurityGroupIds'] = params['security_group_ids']
            if params.get('subnet_id'):
                run_params['SubnetId'] = params['subnet_id']
            if params.get('user_data'):
                run_params['UserData'] = params['user_data']
            
            response = ec2.run_instances(**run_params)
            instance = response['Instances'][0]
            
            # Add tags if provided
            if params.get('tags'):
                ec2.create_tags(
                    Resources=[instance['InstanceId']],
                    Tags=[{'Key': k, 'Value': v} for k, v in params['tags'].items()]
                )
            
            return {
                "success": True,
                "action": "create_instance",
                "data": {
                    "instance_id": instance['InstanceId'],
                    "instance_type": instance['InstanceType'],
                    "state": instance['State']['Name'],
                    "private_ip": instance.get('PrivateIpAddress'),
                    "vpc_id": instance.get('VpcId'),
                    "subnet_id": instance.get('SubnetId')
                }
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": f"AWS API error: {e.response['Error']['Message']}",
                "error_code": e.response['Error']['Code']
            }
    
    async def _describe_vpcs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Describe VPCs."""
        try:
            ec2 = self.aws_manager.get_client('ec2', params.get('region'))
            
            describe_params = {}
            if params.get('vpc_ids'):
                describe_params['VpcIds'] = params['vpc_ids']
            if params.get('filters'):
                describe_params['Filters'] = [
                    {'Name': k, 'Values': [v]} for k, v in params['filters'].items()
                ]
            
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
                    'DhcpOptionsId': vpc['DhcpOptionsId'],
                    'Tags': {tag['Key']: tag['Value'] for tag in vpc.get('Tags', [])}
                })
            
            return {
                "success": True,
                "action": "describe_vpcs",
                "data": {
                    "vpcs": vpcs,
                    "count": len(vpcs)
                }
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": f"AWS API error: {e.response['Error']['Message']}",
                "error_code": e.response['Error']['Code']
            }
    
    async def _create_vpc(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a VPC."""
        try:
            ec2 = self.aws_manager.get_client('ec2', params.get('region'))
            
            cidr_block = params.get('cidr_block', '10.0.0.0/16')
            
            response = ec2.create_vpc(CidrBlock=cidr_block)
            vpc = response['Vpc']
            vpc_id = vpc['VpcId']
            
            # Add name tag if provided
            if params.get('name'):
                ec2.create_tags(
                    Resources=[vpc_id],
                    Tags=[{'Key': 'Name', 'Value': params['name']}]
                )
            
            # Enable DNS hostnames and resolution
            ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
            ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})
            
            return {
                "success": True,
                "action": "create_vpc",
                "data": {
                    "vpc_id": vpc_id,
                    "cidr_block": vpc['CidrBlock'],
                    "state": vpc['State'],
                    "name": params.get('name', 'N/A')
                }
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": f"AWS API error: {e.response['Error']['Message']}",
                "error_code": e.response['Error']['Code']
            }
    
    async def _describe_eks_clusters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Describe EKS clusters."""
        try:
            eks = self.aws_manager.get_client('eks', params.get('region'))
            
            # List clusters first
            list_response = eks.list_clusters()
            cluster_names = list_response['clusters']
            
            if params.get('cluster_names'):
                cluster_names = [name for name in cluster_names if name in params['cluster_names']]
            
            clusters = []
            for cluster_name in cluster_names:
                try:
                    describe_response = eks.describe_cluster(name=cluster_name)
                    cluster = describe_response['cluster']
                    
                    clusters.append({
                        'name': cluster['name'],
                        'status': cluster['status'],
                        'version': cluster['version'],
                        'endpoint': cluster.get('endpoint'),
                        'roleArn': cluster['roleArn'],
                        'createdAt': cluster.get('createdAt', '').isoformat() if cluster.get('createdAt') else None,
                        'platformVersion': cluster.get('platformVersion'),
                        'tags': cluster.get('tags', {})
                    })
                except ClientError as e:
                    logger.warning("Failed to describe cluster", cluster=cluster_name, error=str(e))
            
            return {
                "success": True,
                "action": "describe_eks_clusters",
                "data": {
                    "clusters": clusters,
                    "count": len(clusters)
                }
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": f"AWS API error: {e.response['Error']['Message']}",
                "error_code": e.response['Error']['Code']
            }
    
    def get_tool_spec(self) -> Dict[str, Any]:
        """Get the tool specification for AgentCore framework."""
        return self.tool_spec