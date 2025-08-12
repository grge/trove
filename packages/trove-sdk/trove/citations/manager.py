from typing import Dict, Any, Optional, List, Union
from .types import CitationRef, RecordType
from .extraction import PIDExtractor
from .resolution import PIDResolver
from .formatters import CitationFormatter

class CitationManager:
    """Main interface for citation functionality."""
    
    def __init__(self, resource_factory):
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
        elif record_type == RecordType.TITLE:
            return self.extractor.extract_from_title(record_data)
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