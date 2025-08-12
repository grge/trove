"""Article model for Trove newspaper and gazette articles."""

from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator
from .base import TroveBaseModel
from .common import Tag, Comment, ItemCount


class ArticleTitle(TroveBaseModel):
    """Represents newspaper/gazette title information."""
    id: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None


class LastCorrection(TroveBaseModel):
    """Represents information about the last correction made to an article."""
    by: Optional[str] = None
    lastupdated: Optional[str] = None


class Article(TroveBaseModel):
    """
    Represents a Trove newspaper/gazette article with optional type safety.
    
    Always provides raw dict access via .raw property and dict-like methods
    for backward compatibility and future API changes.
    """
    
    # Core identification
    id: str
    url: Optional[str] = None
    identifier: Optional[str] = None
    trove_url: Optional[str] = Field(None, alias='troveUrl')
    trove_page_url: Optional[str] = Field(None, alias='trovePageUrl')
    
    # Content
    heading: Optional[str] = None
    category: Optional[str] = None
    article_text: Optional[str] = Field(None, alias='articleText')
    snippet: List[str] = Field(default_factory=list)
    
    # Publication info
    title: Optional[ArticleTitle] = None
    date: Optional[str] = None
    page: Optional[str] = None
    page_sequence: Optional[str] = Field(None, alias='pageSequence')
    page_label: Optional[str] = Field(None, alias='pageLabel')
    edition: Optional[str] = None
    supplement: Optional[str] = None
    section: Optional[str] = None
    
    # Article characteristics
    illustrated: Optional[str] = None
    word_count: Optional[int] = Field(None, alias='wordCount')
    
    # Status and corrections
    status: Optional[str] = None
    correction_count: Optional[int] = Field(None, alias='correctionCount')
    last_correction: Optional[LastCorrection] = Field(None, alias='lastCorrection')
    
    # User content
    tag_count: List[ItemCount] = Field(default_factory=list, alias='tagCount')
    comment_count: List[ItemCount] = Field(default_factory=list, alias='commentCount')
    list_count: Optional[int] = Field(None, alias='listCount')
    tag: List[Tag] = Field(default_factory=list)
    comment: List[Comment] = Field(default_factory=list)
    
    # Resources
    pdf: List[str] = Field(default_factory=list)
    
    @field_validator('snippet', 'pdf', mode='before')
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
    
    @field_validator('title', mode='before')
    @classmethod
    def ensure_article_title(cls, v):
        """Ensure title field is an ArticleTitle object."""
        if v is None:
            return None
        elif isinstance(v, dict):
            return ArticleTitle(**v)
        return v
    
    @field_validator('last_correction', mode='before')
    @classmethod
    def ensure_last_correction(cls, v):
        """Ensure last_correction field is a LastCorrection object."""
        if v is None:
            return None
        elif isinstance(v, dict):
            return LastCorrection(**v)
        return v
    
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
    
    @field_validator('word_count', mode='before')
    @classmethod
    def parse_word_count(cls, v):
        """Parse word count from string to int."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v
    
    @field_validator('correction_count', mode='before')
    @classmethod
    def parse_correction_count(cls, v):
        """Parse correction count from string to int."""
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
        """Get displayable title/heading."""
        return self.heading or "Untitled Article"
    
    @property
    def newspaper_title(self) -> Optional[str]:
        """Get newspaper title."""
        if self.title and hasattr(self.title, 'title'):
            return self.title.title
        elif isinstance(self.title, dict):
            return self.title.get('title')
        return str(self.title) if self.title else None
    
    @property
    def has_full_text(self) -> bool:
        """Check if article has full text available."""
        return bool(self.article_text and self.article_text.strip())
    
    @property
    def is_illustrated(self) -> bool:
        """Check if article is illustrated."""
        return self.illustrated == 'Y'
    
    @property
    def has_corrections(self) -> bool:
        """Check if article has corrections."""
        return bool(self.correction_count and self.correction_count > 0)