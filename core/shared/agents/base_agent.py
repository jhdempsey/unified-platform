"""
Base Agent Class

Provides common functionality for all intelligent agents:
- A2A (Agent-to-Agent) communication
- MCP (Model Context Protocol) tool calling
- Observability (OpenTelemetry)
- State management
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable, Awaitable
import asyncio
import logging
import json
from datetime import datetime

import redis.asyncio as redis
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from a2a_protocol import (
    A2AMessage,
    A2AAgent,
    A2AMessageType,
    A2AContext,
    A2APriority,
    A2AError
)


logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class BaseAgent(ABC):
    """
    Base class for all intelligent agents
    
    Provides:
    - A2A message handling
    - MCP tool calling
    - Redis pub/sub for messaging
    - OpenTelemetry tracing
    - State management
    """
    
    def __init__(
        self,
        agent_id: str,
        capabilities: list[str],
        redis_url: str,
        mcp_server_url: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize agent
        
        Args:
            agent_id: Unique agent identifier
            capabilities: List of agent capabilities
            redis_url: Redis connection URL
            mcp_server_url: MCP server URL
            config: Additional configuration
        """
        self.agent_info = A2AAgent(
            agent_id=agent_id,
            capabilities=capabilities,
            version="1.0.0"
        )
        
        self.redis_url = redis_url
        self.mcp_server_url = mcp_server_url
        self.config = config or {}
        
        # Redis clients
        self.redis: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        
        # Message handlers
        self.intent_handlers: Dict[str, Callable[[A2AMessage], Awaitable[Any]]] = {}
        
        # State
        self.running = False
        
        logger.info(f"Initialized agent: {agent_id} with capabilities: {capabilities}")
    
    async def start(self):
        """Start the agent"""
        logger.info(f"Starting agent: {self.agent_info.agent_id}")
        
        # Connect to Redis
        self.redis = redis.from_url(self.redis_url)
        self.pubsub = self.redis.pubsub()
        
        # Subscribe to agent's message channel
        channel = f"agent:{self.agent_info.agent_id}"
        await self.pubsub.subscribe(channel)
        logger.info(f"Subscribed to channel: {channel}")
        
        # Start message processing
        self.running = True
        asyncio.create_task(self._process_messages())
        
        # Call agent-specific startup
        await self.on_start()
        
        logger.info(f"Agent {self.agent_info.agent_id} started successfully")
    
    async def stop(self):
        """Stop the agent"""
        logger.info(f"Stopping agent: {self.agent_info.agent_id}")
        
        self.running = False
        
        # Cleanup
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        
        if self.redis:
            await self.redis.close()
        
        # Call agent-specific shutdown
        await self.on_stop()
        
        logger.info(f"Agent {self.agent_info.agent_id} stopped")
    
    async def _process_messages(self):
        """Process incoming A2A messages"""
        logger.info("Starting message processing loop")
        
        async for message in self.pubsub.listen():
            if not self.running:
                break
            
            if message['type'] == 'message':
                try:
                    # Parse A2A message
                    a2a_message = A2AMessage.from_json(message['data'])
                    
                    # Create trace span
                    with tracer.start_as_current_span(
                        f"agent.message.received",
                        attributes={
                            "agent.id": self.agent_info.agent_id,
                            "message.id": a2a_message.message_id,
                            "message.intent": a2a_message.intent,
                            "message.sender": a2a_message.sender.agent_id
                        }
                    ) as span:
                        # Handle message
                        await self._handle_message(a2a_message, span)
                        
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
    
    async def _handle_message(self, message: A2AMessage, span: trace.Span):
        """Handle incoming A2A message"""
        logger.info(
            f"Received message: {message.message_id} "
            f"from {message.sender.agent_id} "
            f"with intent: {message.intent}"
        )
        
        try:
            # Find handler for intent
            handler = self.intent_handlers.get(message.intent)
            
            if handler:
                # Call handler
                result = await handler(message)
                
                # Send response if handler returned data
                if result is not None and message.message_type == A2AMessageType.REQUEST:
                    reply = message.create_reply(
                        sender=self.agent_info,
                        intent=f"{message.intent}.response",
                        payload=result,
                        message_type=A2AMessageType.RESPONSE
                    )
                    await self.send_message(reply)
                
                span.set_status(Status(StatusCode.OK))
                
            else:
                logger.warning(f"No handler for intent: {message.intent}")
                
                # Send error response
                if message.message_type == A2AMessageType.REQUEST:
                    error = A2AError(
                        code="UNKNOWN_INTENT",
                        message=f"No handler for intent: {message.intent}",
                        details={"intent": message.intent}
                    )
                    
                    reply = message.create_reply(
                        sender=self.agent_info,
                        intent="error",
                        payload={"error": error.to_dict()},
                        message_type=A2AMessageType.ERROR
                    )
                    await self.send_message(reply)
                
                span.set_status(Status(StatusCode.ERROR, "Unknown intent"))
        
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            
            # Send error response
            if message.message_type == A2AMessageType.REQUEST:
                error = A2AError(
                    code="HANDLER_ERROR",
                    message=str(e),
                    details={"exception": type(e).__name__}
                )
                
                reply = message.create_reply(
                    sender=self.agent_info,
                    intent="error",
                    payload={"error": error.to_dict()},
                    message_type=A2AMessageType.ERROR
                )
                await self.send_message(reply)
            
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
    
    async def send_message(self, message: A2AMessage):
        """Send A2A message to another agent"""
        with tracer.start_as_current_span(
            "agent.message.sent",
            attributes={
                "agent.id": self.agent_info.agent_id,
                "message.id": message.message_id,
                "message.intent": message.intent,
                "message.recipient": message.recipient.agent_id
            }
        ):
            # Publish to recipient's channel
            channel = f"agent:{message.recipient.agent_id}"
            await self.redis.publish(channel, message.to_json())
            
            logger.info(
                f"Sent message: {message.message_id} "
                f"to {message.recipient.agent_id} "
                f"with intent: {message.intent}"
            )
    
    async def call_mcp_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Call MCP tool
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            timeout: Timeout in seconds
            
        Returns:
            Tool result
        """
        with tracer.start_as_current_span(
            "agent.mcp.call",
            attributes={
                "agent.id": self.agent_info.agent_id,
                "tool.name": tool_name
            }
        ):
            # TODO: Implement actual MCP client call
            # This is a placeholder
            logger.info(f"Calling MCP tool: {tool_name} with args: {arguments}")
            
            # For now, return mock response
            return {
                "success": True,
                "result": {},
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def register_intent_handler(
        self,
        intent: str,
        handler: Callable[[A2AMessage], Awaitable[Any]]
    ):
        """
        Register handler for specific intent
        
        Args:
            intent: Intent name (e.g., "suggest_product")
            handler: Async function that handles the message
        """
        self.intent_handlers[intent] = handler
        logger.info(f"Registered handler for intent: {intent}")
    
    @abstractmethod
    async def on_start(self):
        """Called when agent starts - implement in subclass"""
        pass
    
    @abstractmethod
    async def on_stop(self):
        """Called when agent stops - implement in subclass"""
        pass
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main agent logic - implement in subclass
        
        Args:
            input_data: Input data for agent
            
        Returns:
            Agent result
        """
        pass


