"""List model for Trove user lists."""

from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator
from .base import TroveBaseModel
from .common import Tag, Comment, ItemCount


class ListItem(TroveBaseModel):
    """Represents an item within a list."""
    # List items can contain works, articles, people, etc.
    # The structure depends on the item type
    id: Optional[str] = None
    type: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    contributor: List[str] = Field(default_factory=list)
    date: Optional[str] = None
    
    @field_validator('contributor', mode='before')
    @classmethod
    def ensure_list(cls, v):
        """Ensure contributor field is always a list."""
        if v is None:
            return []
        elif isinstance(v, (str, dict)):
            return [v]
        elif isinstance(v, list):
            return v
        return []


class ListDate(TroveBaseModel):
    """Represents date information for a list."""
    created: Optional[str] = None
    lastupdated: Optional[str] = None


class TroveList(TroveBaseModel):
    """
    Represents a Trove user list with optional type safety.
    
    Always provides raw dict access via .raw property and dict-like methods
    for backward compatibility and future API changes.
    """
    
    # Core identification
    id: str
    url: Optional[str] = None
    trove_url: Optional[str] = Field(None, alias='troveUrl')
    
    # Content
    title: Optional[str] = None
    description: Optional[str] = None
    
    # Creator info
    creator: Optional[str] = None
    by: Optional[str] = None  # Alternative creator field
    
    # List properties
    list_item_count: Optional[int] = Field(None, alias='listItemCount')
    
    # Timestamps
    last_updated: Optional[str] = Field(None, alias='lastupdated')
    date: Optional[ListDate] = None
    
    # User content
    tag_count: List[ItemCount] = Field(default_factory=list, alias='tagCount')
    comment_count: List[ItemCount] = Field(default_factory=list, alias='commentCount')
    tag: List[Tag] = Field(default_factory=list)
    comment: List[Comment] = Field(default_factory=list)
    
    # List contents (when included)
    list_item: List[ListItem] = Field(default_factory=list, alias='listItem')
    
    @field_validator('date', mode='before')
    @classmethod
    def ensure_list_date(cls, v):
        """Ensure date field is a ListDate object."""
        if v is None:
            return None
        elif isinstance(v, dict):
            return ListDate(**v)
        return v
    
    @field_validator('list_item', mode='before')
    @classmethod
    def ensure_list_item_list(cls, v):
        """Ensure list_item field is always a list of ListItem objects."""
        if v is None:
            return []
        elif isinstance(v, dict):
            return [ListItem(**v)]
        elif isinstance(v, list):
            return [ListItem(**item) if isinstance(item, dict) else item for item in v]
        return []
    
    @field_validator('tag_count', 'comment_count', mode='before')
    @classmethod
    def ensure_item_count_list(cls, v):
        """Ensure count fields are always lists of ItemCount objects."""
        if v is None:
            return []
        elif isinstance(v, dict):
            return [ItemCount(**v)]
        elif isinstance(v, list):
            return [ItemCount(**item) if isinstance(item, dict) else item for item in v]
        return []
    
    @field_validator('list_item_count', mode='before')
    @classmethod
    def parse_list_item_count(cls, v):
        """Parse list item count from string to int."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v
    
    @property
    def display_title(self) -> str:
        """Get displayable title."""
        return self.title or "Untitled List"
    
    @property
    def creator_name(self) -> str:
        """Get creator name with fallback."""
        return self.creator or self.by or "Anonymous"
    
    @property
    def item_count(self) -> int:
        """Get number of items in list."""
        if self.list_item_count is not None:
            return self.list_item_count
        return len(self.list_item)