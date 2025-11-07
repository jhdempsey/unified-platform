from abc import ABC, abstractmethod
from typing import Any, Dict, List

from pydantic import BaseModel


class ToolParameter(BaseModel):
    """MCP tool parameter schema"""

    name: str
    type: str  # "string", "number", "boolean", "object", "array"
    description: str
    required: bool = True
    enum: List[str] = None


class ToolSchema(BaseModel):
    """MCP tool schema"""

    name: str
    description: str
    inputSchema: Dict[str, Any]  # JSON Schema


class BaseTool(ABC):
    """Base class for all MCP tools"""

    name: str
    description: str
    parameters: List[ToolParameter]
    version: str = "1.0.0"

    def to_mcp_schema(self) -> Dict[str, Any]:
        """Convert tool to MCP schema format"""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                properties[param.name]["enum"] = param.enum
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    @abstractmethod
    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Execute the tool with given arguments"""
        pass

    async def validate_arguments(self, arguments: Dict[str, Any]) -> bool:
        """Validate tool arguments"""
        # TODO: Implement JSON schema validation
        return True
