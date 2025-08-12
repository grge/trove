"""Type stub for Article model."""

from typing import List, Optional, Dict, Any
from .base import TroveBaseModel

class Article(TroveBaseModel):
    """Type-safe article model."""
    
    # Core fields
    id: str
    heading: Optional[str] = None
    date: Optional[str] = None
    article_text: Optional[str] = None
    word_count: Optional[int] = None

    # Properties
    @property
    def raw(self) -> Dict[str, Any]: ...
    
    def __getitem__(self, key: str) -> Any: ...
    
    def __contains__(self, key: str) -> bool: ...
    
    def get(self, key: str, default: Any = None) -> Any: ...
