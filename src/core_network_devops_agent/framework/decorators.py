"""
Decorators for Bedrock AgentCore Framework Compatibility
"""

import asyncio
import inspect
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime
import structlog

from .tool_base import Tool, ToolSpec, ToolParameter, ToolResult

logger = structlog.get_logger(__name__)


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[Dict[str, Dict[str, Any]]] = None,
    returns: Optional[Dict[str, Any]] = None,
    examples: Optional[List[Dict[str, Any]]] = None
):
    """
    Decorator to mark a method as a tool following AgentCore patterns.
    
    Args:
        name: Tool name (defaults to function name)
        description: Tool description
        parameters: Parameter specifications
        returns: Return value specification
        examples: Usage examples
    
    Example:
        @tool(
            name="describe_instances",
            description="List EC2 instances",
            parameters={
                "region": {"type": "string", "description": "AWS region", "required": True}
            }
        )
        async def describe_instances(self, region: str):
            # Implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        # Get function metadata
        func_name = name or func.__name__
        func_description = description or func.__doc__ or f"Tool: {func_name}"
        
        # Parse function signature for parameters
        sig = inspect.signature(func)
        tool_parameters = []
        
        if parameters:
            for param_name, param_spec in parameters.items():
                tool_param = ToolParameter(
                    name=param_name,
                    type=param_spec.get("type", "string"),
                    description=param_spec.get("description", f"Parameter: {param_name}"),
                    required=param_spec.get("required", False),
                    default=param_spec.get("default"),
                    enum=param_spec.get("enum")
                )
                tool_parameters.append(tool_param)
        else:
            # Auto-generate from function signature
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                param_type = "string"
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == bool:
                        param_type = "boolean"
                    elif param.annotation == float:
                        param_type = "number"
                
                tool_param = ToolParameter(
                    name=param_name,
                    type=param_type,
                    description=f"Parameter: {param_name}",
                    required=param.default == inspect.Parameter.empty
                )
                tool_parameters.append(tool_param)
        
        # Create tool specification
        tool_spec = ToolSpec(
            name=func_name,
            description=func_description,
            parameters=tool_parameters,
            returns=returns,
            examples=examples
        )
        
        # Mark function as a tool
        func._is_tool = True
        func._tool_spec = tool_spec
        func._tool_name = func_name
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            
            try:
                # Execute the original function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                # If result is already a ToolResult, return it
                if isinstance(result, ToolResult):
                    result.execution_time_ms = execution_time
                    return result
                
                # Otherwise, wrap in ToolResult
                return ToolResult(
                    success=True,
                    data=result if isinstance(result, dict) else {"result": result},
                    execution_time_ms=execution_time
                )
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                logger.error("Tool execution failed",
                           tool=func_name,
                           error=str(e),
                           execution_time_ms=execution_time)
                
                return ToolResult(
                    success=False,
                    error=str(e),
                    execution_time_ms=execution_time
                )
        
        return wrapper
    
    return decorator


def agent_handler(cls):
    """
    Class decorator to mark a class as an agent handler.
    
    This decorator:
    1. Registers all @tool decorated methods as tools
    2. Sets up the agent's tool registry
    3. Provides automatic tool discovery
    
    Example:
        @agent_handler
        class MyAgent(Agent):
            @tool(name="my_tool", description="Does something")
            async def my_tool(self, param: str):
                return {"result": param}
    """
    
    # Find all tool methods
    tool_methods = []
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if hasattr(attr, '_is_tool') and attr._is_tool:
            tool_methods.append((attr_name, attr))
    
    # Store tool methods metadata
    cls._tool_methods = tool_methods
    
    # Override __init__ to register tools
    original_init = cls.__init__
    
    def new_init(self, *args, **kwargs):
        # Call original __init__
        original_init(self, *args, **kwargs)
        
        # Register tool methods as tools
        for method_name, method in tool_methods:
            tool_wrapper = MethodToolWrapper(self, method_name, method)
            self.register_tool(method._tool_name, tool_wrapper)
        
        logger.info("Agent handler initialized",
                   agent=self.__class__.__name__,
                   tools=[method._tool_name for _, method in tool_methods])
    
    cls.__init__ = new_init
    
    return cls


class MethodToolWrapper(Tool):
    """Wrapper to make a method behave like a Tool."""
    
    def __init__(self, instance: Any, method_name: str, method: Callable):
        """
        Initialize the method tool wrapper.
        
        Args:
            instance: Instance that owns the method
            method_name: Name of the method
            method: The method itself
        """
        self.instance = instance
        self.method_name = method_name
        self.method = method
        
        super().__init__(
            name=method._tool_name,
            description=method._tool_spec.description
        )
        
        self._spec = method._tool_spec
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute the wrapped method."""
        # Bind method to instance and call
        bound_method = getattr(self.instance, self.method_name)
        
        # Call the method with parameters
        if asyncio.iscoroutinefunction(bound_method):
            return await bound_method(**parameters)
        else:
            return bound_method(**parameters)
    
    def get_spec(self) -> ToolSpec:
        """Get the tool specification."""
        return self._spec


def validate_tool_parameters(**param_specs):
    """
    Decorator to validate tool parameters.
    
    Args:
        **param_specs: Parameter specifications
    
    Example:
        @validate_tool_parameters(
            region={"type": str, "required": True},
            count={"type": int, "default": 10}
        )
        def my_tool(self, region, count=10):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Validate parameters
            for param_name, spec in param_specs.items():
                param_type = spec.get("type")
                required = spec.get("required", False)
                default = spec.get("default")
                
                if param_name not in kwargs:
                    if required:
                        raise ValueError(f"Required parameter '{param_name}' is missing")
                    elif default is not None:
                        kwargs[param_name] = default
                
                if param_name in kwargs and param_type:
                    value = kwargs[param_name]
                    if not isinstance(value, param_type):
                        raise TypeError(f"Parameter '{param_name}' must be of type {param_type.__name__}")
            
            # Call original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def retry_on_failure(max_retries: int = 3, delay_seconds: float = 1.0):
    """
    Decorator to retry tool execution on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay_seconds: Delay between retries
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning("Tool execution failed, retrying",
                                     tool=func.__name__,
                                     attempt=attempt + 1,
                                     max_retries=max_retries,
                                     error=str(e))
                        
                        await asyncio.sleep(delay_seconds)
                    else:
                        logger.error("Tool execution failed after all retries",
                                   tool=func.__name__,
                                   attempts=max_retries + 1,
                                   error=str(e))
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator