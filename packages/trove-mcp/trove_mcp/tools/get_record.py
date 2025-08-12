"""Record retrieval tools for MCP."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from trove import TroveClient
from .base import BaseTool


class RecordInput(BaseModel):
    """Base input schema for record retrieval."""
    
    record_id: str = Field(description="The record identifier")
    include_fields: Optional[List[str]] = Field(
        default_factory=list,
        description="Optional fields to include"
    )
    record_level: Optional[str] = Field(
        "brief",
        description="Record detail level: brief or full"
    )
    
    class Config:
        extra = "forbid"  # Prevent additional fields


class GetWorkTool(BaseTool):
    """Tool for retrieving work records."""
    
    name = "get_work"
    description = """
    Retrieve a specific work record (book, image, map, music, etc.) by ID.
    
    Supports include parameters: all, comments, holdings, links, lists, 
    subscribinglibs, tags, workversions.
    """
    
    input_schema = RecordInput.model_json_schema()
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute work retrieval."""
        input_data = RecordInput(**arguments)
        
        work_resource = self.client.resources.get_work_resource()
        
        work = await work_resource.aget(
            input_data.record_id,
            include=input_data.include_fields,
            reclevel=input_data.record_level
        )
        
        return {
            "record_type": "work",
            "record_id": input_data.record_id,
            "data": work
        }


class ArticleInput(BaseModel):
    """Input schema for article retrieval."""
    
    article_id: str = Field(description="The article identifier")
    article_type: Optional[str] = Field(
        "newspaper",
        description="Article type: newspaper or gazette"
    )
    include_fields: Optional[List[str]] = Field(
        default_factory=list,
        description="Optional fields: all, articletext, comments, lists, tags"
    )
    record_level: Optional[str] = Field(
        "brief",
        description="Record detail level: brief or full"
    )


class GetArticleTool(BaseTool):
    """Tool for retrieving newspaper/gazette articles."""
    
    name = "get_article" 
    description = """
    Retrieve a specific newspaper or gazette article by ID.
    
    Supports include parameters: all, articletext, comments, lists, tags.
    Set article_type to 'gazette' for gazette articles.
    """
    
    input_schema = ArticleInput.model_json_schema()
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute article retrieval."""
        input_data = ArticleInput(**arguments)
        
        if input_data.article_type == "gazette":
            article_resource = self.client.resources.get_gazette_resource()
        else:
            article_resource = self.client.resources.get_newspaper_resource()
        
        article = await article_resource.aget(
            input_data.article_id,
            include=input_data.include_fields,
            reclevel=input_data.record_level
        )
        
        return {
            "record_type": "article",
            "article_type": input_data.article_type,
            "record_id": input_data.article_id,
            "data": article
        }


class GetPeopleTool(BaseTool):
    """Tool for retrieving people/organization records."""
    
    name = "get_people"
    description = """
    Retrieve a specific people or organization record by ID.
    
    Supports include parameters: all, comments, lists, raweaccpf, tags.
    """
    
    input_schema = RecordInput.model_json_schema()
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute people record retrieval."""
        input_data = RecordInput(**arguments)
        
        people_resource = self.client.resources.get_people_resource()
        
        # Validate include fields for people records
        valid_includes = ['all', 'comments', 'lists', 'raweaccpf', 'tags']
        invalid_includes = set(input_data.include_fields) - set(valid_includes)
        if invalid_includes:
            raise ValueError(f"Invalid include fields for people records: {', '.join(invalid_includes)}")
        
        people = await people_resource.aget(
            input_data.record_id,
            include=input_data.include_fields,
            reclevel=input_data.record_level
        )
        
        return {
            "record_type": "people",
            "record_id": input_data.record_id,
            "data": people
        }


class GetListTool(BaseTool):
    """Tool for retrieving list records."""
    
    name = "get_list"
    description = """
    Retrieve a specific user-created list by ID.
    
    Supports include parameters: all, comments, listitems, tags.
    """
    
    input_schema = RecordInput.model_json_schema()
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute list retrieval."""
        input_data = RecordInput(**arguments)
        
        list_resource = self.client.resources.get_list_resource()
        
        # Validate include fields for list records
        valid_includes = ['all', 'comments', 'listitems', 'tags']
        invalid_includes = set(input_data.include_fields) - set(valid_includes)
        if invalid_includes:
            raise ValueError(f"Invalid include fields for list records: {', '.join(invalid_includes)}")
        
        list_data = await list_resource.aget(
            input_data.record_id,
            include=input_data.include_fields,
            reclevel=input_data.record_level
        )
        
        return {
            "record_type": "list",
            "record_id": input_data.record_id,
            "data": list_data
        }