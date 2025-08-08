"""
AWS Client Manager for Core Network DevOps Agent

Provides centralized AWS client management following AgentCore patterns.
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, Optional, Any
import structlog

logger = structlog.get_logger(__name__)


class AWSClientManager:
    """
    Centralized AWS client manager following AgentCore framework patterns.
    
    This class provides thread-safe, cached AWS service clients with proper
    error handling and credential management.
    """
    
    def __init__(self, region: str = "us-east-1", profile: Optional[str] = None):
        """
        Initialize the AWS client manager.
        
        Args:
            region: Default AWS region
            profile: AWS profile name (optional)
        """
        self.region = region
        self.profile = profile
        self._session: Optional[boto3.Session] = None
        self._clients: Dict[str, boto3.client] = {}
        self._account_id: Optional[str] = None
        
        logger.info("AWSClientManager initialized", region=region, profile=profile)
    
    @property
    def session(self) -> boto3.Session:
        """Get or create a boto3 session."""
        if self._session is None:
            try:
                if self.profile:
                    self._session = boto3.Session(profile_name=self.profile)
                else:
                    self._session = boto3.Session()
                
                # Test credentials by getting caller identity
                sts = self._session.client('sts')
                identity = sts.get_caller_identity()
                self._account_id = identity['Account']
                
                logger.info("AWS session created successfully", 
                           account_id=self._account_id,
                           region=self._session.region_name)
                
            except NoCredentialsError:
                logger.error("AWS credentials not found")
                raise Exception(
                    "AWS credentials not configured. Please configure AWS credentials "
                    "using 'aws configure', environment variables, or IAM roles."
                )
            except Exception as e:
                logger.error("Failed to create AWS session", error=str(e))
                raise Exception(f"Failed to initialize AWS session: {str(e)}")
        
        return self._session
    
    def get_client(self, service_name: str, region: Optional[str] = None) -> boto3.client:
        """
        Get an AWS service client with caching.
        
        Args:
            service_name: AWS service name (e.g., 'ec2', 'eks', 's3')
            region: AWS region (uses default if not specified)
            
        Returns:
            Boto3 client for the specified service
        """
        effective_region = region or self.region
        cache_key = f"{service_name}:{effective_region}"
        
        if cache_key not in self._clients:
            try:
                self._clients[cache_key] = self.session.client(
                    service_name, 
                    region_name=effective_region
                )
                logger.debug("Created AWS client", 
                           service=service_name, 
                           region=effective_region)
            except Exception as e:
                logger.error("Failed to create AWS client", 
                           service=service_name, 
                           region=effective_region, 
                           error=str(e))
                raise
        
        return self._clients[cache_key]
    
    def get_account_id(self) -> str:
        """Get the current AWS account ID."""
        if self._account_id is None:
            try:
                sts = self.get_client('sts')
                identity = sts.get_caller_identity()
                self._account_id = identity['Account']
            except Exception as e:
                logger.error("Failed to get account ID", error=str(e))
                raise
        
        return self._account_id
    
    def get_current_region(self) -> str:
        """Get the current AWS region."""
        return self.session.region_name or self.region
    
    def list_regions(self, service: str = 'ec2') -> list:
        """
        List available AWS regions for a service.
        
        Args:
            service: AWS service name
            
        Returns:
            List of region names
        """
        try:
            if service == 'ec2':
                ec2 = self.get_client('ec2')
                response = ec2.describe_regions()
                return [region['RegionName'] for region in response['Regions']]
            else:
                # For other services, return common regions
                return [
                    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
                    'eu-west-1', 'eu-west-2', 'eu-central-1',
                    'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1'
                ]
        except Exception as e:
            logger.error("Failed to list regions", service=service, error=str(e))
            return []
    
    def validate_credentials(self) -> Dict[str, Any]:
        """
        Validate AWS credentials and return account information.
        
        Returns:
            Dictionary with account information and validation status
        """
        try:
            sts = self.get_client('sts')
            identity = sts.get_caller_identity()
            
            return {
                'valid': True,
                'account_id': identity['Account'],
                'user_id': identity['UserId'],
                'arn': identity['Arn'],
                'region': self.get_current_region()
            }
        except Exception as e:
            logger.error("Credential validation failed", error=str(e))
            return {
                'valid': False,
                'error': str(e)
            }
    
    def get_service_endpoints(self, service_name: str, region: Optional[str] = None) -> Dict[str, str]:
        """
        Get service endpoints for a region.
        
        Args:
            service_name: AWS service name
            region: AWS region
            
        Returns:
            Dictionary with endpoint information
        """
        effective_region = region or self.region
        
        try:
            session = self.session
            endpoints = session.get_available_regions(service_name)
            
            if effective_region in endpoints:
                client = self.get_client(service_name, effective_region)
                endpoint_url = client._endpoint.host
                
                return {
                    'service': service_name,
                    'region': effective_region,
                    'endpoint_url': endpoint_url,
                    'available_regions': endpoints
                }
            else:
                return {
                    'service': service_name,
                    'region': effective_region,
                    'error': f'Service {service_name} not available in region {effective_region}',
                    'available_regions': endpoints
                }
        except Exception as e:
            logger.error("Failed to get service endpoints", 
                        service=service_name, 
                        region=effective_region, 
                        error=str(e))
            return {
                'service': service_name,
                'region': effective_region,
                'error': str(e)
            }
    
    def clear_client_cache(self) -> None:
        """Clear the client cache."""
        self._clients.clear()
        logger.info("AWS client cache cleared")
    
    def get_client_info(self) -> Dict[str, Any]:
        """
        Get information about cached clients.
        
        Returns:
            Dictionary with client cache information
        """
        return {
            'cached_clients': list(self._clients.keys()),
            'account_id': self._account_id,
            'region': self.region,
            'profile': self.profile,
            'session_region': self.session.region_name if self._session else None
        }