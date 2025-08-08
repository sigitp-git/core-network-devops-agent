"""Network Function data models."""

from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class NetworkFunctionType(str, Enum):
    """Supported network function types."""
    
    # 5G Core Network Functions
    AMF = "amf"  # Access and Mobility Management Function
    SMF = "smf"  # Session Management Function
    UPF = "upf"  # User Plane Function
    AUSF = "ausf"  # Authentication Server Function
    UDM = "udm"  # Unified Data Management
    UDR = "udr"  # Unified Data Repository
    NRF = "nrf"  # Network Repository Function
    NSSF = "nssf"  # Network Slice Selection Function
    PCF = "pcf"  # Policy Control Function
    
    # LTE Core Network Elements
    MME = "mme"  # Mobility Management Entity
    SGW = "sgw"  # Serving Gateway
    PGW = "pgw"  # Packet Data Network Gateway
    HSS = "hss"  # Home Subscriber Server
    PCRF = "pcrf"  # Policy and Charging Rules Function
    
    # Common Network Functions
    DNS = "dns"  # Domain Name System
    DHCP = "dhcp"  # Dynamic Host Configuration Protocol
    RADIUS = "radius"  # Remote Authentication Dial-In User Service


class NetworkFunctionStatus(str, Enum):
    """Network function status."""
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    STOPPED = "stopped"
    SCALING = "scaling"
    UPDATING = "updating"


class ResourceRequirements(BaseModel):
    """Resource requirements for a network function."""
    
    cpu: str = Field(..., description="CPU requirement (e.g., '1000m', '2')")
    memory: str = Field(..., description="Memory requirement (e.g., '2Gi', '1024Mi')")
    storage: Optional[str] = Field(None, description="Storage requirement (e.g., '10Gi')")
    
    @validator('cpu')
    def validate_cpu(cls, v):
        """Validate CPU format."""
        if not (v.endswith('m') or v.isdigit() or '.' in v):
            raise ValueError('CPU must be in format like "1000m", "2", or "1.5"')
        return v
    
    @validator('memory')
    def validate_memory(cls, v):
        """Validate memory format."""
        if not any(v.endswith(unit) for unit in ['Ki', 'Mi', 'Gi', 'Ti']):
            raise ValueError('Memory must include unit (Ki, Mi, Gi, Ti)')
        return v


class NetworkInterface(BaseModel):
    """Network interface configuration."""
    
    name: str = Field(..., description="Interface name")
    type: str = Field(..., description="Interface type (e.g., 'N1', 'N2', 'N3')")
    port: int = Field(..., description="Port number")
    protocol: str = Field(default="TCP", description="Protocol (TCP/UDP/SCTP)")


class NetworkFunctionConfig(BaseModel):
    """Configuration for a network function."""
    
    name: str = Field(..., description="Network function name")
    type: NetworkFunctionType = Field(..., description="Network function type")
    version: str = Field(default="latest", description="Network function version")
    
    # Deployment configuration
    replicas: int = Field(default=1, description="Number of replicas")
    resources: ResourceRequirements = Field(..., description="Resource requirements")
    
    # Container configuration
    image: str = Field(..., description="Container image")
    image_pull_policy: str = Field(default="IfNotPresent", description="Image pull policy")
    
    # Network configuration
    interfaces: List[NetworkInterface] = Field(default_factory=list, description="Network interfaces")
    service_ports: List[int] = Field(default_factory=list, description="Service ports")
    
    # Environment and configuration
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    config_maps: List[str] = Field(default_factory=list, description="ConfigMap references")
    secrets: List[str] = Field(default_factory=list, description="Secret references")
    
    # Volumes and storage
    volumes: List[Dict[str, Any]] = Field(default_factory=list, description="Volume mounts")
    persistent_volumes: List[Dict[str, Any]] = Field(default_factory=list, description="Persistent volumes")
    
    # Health checks
    health_check_path: Optional[str] = Field(None, description="Health check endpoint path")
    readiness_probe: Optional[Dict[str, Any]] = Field(None, description="Readiness probe configuration")
    liveness_probe: Optional[Dict[str, Any]] = Field(None, description="Liveness probe configuration")
    
    # Labels and annotations
    labels: Dict[str, str] = Field(default_factory=dict, description="Kubernetes labels")
    annotations: Dict[str, str] = Field(default_factory=dict, description="Kubernetes annotations")
    
    @validator('replicas')
    def validate_replicas(cls, v, values):
        """Validate replica count based on NF type."""
        nf_type = values.get('type')
        if nf_type == NetworkFunctionType.UPF and v > 1:
            raise ValueError('UPF typically runs as single instance due to stateful nature')
        return v


