import re
from typing import Dict, Any, Optional, List, Pattern, Tuple
from .types import CitationRef, RecordType

class PIDExtractor:
    """Extracts PIDs and bibliographic information from Trove records."""
    
    # URL patterns for PID extraction
    PID_PATTERNS = [
        # Work records
        (RecordType.WORK, re.compile(r'https?://nla\.gov\.au/(nla\.obj-\d+)')),
        (RecordType.WORK, re.compile(r'https?://nla\.gov\.au/(nla\.pic-\w+)')), 
        (RecordType.WORK, re.compile(r'https?://nla\.gov\.au/(nla\.mus-\w+)')),
        (RecordType.WORK, re.compile(r'https?://nla\.gov\.au/(nla\.map-[\w-]+)')),
        
        # Newspaper articles
        (RecordType.ARTICLE, re.compile(r'https?://nla\.gov\.au/(nla\.news-article\d+)')),
        (RecordType.ARTICLE, re.compile(r'https?://trove\.nla\.gov\.au/ndp/del/article/(\d+)')),
        
        # API URLs
        (RecordType.WORK, re.compile(r'https?://api\.trove\.nla\.gov\.au/v3/work/(\d+)')),
        (RecordType.ARTICLE, re.compile(r'https?://api\.trove\.nla\.gov\.au/v3/newspaper/(\d+)')),
        (RecordType.ARTICLE, re.compile(r'https?://api\.trove\.nla\.gov\.au/v3/gazette/(\d+)')),
        (RecordType.PEOPLE, re.compile(r'https?://api\.trove\.nla\.gov\.au/v3/people/(\d+)')),
        (RecordType.LIST, re.compile(r'https?://api\.trove\.nla\.gov\.au/v3/list/(\d+)')),
        (RecordType.TITLE, re.compile(r'https?://api\.trove\.nla\.gov\.au/v3/newspaper/title/(\d+)')),
        (RecordType.TITLE, re.compile(r'https?://api\.trove\.nla\.gov\.au/v3/magazine/title/(\d+)')),
        (RecordType.TITLE, re.compile(r'https?://api\.trove\.nla\.gov\.au/v3/gazette/title/(\d+)')),
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
        
    def extract_from_title(self, title_data: Dict[str, Any]) -> CitationRef:
        """Extract citation information from title record."""
        return CitationRef(
            record_type=RecordType.TITLE,
            record_id=str(title_data.get('id', '')),
            trove_url=title_data.get('troveUrl'),
            api_url=title_data.get('url'),
            title=title_data.get('title'),
            publisher=title_data.get('publisher'),
            place_of_publication=self._extract_place_of_publication(title_data),
            publication_date=self._normalize_date(title_data.get('startDate')),
            format_type=title_data.get('type', 'title'),
            raw_data=title_data
        )
        
    def extract_pid_from_url(self, url: str) -> Optional[Tuple[RecordType, str]]:
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
            elif isinstance(identifier, str):
                if 'nla.obj-' in identifier or 'nla.pic-' in identifier:
                    return identifier
                    
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
            
        # Extract year from various formats first
        year_match = re.search(r'(\d{4})', date_str)
        if year_match:
            year = year_match.group(1)
            # For date ranges, still return just the first year found
            return year
            
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
        # Check for birth date in various fields
        birth_info = people_data.get('birth', {})
        if isinstance(birth_info, dict):
            return birth_info.get('date')
        
        # Check for date range
        date_range = people_data.get('dateRange', '')
        if date_range and '-' in date_range:
            start_date = date_range.split('-')[0].strip()
            if start_date:
                return start_date
                
        return None
        
    def _extract_death_date(self, people_data: Dict[str, Any]) -> Optional[str]:
        """Extract death/dissolution date from people record."""  
        # Check for death date in various fields
        death_info = people_data.get('death', {})
        if isinstance(death_info, dict):
            return death_info.get('date')
        
        # Check for date range
        date_range = people_data.get('dateRange', '')
        if date_range and '-' in date_range:
            parts = date_range.split('-')
            if len(parts) > 1:
                end_date = parts[1].strip()
                if end_date:
                    return end_date
                    
        return None
        
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
        elif isinstance(date_info, str):
            return date_info
        return None