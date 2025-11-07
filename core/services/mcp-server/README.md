# AI Platform MCP Server

Model Context Protocol (MCP) server for multi-tenant AI agent platform.

## Overview

This MCP server provides a standardized interface for AI agents to access platform tools and services. It implements the Model Context Protocol, allowing any MCP-compatible agent framework (Vertex Agent Builder, Claude, LangGraph, etc.) to use your platform's capabilities.

## Features

- **MCP Protocol Support**: Full JSON-RPC 2.0 implementation
- **Tool Registry**: Dynamically registered tools with automatic discovery
- **RAG Integration**: Query supply chain documentation
- **Observability Ready**: Structured logging (metrics/tracing to be added)
- **Cloud Run Deployment**: Production-ready containerization

## Architecture

```
Agent Client (Vertex/Claude/LangGraph)
           ↓ MCP Protocol (JSON-RPC 2.0)
      MCP Server
           ↓
    Tool Registry → RAG Query Tool → RAG Service
```

## Available Tools

### 1. `query_documentation`
Query supply chain policies, procedures, and compliance documentation.

**Parameters:**
- `question` (string, required): Natural language question
- `max_results` (number, optional): Maximum results (default: 3)

**Returns:**
- `answer`: Synthesized answer from documentation
- `sources`: List of source documents with relevance scores
- `confidence`: Confidence level (high/medium/low)

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export RAG_SERVICE_URL="https://rag-service-dakmfhg3aa-uc.a.run.app"

# Run server
python main.py

# Server runs on http://localhost:8000
```

### Test the Server

```bash
# Run test script
python test_mcp.py

# Or test manually with curl
curl http://localhost:8000/health
curl http://localhost:8000/tools

# Test MCP protocol
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

### Docker Deployment

```bash
# Build image
docker build -t mcp-server:latest .

# Run container
docker run -p 8000:8000 \
  -e RAG_SERVICE_URL="https://rag-service-dakmfhg3aa-uc.a.run.app" \
  mcp-server:latest
```

### Google Cloud Run Deployment

```bash
# Build and push to Artifact Registry
docker build --platform linux/amd64 \
  -t us-central1-docker.pkg.dev/YOUR_PROJECT/ai-platform/mcp-server:latest .

docker push us-central1-docker.pkg.dev/YOUR_PROJECT/ai-platform/mcp-server:latest

# Deploy to Cloud Run
gcloud run deploy mcp-server \
  --image=us-central1-docker.pkg.dev/YOUR_PROJECT/ai-platform/mcp-server:latest \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars=RAG_SERVICE_URL=https://rag-service-dakmfhg3aa-uc.a.run.app
```

## MCP Protocol Endpoints

### POST `/mcp`
Main MCP protocol endpoint. Accepts JSON-RPC 2.0 requests.

**Supported Methods:**
- `tools/list` - List available tools
- `tools/call` - Execute a tool
- `resources/list` - List resources (not implemented)
- `prompts/list` - List prompts (not implemented)

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "query_documentation",
    "arguments": {
      "question": "What are supplier quality requirements?",
      "max_results": 3
    }
  }
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"answer\": \"...\", \"sources\": [...], \"confidence\": \"high\"}"
      }
    ]
  }
}
```

## Adding New Tools

1. Create a new tool class inheriting from `BaseTool`:

```python
from base_tool import BaseTool, ToolParameter

class MyTool(BaseTool):
    name = "my_tool"
    description = "Description of what the tool does"
    parameters = [
        ToolParameter(
            name="input",
            type="string",
            description="Input parameter description",
            required=True
        )
    ]

    async def execute(self, arguments, context):
        # Tool implementation
        return {"result": "success"}
```

2. Register in `tool_registry.py`:

```python
from my_tool import MyTool

def _register_builtin_tools(self):
    self.register_tool(RAGQueryTool())
    self.register_tool(MyTool())  # Add here
```

## Environment Variables

- `RAG_SERVICE_URL`: URL of the RAG service (default: production URL)
- `PORT`: Server port (default: 8000)

## API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Next Steps

### Phase 2: Authentication & Authorization
- [ ] JWT validation
- [ ] Team-based access control
- [ ] API key management
- [ ] Rate limiting per team

### Phase 3: Additional Tools
- [ ] ML model inference tool
- [ ] Supplier database lookup tool
- [ ] Inventory query tool
- [ ] Report generation tool

### Phase 4: Observability
- [ ] Prometheus metrics
- [ ] OpenTelemetry tracing
- [ ] Usage tracking
- [ ] Cost attribution

### Phase 5: Agent Integration
- [ ] Vertex Agent Builder integration guide
- [ ] Claude Desktop/API integration
- [ ] LangGraph examples
- [ ] Multi-step workflow examples

## Architecture Decisions

### Why MCP?
- **Standard Protocol**: Industry-standard way to expose tools to agents
- **Framework Agnostic**: Works with any MCP-compatible agent
- **Future Proof**: As agent frameworks evolve, they can consume your tools
- **Separation of Concerns**: Agents handle orchestration, your platform provides tools

### Why Cloud Run?
- **Serverless**: No infrastructure management
- **Auto-scaling**: Scales to zero, handles bursts
- **Cost Effective**: Pay only for usage
- **Fast Deployments**: Update tools without downtime

## Troubleshooting

### Server won't start
- Check `RAG_SERVICE_URL` is set correctly
- Verify port 8000 is available
- Check logs: `docker logs <container-id>`

### Tool execution fails
- Verify RAG service is accessible
- Check network connectivity
- Review logs for detailed error messages

### MCP protocol errors
- Validate JSON-RPC 2.0 format
- Check method name spelling
- Verify parameter schema matches tool definition

## License

Internal use only - AI Platform Team

## Support

For questions or issues, contact the AI Platform team.
