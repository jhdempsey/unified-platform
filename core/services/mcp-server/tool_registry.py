"""
Tool Registry
Manages registration and discovery of MCP tools
"""

import logging
from typing import Dict, List, Optional

from base_tool import BaseTool
from rag_tool import RAGQueryTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry of available MCP tools"""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.team_access: Dict[str, List[str]] = {}  # team_id -> list of tool names

        # Register built-in tools
        self._register_builtin_tools()

        logger.info(f"Tool Registry initialized with {len(self.tools)} tools")

    def _register_builtin_tools(self):
        """Register platform-provided tools"""
        self.register_tool(RAGQueryTool())
        # Add more tools here as they're implemented
        # self.register_tool(MLInferenceTool())
        # self.register_tool(SupplierLookupTool())

    def register_tool(self, tool: BaseTool):
        """Register a new tool"""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name} v{tool.version}")

    async def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get tool by name"""
        return self.tools.get(name)

    async def get_tools_for_team(self, team_id: str) -> List[BaseTool]:
        """
        Get all tools accessible by a team

        TODO: Implement team-based access control
        For MVP, return all tools
        """
        return list(self.tools.values())

    def list_all_tools(self) -> List[Dict[str, any]]:
        """List all registered tools in MCP schema format"""
        return [tool.to_mcp_schema() for tool in self.tools.values()]

    def get_tool_count(self) -> int:
        """Get number of registered tools"""
        return len(self.tools)
