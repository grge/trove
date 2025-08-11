# Stage 5 - Citations Design Document

## Overview

Stage 5 implements comprehensive citation support for Trove resources, including PID (Persistent Identifier) extraction, URL/PID resolution, and citation formatting in BibTeX and CSL-JSON formats. This stage provides researchers with proper citation tools for academic and reference use.

## Citation Requirements Analysis

Based on the API documentation review, Trove records contain various identifier patterns:

- **Work Records**: URLs like `https://nla.gov.au/nla.obj-123456789` and internal IDs
- **Newspaper Articles**: URLs like `https://nla.gov.au/nla.news-article18341291`
- **People Records**: Internal IDs and contributor URLs
- **Lists**: User-generated list IDs
- **Gazette Articles**: URLs similar to newspaper articles
- **Title Records**: Title-specific identifiers

## Architecture Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Citation Interface                             │
├─────────────────────────────────────────────────────────────────────┤
│  CitationRef │ PIDResolver │ BibTeXFormatter │ CSLJSONFormatter     │
├──────────────┼─────────────┼─────────────────┼─────────────────────┤
│              PID Extraction Patterns & Mapping                     │
├─────────────────────────────────────────────────────────────────────┤
│                Resource Layer (Stage 3)                            │
└─────────────────────────────────────────────────────────────────────┘
```

## Detailed Component Design

### 1. Citation Reference Types (`trove/citations/types.py`)

```python
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from datetime import datetime

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
            self.creators = []
        if self.occupation is None:
            self.occupation = []
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
        import re
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
```

### 2. PID Extraction (`trove/citations/extraction.py`)

```python
import re
from typing import Dict, Any, Optional, List, Pattern
from .types import CitationRef, RecordType

class PIDExtractor:
    """Extracts PIDs and bibliographic information from Trove records."""
    
    # URL patterns for PID extraction
    PID_PATTERNS = [
        # Work records
        (RecordType.WORK, re.compile(r'https?://nla\.gov\.au/(nla\.obj-\d+)')),
        (RecordType.WORK, re.compile(r'https?://nla\.gov\.au/(nla\.pic-\w+)')), 
        (RecordType.WORK, re.compile(r'https?://nla\.gov\.au/(nla\.mus-\w+)')),
        (RecordType.WORK, re.compile(r'https?://nla\.gov\.au/(nla\.map-\w+)')),
        
        # Newspaper articles
        (RecordType.ARTICLE, re.compile(r'https?://nla\.gov\.au/(nla\.news-article\d+)')),
        (RecordType.ARTICLE, re.compile(r'https?://trove\.nla\.gov\.au/ndp/del/article/(\d+)')),
        
        # API URLs
        (RecordType.WORK, re.compile(r'https?://api\.trove\.nla\.gov\.au/v3/work/(\d+)')),
        (RecordType.ARTICLE, re.compile(r'https?://api\.trove\.nla\.gov\.au/v3/newspaper/(\d+)')),
        (RecordType.ARTICLE, re.compile(r'https?://api\.trove\.nla\.gov\.au/v3/gazette/(\d+)')),
        (RecordType.PEOPLE, re.compile(r'https?://api\.trove\.nla\.gov\.au/v3/people/(\d+)')),
        (RecordType.LIST, re.compile(r'https?://api\.trove\.nla\.gov\.au/v3/list/(\d+)')),
    ]
    
    def extract_from_work(self, work_data: Dict[str, Any]) -> CitationRef:
        """Extract citation information from work record."""
        return CitationRef(
            record_type=RecordType.WORK,
            record_id=str(work_data.get('id', '')),
            pid=self._extract_work_pid(work_data),
            trove_url=work_data.get('troveUrl'),
            api_url=work_data.get('url'),
            title=self._clean_title(work_data.get('title', '')),
            creators=self._extract_creators(work_data.get('contributor', [])),
            publication_date=self._normalize_date(work_data.get('issued')),
            publisher=self._extract_publisher(work_data),
            place_of_publication=self._extract_place_of_publication(work_data),
            format_type=self._extract_format(work_data),
            language=self._extract_language(work_data),
            raw_data=work_data
        )
        
    def extract_from_article(self, article_data: Dict[str, Any]) -> CitationRef:
        """Extract citation information from newspaper/gazette article."""
        title_info = article_data.get('title', {})
        newspaper_title = title_info.get('title') if isinstance(title_info, dict) else str(title_info)
        
        return CitationRef(
            record_type=RecordType.ARTICLE,
            record_id=str(article_data.get('id', '')),
            pid=self._extract_article_pid(article_data),
            trove_url=article_data.get('troveUrl'),
            api_url=article_data.get('url'),
            title=self._clean_title(article_data.get('heading', '')),
            publication_date=article_data.get('date'),
            newspaper_title=newspaper_title,
            page=article_data.get('page'),
            edition=article_data.get('edition'),
            format_type='newspaper article',
            raw_data=article_data
        )
        
    def extract_from_people(self, people_data: Dict[str, Any]) -> CitationRef:
        """Extract citation information from people/organization record."""
        return CitationRef(
            record_type=RecordType.PEOPLE,
            record_id=str(people_data.get('id', '')),
            trove_url=people_data.get('troveUrl'),
            api_url=people_data.get('url'),
            title=people_data.get('primaryName') or people_data.get('primaryDisplayName'),
            birth_date=self._extract_birth_date(people_data),
            death_date=self._extract_death_date(people_data),
            occupation=self._extract_occupation(people_data),
            format_type=people_data.get('type', 'person'),
            raw_data=people_data
        )
        
    def extract_from_list(self, list_data: Dict[str, Any]) -> CitationRef:
        """Extract citation information from list record.""" 
        return CitationRef(
            record_type=RecordType.LIST,
            record_id=str(list_data.get('id', '')),
            trove_url=list_data.get('troveUrl'),
            api_url=list_data.get('url'),
            title=list_data.get('title'),
            list_creator=list_data.get('creator') or list_data.get('by'),
            list_description=list_data.get('description'),
            publication_date=self._extract_list_date(list_data),
            format_type='user list',
            raw_data=list_data
        )
        
    def extract_pid_from_url(self, url: str) -> Optional[tuple[RecordType, str]]:
        """Extract PID and record type from URL."""
        for record_type, pattern in self.PID_PATTERNS:
            match = pattern.search(url)
            if match:
                return record_type, match.group(1)
        return None
        
    def _extract_work_pid(self, work_data: Dict[str, Any]) -> Optional[str]:
        """Extract PID from work record."""
        # Check identifier field
        identifiers = work_data.get('identifier', [])
        if isinstance(identifiers, dict):
            identifiers = [identifiers]
            
        for identifier in identifiers:
            if isinstance(identifier, dict):
                value = identifier.get('value', '')
                if 'nla.obj-' in value or 'nla.pic-' in value:
                    return value
                    
        # Check troveUrl
        trove_url = work_data.get('troveUrl')
        if trove_url:
            result = self.extract_pid_from_url(trove_url)
            if result:
                return result[1]
                
        return None
        
    def _extract_article_pid(self, article_data: Dict[str, Any]) -> Optional[str]:
        """Extract PID from article record."""
        # Check identifier field
        identifier = article_data.get('identifier')
        if identifier and 'nla.news-article' in identifier:
            return identifier.split('/')[-1]  # Extract from full URL
            
        # Fallback to ID with prefix
        article_id = article_data.get('id')
        if article_id:
            return f"nla.news-article{article_id}"
            
        return None
        
    def _clean_title(self, title: str) -> str:
        """Clean and normalize title text."""
        if not title:
            return ""
            
        # Remove excessive whitespace
        title = re.sub(r'\s+', ' ', title.strip())
        
        # Remove trailing punctuation that's not meaningful
        title = re.sub(r'\s*[,;]\s*$', '', title)
        
        return title
        
    def _extract_creators(self, contributor_data) -> List[str]:
        """Extract creator names from contributor field."""
        if not contributor_data:
            return []
            
        if isinstance(contributor_data, str):
            return [contributor_data]
        elif isinstance(contributor_data, list):
            return [str(c) for c in contributor_data if c]
        else:
            return []
            
    def _normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        """Normalize date strings for citations."""
        if not date_str:
            return None
            
        # Handle date ranges (e.g., "2001-2011")
        if '-' in date_str and len(date_str) > 4:
            # For ranges, use the start date
            return date_str.split('-')[0]
            
        # Extract year from various formats
        year_match = re.search(r'(\d{4})', date_str)
        if year_match:
            return year_match.group(1)
            
        return date_str
        
    def _extract_publisher(self, work_data: Dict[str, Any]) -> Optional[str]:
        """Extract publisher information.""" 
        # Check various fields where publisher info might be
        for field in ['publisher', 'contributor', 'isPartOf']:
            value = work_data.get(field)
            if value and isinstance(value, (str, list)):
                if isinstance(value, list) and value:
                    return str(value[0])
                elif isinstance(value, str):
                    return value
        return None
        
    def _extract_place_of_publication(self, work_data: Dict[str, Any]) -> Optional[str]:
        """Extract place of publication."""
        places = work_data.get('placeOfPublication', [])
        if isinstance(places, list) and places:
            return places[0]
        elif isinstance(places, str):
            return places
        return None
        
    def _extract_format(self, work_data: Dict[str, Any]) -> Optional[str]:
        """Extract format information."""
        format_info = work_data.get('format', work_data.get('type'))
        if isinstance(format_info, list) and format_info:
            return format_info[0]
        elif isinstance(format_info, str):
            return format_info
        return None
        
    def _extract_language(self, work_data: Dict[str, Any]) -> Optional[str]:
        """Extract language information."""
        language_info = work_data.get('language', [])
        if isinstance(language_info, list) and language_info:
            lang = language_info[0]
            if isinstance(lang, dict):
                return lang.get('name') or lang.get('code')
            return str(lang)
        elif isinstance(language_info, dict):
            return language_info.get('name') or language_info.get('code')
        return None
        
    def _extract_birth_date(self, people_data: Dict[str, Any]) -> Optional[str]:
        """Extract birth/establishment date from people record."""
        # Implementation depends on actual data structure
        return None  # Placeholder
        
    def _extract_death_date(self, people_data: Dict[str, Any]) -> Optional[str]:
        """Extract death/dissolution date from people record."""
        # Implementation depends on actual data structure  
        return None  # Placeholder
        
    def _extract_occupation(self, people_data: Dict[str, Any]) -> List[str]:
        """Extract occupation information."""
        occupations = people_data.get('occupation', [])
        if isinstance(occupations, list):
            return [str(o) for o in occupations if o]
        elif isinstance(occupations, str):
            return [occupations]
        return []
        
    def _extract_list_date(self, list_data: Dict[str, Any]) -> Optional[str]:
        """Extract creation date from list record."""
        date_info = list_data.get('date', {})
        if isinstance(date_info, dict):
            return date_info.get('created')
        return None
