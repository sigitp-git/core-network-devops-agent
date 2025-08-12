"""
Bedrock AgentCore Framework Integration

This module provides the integration layer with Amazon Bedrock's AgentCore framework.
Since the actual AgentCore SDK may not be available, we implement compatible patterns.
"""

from .agent_base import Agent, AgentResponse
from .tool_base import Tool, ToolResult
from .memory import ConversationMemory
from .decorators import tool, agent_handler

__all__ = [
    'Agent',
    'AgentResponse', 
    'Tool',
    'ToolResult',
    'ConversationMemory',
    'tool',
    'agent_handler'
]