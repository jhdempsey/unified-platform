"""
Supply Chain AI Agent
A fully-automated, IaC-compatible agent using existing platform services
"""
import os
import json
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from anthropic import Anthropic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Supply Chain AI Agent",
    description="AI-powered assistant using platform services",
    version="1.0.0"
)

# =============================================================================
# Configuration
# =============================================================================

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "https://rag-service-742330383495.us-central1.run.app")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "https://product-service-742330383495.us-central1.run.app")
DISCOVERY_AGENT_URL = os.getenv("DISCOVERY_AGENT_URL", "https://discovery-agent-742330383495.us-central1.run.app")
PRODUCT_GENERATOR_URL = os.getenv("PRODUCT_GENERATOR_URL", "https://product-generator-742330383495.us-central1.run.app")
STREAM_ANALYSIS_URL = os.getenv("STREAM_ANALYSIS_URL", "https://stream-analysis-742330383495.us-central1.run.app")
ML_CONSUMER_URL = os.getenv("ML_CONSUMER_URL", "https://ml-consumer-742330383495.us-central1.run.app")

# Initialize Anthropic client
client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

# =============================================================================
# Tool Definitions (for Claude tool use)
# =============================================================================

TOOLS = [
    {
        "name": "search_documents",
        "description": "Search supply chain documentation and knowledge base using RAG. Use this for questions about policies, procedures, or general supply chain knowledge.",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to search for in the knowledge base"
                }
            },
            "required": ["question"]
        }
    },
    {
        "name": "list_products",
        "description": "Get a list of products from the product catalog",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of products to return",
                    "default": 10
                }
            }
        }
    },
    {
        "name": "get_product",
        "description": "Get details of a specific product by ID",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "The product ID to look up"
                }
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "discover_kafka_topics",
        "description": "Discover available Kafka topics and their schemas",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_stream_stats",
        "description": "Get real-time stream processing statistics and alerts",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_ml_predictions_stats",
        "description": "Get ML consumer statistics including messages processed and predictions made",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "generate_product",
        "description": "Use AI to generate a new product based on a description or category",
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Description of the product to generate"
                },
                "category": {
                    "type": "string",
                    "description": "Product category (e.g., Electronics, Food, Clothing)"
                }
            },
            "required": ["description"]
        }
    }
]

# =============================================================================
# Tool Implementations
# =============================================================================

async def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool and return the result"""
    
    async with httpx.AsyncClient(timeout=90.0) as http_client:
        try:
            if tool_name == "search_documents":
                response = await http_client.post(
                    f"{RAG_SERVICE_URL}/query",
                    json={"question": tool_input["question"], "top_k": 3}
                )
                if response.status_code in (200, 201):
                    data = response.json()
                    return json.dumps({
                        "answer": data.get("answer", "No answer found"),
                        "sources": len(data.get("sources", []))
                    })
                return f"RAG service error: {response.status_code}"

            elif tool_name == "list_products":
                limit = tool_input.get("limit", 10)
                response = await http_client.get(
                    f"{PRODUCT_SERVICE_URL}/products",
                    params={"limit": limit}
                )
                if response.status_code in (200, 201):
                    return json.dumps(response.json())
                return f"Product service error: {response.status_code}"

            elif tool_name == "get_product":
                response = await http_client.get(
                    f"{PRODUCT_SERVICE_URL}/products/{tool_input['product_id']}"
                )
                if response.status_code in (200, 201):
                    return json.dumps(response.json())
                return f"Product not found: {tool_input['product_id']}"

            elif tool_name == "discover_kafka_topics":
                response = await http_client.get(f"{STREAM_ANALYSIS_URL}/stats")
                if response.status_code in (200, 201):
                    return json.dumps(response.json())
                return f"Discovery agent error: {response.status_code}"

            elif tool_name == "get_stream_stats":
                response = await http_client.get(f"{STREAM_ANALYSIS_URL}/stats")
                if response.status_code in (200, 201):
                    return json.dumps(response.json())
                return f"Stream analysis error: {response.status_code}"

            elif tool_name == "get_ml_predictions_stats":
                response = await http_client.get(f"{ML_CONSUMER_URL}/health")
                if response.status_code in (200, 201):
                    return json.dumps(response.json())
                return f"ML consumer error: {response.status_code}"

            elif tool_name == "generate_product":
                response = await http_client.post(
                    f"{PRODUCT_GENERATOR_URL}/generate",
                    json={
                        "product_name": tool_input["description"],
                        "description": tool_input["description"],
                        "owner": "supply-chain-agent",
                        "category": tool_input.get("category", "General")
                    }
                )
                if response.status_code in (200, 201):
                    return json.dumps(response.json())
                return f"Product generator error: {response.status_code}"

            else:
                return f"Unknown tool: {tool_name}"

        except httpx.TimeoutException:
            return f"Timeout calling {tool_name}"
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return f"Error executing {tool_name}: {str(e)}"

# =============================================================================
# Agent Logic
# =============================================================================

SYSTEM_PROMPT = """You are the Supply Chain AI Assistant for demoSupplyChainInc. You help users with:

