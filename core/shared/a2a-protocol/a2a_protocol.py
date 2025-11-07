"""
Agent-to-Agent (A2A) Protocol Implementation

Enables standardized communication between intelligent agents.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import uuid
import json


class A2AMessageType(str, Enum):
    """A2A message types"""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ERROR = "error"


class A2APriority(str, Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class A2AAgent:
    """Agent identifier and capabilities"""
    agent_id: str
    capabilities: List[str] = field(default_factory=list)
    version: str = "1.0.0"


@dataclass
class A2AContext:
    """Contextual information for message routing and tracing"""
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    priority: A2APriority = A2APriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class A2AMessage:
    """
    Agent-to-Agent Protocol Message
    
    Standardized message format for agent communication.
    """
    # Protocol version
    protocol: str = "a2a/1.0"
    
    # Message identification
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    
    # Message type
    message_type: A2AMessageType = A2AMessageType.REQUEST
    
    # Sender and recipient
    sender: A2AAgent = field(default_factory=lambda: A2AAgent(agent_id="unknown"))
    recipient: A2AAgent = field(default_factory=lambda: A2AAgent(agent_id="unknown"))
    
    # Message content
    intent: str = ""  # What the sender wants (e.g., "suggest_product", "validate_schema")
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # Context
    context: A2AContext = field(default_factory=A2AContext)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ttl_seconds: Optional[int] = 300  # Message expires after 5 minutes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "protocol": self.protocol,
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "in_reply_to": self.in_reply_to,
            "message_type": self.message_type.value,
            "sender": {
                "agent_id": self.sender.agent_id,
                "capabilities": self.sender.capabilities,
                "version": self.sender.version
            },
            "recipient": {
                "agent_id": self.recipient.agent_id,
                "capabilities": self.recipient.capabilities,
                "version": self.recipient.version
            },
            "intent": self.intent,
            "payload": self.payload,
            "context": {
                "user_id": self.context.user_id,
                "tenant_id": self.context.tenant_id,
                "session_id": self.context.session_id,
                "trace_id": self.context.trace_id,
                "span_id": self.context.span_id,
                "priority": self.context.priority.value,
                "metadata": self.context.metadata
            },
            "timestamp": self.timestamp.isoformat(),
            "ttl_seconds": self.ttl_seconds
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'A2AMessage':
        """Create message from dictionary"""
        return cls(
            protocol=data.get("protocol", "a2a/1.0"),
            message_id=data.get("message_id", str(uuid.uuid4())),
            conversation_id=data.get("conversation_id"),
            in_reply_to=data.get("in_reply_to"),
            message_type=A2AMessageType(data.get("message_type", "request")),
            sender=A2AAgent(
                agent_id=data["sender"]["agent_id"],
                capabilities=data["sender"].get("capabilities", []),
                version=data["sender"].get("version", "1.0.0")
            ),
            recipient=A2AAgent(
                agent_id=data["recipient"]["agent_id"],
                capabilities=data["recipient"].get("capabilities", []),
                version=data["recipient"].get("version", "1.0.0")
            ),
            intent=data.get("intent", ""),
            payload=data.get("payload", {}),
            context=A2AContext(
                user_id=data["context"].get("user_id"),
                tenant_id=data["context"].get("tenant_id"),
                session_id=data["context"].get("session_id"),
                trace_id=data["context"].get("trace_id"),
                span_id=data["context"].get("span_id"),
                priority=A2APriority(data["context"].get("priority", "normal")),
                metadata=data["context"].get("metadata", {})
            ),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
            ttl_seconds=data.get("ttl_seconds", 300)
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'A2AMessage':
        """Create message from JSON string"""
        return cls.from_dict(json.loads(json_str))
    
    def create_reply(
        self,
        sender: A2AAgent,
        intent: str,
        payload: Dict[str, Any],
        message_type: A2AMessageType = A2AMessageType.RESPONSE
    ) -> 'A2AMessage':
        """Create a reply to this message"""
        return A2AMessage(
            message_type=message_type,
            conversation_id=self.conversation_id or self.message_id,
            in_reply_to=self.message_id,
            sender=sender,
            recipient=self.sender,  # Reply to original sender
            intent=intent,
            payload=payload,
            context=self.context  # Preserve context
        )


@dataclass
class A2AError:
    """Error information for A2A messages"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }
