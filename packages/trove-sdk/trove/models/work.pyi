"""Type stub for Work model."""

from typing import List, Optional, Dict, Any
from .base import TroveBaseModel

class Work(TroveBaseModel):
    """Type-safe work model."""
    
    # Core fields
    id: str
    title: Optional[str] = None
    contributor: List[str]
    issued: Optional[str] = None
    publication_year: Optional[int] = None

    # Properties
    @property
    def raw(self) -> Dict[str, Any]: ...
    
    def __getitem__(self, key: str) -> Any: ...
    
    def __contains__(self, key: str) -> bool: ...
    
    def get(self, key: str, default: Any = None) -> Any: ...