```

### 3. PID Resolution (`trove/citations/resolution.py`)

```python
from typing import Optional, Dict, Any, Union
import re
from ..resources import ResourceFactory
from ..exceptions import ResourceNotFoundError, TroveAPIError
from .types import CitationRef, RecordType
from .extraction import PIDExtractor

class PIDResolver:
    """Resolves PIDs and URLs to CitationRef objects."""
    
    def __init__(self, resource_factory: ResourceFactory):
        self.resource_factory = resource_factory
        self.extractor = PIDExtractor()
        
    def resolve(self, identifier: Union[str, CitationRef]) -> Optional[CitationRef]:
        """Resolve a PID, URL, or existing CitationRef to complete citation.
        
        Args:
            identifier: PID, URL string, or existing CitationRef
            
        Returns:
            Complete CitationRef with all available information
            
        Examples:
            resolver.resolve("nla.obj-123456789")
            resolver.resolve("https://nla.gov.au/nla.news-article18341291")
            resolver.resolve("https://trove.nla.gov.au/work/123456")
            resolver.resolve(existing_citation_ref)  # Enriches with latest data
        """
        if isinstance(identifier, CitationRef):
            return self._enrich_citation_ref(identifier)
        
        # Try to parse as URL first
        url_result = self._resolve_url(identifier)
        if url_result:
            return url_result
            
        # Try to parse as PID
        pid_result = self._resolve_pid(identifier)
        if pid_result:
            return pid_result
            
        # Try search fallback
        return self._search_fallback(identifier)
        
    def _resolve_url(self, url: str) -> Optional[CitationRef]:
        """Resolve URL to citation reference."""
        parsed = self.extractor.extract_pid_from_url(url)
        if not parsed:
            return None
            
        record_type, record_id = parsed
        
        try:
            if record_type == RecordType.WORK:
                work = self.resource_factory.get_work_resource().get(record_id)
                return self.extractor.extract_from_work(work)
                
            elif record_type == RecordType.ARTICLE:
                # Determine if newspaper or gazette
                if 'gazette' in url.lower():
                    article = self.resource_factory.get_gazette_resource().get(record_id)
                else:
                    article = self.resource_factory.get_newspaper_resource().get(record_id)
                return self.extractor.extract_from_article(article)
                
            elif record_type == RecordType.PEOPLE:
                people = self.resource_factory.get_people_resource().get(record_id)
                return self.extractor.extract_from_people(people)
                
            elif record_type == RecordType.LIST:
                list_data = self.resource_factory.get_list_resource().get(record_id)
                return self.extractor.extract_from_list(list_data)
                
        except ResourceNotFoundError:
            return None
        except TroveAPIError:
            return None
            
        return None
        
    def _resolve_pid(self, pid: str) -> Optional[CitationRef]:
        """Resolve PID to citation reference."""
        # Classify PID type based on pattern
        if 'nla.obj-' in pid or 'nla.pic-' in pid or 'nla.mus-' in pid or 'nla.map-' in pid:
            return self._resolve_work_pid(pid)
        elif 'nla.news-article' in pid:
            return self._resolve_article_pid(pid)
        elif pid.isdigit():
            # Bare numeric ID - try different record types
            return self._resolve_numeric_id(pid)
            
        return None
        
    def _resolve_work_pid(self, pid: str) -> Optional[CitationRef]:
        """Resolve work PID by searching.""" 
        # Use search to find work with this PID
        search_resource = self.resource_factory._transport
        # This would require implementing search by identifier
        # For now, return None and rely on search fallback
        return None
        
    def _resolve_article_pid(self, pid: str) -> Optional[CitationRef]:
        """Resolve article PID."""
        # Extract numeric ID from PID
        match = re.search(r'(\d+)', pid)
        if match:
            article_id = match.group(1)
            try:
                article = self.resource_factory.get_newspaper_resource().get(article_id)
                return self.extractor.extract_from_article(article)
            except ResourceNotFoundError:
                # Try gazette
                try:
                    article = self.resource_factory.get_gazette_resource().get(article_id)
                    return self.extractor.extract_from_article(article)
                except ResourceNotFoundError:
                    pass
        return None
        
    def _resolve_numeric_id(self, id_str: str) -> Optional[CitationRef]:
        """Try to resolve numeric ID across different resource types."""
        # Try work first (most common)
        try:
            work = self.resource_factory.get_work_resource().get(id_str)
            return self.extractor.extract_from_work(work)
        except ResourceNotFoundError:
            pass
            
        # Try article
        try:
            article = self.resource_factory.get_newspaper_resource().get(id_str)
            return self.extractor.extract_from_article(article)
        except ResourceNotFoundError:
            pass
            
        # Try people
        try:
            people = self.resource_factory.get_people_resource().get(id_str)
            return self.extractor.extract_from_people(people)
        except ResourceNotFoundError:
            pass
            
        # Try list
        try:
            list_data = self.resource_factory.get_list_resource().get(id_str)
            return self.extractor.extract_from_list(list_data)
        except ResourceNotFoundError:
            pass
            
        return None
        
    def _search_fallback(self, identifier: str) -> Optional[CitationRef]:
        """Use search as fallback to find records."""
        # This is a simplified implementation
        # In practice, would use the search API to find records
        # that match the identifier in title or other fields
        return None
        
    def _enrich_citation_ref(self, citation_ref: CitationRef) -> CitationRef:
        """Enrich existing citation with latest data."""
        if not citation_ref.record_id:
            return citation_ref
            
        try:
            if citation_ref.record_type == RecordType.WORK:
                work = self.resource_factory.get_work_resource().get(citation_ref.record_id)
                return self.extractor.extract_from_work(work)
            elif citation_ref.record_type == RecordType.ARTICLE:
                article = self.resource_factory.get_newspaper_resource().get(citation_ref.record_id)
                return self.extractor.extract_from_article(article)
            elif citation_ref.record_type == RecordType.PEOPLE:
                people = self.resource_factory.get_people_resource().get(citation_ref.record_id)
                return self.extractor.extract_from_people(people)
            elif citation_ref.record_type == RecordType.LIST:
                list_data = self.resource_factory.get_list_resource().get(citation_ref.record_id)
                return self.extractor.extract_from_list(list_data)
        except (ResourceNotFoundError, TroveAPIError):
            pass
            
        return citation_ref
        
    def bulk_resolve(self, identifiers: List[Union[str, CitationRef]]) -> Dict[str, Optional[CitationRef]]:
        """Resolve multiple identifiers efficiently."""
        results = {}
        
        for identifier in identifiers:
            key = str(identifier) if isinstance(identifier, str) else identifier.record_id
            try:
                results[key] = self.resolve(identifier)
            except Exception:
                results[key] = None
                
        return results
