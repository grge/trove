"""Base tool class for MCP tools."""

from abc import ABC, abstractmethod
from typing import Dict, Any

from trove import TroveClient


class BaseTool(ABC):
    """Base class for all MCP tools."""
    
    def __init__(self, client: TroveClient):
        self.client = client
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """JSON schema for tool input."""
        pass
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        """Execute the tool with given arguments."""
        pass