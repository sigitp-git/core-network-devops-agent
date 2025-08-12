"""
Deployment models for Core Network DevOps Agent
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class DeploymentStatus(str, Enum):
    """Deployment status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeploymentType(str, Enum):
    """Deployment type enumeration."""
    NETWORK_FUNCTION = "network_function"
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    CONFIGURATION = "configuration"


class ResourceRequirements(BaseModel):
    """Resource requirements for deployments."""
    cpu: str = Field(default="1000m", description="CPU requirement")
    memory: str = Field(default="2Gi", description="Memory requirement")
    storage: Optional[str] = Field(default=None, description="Storage requirement")
    replicas: int = Field(default=1, description="Number of replicas")


class DeploymentRequest(BaseModel):
    """Deployment request model."""
    name: str = Field(..., description="Deployment name")
    type: DeploymentType = Field(..., description="Deployment type")
    namespace: str = Field(default="default", description="Kubernetes namespace")
    image: Optional[str] = Field(default=None, description="Container image")
    resources: ResourceRequirements = Field(default_factory=ResourceRequirements)
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    ports: List[int] = Field(default_factory=list)
    config_maps: List[str] = Field(default_factory=list)
    secrets: List[str] = Field(default_factory=list)
    volumes: List[Dict[str, Any]] = Field(default_factory=list)
    network_policies: List[str] = Field(default_factory=list)
    service_account: Optional[str] = Field(default=None)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class DeploymentStatusModel(BaseModel):
    """Deployment status model."""
    deployment_id: str = Field(..., description="Unique deployment identifier")
    name: str = Field(..., description="Deployment name")
    status: DeploymentStatus = Field(..., description="Current status")
    type: DeploymentType = Field(..., description="Deployment type")
    namespace: str = Field(..., description="Kubernetes namespace")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    
    # Resource information
    desired_replicas: int = Field(default=1)
    ready_replicas: int = Field(default=0)
    available_replicas: int = Field(default=0)
    
    # Status details
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)
    
    # Metadata
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    
    # Error information
    error_message: Optional[str] = Field(default=None)
    error_details: Optional[Dict[str, Any]] = Field(default=None)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class NetworkFunctionDeployment(DeploymentRequest):
    """Network function specific deployment model."""
    function_type: str = Field(..., description="Network function type (AMF, SMF, UPF, etc.)")
    network_slice_id: Optional[str] = Field(default=None, description="Network slice identifier")
    plmn_id: Optional[str] = Field(default=None, description="PLMN identifier")
    
    # 5G Core specific configurations
    amf_config: Optional[Dict[str, Any]] = Field(default=None)
    smf_config: Optional[Dict[str, Any]] = Field(default=None)
    upf_config: Optional[Dict[str, Any]] = Field(default=None)
    
    # LTE Core specific configurations
    mme_config: Optional[Dict[str, Any]] = Field(default=None)
    sgw_config: Optional[Dict[str, Any]] = Field(default=None)
    pgw_config: Optional[Dict[str, Any]] = Field(default=None)


class InfrastructureDeployment(DeploymentRequest):
    """Infrastructure specific deployment model."""
    infrastructure_type: str = Field(..., description="Infrastructure type (VPC, EKS, EC2, etc.)")
    region: str = Field(..., description="AWS region")
    availability_zones: List[str] = Field(default_factory=list)
    
    # AWS specific configurations
    vpc_config: Optional[Dict[str, Any]] = Field(default=None)
    eks_config: Optional[Dict[str, Any]] = Field(default=None)
    ec2_config: Optional[Dict[str, Any]] = Field(default=None)
    rds_config: Optional[Dict[str, Any]] = Field(default=None)


class DeploymentPlan(BaseModel):
    """Deployment plan model."""
    plan_id: str = Field(..., description="Unique plan identifier")
    name: str = Field(..., description="Plan name")
    description: Optional[str] = Field(default=None)
    
    # Deployment steps
    deployments: List[DeploymentRequest] = Field(default_factory=list)
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    
    # Execution configuration
    parallel_execution: bool = Field(default=False)
    rollback_on_failure: bool = Field(default=True)
    timeout_minutes: int = Field(default=30)
    
    # Validation rules
    validation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    created_by: str = Field(..., description="Creator identifier")
    created_at: datetime = Field(default_factory=datetime.now)
    tags: Dict[str, str] = Field(default_factory=dict)


class DeploymentResult(BaseModel):
    """Deployment execution result."""
    deployment_id: str = Field(..., description="Deployment identifier")
    plan_id: Optional[str] = Field(default=None, description="Plan identifier")
    status: DeploymentStatus = Field(..., description="Final status")
    
    # Execution details
    started_at: datetime = Field(..., description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None)
    duration_seconds: Optional[float] = Field(default=None)
    
    # Results
    success: bool = Field(..., description="Success indicator")
    resources_created: List[Dict[str, Any]] = Field(default_factory=list)
    resources_updated: List[Dict[str, Any]] = Field(default_factory=list)
    resources_deleted: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Output and logs
    output: Dict[str, Any] = Field(default_factory=dict)
    logs: List[str] = Field(default_factory=list)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Error information
    error_message: Optional[str] = Field(default=None)
    error_details: Optional[Dict[str, Any]] = Field(default=None)
    rollback_performed: bool = Field(default=False)
    rollback_details: Optional[Dict[str, Any]] = Field(default=None)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True