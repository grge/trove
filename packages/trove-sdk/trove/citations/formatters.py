from typing import Dict, Any, List, Optional
from datetime import datetime
import re
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
        elif citation.record_type == RecordType.TITLE:
            return 'periodical'
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
                    parts.append(surname.lower())
                    
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
                
        elif citation.record_type == RecordType.TITLE:
            fields['publisher'] = citation.publisher
            fields['address'] = citation.place_of_publication
                
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
                
        elif citation.record_type == RecordType.TITLE:
            if citation.publisher:
                csl_item['publisher'] = citation.publisher
            if citation.place_of_publication:
                csl_item['publisher-place'] = citation.place_of_publication
                
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
        elif citation.record_type == RecordType.TITLE:
            return 'periodical'
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