1. **Knowledge Search** - Search documentation and policies using the search_documents tool
2. **Product Management** - List, view, and generate products
3. **Data Discovery** - Discover Kafka topics and data flows
4. **Monitoring** - Check stream processing stats and ML predictions

Always be helpful and concise. Use the available tools to provide accurate, real-time information.
When you don't have enough information, ask clarifying questions.

Available capabilities:
- Search knowledge base (RAG)
- List/view products from catalog
- Discover Kafka topics and schemas
- Get real-time stream statistics
- Get ML prediction stats
- Generate new products using AI
"""

async def run_agent(user_message: str, conversation_history: list = None) -> dict:
    """Run the agent with tool use"""
    
    if not client:
        return {
            "response": "AI agent not configured. Please set ANTHROPIC_API_KEY.",
            "tools_used": []
        }
    
    messages = conversation_history or []
    messages.append({"role": "user", "content": user_message})
    
    tools_used = []
    max_iterations = 5
    
    for _ in range(max_iterations):
        # Call Claude with tools
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )
        
        # Check if we need to use tools
        if response.stop_reason == "tool_use":
            # Process tool calls
            tool_results = []
            
            for content in response.content:
                if content.type == "tool_use":
                    tool_name = content.name
                    tool_input = content.input
                    
                    logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
                    result = await execute_tool(tool_name, tool_input)
                    
                    tools_used.append({
                        "tool": tool_name,
                        "input": tool_input,
                        "success": not result.startswith("Error")
                    })
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": result
                    })
            
            # Add assistant response and tool results to messages
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            
        else:
            # Final response
            final_text = ""
            for content in response.content:
                if hasattr(content, "text"):
                    final_text += content.text
            
            return {
                "response": final_text,
                "tools_used": tools_used
            }
    
    return {
        "response": "Max iterations reached. Please try a simpler query.",
        "tools_used": tools_used
    }

# =============================================================================
# API Endpoints
# =============================================================================

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    tools_used: list
    conversation_id: Optional[str] = None

# Simple in-memory conversation storage (use Redis in production)
conversations = {}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "supply-chain-agent",
        "version": "1.0.0",
        "ai_configured": client is not None,
        "tools_available": len(TOOLS)
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with the AI agent"""
    
    if not client:
        raise HTTPException(
            status_code=503,
            detail="AI agent not configured. Set ANTHROPIC_API_KEY."
        )
    
    # Get or create conversation history
    conv_id = request.conversation_id or "default"
    history = conversations.get(conv_id, [])
    
    # Run agent
    result = await run_agent(request.message, history.copy())
    
    # Update conversation history (keep last 10 exchanges)
    history.append({"role": "user", "content": request.message})
    history.append({"role": "assistant", "content": result["response"]})
    conversations[conv_id] = history[-20:]  # Keep last 20 messages
    
    return ChatResponse(
        response=result["response"],
        tools_used=result["tools_used"],
        conversation_id=conv_id
    )

@app.get("/tools")
async def list_tools():
    """List available tools"""
    return {
        "tools": [
            {"name": t["name"], "description": t["description"]}
            for t in TOOLS
        ]
    }

@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, tool_input: dict = {}):
    """Directly call a tool (for testing)"""
    
    valid_tools = [t["name"] for t in TOOLS]
    if tool_name not in valid_tools:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
    
    result = await execute_tool(tool_name, tool_input)
    return {"tool": tool_name, "result": json.loads(result) if result.startswith("{") else result}

@app.delete("/conversations/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear conversation history"""
    if conversation_id in conversations:
        del conversations[conversation_id]
    return {"status": "cleared"}

# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
