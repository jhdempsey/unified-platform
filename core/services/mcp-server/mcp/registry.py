from typing import Any, Dict, List, Optional

from tools.base import BaseTool
from tools.ml_inference import MLInferenceTool
from tools.rag_query import RAGQueryTool
from tools.supplier_lookup import SupplierLookupTool


class ToolRegistry:
    """Registry of available MCP tools"""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.team_access: Dict[str, List[str]] = {}  # team_id -> list of tool names

        # Register built-in tools
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        """Register platform-provided tools"""
        self.register_tool(RAGQueryTool())
        self.register_tool(MLInferenceTool())
        self.register_tool(SupplierLookupTool())

    def register_tool(self, tool: BaseTool):
        """Register a new tool"""
        self.tools[tool.name] = tool

    async def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get tool by name"""
        return self.tools.get(name)

    async def get_tools_for_team(self, team_id: str) -> List[BaseTool]:
        """Get all tools accessible by a team"""
        # TODO: Implement team-based access control
        # For now, return all tools
        return list(self.tools.values())

    def list_all_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools"""
        return [tool.to_mcp_schema() for tool in self.tools.values()]
