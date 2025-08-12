from typing import Optional, Dict, Any, Union, List
import re
from ..exceptions import ResourceNotFoundError, TroveAPIError
from .types import CitationRef, RecordType
from .extraction import PIDExtractor

class PIDResolver:
    """Resolves PIDs and URLs to CitationRef objects."""
    
    def __init__(self, resource_factory):
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
                
            elif record_type == RecordType.TITLE:
                # Determine title type from URL
                if 'newspaper/title' in url:
                    title = self.resource_factory.get_newspaper_title_resource().get(record_id)
                elif 'magazine/title' in url:
                    title = self.resource_factory.get_magazine_title_resource().get(record_id)
                elif 'gazette/title' in url:
                    title = self.resource_factory.get_gazette_title_resource().get(record_id)
                else:
                    # Default to newspaper title
                    title = self.resource_factory.get_newspaper_title_resource().get(record_id)
                return self.extractor.extract_from_title(title)
                
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
        # For work PIDs, we need to use search to find the record
        # This is a limitation since we can't directly lookup by PID
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
        try:
            # Use search resource to find potential matches
            search_resource = self.resource_factory.get_search_resource()
            result = search_resource.page(q=identifier, l_format='all', n=1)
            
            if 'category' in result and result['category']:
                # Get the first category with results
                for category in result['category']:
                    if 'records' in category and 'record' in category['records']:
                        records = category['records']['record']
                        if isinstance(records, dict):
                            records = [records]
                        
                        if records:
                            # Try to extract citation from first result
                            record = records[0]
                            # Determine record type from category
                            category_code = category.get('code', '')
                            
                            if category_code in ['book', 'article', 'picture', 'map', 'music']:
                                return self.extractor.extract_from_work(record)
                            elif category_code in ['newspaper', 'gazette']:
                                return self.extractor.extract_from_article(record)
                            elif category_code == 'people':
                                return self.extractor.extract_from_people(record)
                            elif category_code == 'list':
                                return self.extractor.extract_from_list(record)
                                
        except Exception:
            # If search fails, return None
            pass
            
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
                # Try newspaper first, then gazette
                try:
                    article = self.resource_factory.get_newspaper_resource().get(citation_ref.record_id)
                    return self.extractor.extract_from_article(article)
                except ResourceNotFoundError:
                    article = self.resource_factory.get_gazette_resource().get(citation_ref.record_id)
                    return self.extractor.extract_from_article(article)
            elif citation_ref.record_type == RecordType.PEOPLE:
                people = self.resource_factory.get_people_resource().get(citation_ref.record_id)
                return self.extractor.extract_from_people(people)
            elif citation_ref.record_type == RecordType.LIST:
                list_data = self.resource_factory.get_list_resource().get(citation_ref.record_id)
                return self.extractor.extract_from_list(list_data)
            elif citation_ref.record_type == RecordType.TITLE:
                # Default to newspaper title - could be enhanced to detect type
                title = self.resource_factory.get_newspaper_title_resource().get(citation_ref.record_id)
                return self.extractor.extract_from_title(title)
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