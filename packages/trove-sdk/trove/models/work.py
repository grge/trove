"""Work model for Trove work records."""

import re
from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator
from .base import TroveBaseModel
from .common import Identifier, Language, Spatial, ItemCount, Tag, Comment, Relevance


class WorkVersion(TroveBaseModel):
    """Represents a version/edition within a work."""
    id: Optional[str] = None
    title: Optional[str] = None
    contributor: List[str] = Field(default_factory=list)
    publisher: List[str] = Field(default_factory=list)
    date: Optional[str] = None
    format: List[str] = Field(default_factory=list)
    isbn: List[str] = Field(default_factory=list)
    extent: Optional[str] = None
    language: List[Language] = Field(default_factory=list)
    identifier: List[Identifier] = Field(default_factory=list)


class WorkHolding(TroveBaseModel):
    """Represents library holding information."""
    id: Optional[str] = None
    subunit: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None
    callNumber: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class IsPartOf(TroveBaseModel):
    """Represents parent work relationship."""
    url: Optional[str] = None
    title: Optional[str] = None
    identifier: Optional[str] = None


class Work(TroveBaseModel):
    """
    Represents a Trove work record with optional type safety.
    
    Always provides raw dict access via .raw property and dict-like methods
    for backward compatibility and future API changes.
    """
    
    # Core identification
    id: str
    title: Optional[str] = None
    url: Optional[str] = None
    trove_url: Optional[str] = Field(None, alias='troveUrl')
    
    # Content metadata
    contributor: List[str] = Field(default_factory=list)
    issued: Optional[str] = None
    type: List[str] = Field(default_factory=list)
    format: List[str] = Field(default_factory=list)
    subject: List[str] = Field(default_factory=list)
    abstract: Optional[str] = None
    audience: List[str] = Field(default_factory=list)
    rights: List[str] = Field(default_factory=list)
    extent: Optional[str] = None
    table_of_contents: Optional[str] = Field(None, alias='tableOfContents')
    
    # Publication info
    publisher: List[str] = Field(default_factory=list)
    place_of_publication: List[str] = Field(default_factory=list, alias='placeOfPublication')
    language: List[Language] = Field(default_factory=list)
    
    # Geographic and spatial
    spatial: List[Spatial] = Field(default_factory=list)
    
    # Relationships
    is_part_of: List[IsPartOf] = Field(default_factory=list, alias='isPartOf')
    identifier: List[Identifier] = Field(default_factory=list)
    snippet: List[str] = Field(default_factory=list)
    
    # Enrichment data
    wikipedia: Optional[str] = None
    has_corrections: Optional[str] = Field(None, alias='hasCorrections')
    last_updated: Optional[str] = Field(None, alias='lastUpdated')
    
    # Quantitative data
    holdings_count: Optional[int] = Field(None, alias='holdingsCount')
    version_count: Optional[int] = Field(None, alias='versionCount')
    list_count: Optional[int] = Field(None, alias='listCount')
    
    # User-generated content
    tag_count: List[ItemCount] = Field(default_factory=list, alias='tagCount')
    comment_count: List[ItemCount] = Field(default_factory=list, alias='commentCount')
    tag: List[Tag] = Field(default_factory=list)
    comment: List[Comment] = Field(default_factory=list)
    
    # Cultural sensitivity
    culturally_sensitive: Optional[str] = Field(None, alias='culturallySensitive')
    first_australians: Optional[str] = Field(None, alias='firstAustralians')
    
    # Complex nested objects (when includes are used)
    version: List[WorkVersion] = Field(default_factory=list)
    holding: List[WorkHolding] = Field(default_factory=list)
    relevance: Optional[Relevance] = None
    
    @field_validator('contributor', 'type', 'format', 'subject', 'publisher', 
                     'place_of_publication', 'audience', 'rights', 'snippet', mode='before')
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
    def primary_title(self) -> str:
        """Get the primary title, with fallback."""
        return self.title or "Untitled Work"
    
    @property
    def primary_contributor(self) -> Optional[str]:
        """Get the first contributor."""
        return self.contributor[0] if self.contributor else None
    
    @property
    def publication_year(self) -> Optional[int]:
        """Extract publication year from issued date."""
        if not self.issued:
            return None
        match = re.search(r'(\d{4})', self.issued)
        return int(match.group(1)) if match else None
    
    @property
    def is_online(self) -> bool:
        """Check if work has online availability."""
        # Check various indicators of online availability
        for identifier in self.identifier:
            if isinstance(identifier, dict):
                value = identifier.get('value', '')
                if 'http' in str(value).lower():
                    return True
            elif hasattr(identifier, 'value') and 'http' in str(identifier.value).lower():
                return True
        return False
    
    @property
    def has_corrections(self) -> bool:
        """Check if work has corrections."""
        return self.has_corrections == 'Y' if self.has_corrections else False