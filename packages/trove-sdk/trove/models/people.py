"""People model for Trove people and organization records."""

from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator
from .base import TroveBaseModel
from .common import Identifier, Tag, Comment, ItemCount


class Biography(TroveBaseModel):
    """Biographical information."""
    contributor: Optional[str] = None
    contributor_id: Optional[str] = Field(None, alias='contributorId')
    biography: Optional[str] = None
    lastupdated: Optional[str] = None


class DisambiguationName(TroveBaseModel):
    """Name used for disambiguation."""
    name: Optional[str] = None
    role: Optional[str] = None


class People(TroveBaseModel):
    """
    Represents a Trove people/organisation record with optional type safety.
    
    Always provides raw dict access via .raw property and dict-like methods
    for backward compatibility and future API changes.
    """
    
    # Core identification
    id: str
    url: Optional[str] = None
    trove_url: Optional[str] = Field(None, alias='troveUrl')
    type: Optional[str] = None  # person, corporatebody, family
    
    # Names
    primary_name: Optional[str] = Field(None, alias='primaryName')
    primary_display_name: Optional[str] = Field(None, alias='primaryDisplayName')
    alternate_name: List[str] = Field(default_factory=list, alias='alternateName')
    alternate_display_name: List[str] = Field(default_factory=list, alias='alternateDisplayName')
    
    # Disambiguation
    disambiguation: Optional[bool] = None
    disambiguation_name: List[DisambiguationName] = Field(default_factory=list, alias='disambiguationName')
    
    # Person-specific
    title: List[str] = Field(default_factory=list)
    occupation: List[str] = Field(default_factory=list)
    
    # Biography
    biography: List[Biography] = Field(default_factory=list)
    
    # Metadata
    contributor: List[str] = Field(default_factory=list)
    identifier: List[Identifier] = Field(default_factory=list)
    
    # User content
    tag_count: List[ItemCount] = Field(default_factory=list, alias='tagCount')
    comment_count: List[ItemCount] = Field(default_factory=list, alias='commentCount')
    list_count: Optional[int] = Field(None, alias='listCount')
    tag: List[Tag] = Field(default_factory=list)
    comment: List[Comment] = Field(default_factory=list)
    
    # Cultural sensitivity
    culturally_sensitive: Optional[str] = Field(None, alias='culturallySensitive')
    first_australians: Optional[str] = Field(None, alias='firstAustralians')
    
    @field_validator('alternate_name', 'alternate_display_name', 'title', 'occupation', 
                     'contributor', mode='before')
    @classmethod
    def ensure_list(cls, v):
        """Ensure certain fields are always lists."""
        if v is None:
            return []
        elif isinstance(v, (str, dict)):
            return [v]
        elif isinstance(v, list):
            return v
        return []
    
    @field_validator('biography', mode='before')
    @classmethod
    def ensure_biography_list(cls, v):
        """Ensure biography field is always a list of Biography objects."""
        if v is None:
            return []
        elif isinstance(v, dict):
            return [Biography(**v)]
        elif isinstance(v, list):
            return [Biography(**item) if isinstance(item, dict) else item for item in v]
        return []
    
    @field_validator('disambiguation_name', mode='before')
    @classmethod
    def ensure_disambiguation_name_list(cls, v):
        """Ensure disambiguation_name field is always a list of DisambiguationName objects."""
        if v is None:
            return []
        elif isinstance(v, dict):
            return [DisambiguationName(**v)]
        elif isinstance(v, list):
            return [DisambiguationName(**item) if isinstance(item, dict) else item for item in v]
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
    
    @property
    def display_name(self) -> str:
        """Get primary display name with fallback."""
        return (self.primary_display_name or 
                self.primary_name or 
                "Unnamed Entity")
    
    @property
    def is_person(self) -> bool:
        """Check if record represents a person."""
        return self.type == 'person'
    
    @property
    def is_organization(self) -> bool:
        """Check if record represents an organization."""
        return self.type in ['corporatebody', 'family']
    
    @property
    def primary_biography(self) -> Optional[str]:
        """Get the primary biographical text."""
        if self.biography:
            return self.biography[0].biography if hasattr(self.biography[0], 'biography') else None
        return None