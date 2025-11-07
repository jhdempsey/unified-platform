"""
AI Platform MCP Server
Model Context Protocol server for multi-tenant AI agent platform
"""

import logging

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from mcp_protocol import MCPRequest, MCPServer
from tool_registry import ToolRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Platform MCP Server",
    description="Model Context Protocol server for AI agents",
    version="1.0.0",
    openapi_url=None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MCP server
tool_registry = ToolRegistry()
mcp_server = MCPServer(tool_registry)


@app.get("/")
async def root():
    """API root with service information"""
    return {
        "service": "AI Platform MCP Server",
        "version": "1.0.0",
        "protocol": "MCP (Model Context Protocol)",
        "endpoints": {
            "/mcp": "MCP protocol endpoint (POST)",
            "/health": "Health check",
            "/tools": "List available tools",
            "/docs": "API documentation",
        },
        "tools_registered": len(tool_registry.tools),
    }


@app.get("/health")
async def health():
    """Kubernetes health check endpoint"""
    return {
        "status": "healthy",
        "service": "mcp-server",
        "tools_available": len(tool_registry.tools),
    }


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """
    Main MCP protocol endpoint
    Handles JSON-RPC 2.0 requests per MCP spec
    """
    try:
        # Parse request body
        body = await request.json()
        logger.info(f"MCP request: {body.get('method')}")

        # Create MCP request
        mcp_request = MCPRequest(**body)

        # Build context (no auth for MVP)
        context = {
            "request_id": request.headers.get("x-request-id", "unknown"),
            "team_id": "default",  # TODO: Extract from JWT
            "user_id": "system",  # TODO: Extract from JWT
        }

        # Handle request
        response = await mcp_server.handle_request(mcp_request, context)

        return response.dict(exclude_none=True)

    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e

    except Exception as e:
        logger.error(f"MCP request failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/openapi.json")
async def get_openapi_schema():
    """OpenAPI schema for Vertex Agent Builder"""
    tools = tool_registry.list_all_tools()

    paths = {}
    for tool in tools:
        tool_name = tool["name"]
        paths[f"/tools/{tool_name}"] = {
            "post": {
                "summary": tool["description"],
                "operationId": f"execute_{tool_name}",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": tool["inputSchema"]}},
                },
                "responses": {
                    "200": {
                        "description": "Tool execution result",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "answer": {
                                            "type": "string",
                                            "description": "Detailed answer in markdown format",  # noqa: E501
                                        },
                                        "sources": {
                                            "type": "array",
                                            "description": "Source documents used",
                                            "items": {"type": "object"},
                                        },
                                        "confidence": {
                                            "type": "string",
                                            "enum": ["high", "medium", "low"],
                                        },
                                    },
                                    "required": ["answer"],
                                }
                            }
                        },
                    }
                },
            }
        }

    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Supply Chain AI Tools",
            "version": "1.0.0",
            "description": "AI tools for supply chain operations",
        },
        "servers": [{"url": "https://mcp-server-dakmfhg3aa-uc.a.run.app"}],
        "paths": paths,
    }


@app.post("/tools/{tool_name}")
async def execute_tool_rest(tool_name: str, request: Request):
    """REST endpoint for Vertex Agent Builder"""
    try:
        arguments = await request.json()

        tool = await tool_registry.get_tool(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

        context = {
            "request_id": request.headers.get("x-request-id", "unknown"),
            "team_id": "default",
            "user_id": "vertex-agent",
        }

        result = await tool.execute(arguments, context)
        return result

    except Exception as e:
        logger.error(f"Tool execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/tools")
async def list_tools():
    """List all available tools (convenience endpoint)"""
    tools = tool_registry.list_all_tools()
    return {
        "tools": tools,
        "count": len(tools),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
