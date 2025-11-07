"""
MCP Protocol Implementation
JSON-RPC 2.0 protocol handler for Model Context Protocol
"""

import json
import logging
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MCPRequest(BaseModel):
    """MCP JSON-RPC 2.0 request"""

    jsonrpc: str = "2.0"
    id: str | int
    method: str
    params: Dict[str, Any] = Field(default_factory=dict)


class MCPResponse(BaseModel):
    """MCP JSON-RPC 2.0 response"""

    jsonrpc: str = "2.0"
    id: str | int
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class MCPServer:
    """MCP protocol server implementation"""

    def __init__(self, tool_registry):
        self.tool_registry = tool_registry
        logger.info("MCP Server initialized")

    async def handle_request(
        self, request: MCPRequest, context: Dict[str, Any]
    ) -> MCPResponse:
        """Route MCP request to appropriate handler"""

        logger.info(f"Handling MCP method: {request.method}")

        try:
            if request.method == "tools/list":
                return await self.list_tools(request, context)

            elif request.method == "tools/call":
                return await self.call_tool(request, context)

            elif request.method == "resources/list":
                return await self.list_resources(request, context)

            elif request.method == "prompts/list":
                return await self.list_prompts(request, context)

            else:
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {request.method}",
                    },
                )

        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            return MCPResponse(id=request.id, error={"code": -32000, "message": str(e)})

    async def list_tools(
        self, request: MCPRequest, context: Dict[str, Any]
    ) -> MCPResponse:
        """Return available tools"""
        logger.info("Listing tools")

        tools = self.tool_registry.list_all_tools()

        return MCPResponse(id=request.id, result={"tools": tools})

    async def call_tool(
        self, request: MCPRequest, context: Dict[str, Any]
    ) -> MCPResponse:
        """Execute a tool"""
        tool_name = request.params.get("name")
        arguments = request.params.get("arguments", {})

        logger.info(f"Calling tool: {tool_name} with args: {arguments}")

        # Get tool from registry
        tool = await self.tool_registry.get_tool(tool_name)
        if not tool:
            return MCPResponse(
                id=request.id,
                error={"code": -32602, "message": f"Tool not found: {tool_name}"},
            )

        try:
            # Execute tool
            result = await tool.execute(arguments, context)

            logger.info(f"Tool {tool_name} executed successfully")

            # Format response per MCP spec
            return MCPResponse(
                id=request.id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ]
                },
            )

        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return MCPResponse(
                id=request.id,
                error={"code": -32000, "message": f"Tool execution error: {str(e)}"},
            )

    async def list_resources(
        self, request: MCPRequest, context: Dict[str, Any]
    ) -> MCPResponse:
        """List available resources (files, data sources, etc.)"""
        # Not implemented in MVP
        return MCPResponse(id=request.id, result={"resources": []})

    async def list_prompts(
        self, request: MCPRequest, context: Dict[str, Any]
    ) -> MCPResponse:
        """List available prompt templates"""
        # Not implemented in MVP
        return MCPResponse(id=request.id, result={"prompts": []})