class NetworkFunction(BaseModel):
    """Runtime representation of a network function."""
    
    # Basic information
    name: str = Field(..., description="Network function name")
    type: NetworkFunctionType = Field(..., description="Network function type")
    namespace: str = Field(default="core-network", description="Kubernetes namespace")
    
    # Configuration
    config: NetworkFunctionConfig = Field(..., description="Network function configuration")
    
    # Runtime status
    status: NetworkFunctionStatus = Field(default=NetworkFunctionStatus.PENDING, description="Current status")
    replicas_status: Dict[str, int] = Field(
        default_factory=lambda: {"desired": 0, "ready": 0, "available": 0},
        description="Replica status"
    )
    
    # Endpoints and connectivity
    endpoints: List[str] = Field(default_factory=list, description="Service endpoints")
    internal_ip: Optional[str] = Field(None, description="Internal cluster IP")
    external_ip: Optional[str] = Field(None, description="External IP (if exposed)")
    
    # Metrics and monitoring
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Current metrics")
    health_status: Dict[str, str] = Field(
        default_factory=lambda: {"liveness": "unknown", "readiness": "unknown"},
        description="Health check status"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    # Kubernetes resources
    deployment_name: Optional[str] = Field(None, description="Kubernetes deployment name")
    service_name: Optional[str] = Field(None, description="Kubernetes service name")
    pod_names: List[str] = Field(default_factory=list, description="Pod names")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def update_status(self, status: NetworkFunctionStatus) -> None:
        """Update the network function status."""
        self.status = status
        self.updated_at = datetime.now()
    
    def update_replicas_status(self, desired: int, ready: int, available: int) -> None:
        """Update replica status."""
        self.replicas_status = {
            "desired": desired,
            "ready": ready,
            "available": available
        }
        self.updated_at = datetime.now()
    
    def add_endpoint(self, endpoint: str) -> None:
        """Add a service endpoint."""
        if endpoint not in self.endpoints:
            self.endpoints.append(endpoint)
            self.updated_at = datetime.now()
    
    def update_health_status(self, liveness: str, readiness: str) -> None:
        """Update health check status."""
        self.health_status = {
            "liveness": liveness,
            "readiness": readiness
        }
        self.updated_at = datetime.now()
    
    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update metrics."""
        self.metrics.update(metrics)
        self.updated_at = datetime.now()
    
    def is_healthy(self) -> bool:
        """Check if the network function is healthy."""
        return (
            self.status == NetworkFunctionStatus.RUNNING and
            self.health_status.get("liveness") == "healthy" and
            self.health_status.get("readiness") == "healthy" and
            self.replicas_status.get("ready", 0) > 0
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the network function."""
        return {
            "name": self.name,
            "type": self.type,
            "status": self.status,
            "replicas": f"{self.replicas_status.get('ready', 0)}/{self.replicas_status.get('desired', 0)}",
            "health": "healthy" if self.is_healthy() else "unhealthy",
            "endpoints": len(self.endpoints),
            "uptime": (datetime.now() - self.created_at).total_seconds() if self.created_at else 0
        }