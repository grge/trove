"""PID resolution tool for MCP."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from trove.citations import CitationManager
from .base import BaseTool


class ResolvePIDInput(BaseModel):
    """Input schema for PID resolution."""
    
    identifier: str = Field(
        description="PID, URL, or identifier to resolve"
    )
    
    class Config:
        extra = "forbid"


class ResolvePIDOutput(BaseModel):
    """Output schema for PID resolution."""
    
    resolved: bool = Field(description="Whether the identifier was successfully resolved")
    record_type: Optional[str] = Field(None, description="Type of record (work, article, people, list)")
    record_id: Optional[str] = Field(None, description="Resolved record ID")
    pid: Optional[str] = Field(None, description="Canonical PID if available")
    trove_url: Optional[str] = Field(None, description="Trove web interface URL")
    api_url: Optional[str] = Field(None, description="API endpoint URL")
    title: Optional[str] = Field(None, description="Record title")
    error_message: Optional[str] = Field(None, description="Error message if resolution failed")


class ResolvePIDTool(BaseTool):
    """Tool for resolving PIDs and URLs to record information."""
    
    name = "resolve_pid"
    description = """
    Resolve a PID, URL, or identifier to detailed record information.
    
    Supports:
    - Trove PIDs (e.g., nla.obj-123456789, nla.news-article18341291)
    - Trove URLs (web interface and API URLs)
    - Bare record IDs (attempts resolution across record types)
    
    Returns basic record information without full metadata.
    Use get_* tools to retrieve complete record data.
    """
    
    input_schema = ResolvePIDInput.model_json_schema()
    output_schema = ResolvePIDOutput.model_json_schema()
    
    def __init__(self, client):
        super().__init__(client)
        self.citation_manager = CitationManager(client.resources)
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PID resolution."""
        input_data = ResolvePIDInput(**arguments)
        
        try:
            citation_ref = await self.citation_manager.aresolve_identifier(input_data.identifier)
            
            if citation_ref:
                return ResolvePIDOutput(
                    resolved=True,
                    record_type=citation_ref.record_type.value,
                    record_id=citation_ref.record_id,
                    pid=citation_ref.canonical_pid,
                    trove_url=citation_ref.trove_url,
                    api_url=citation_ref.api_url,
                    title=citation_ref.title,
                    error_message=None
                ).model_dump()
            else:
                return ResolvePIDOutput(
                    resolved=False,
                    error_message=f"Could not resolve identifier: {input_data.identifier}"
                ).model_dump()
                
        except Exception as e:
            return ResolvePIDOutput(
                resolved=False,
                error_message=str(e)
            ).model_dump()