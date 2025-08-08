"""
Kubernetes Client Manager for Core Network DevOps Agent

Provides centralized Kubernetes client management following AgentCore patterns.
"""

import asyncio
from typing import Dict, List, Optional, Any
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import structlog

logger = structlog.get_logger(__name__)


class KubernetesClientManager:
    """
    Centralized Kubernetes client manager following AgentCore framework patterns.
    
    This class provides thread-safe Kubernetes API clients with proper
    error handling and configuration management.
    """
    
    def __init__(self, config_path: Optional[str] = None, context: Optional[str] = None):
        """
        Initialize the Kubernetes client manager.
        
        Args:
            config_path: Path to kubeconfig file (optional)
            context: Kubernetes context to use (optional)
        """
        self.config_path = config_path
        self.context = context
        self._api_client: Optional[client.ApiClient] = None
        self._clients: Dict[str, Any] = {}
        self._cluster_info: Optional[Dict[str, Any]] = None
        
        logger.info("KubernetesClientManager initialized", 
                   config_path=config_path, context=context)
    
    def _load_config(self) -> None:
        """Load Kubernetes configuration."""
        try:
            if self.config_path:
                config.load_kube_config(config_file=self.config_path, context=self.context)
            else:
                # Try in-cluster config first, then local config
                try:
                    config.load_incluster_config()
                    logger.info("Loaded in-cluster Kubernetes configuration")
                except config.ConfigException:
                    config.load_kube_config(context=self.context)
                    logger.info("Loaded local Kubernetes configuration")
            
            # Create API client
            self._api_client = client.ApiClient()
            
        except Exception as e:
            logger.error("Failed to load Kubernetes configuration", error=str(e))
            raise Exception(f"Failed to load Kubernetes configuration: {str(e)}")
    
    @property
    def api_client(self) -> client.ApiClient:
        """Get the Kubernetes API client."""
        if self._api_client is None:
            self._load_config()
        return self._api_client
    
    def get_core_v1_api(self) -> client.CoreV1Api:
        """Get CoreV1Api client."""
        if 'core_v1' not in self._clients:
            self._clients['core_v1'] = client.CoreV1Api(self.api_client)
        return self._clients['core_v1']
    
    def get_apps_v1_api(self) -> client.AppsV1Api:
        """Get AppsV1Api client."""
        if 'apps_v1' not in self._clients:
            self._clients['apps_v1'] = client.AppsV1Api(self.api_client)
        return self._clients['apps_v1']
    
    def get_networking_v1_api(self) -> client.NetworkingV1Api:
        """Get NetworkingV1Api client."""
        if 'networking_v1' not in self._clients:
            self._clients['networking_v1'] = client.NetworkingV1Api(self.api_client)
        return self._clients['networking_v1']
    
    def get_custom_objects_api(self) -> client.CustomObjectsApi:
        """Get CustomObjectsApi client."""
        if 'custom_objects' not in self._clients:
            self._clients['custom_objects'] = client.CustomObjectsApi(self.api_client)
        return self._clients['custom_objects']
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the Kubernetes cluster.
        
        Returns:
            Dictionary with health check results
        """
        try:
            core_v1 = self.get_core_v1_api()
            
            # Get cluster version
            version_api = client.VersionApi(self.api_client)
            version_info = version_api.get_code()
            
            # Get node information
            nodes = core_v1.list_node()
            node_count = len(nodes.items)
            ready_nodes = sum(1 for node in nodes.items 
                            if any(condition.type == "Ready" and condition.status == "True" 
                                  for condition in node.status.conditions))
            
            # Get namespace information
            namespaces = core_v1.list_namespace()
            namespace_count = len(namespaces.items)
            
            return {
                'healthy': True,
                'cluster_version': f"{version_info.major}.{version_info.minor}",
                'git_version': version_info.git_version,
                'nodes': {
                    'total': node_count,
                    'ready': ready_nodes
                },
                'namespaces': namespace_count,
                'timestamp': core_v1.api_client.configuration.host
            }
            
        except Exception as e:
            logger.error("Kubernetes health check failed", error=str(e))
            return {
                'healthy': False,
                'error': str(e)
            }
    
    async def get_cluster_info(self) -> Dict[str, Any]:
        """
        Get comprehensive cluster information.
        
        Returns:
            Dictionary with cluster information
        """
        if self._cluster_info is None:
            try:
                core_v1 = self.get_core_v1_api()
                version_api = client.VersionApi(self.api_client)
                
                # Get version info
                version_info = version_api.get_code()
                
                # Get nodes
                nodes = core_v1.list_node()
                node_info = []
                for node in nodes.items:
                    node_info.append({
                        'name': node.metadata.name,
                        'status': next((condition.status for condition in node.status.conditions 
                                      if condition.type == "Ready"), "Unknown"),
                        'version': node.status.node_info.kubelet_version,
                        'os': node.status.node_info.os_image,
                        'architecture': node.status.node_info.architecture,
                        'instance_type': node.metadata.labels.get('node.kubernetes.io/instance-type', 'Unknown')
                    })
                
                # Get namespaces
                namespaces = core_v1.list_namespace()
                namespace_names = [ns.metadata.name for ns in namespaces.items]
                
                self._cluster_info = {
                    'version': {
                        'kubernetes': f"{version_info.major}.{version_info.minor}",
                        'git_version': version_info.git_version,
                        'platform': version_info.platform
                    },
                    'nodes': node_info,
                    'namespaces': namespace_names,
                    'endpoint': self.api_client.configuration.host
                }
                
            except Exception as e:
                logger.error("Failed to get cluster info", error=str(e))
                self._cluster_info = {'error': str(e)}
        
        return self._cluster_info
    
    async def create_namespace(self, name: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Create a Kubernetes namespace.
        
        Args:
            name: Namespace name
            labels: Optional labels for the namespace
            
        Returns:
            Dictionary with creation result
        """
        try:
            core_v1 = self.get_core_v1_api()
            
            # Check if namespace already exists
            try:
                existing_ns = core_v1.read_namespace(name)
                return {
                    'success': True,
                    'exists': True,
                    'namespace': name,
                    'message': f'Namespace {name} already exists'
                }
            except ApiException as e:
                if e.status != 404:
                    raise
            
            # Create namespace
            namespace = client.V1Namespace(
                metadata=client.V1ObjectMeta(
                    name=name,
                    labels=labels or {}
                )
            )
            
            result = core_v1.create_namespace(namespace)
            
            return {
                'success': True,
                'exists': False,
                'namespace': name,
                'uid': result.metadata.uid,
                'creation_timestamp': result.metadata.creation_timestamp.isoformat()
            }
            
        except ApiException as e:
            logger.error("Failed to create namespace", namespace=name, error=str(e))
            return {
                'success': False,
                'error': f'Kubernetes API error: {e.reason}',
                'status': e.status
            }
        except Exception as e:
            logger.error("Failed to create namespace", namespace=name, error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    async def list_pods(self, namespace: str = "default", label_selector: Optional[str] = None) -> Dict[str, Any]:
        """
        List pods in a namespace.
        
        Args:
            namespace: Kubernetes namespace
            label_selector: Optional label selector
            
        Returns:
            Dictionary with pod information
        """
        try:
            core_v1 = self.get_core_v1_api()
            
            pods = core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
            
            pod_info = []
            for pod in pods.items:
                pod_info.append({
                    'name': pod.metadata.name,
                    'namespace': pod.metadata.namespace,
                    'status': pod.status.phase,
                    'ready': sum(1 for condition in (pod.status.conditions or []) 
                               if condition.type == "Ready" and condition.status == "True"),
                    'restarts': sum(container.restart_count for container in (pod.status.container_statuses or [])),
                    'node': pod.spec.node_name,
                    'created': pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
                    'labels': pod.metadata.labels or {}
                })
            
            return {
                'success': True,
                'namespace': namespace,
                'pods': pod_info,
                'count': len(pod_info)
            }
            
        except ApiException as e:
            logger.error("Failed to list pods", namespace=namespace, error=str(e))
            return {
                'success': False,
                'error': f'Kubernetes API error: {e.reason}',
                'status': e.status
            }
        except Exception as e:
            logger.error("Failed to list pods", namespace=namespace, error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    async def apply_manifest(self, manifest: Dict[str, Any], namespace: str = "default") -> Dict[str, Any]:
        """
        Apply a Kubernetes manifest.
        
        Args:
            manifest: Kubernetes manifest dictionary
            namespace: Target namespace
            
        Returns:
            Dictionary with application result
        """
        try:
            kind = manifest.get('kind')
            api_version = manifest.get('apiVersion')
            
            if not kind or not api_version:
                return {
                    'success': False,
                    'error': 'Manifest must include kind and apiVersion'
                }
            
            # Ensure namespace is set
            if 'metadata' not in manifest:
                manifest['metadata'] = {}
            manifest['metadata']['namespace'] = namespace
            
            # Route to appropriate API based on kind
            if kind == 'Deployment' and api_version.startswith('apps/'):
                apps_v1 = self.get_apps_v1_api()
                deployment = client.V1Deployment(**manifest)
                
                try:
                    # Try to update existing deployment
                    result = apps_v1.patch_namespaced_deployment(
                        name=deployment.metadata.name,
                        namespace=namespace,
                        body=deployment
                    )
                    action = 'updated'
                except ApiException as e:
                    if e.status == 404:
                        # Create new deployment
                        result = apps_v1.create_namespaced_deployment(
                            namespace=namespace,
                            body=deployment
                        )
                        action = 'created'
                    else:
                        raise
                
                return {
                    'success': True,
                    'action': action,
                    'kind': kind,
                    'name': result.metadata.name,
                    'namespace': result.metadata.namespace,
                    'uid': result.metadata.uid
                }
            
            elif kind == 'Service' and api_version == 'v1':
                core_v1 = self.get_core_v1_api()
                service = client.V1Service(**manifest)
                
                try:
                    result = core_v1.patch_namespaced_service(
                        name=service.metadata.name,
                        namespace=namespace,
                        body=service
                    )
                    action = 'updated'
                except ApiException as e:
                    if e.status == 404:
                        result = core_v1.create_namespaced_service(
                            namespace=namespace,
                            body=service
                        )
                        action = 'created'
                    else:
                        raise
                
                return {
                    'success': True,
                    'action': action,
                    'kind': kind,
                    'name': result.metadata.name,
                    'namespace': result.metadata.namespace,
                    'uid': result.metadata.uid
                }
            
            else:
                return {
                    'success': False,
                    'error': f'Unsupported resource kind: {kind} with apiVersion: {api_version}'
                }
                
        except ApiException as e:
            logger.error("Failed to apply manifest", kind=manifest.get('kind'), error=str(e))
            return {
                'success': False,
                'error': f'Kubernetes API error: {e.reason}',
                'status': e.status
            }
        except Exception as e:
            logger.error("Failed to apply manifest", kind=manifest.get('kind'), error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    def clear_client_cache(self) -> None:
        """Clear the client cache."""
        self._clients.clear()
        self._cluster_info = None
        logger.info("Kubernetes client cache cleared")