"""
Tool Base Classes for Bedrock AgentCore Framework Compatibility
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[float] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'metadata': self.metadata or {},
            'execution_time_ms': self.execution_time_ms,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class ToolParameter(BaseModel):
    """Tool parameter specification."""
    name: str
    type: str
    description: str
    required: bool = False
    default: Optional[Any] = None
    enum: Optional[List[str]] = None
    
    class Config:
        """Pydantic configuration."""
        extra = "allow"


class ToolSpec(BaseModel):
    """Tool specification following AgentCore patterns."""
    name: str
    description: str
    parameters: List[ToolParameter] = Field(default_factory=list)
    returns: Optional[Dict[str, Any]] = None
    examples: Optional[List[Dict[str, Any]]] = None
    
    def to_bedrock_format(self) -> Dict[str, Any]:
        """Convert to Bedrock tool specification format."""
        properties = {}
        required = []
        
        for param in self.parameters:
            param_spec = {
                "type": param.type,
                "description": param.description
            }
            
            if param.enum:
                param_spec["enum"] = param.enum
            
            if param.default is not None:
                param_spec["default"] = param.default
            
            properties[param.name] = param_spec
            
            if param.required:
                required.append(param.name)
        
        return {
            "toolSpec": {
                "name": self.name,
                "description": self.description,
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            }
        }


class Tool(ABC):
    """
    Base Tool class following Bedrock AgentCore framework patterns.
    
    Tools are the primary way agents interact with external systems.
    Each tool should be focused on a specific domain or capability.
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize the tool.
        
        Args:
            name: Tool name
            description: Tool description
        """
        self.name = name
        self.description = description
        self._spec: Optional[ToolSpec] = None
        self._initialized = False
        
        logger.info("Tool initialized", tool=name)
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool with given parameters.
        
        Args:
            parameters: Tool execution parameters
            
        Returns:
            ToolResult with execution results
        """
        pass
    
    @abstractmethod
    def get_spec(self) -> ToolSpec:
        """Get the tool specification."""
        pass
    
    async def initialize(self) -> None:
        """Initialize the tool (override if needed)."""
        self._initialized = True
        logger.info("Tool initialized", tool=self.name)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the tool."""
        return {
            'tool': self.name,
            'status': 'healthy' if self._initialized else 'not_initialized',
            'description': self.description,
            'timestamp': datetime.now().isoformat()
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tool parameters against the specification."""
        spec = self.get_spec()
        validated = {}
        errors = []
        
        # Check required parameters
        required_params = [p.name for p in spec.parameters if p.required]
        for param_name in required_params:
            if param_name not in parameters:
                errors.append(f"Missing required parameter: {param_name}")
        
        # Validate parameter types and values
        for param in spec.parameters:
            if param.name in parameters:
                value = parameters[param.name]
                
                # Type validation (basic)
                if param.type == "string" and not isinstance(value, str):
                    errors.append(f"Parameter {param.name} must be a string")
                elif param.type == "integer" and not isinstance(value, int):
                    errors.append(f"Parameter {param.name} must be an integer")
                elif param.type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Parameter {param.name} must be a boolean")
                
                # Enum validation
                if param.enum and value not in param.enum:
                    errors.append(f"Parameter {param.name} must be one of: {param.enum}")
                
                validated[param.name] = value
            elif param.default is not None:
                validated[param.name] = param.default
        
        if errors:
            raise ValueError(f"Parameter validation failed: {'; '.join(errors)}")
        
        return validated
    
    async def execute_with_validation(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute the tool with parameter validation."""
        start_time = datetime.now()
        
        try:
            # Validate parameters
            validated_params = self.validate_parameters(parameters)
            
            # Execute the tool
            result = await self.execute(validated_params)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time
            
            logger.info("Tool executed successfully", 
                       tool=self.name, 
                       execution_time_ms=execution_time)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.error("Tool execution failed", 
                        tool=self.name, 
                        error=str(e),
                        execution_time_ms=execution_time)
            
            return ToolResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time
            )


class ToolRegistry:
    """Registry for managing tools."""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.info("Tool registered in registry", tool=tool.name)
    
    def unregister(self, tool_name: str) -> None:
        """Unregister a tool."""
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.info("Tool unregistered from registry", tool=tool_name)
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(tool_name)
    
    def get_all_tools(self) -> Dict[str, Tool]:
        """Get all registered tools."""
        return self._tools.copy()
    
    def get_tool_specs(self) -> List[Dict[str, Any]]:
        """Get specifications for all tools."""
        specs = []
        for tool in self._tools.values():
            try:
                spec = tool.get_spec()
                specs.append(spec.to_bedrock_format())
            except Exception as e:
                logger.error("Failed to get tool spec", tool=tool.name, error=str(e))
        return specs
    
    async def initialize_all(self) -> None:
        """Initialize all registered tools."""
        for tool in self._tools.values():
            try:
                await tool.initialize()
            except Exception as e:
                logger.error("Failed to initialize tool", tool=tool.name, error=str(e))
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health check on all tools."""
        results = {}
        for tool_name, tool in self._tools.items():
            try:
                results[tool_name] = await tool.health_check()
            except Exception as e:
                results[tool_name] = {
                    'tool': tool_name,
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        return results