```

### 4. Citation Formatters (`trove/citations/formatters.py`)

```python
from typing import Dict, Any, List, Optional
from datetime import datetime
from .types import CitationRef, RecordType

class BibTeXFormatter:
    """Format citations as BibTeX entries."""
    
    def format(self, citation: CitationRef) -> str:
        """Format citation as BibTeX entry.
        
        Args:
            citation: Citation reference to format
            
        Returns:
            BibTeX formatted string
        """
        entry_type = self._determine_bibtex_type(citation)
        entry_key = self._generate_entry_key(citation)
        
        fields = self._extract_bibtex_fields(citation)
        
        # Build BibTeX entry
        lines = [f"@{entry_type}{{{entry_key},"]
        
        for key, value in fields.items():
            if value:
                # Escape special characters
                escaped_value = self._escape_bibtex(str(value))
                lines.append(f"  {key} = {{{escaped_value}}},")
                
        # Remove trailing comma and close
        if lines[-1].endswith(','):
            lines[-1] = lines[-1][:-1]
        lines.append("}")
        
        return "\n".join(lines)
        
    def _determine_bibtex_type(self, citation: CitationRef) -> str:
        """Determine appropriate BibTeX entry type."""
        if citation.record_type == RecordType.WORK:
            format_type = citation.format_type or ""
            if 'book' in format_type.lower():
                return 'book'
            elif 'journal' in format_type.lower() or 'article' in format_type.lower():
                return 'article'
            elif 'map' in format_type.lower():
                return 'misc'  # No standard map type
            else:
                return 'misc'
        elif citation.record_type == RecordType.ARTICLE:
            return 'article'
        elif citation.record_type == RecordType.PEOPLE:
            return 'misc'  # No standard person type
        elif citation.record_type == RecordType.LIST:
            return 'misc'
        else:
            return 'misc'
            
    def _generate_entry_key(self, citation: CitationRef) -> str:
        """Generate BibTeX entry key."""
        parts = []
        
        # Add primary creator surname
        if citation.primary_creator:
            # Extract surname (simplified)
            creator_parts = citation.primary_creator.split(',')
            if creator_parts:
                surname = creator_parts[0].strip()
                # Clean and take first word
                surname = ''.join(c for c in surname if c.isalnum())
                if surname:
                    parts.append(surname)
                    
        # Add year
        if citation.publication_date:
            year_match = re.search(r'(\d{4})', citation.publication_date)
            if year_match:
                parts.append(year_match.group(1))
                
        # Add record ID as fallback
        if citation.record_id:
            parts.append(citation.record_id[:8])  # First 8 chars
            
        # Fallback
        if not parts:
            parts.append('trove')
            
        return '_'.join(parts)
        
    def _extract_bibtex_fields(self, citation: CitationRef) -> Dict[str, Optional[str]]:
        """Extract BibTeX fields from citation."""
        fields = {}
        
        # Common fields
        fields['title'] = citation.title
        fields['year'] = self._extract_year(citation.publication_date)
        fields['url'] = citation.trove_url or citation.api_url
        fields['urldate'] = citation.access_date.strftime('%Y-%m-%d') if citation.access_date else None
        fields['note'] = f"Retrieved from Trove, National Library of Australia"
        
        # Authors/editors
        if citation.creators:
            if len(citation.creators) == 1:
                fields['author'] = citation.creators[0]
            else:
                fields['author'] = ' and '.join(citation.creators)
                
        # Type-specific fields
        if citation.record_type == RecordType.WORK:
            fields['publisher'] = citation.publisher
            fields['address'] = citation.place_of_publication
            if citation.language:
                fields['language'] = citation.language
                
        elif citation.record_type == RecordType.ARTICLE:
            fields['journal'] = citation.newspaper_title
            if citation.page:
                fields['pages'] = citation.page
            if citation.edition:
                fields['note'] = f"{fields.get('note', '')}, {citation.edition}".strip(', ')
                
        elif citation.record_type == RecordType.PEOPLE:
            if citation.birth_date or citation.death_date:
                dates = []
                if citation.birth_date:
                    dates.append(f"b. {citation.birth_date}")
                if citation.death_date:
                    dates.append(f"d. {citation.death_date}")
                fields['note'] = f"{fields.get('note', '')}, {', '.join(dates)}".strip(', ')
                
        elif citation.record_type == RecordType.LIST:
            if citation.list_creator:
                fields['author'] = citation.list_creator
            if citation.list_description:
                fields['abstract'] = citation.list_description
                
        return fields
        
    def _extract_year(self, date_str: Optional[str]) -> Optional[str]:
        """Extract year from date string.""" 
        if not date_str:
            return None
        year_match = re.search(r'(\d{4})', date_str)
        return year_match.group(1) if year_match else None
        
    def _escape_bibtex(self, text: str) -> str:
        """Escape special BibTeX characters."""
        # Basic escaping - expand as needed
        replacements = {
            '{': '\\{',
            '}': '\\}',
            '\\': '\\textbackslash{}',
            '%': '\\%',
            '$': '\\$',
            '&': '\\&',
            '#': '\\#',
            '^': '\\textasciicircum{}',
            '_': '\\_',
            '~': '\\textasciitilde{}'
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
            
        return text

class CSLJSONFormatter:
    """Format citations as CSL-JSON."""
    
    def format(self, citation: CitationRef) -> Dict[str, Any]:
        """Format citation as CSL-JSON object.
        
        Args:
            citation: Citation reference to format
            
        Returns:
            CSL-JSON formatted dictionary
        """
        csl_item = {
            'id': citation.canonical_pid or citation.record_id,
            'type': self._determine_csl_type(citation),
        }
        
        # Add title
        if citation.title:
            csl_item['title'] = citation.title
            
        # Add authors
        if citation.creators:
            csl_item['author'] = [
                self._parse_author_name(creator) 
                for creator in citation.creators
            ]
            
        # Add dates
        if citation.publication_date:
            csl_item['issued'] = self._parse_csl_date(citation.publication_date)
            
        if citation.access_date:
            csl_item['accessed'] = self._parse_csl_date(citation.access_date.isoformat()[:10])
            
        # Add URLs
        if citation.trove_url:
            csl_item['URL'] = citation.trove_url
        elif citation.api_url:
            csl_item['URL'] = citation.api_url
            
        # Type-specific fields
        if citation.record_type == RecordType.WORK:
            if citation.publisher:
                csl_item['publisher'] = citation.publisher
            if citation.place_of_publication:
                csl_item['publisher-place'] = citation.place_of_publication
            if citation.language:
                csl_item['language'] = citation.language
                
        elif citation.record_type == RecordType.ARTICLE:
            if citation.newspaper_title:
                csl_item['container-title'] = citation.newspaper_title
            if citation.page:
                csl_item['page'] = citation.page
            if citation.edition:
                csl_item['edition'] = citation.edition
                
        elif citation.record_type == RecordType.LIST:
            if citation.list_creator:
                csl_item['author'] = [self._parse_author_name(citation.list_creator)]
            if citation.list_description:
                csl_item['abstract'] = citation.list_description
                
        # Add source note
        csl_item['note'] = 'Retrieved from Trove, National Library of Australia'
        
        return csl_item
        
    def _determine_csl_type(self, citation: CitationRef) -> str:
        """Determine CSL-JSON item type."""
        if citation.record_type == RecordType.WORK:
            format_type = citation.format_type or ""
            if 'book' in format_type.lower():
                return 'book'
            elif 'map' in format_type.lower():
                return 'map'
            elif 'article' in format_type.lower() or 'journal' in format_type.lower():
                return 'article-journal'
            else:
                return 'document'
        elif citation.record_type == RecordType.ARTICLE:
            return 'article-newspaper'
        elif citation.record_type == RecordType.PEOPLE:
            return 'personal_communication'
        elif citation.record_type == RecordType.LIST:
            return 'dataset'
        else:
            return 'document'
            
    def _parse_author_name(self, name_str: str) -> Dict[str, str]:
        """Parse author name into CSL format."""
        # Simple parsing - could be enhanced
        if ',' in name_str:
            parts = name_str.split(',', 1)
            return {
                'family': parts[0].strip(),
                'given': parts[1].strip() if len(parts) > 1 else ''
            }
        else:
            # Assume "First Last" format
            parts = name_str.strip().rsplit(' ', 1)
            if len(parts) == 2:
                return {
                    'given': parts[0],
                    'family': parts[1]
                }
            else:
                return {'literal': name_str}
                
    def _parse_csl_date(self, date_str: str) -> Dict[str, Any]:
        """Parse date string into CSL date format."""
        if not date_str:
            return {}
            
        # Extract year
        year_match = re.search(r'(\d{4})', date_str)
        if year_match:
            year = int(year_match.group(1))
            
            # Try to extract month and day for full dates
            if '-' in date_str:
                try:
                    # Try parsing ISO format
                    date_obj = datetime.fromisoformat(date_str[:10])
                    return {
                        'date-parts': [[date_obj.year, date_obj.month, date_obj.day]]
                    }
                except:
                    pass
                    
            return {'date-parts': [[year]]}
            
        return {}

class CitationFormatter:
    """Main citation formatter interface."""
    
    def __init__(self):
        self.bibtex = BibTeXFormatter()
        self.csl_json = CSLJSONFormatter()
        
    def format_bibtex(self, citation: CitationRef) -> str:
        """Format citation as BibTeX."""
        return self.bibtex.format(citation)
        
    def format_csl_json(self, citation: CitationRef) -> Dict[str, Any]:
        """Format citation as CSL-JSON."""
        return self.csl_json.format(citation)
        
    def format_multiple_bibtex(self, citations: List[CitationRef]) -> str:
        """Format multiple citations as BibTeX bibliography."""
        entries = [self.bibtex.format(citation) for citation in citations]
        return '\n\n'.join(entries)
        
    def format_multiple_csl_json(self, citations: List[CitationRef]) -> List[Dict[str, Any]]:
        """Format multiple citations as CSL-JSON array."""
        return [self.csl_json.format(citation) for citation in citations]
```

### 5. Main Citation Interface (`trove/citations/__init__.py`)

```python
from .types import CitationRef, RecordType
from .extraction import PIDExtractor
from .resolution import PIDResolver
from .formatters import CitationFormatter, BibTeXFormatter, CSLJSONFormatter
from ..resources import ResourceFactory

class CitationManager:
    """Main interface for citation functionality."""
    
    def __init__(self, resource_factory: ResourceFactory):
        self.resource_factory = resource_factory
        self.extractor = PIDExtractor()
        self.resolver = PIDResolver(resource_factory)
        self.formatter = CitationFormatter()
        
    def extract_from_record(self, record_data: Dict[str, Any], record_type: RecordType) -> CitationRef:
        """Extract citation from raw record data.""" 
        if record_type == RecordType.WORK:
            return self.extractor.extract_from_work(record_data)
        elif record_type == RecordType.ARTICLE:
            return self.extractor.extract_from_article(record_data)
        elif record_type == RecordType.PEOPLE:
            return self.extractor.extract_from_people(record_data)
        elif record_type == RecordType.LIST:
            return self.extractor.extract_from_list(record_data)
        else:
            raise ValueError(f"Unsupported record type: {record_type}")
            
    def resolve_identifier(self, identifier: str) -> Optional[CitationRef]:
        """Resolve PID or URL to citation reference."""
        return self.resolver.resolve(identifier)
        
    def cite_bibtex(self, identifier_or_citation: Union[str, CitationRef]) -> str:
        """Generate BibTeX citation."""
        if isinstance(identifier_or_citation, str):
            citation = self.resolver.resolve(identifier_or_citation)
            if not citation:
                raise ValueError(f"Could not resolve identifier: {identifier_or_citation}")
        else:
            citation = identifier_or_citation
            
        return self.formatter.format_bibtex(citation)
        
    def cite_csl_json(self, identifier_or_citation: Union[str, CitationRef]) -> Dict[str, Any]:
        """Generate CSL-JSON citation."""
        if isinstance(identifier_or_citation, str):
            citation = self.resolver.resolve(identifier_or_citation)
            if not citation:
                raise ValueError(f"Could not resolve identifier: {identifier_or_citation}")
        else:
            citation = identifier_or_citation
            
        return self.formatter.format_csl_json(citation)
        
    def bibliography_bibtex(self, identifiers_or_citations: List[Union[str, CitationRef]]) -> str:
        """Generate BibTeX bibliography for multiple items."""
        citations = []
        
        for item in identifiers_or_citations:
            if isinstance(item, str):
                citation = self.resolver.resolve(item)
                if citation:
                    citations.append(citation)
            else:
                citations.append(item)
                
        return self.formatter.format_multiple_bibtex(citations)
        
    def bibliography_csl_json(self, identifiers_or_citations: List[Union[str, CitationRef]]) -> List[Dict[str, Any]]:
        """Generate CSL-JSON bibliography for multiple items."""
        citations = []
        
        for item in identifiers_or_citations:
            if isinstance(item, str):
                citation = self.resolver.resolve(item)
                if citation:
                    citations.append(citation)
            else:
                citations.append(item)
                
        return self.formatter.format_multiple_csl_json(citations)

# Convenience exports
__all__ = [
    'CitationManager',
    'CitationRef', 
    'RecordType',
    'PIDExtractor',
    'PIDResolver',
    'CitationFormatter',
    'BibTeXFormatter',
    'CSLJSONFormatter'
]
```

## Testing Strategy

### Unit Tests

```python
# test_citations.py
import pytest
from trove.citations import CitationManager, CitationRef, RecordType
from trove.citations.extraction import PIDExtractor
from trove.citations.formatters import BibTeXFormatter, CSLJSONFormatter

def test_pid_extraction():
    """Test PID extraction from various URL formats."""
    extractor = PIDExtractor()
    
    test_cases = [
        ("https://nla.gov.au/nla.obj-123456789", (RecordType.WORK, "nla.obj-123456789")),
        ("https://nla.gov.au/nla.news-article18341291", (RecordType.ARTICLE, "nla.news-article18341291")),
        ("https://trove.nla.gov.au/ndp/del/article/18341291", (RecordType.ARTICLE, "18341291")),
        ("https://api.trove.nla.gov.au/v3/work/123456", (RecordType.WORK, "123456")),
    ]
    
    for url, expected in test_cases:
        result = extractor.extract_pid_from_url(url)
        assert result == expected

def test_work_citation_extraction():
    """Test citation extraction from work record."""
    extractor = PIDExtractor()
    
    work_data = {
        'id': '123456',
        'title': 'Australian History: A Complete Guide',
        'contributor': ['Smith, John', 'Jones, Mary'],
        'issued': '2020',
        'troveUrl': 'https://trove.nla.gov.au/work/123456',
        'identifier': [{'value': 'nla.obj-123456789'}]
    }
    
    citation = extractor.extract_from_work(work_data)
    
    assert citation.record_type == RecordType.WORK
    assert citation.record_id == '123456'
    assert citation.title == 'Australian History: A Complete Guide'
    assert citation.creators == ['Smith, John', 'Jones, Mary']
    assert citation.publication_date == '2020'
    assert citation.pid == 'nla.obj-123456789'

def test_bibtex_formatting():
    """Test BibTeX citation formatting."""
    citation = CitationRef(
        record_type=RecordType.WORK,
        record_id='123456',
        title='Australian Poetry Anthology',
        creators=['Smith, John'],
        publication_date='2020',
        publisher='University Press',
        place_of_publication='Melbourne',
        trove_url='https://trove.nla.gov.au/work/123456'
    )
    
    formatter = BibTeXFormatter()
    bibtex = formatter.format(citation)
    
    assert '@book{' in bibtex
    assert 'title = {Australian Poetry Anthology}' in bibtex
    assert 'author = {Smith, John}' in bibtex
    assert 'year = {2020}' in bibtex
    assert 'publisher = {University Press}' in bibtex

def test_csl_json_formatting():
    """Test CSL-JSON citation formatting."""
    citation = CitationRef(
        record_type=RecordType.ARTICLE,
        record_id='18341291',
        title='Federation Celebrations in Sydney',
        newspaper_title='The Sydney Morning Herald',
        publication_date='1901-01-01',
        page='1',
        trove_url='https://nla.gov.au/nla.news-article18341291'
    )
    
    formatter = CSLJSONFormatter()
    csl_json = formatter.format(citation)
    
    assert csl_json['type'] == 'article-newspaper'
    assert csl_json['title'] == 'Federation Celebrations in Sydney'
    assert csl_json['container-title'] == 'The Sydney Morning Herald'
    assert csl_json['issued']['date-parts'] == [[1901, 1, 1]]

def test_title_cleaning():
    """Test title cleaning and normalization."""
    extractor = PIDExtractor()
    
    test_cases = [
        ("  Title with   spaces  ", "Title with spaces"),
        ("Title with trailing comma,", "Title with trailing comma"),
        ("Title\twith\ttabs", "Title with tabs"),
        ("", "")
    ]
    
    for input_title, expected in test_cases:
        result = extractor._clean_title(input_title)
        assert result == expected

def test_date_normalization():
    """Test date normalization for citations."""
    extractor = PIDExtractor()
    
    test_cases = [
        ("2020", "2020"),
        ("2001-2011", "2001"),  # Range -> start date
        ("Published in 1995", "1995"),
        ("c. 1890", "1890"),
        (None, None)
    ]
    
    for input_date, expected in test_cases:
        result = extractor._normalize_date(input_date)
        assert result == expected
```

### Integration Tests

```python
# test_citations_integration.py
import pytest
import os
from trove import TroveClient
from trove.citations import CitationManager

@pytest.mark.integration
class TestCitationsIntegration:
    """Integration tests for citations with real API."""
    
    @pytest.fixture(scope="class")  
    def citation_manager(self):
        api_key = os.environ.get('TROVE_API_KEY')
        if not api_key:
            pytest.skip("TROVE_API_KEY not set")
            
        client = TroveClient.from_api_key(api_key, rate_limit=1.0)
        return CitationManager(client.resources)
    
    def test_work_citation_real_data(self, citation_manager):
        """Test work citation with real API data."""
        work_id = "123456"  # Replace with actual work ID
        
        try:
            work = citation_manager.resource_factory.get_work_resource().get(work_id)
            citation = citation_manager.extract_from_record(work, RecordType.WORK)
            
            assert citation.record_id == work_id
            assert citation.title is not None
            assert len(citation.title) > 0
            
            # Test BibTeX generation
            bibtex = citation_manager.cite_bibtex(citation)
            assert '@' in bibtex
            assert citation.title in bibtex
            
            # Test CSL-JSON generation
            csl_json = citation_manager.cite_csl_json(citation)
            assert 'title' in csl_json
            assert csl_json['title'] == citation.title
            
        except ResourceNotFoundError:
            pytest.skip(f"Work {work_id} not found")
            
    def test_article_citation_real_data(self, citation_manager):
        """Test article citation with real API data."""
        article_id = "18341291"  # Known article from API docs
        
        try:
            article = citation_manager.resource_factory.get_newspaper_resource().get(article_id)
            citation = citation_manager.extract_from_record(article, RecordType.ARTICLE)
            
            assert citation.record_id == article_id
            assert citation.title is not None or citation.newspaper_title is not None
            
            # Test BibTeX generation
            bibtex = citation_manager.cite_bibtex(citation)
            assert '@article' in bibtex
            
            # Test CSL-JSON generation
            csl_json = citation_manager.cite_csl_json(citation)
            assert csl_json['type'] == 'article-newspaper'
            
        except ResourceNotFoundError:
            pytest.skip(f"Article {article_id} not found")
            
    def test_pid_resolution_real_data(self, citation_manager):
        """Test PID resolution with real data.""" 
        test_identifiers = [
            "nla.obj-123456789",
            "https://nla.gov.au/nla.news-article18341291",
            "https://trove.nla.gov.au/work/123456"
        ]
        
        for identifier in test_identifiers:
            try:
                citation = citation_manager.resolve_identifier(identifier)
                if citation:  # May be None if identifier doesn't exist
                    assert citation.record_id is not None
                    assert citation.record_type is not None
            except Exception as e:
                # Log but don't fail - identifiers may not exist
                print(f"Could not resolve {identifier}: {e}")
                
    def test_bibliography_generation_real_data(self, citation_manager):
        """Test bibliography generation with multiple items."""
        # Use search to find some real items
        client = TroveClient.from_env()
        search_result = (client.search()
                        .text("Australian poetry")
                        .in_("book")
                        .page_size(3)
                        .first_page())
                        
        citations = []
        for record in search_result.all_records():
            try:
                citation = citation_manager.extract_from_record(record.data, RecordType.WORK)
                citations.append(citation)
            except:
                continue  # Skip problematic records
                
        if citations:
            # Test BibTeX bibliography
            bibtex_bib = citation_manager.bibliography_bibtex(citations)
            assert bibtex_bib.count('@') == len(citations)
            
            # Test CSL-JSON bibliography
            csl_json_bib = citation_manager.bibliography_csl_json(citations)
            assert len(csl_json_bib) == len(citations)
            assert all('title' in item for item in csl_json_bib)
```

## Performance Tests

```python
# test_citation_performance.py
import time
import pytest

@pytest.mark.performance 
class TestCitationPerformance:
    """Performance tests for citation functionality."""
    
    def test_extraction_performance(self, citation_manager):
        """Test citation extraction performance."""
        # Mock work data
        work_data = {
            'id': '123456',
            'title': 'Test Work',
            'contributor': ['Author, Test'],
            'issued': '2020'
        }
        
        start_time = time.time()
        
        # Extract 100 citations
        for i in range(100):
            citation = citation_manager.extract_from_record(work_data, RecordType.WORK)
            
        duration = time.time() - start_time
        
        # Should be very fast
        assert duration < 1.0  # Less than 1 second for 100 extractions
        
    def test_formatting_performance(self, citation_manager):
        """Test citation formatting performance."""
        citation = CitationRef(
            record_type=RecordType.WORK,
            record_id='123456', 
            title='Test Work',
            creators=['Author, Test'],
            publication_date='2020'
        )
        
        # Test BibTeX performance
        start_time = time.time()
        for i in range(100):
            bibtex = citation_manager.cite_bibtex(citation)
        bibtex_duration = time.time() - start_time
        
        # Test CSL-JSON performance  
        start_time = time.time()
        for i in range(100):
            csl_json = citation_manager.cite_csl_json(citation)
        csl_duration = time.time() - start_time
        
        # Should be fast
        assert bibtex_duration < 0.5  # Less than 500ms for 100 formats
        assert csl_duration < 0.5
```

## Definition of Done

Stage 5 is complete when:

- ✅ **PID extraction working** - Can extract PIDs from all record types
- ✅ **URL resolution working** - Can resolve Trove URLs to citations
- ✅ **Search fallback working** - Can find records when direct resolution fails
- ✅ **BibTeX formatting** - Generates valid BibTeX for all record types
- ✅ **CSL-JSON formatting** - Generates valid CSL-JSON for all record types
- ✅ **Round-trip testing** - Record → PID → Record resolution works
- ✅ **Bulk operations** - Can process multiple citations efficiently
- ✅ **Error handling** - Graceful handling of missing/malformed data
- ✅ **Performance** - Citation operations are fast (<100ms typical)
- ✅ **Documentation** - All citation methods documented with examples
- ✅ **Tests passing** - Unit and integration tests with real data
- ✅ **Examples working** - Citation workflow examples execute successfully

This comprehensive citation system enables researchers to properly cite Trove resources in academic and reference contexts.