class ScheduledAgent(BaseAgent):
    """Agent that runs on a schedule"""
    
    def __init__(
        self,
        agent_id: str,
        capabilities: list[str],
        redis_url: str,
        mcp_server_url: str,
        schedule_interval_seconds: int = 300,  # 5 minutes default
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(agent_id, capabilities, redis_url, mcp_server_url, config)
        self.schedule_interval_seconds = schedule_interval_seconds
        self.schedule_task: Optional[asyncio.Task] = None
    
    async def on_start(self):
        """Start scheduled execution"""
        self.schedule_task = asyncio.create_task(self._scheduled_execution())
        logger.info(
            f"Started scheduled execution with interval: "
            f"{self.schedule_interval_seconds}s"
        )
    
    async def on_stop(self):
        """Stop scheduled execution"""
        if self.schedule_task:
            self.schedule_task.cancel()
            try:
                await self.schedule_task
            except asyncio.CancelledError:
                pass
    
    async def _scheduled_execution(self):
        """Run agent execute method on schedule"""
        while self.running:
            try:
                logger.info(f"Running scheduled execution for {self.agent_info.agent_id}")
                
                with tracer.start_as_current_span("agent.scheduled.execution"):
                    await self.execute({})
                
                await asyncio.sleep(self.schedule_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduled execution: {e}", exc_info=True)
                await asyncio.sleep(self.schedule_interval_seconds)
