"""
Conversation Memory Management for Bedrock AgentCore Framework Compatibility
"""

import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class MessageRole(str, Enum):
    """Message roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class ConversationMessage:
    """A single message in a conversation."""
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    tool_results: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'role': self.role.value,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata or {},
            'tool_results': self.tool_results or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """Create from dictionary format."""
        return cls(
            role=MessageRole(data['role']),
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata'),
            tool_results=data.get('tool_results')
        )


class ConversationMemory:
    """
    Conversation memory management following AgentCore patterns.
    
    Handles conversation history, context management, and memory persistence.
    """
    
    def __init__(
        self,
        max_messages: int = 100,
        retention_hours: int = 24,
        enable_summarization: bool = True
    ):
        """
        Initialize conversation memory.
        
        Args:
            max_messages: Maximum number of messages to keep
            retention_hours: Hours to retain messages
            enable_summarization: Whether to enable automatic summarization
        """
        self.max_messages = max_messages
        self.retention_hours = retention_hours
        self.enable_summarization = enable_summarization
        
        self._messages: List[ConversationMessage] = []
        self._context: Dict[str, Any] = {}
        self._summary: Optional[str] = None
        
        logger.info("ConversationMemory initialized",
                   max_messages=max_messages,
                   retention_hours=retention_hours)
    
    def add_message(
        self,
        role: Union[MessageRole, str],
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tool_results: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            role: Message role
            content: Message content
            metadata: Optional metadata
            tool_results: Optional tool execution results
        """
        if isinstance(role, str):
            role = MessageRole(role)
        
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata,
            tool_results=tool_results
        )
        
        self._messages.append(message)
        
        # Cleanup old messages
        self._cleanup_messages()
        
        logger.debug("Message added to conversation",
                    role=role.value,
                    content_length=len(content))
    
    def get_messages(
        self,
        limit: Optional[int] = None,
        role_filter: Optional[MessageRole] = None,
        since: Optional[datetime] = None
    ) -> List[ConversationMessage]:
        """
        Get conversation messages with optional filtering.
        
        Args:
            limit: Maximum number of messages to return
            role_filter: Filter by message role
            since: Only return messages after this timestamp
            
        Returns:
            List of conversation messages
        """
        messages = self._messages.copy()
        
        # Apply filters
        if role_filter:
            messages = [m for m in messages if m.role == role_filter]
        
        if since:
            messages = [m for m in messages if m.timestamp >= since]
        
        # Apply limit
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversation history in dictionary format."""
        return [msg.to_dict() for msg in self._messages]
    
    def get_context(self) -> Dict[str, Any]:
        """Get current conversation context."""
        return self._context.copy()
    
    def update_context(self, context: Dict[str, Any]) -> None:
        """Update conversation context."""
        self._context.update(context)
        logger.debug("Conversation context updated", keys=list(context.keys()))
    
    def clear_context(self) -> None:
        """Clear conversation context."""
        self._context.clear()
        logger.debug("Conversation context cleared")
    
    def get_recent_messages(self, count: int = 10) -> List[ConversationMessage]:
        """Get the most recent messages."""
        return self._messages[-count:] if self._messages else []
    
    def get_user_messages(self, limit: Optional[int] = None) -> List[ConversationMessage]:
        """Get user messages only."""
        return self.get_messages(limit=limit, role_filter=MessageRole.USER)
    
    def get_assistant_messages(self, limit: Optional[int] = None) -> List[ConversationMessage]:
        """Get assistant messages only."""
        return self.get_messages(limit=limit, role_filter=MessageRole.ASSISTANT)
    
    def clear(self) -> None:
        """Clear all conversation history and context."""
        self._messages.clear()
        self._context.clear()
        self._summary = None
        logger.info("Conversation memory cleared")
    
    def get_summary(self) -> Optional[str]:
        """Get conversation summary."""
        return self._summary
    
    def set_summary(self, summary: str) -> None:
        """Set conversation summary."""
        self._summary = summary
        logger.debug("Conversation summary updated", length=len(summary))
    
    def _cleanup_messages(self) -> None:
        """Clean up old messages based on retention policy."""
        # Remove messages older than retention period
        if self.retention_hours > 0:
            cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
            self._messages = [m for m in self._messages if m.timestamp >= cutoff_time]
        
        # Limit total number of messages
        if len(self._messages) > self.max_messages:
            # Keep the most recent messages
            removed_count = len(self._messages) - self.max_messages
            self._messages = self._messages[-self.max_messages:]
            
            logger.debug("Messages cleaned up",
                        removed_count=removed_count,
                        remaining_count=len(self._messages))
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics."""
        if not self._messages:
            return {
                'total_messages': 0,
                'user_messages': 0,
                'assistant_messages': 0,
                'oldest_message': None,
                'newest_message': None
            }
        
        user_count = len([m for m in self._messages if m.role == MessageRole.USER])
        assistant_count = len([m for m in self._messages if m.role == MessageRole.ASSISTANT])
        
        return {
            'total_messages': len(self._messages),
            'user_messages': user_count,
            'assistant_messages': assistant_count,
            'oldest_message': self._messages[0].timestamp.isoformat(),
            'newest_message': self._messages[-1].timestamp.isoformat(),
            'context_keys': list(self._context.keys()),
            'has_summary': self._summary is not None
        }
    
    def to_bedrock_format(self) -> List[Dict[str, Any]]:
        """Convert conversation to Bedrock API format."""
        bedrock_messages = []
        
        for message in self._messages:
            bedrock_message = {
                'role': message.role.value,
                'content': message.content
            }
            
            # Add tool results if present
            if message.tool_results:
                bedrock_message['tool_results'] = message.tool_results
            
            bedrock_messages.append(bedrock_message)
        
        return bedrock_messages
    
    def save_to_file(self, filepath: str) -> None:
        """Save conversation to a JSON file."""
        data = {
            'messages': [msg.to_dict() for msg in self._messages],
            'context': self._context,
            'summary': self._summary,
            'stats': self.get_conversation_stats(),
            'saved_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info("Conversation saved to file", filepath=filepath)
    
    def load_from_file(self, filepath: str) -> None:
        """Load conversation from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Load messages
        self._messages = [
            ConversationMessage.from_dict(msg_data)
            for msg_data in data.get('messages', [])
        ]
        
        # Load context and summary
        self._context = data.get('context', {})
        self._summary = data.get('summary')
        
        logger.info("Conversation loaded from file",
                   filepath=filepath,
                   message_count=len(self._messages))