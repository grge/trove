from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from datetime import datetime
import re

class RecordType(Enum):
    WORK = "work"
    ARTICLE = "article" 
    PEOPLE = "people"
    LIST = "list"
    TITLE = "title"

@dataclass
class CitationRef:
    """Immutable citation reference for a Trove record."""
    
    # Core identification
    record_type: RecordType
    record_id: str
    pid: Optional[str] = None
    trove_url: Optional[str] = None
    api_url: Optional[str] = None
    
    # Bibliographic information
    title: Optional[str] = None
    creators: List[str] = None
    publication_date: Optional[str] = None
    publisher: Optional[str] = None
    place_of_publication: Optional[str] = None
    
    # Article-specific
    newspaper_title: Optional[str] = None
    page: Optional[str] = None
    edition: Optional[str] = None
    
    # People-specific
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    occupation: List[str] = None
    
    # List-specific
    list_creator: Optional[str] = None
    list_description: Optional[str] = None
    
    # Technical metadata
    access_date: Optional[datetime] = None
    format_type: Optional[str] = None
    language: Optional[str] = None
    
    # Raw data for fallback
    raw_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.creators is None:
            object.__setattr__(self, 'creators', [])
        if self.occupation is None:
            object.__setattr__(self, 'occupation', [])
        if self.access_date is None:
            object.__setattr__(self, 'access_date', datetime.now())
    
    @property
    def canonical_pid(self) -> Optional[str]:
        """Get the canonical persistent identifier."""
        if self.pid:
            return self.pid
        elif self.trove_url:
            return self._extract_pid_from_url(self.trove_url)
        return None
        
    @property
    def display_title(self) -> str:
        """Get displayable title."""
        return self.title or f"Untitled {self.record_type.value}"
        
    @property
    def primary_creator(self) -> Optional[str]:
        """Get primary creator/author."""
        return self.creators[0] if self.creators else None
        
    def _extract_pid_from_url(self, url: str) -> Optional[str]:
        """Extract PID from Trove URL."""
        # Implementation matches PIDExtractor patterns
        patterns = [
            r'https?://nla\.gov\.au/(nla\.[^/?]+)',
            r'https?://trove\.nla\.gov\.au/ndp/del/article/(\d+)',
            r'https?://api\.trove\.nla\.gov\.au/v3/work/(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None