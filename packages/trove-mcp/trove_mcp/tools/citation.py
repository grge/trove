"""Citation generation tool for MCP."""

from typing import Dict, Any, Union, Optional
from pydantic import BaseModel, Field, validator

from trove.citations import CitationManager, RecordType
from .base import BaseTool


class CitationInput(BaseModel):
    """Input schema for citation generation."""
    
    source: Union[str, Dict[str, Any]] = Field(
        description="PID/URL to cite, or raw record data with record_type"
    )
    record_type: Optional[str] = Field(
        None,
        description="Record type when providing raw data (work, article, people, list)"
    )
    format_type: str = Field(
        "bibtex",
        description="Citation format: bibtex or csl_json"
    )
    
    @validator('record_type')
    def validate_record_type(cls, v):
        if v and v not in ['work', 'article', 'people', 'list']:
            raise ValueError("record_type must be one of: work, article, people, list")
        return v
    
    @validator('format_type')
    def validate_format_type(cls, v):
        if v not in ['bibtex', 'csl_json']:
            raise ValueError("format_type must be 'bibtex' or 'csl_json'")
        return v
    
    class Config:
        extra = "forbid"


class CitationTool(BaseTool):
    """Tool for generating citations in various formats."""
    
    def __init__(self, client, format_type: str = 'bibtex'):
        super().__init__(client)
        self.format_type = format_type
        self.citation_manager = CitationManager(client.resources)
    
    @property
    def name(self) -> str:
        return f"citation_{self.format_type}"
    
    @property 
    def description(self) -> str:
        format_desc = {
            'bibtex': 'BibTeX format for LaTeX documents',
            'csl_json': 'CSL-JSON format for reference managers'
        }
        
        return f"""
        Generate {format_desc.get(self.format_type, 'formatted')} citations for Trove records.
        
        Can cite by:
        - PID or URL (automatically resolves to record)
        - Raw record data (must specify record_type)
        
        Produces properly formatted citations suitable for academic use.
        """
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        schema = CitationInput.model_json_schema()
        # Override format_type default for this specific tool
        schema['properties']['format_type']['default'] = self.format_type
        return schema
    
    async def execute(self, arguments: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        """Execute citation generation."""
        input_data = CitationInput(**arguments)
        
        # Override format type from tool configuration
        input_data.format_type = self.format_type
        
        if isinstance(input_data.source, str):
            # Resolve PID/URL to citation
            if self.format_type == 'bibtex':
                citation = await self.citation_manager.acite_bibtex(input_data.source)
            else:
                citation = await self.citation_manager.acite_csl_json(input_data.source)
        else:
            # Use raw record data
            if not input_data.record_type:
                raise ValueError("record_type is required when providing raw record data")
            
            record_type = RecordType(input_data.record_type)
            citation_ref = await self.citation_manager.aextract_from_record(input_data.source, record_type)
            
            if self.format_type == 'bibtex':
                citation = await self.citation_manager.acite_bibtex(citation_ref)
            else:
                citation = await self.citation_manager.acite_csl_json(citation_ref)
        
        return citation