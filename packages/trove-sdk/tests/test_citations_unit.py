import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from trove.citations import CitationRef, RecordType, PIDExtractor, CitationFormatter, BibTeXFormatter, CSLJSONFormatter

class TestPIDExtractor:
    """Test PID extraction functionality."""
    
    def setup_method(self):
        self.extractor = PIDExtractor()
    
    def test_extract_pid_from_url_work_patterns(self):
        """Test PID extraction from work URL patterns.""" 
        test_cases = [
            ("https://nla.gov.au/nla.obj-123456789", (RecordType.WORK, "nla.obj-123456789")),
            ("https://nla.gov.au/nla.pic-an24009937", (RecordType.WORK, "nla.pic-an24009937")), 
            ("https://nla.gov.au/nla.mus-vn3630286", (RecordType.WORK, "nla.mus-vn3630286")),
            ("https://nla.gov.au/nla.map-gmod7-st", (RecordType.WORK, "nla.map-gmod7-st")),
            ("https://api.trove.nla.gov.au/v3/work/123456", (RecordType.WORK, "123456")),
        ]
        
        for url, expected in test_cases:
            result = self.extractor.extract_pid_from_url(url)
            assert result == expected, f"Failed for URL: {url}"
    
    def test_extract_pid_from_url_article_patterns(self):
        """Test PID extraction from article URL patterns."""
        test_cases = [
            ("https://nla.gov.au/nla.news-article18341291", (RecordType.ARTICLE, "nla.news-article18341291")),
            ("https://trove.nla.gov.au/ndp/del/article/18341291", (RecordType.ARTICLE, "18341291")),
            ("https://api.trove.nla.gov.au/v3/newspaper/18341291", (RecordType.ARTICLE, "18341291")),
            ("https://api.trove.nla.gov.au/v3/gazette/18341291", (RecordType.ARTICLE, "18341291")),
        ]
        
        for url, expected in test_cases:
            result = self.extractor.extract_pid_from_url(url)
            assert result == expected, f"Failed for URL: {url}"
    
    def test_extract_pid_from_url_other_patterns(self):
        """Test PID extraction from other resource URL patterns."""
        test_cases = [
            ("https://api.trove.nla.gov.au/v3/people/123456", (RecordType.PEOPLE, "123456")),
            ("https://api.trove.nla.gov.au/v3/list/123456", (RecordType.LIST, "123456")),
            ("https://api.trove.nla.gov.au/v3/newspaper/title/123456", (RecordType.TITLE, "123456")),
        ]
        
        for url, expected in test_cases:
            result = self.extractor.extract_pid_from_url(url)
            assert result == expected, f"Failed for URL: {url}"
    
    def test_extract_pid_from_url_invalid(self):
        """Test PID extraction with invalid URLs."""
        invalid_urls = [
            "https://example.com/invalid",
            "not-a-url",
            "",
            "https://nla.gov.au/invalid-pattern",
        ]
        
        for url in invalid_urls:
            result = self.extractor.extract_pid_from_url(url)
            assert result is None, f"Should return None for invalid URL: {url}"
    
    def test_extract_from_work_basic(self):
        """Test citation extraction from basic work record."""
        work_data = {
            'id': '123456',
            'title': 'Australian History: A Complete Guide',
            'contributor': ['Smith, John', 'Jones, Mary'],
            'issued': '2020',
            'troveUrl': 'https://trove.nla.gov.au/work/123456',
            'identifier': [{'value': 'nla.obj-123456789'}]
        }
        
        citation = self.extractor.extract_from_work(work_data)
        
        assert citation.record_type == RecordType.WORK
        assert citation.record_id == '123456'
        assert citation.title == 'Australian History: A Complete Guide'
        assert citation.creators == ['Smith, John', 'Jones, Mary']
        assert citation.publication_date == '2020'
        assert citation.pid == 'nla.obj-123456789'
        assert citation.trove_url == 'https://trove.nla.gov.au/work/123456'
    
    def test_extract_from_work_minimal(self):
        """Test citation extraction from minimal work record."""
        work_data = {
            'id': '123456',
        }
        
        citation = self.extractor.extract_from_work(work_data)
        
        assert citation.record_type == RecordType.WORK
        assert citation.record_id == '123456'
        assert citation.title == ''
        assert citation.creators == []
        assert citation.publication_date is None
        assert citation.pid is None
    
    def test_extract_from_article_basic(self):
        """Test citation extraction from article record.""" 
        article_data = {
            'id': '18341291',
            'heading': 'Federation Celebrations in Sydney',
            'title': {'title': 'The Sydney Morning Herald'},
            'date': '1901-01-01',
            'page': '1',
            'edition': 'Morning Edition',
            'troveUrl': 'https://nla.gov.au/nla.news-article18341291',
            'identifier': 'https://nla.gov.au/nla.news-article18341291'
        }
        
        citation = self.extractor.extract_from_article(article_data)
        
        assert citation.record_type == RecordType.ARTICLE
        assert citation.record_id == '18341291'
        assert citation.title == 'Federation Celebrations in Sydney'
        assert citation.newspaper_title == 'The Sydney Morning Herald'
        assert citation.publication_date == '1901-01-01'
        assert citation.page == '1'
        assert citation.edition == 'Morning Edition'
    
    def test_extract_from_people_basic(self):
        """Test citation extraction from people record."""
        people_data = {
            'id': '123456',
            'primaryName': 'Smith, John',
            'primaryDisplayName': 'John Smith',
            'birth': {'date': '1850'},
            'death': {'date': '1920'},
            'occupation': ['Author', 'Journalist'],
            'type': 'person',
            'troveUrl': 'https://trove.nla.gov.au/people/123456'
        }
        
        citation = self.extractor.extract_from_people(people_data)
        
        assert citation.record_type == RecordType.PEOPLE
        assert citation.record_id == '123456'
        assert citation.title == 'Smith, John'
        assert citation.birth_date == '1850'
        assert citation.death_date == '1920'
        assert citation.occupation == ['Author', 'Journalist']
        assert citation.format_type == 'person'
    
    def test_extract_from_list_basic(self):
        """Test citation extraction from list record."""
        list_data = {
            'id': '123456',
            'title': 'Australian Literature Collection',
            'creator': 'Library User',
            'description': 'A curated collection of Australian literary works',
            'date': {'created': '2023-01-15'},
            'troveUrl': 'https://trove.nla.gov.au/list/123456'
        }
        
        citation = self.extractor.extract_from_list(list_data)
        
        assert citation.record_type == RecordType.LIST
        assert citation.record_id == '123456'
        assert citation.title == 'Australian Literature Collection'
        assert citation.list_creator == 'Library User'
        assert citation.list_description == 'A curated collection of Australian literary works'
        assert citation.publication_date == '2023-01-15'
        assert citation.format_type == 'user list'
    
    def test_clean_title(self):
        """Test title cleaning and normalization."""
        test_cases = [
            ("  Title with   spaces  ", "Title with spaces"),
            ("Title with trailing comma,", "Title with trailing comma"),
            ("Title\twith\ttabs", "Title with tabs"),
            ("Title with semicolon;", "Title with semicolon"),
            ("", ""),
            ("Normal title", "Normal title")
        ]
        
        for input_title, expected in test_cases:
            result = self.extractor._clean_title(input_title)
            assert result == expected
    
    def test_normalize_date(self):
        """Test date normalization for citations."""
        test_cases = [
            ("2020", "2020"),
            ("2001-2011", "2001"),  # Range -> start date
            ("Published in 1995", "1995"),
            ("c. 1890", "1890"),
            ("circa 1850-1900", "1850"),
            (None, None),
            ("", None)
        ]
        
        for input_date, expected in test_cases:
            result = self.extractor._normalize_date(input_date)
            assert result == expected
    
    def test_extract_creators_variations(self):
        """Test creator extraction from various input formats."""
        test_cases = [
            ("Single Author", ["Single Author"]),
            (["Author One", "Author Two"], ["Author One", "Author Two"]),
            ([], []),
            (None, []),
            (["Author", "", "Another Author"], ["Author", "Another Author"]),  # Filters empty
        ]
        
        for input_creators, expected in test_cases:
            result = self.extractor._extract_creators(input_creators)
            assert result == expected


class TestCitationRef:
    """Test CitationRef data class."""
    
    def test_citation_ref_creation(self):
        """Test basic citation ref creation."""
        citation = CitationRef(
            record_type=RecordType.WORK,
            record_id='123456',
            title='Test Work'
        )
        
        assert citation.record_type == RecordType.WORK
        assert citation.record_id == '123456'
        assert citation.title == 'Test Work'
        assert citation.creators == []  # Default empty list
        assert citation.occupation == []  # Default empty list
        assert isinstance(citation.access_date, datetime)
    
    def test_canonical_pid_from_pid_field(self):
        """Test canonical PID when PID field is set."""
        citation = CitationRef(
            record_type=RecordType.WORK,
            record_id='123456',
            pid='nla.obj-123456789'
        )
        
        assert citation.canonical_pid == 'nla.obj-123456789'
    
    def test_canonical_pid_from_url(self):
        """Test canonical PID extraction from trove URL."""
        citation = CitationRef(
            record_type=RecordType.WORK,
            record_id='123456',
            trove_url='https://nla.gov.au/nla.obj-123456789'
        )
        
        assert citation.canonical_pid == 'nla.obj-123456789'
    
    def test_display_title(self):
        """Test display title property."""
        # With title
        citation = CitationRef(
            record_type=RecordType.WORK,
            record_id='123456',
            title='Test Work'
        )
        assert citation.display_title == 'Test Work'
        
        # Without title
        citation = CitationRef(
            record_type=RecordType.WORK,
            record_id='123456'
        )
        assert citation.display_title == 'Untitled work'
    
    def test_primary_creator(self):
        """Test primary creator property."""
        # With creators
        citation = CitationRef(
            record_type=RecordType.WORK,
            record_id='123456',
            creators=['Smith, John', 'Doe, Jane']
        )
        assert citation.primary_creator == 'Smith, John'
        
        # Without creators
        citation = CitationRef(
            record_type=RecordType.WORK,
            record_id='123456'
        )
        assert citation.primary_creator is None


class TestBibTeXFormatter:
    """Test BibTeX citation formatting."""
    
    def setup_method(self):
        self.formatter = BibTeXFormatter()
    
    def test_format_work_citation(self):
        """Test BibTeX formatting for work citation."""
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
        
        bibtex = self.formatter.format(citation)
        
        assert '@misc{smith_2020_123456,' in bibtex
        assert 'title = {Australian Poetry Anthology}' in bibtex
        assert 'author = {Smith, John}' in bibtex
        assert 'year = {2020}' in bibtex
        assert 'publisher = {University Press}' in bibtex
        assert 'address = {Melbourne}' in bibtex
        assert 'url = {https://trove.nla.gov.au/work/123456}' in bibtex
        assert 'note = {Retrieved from Trove, National Library of Australia}' in bibtex
    
    def test_format_article_citation(self):
        """Test BibTeX formatting for article citation."""
        citation = CitationRef(
            record_type=RecordType.ARTICLE,
            record_id='18341291',
            title='Federation Celebrations in Sydney',
            newspaper_title='The Sydney Morning Herald',
            publication_date='1901-01-01',
            page='1',
            trove_url='https://nla.gov.au/nla.news-article18341291'
        )
        
        bibtex = self.formatter.format(citation)
        
        assert '@article{' in bibtex
        assert 'title = {Federation Celebrations in Sydney}' in bibtex
        assert 'journal = {The Sydney Morning Herald}' in bibtex
        assert 'year = {1901}' in bibtex
        assert 'pages = {1}' in bibtex
    
    def test_bibtex_escaping(self):
        """Test BibTeX special character escaping."""
        test_cases = [
            ('Title with & ampersand', 'Title with \\& ampersand'),
            ('Title with % percent', 'Title with \\% percent'),
            ('Title with $ dollar', 'Title with \\$ dollar'),
            ('Title with # hash', 'Title with \\# hash'),
            ('Title with _ underscore', 'Title with \\_ underscore'),
        ]
        
        for input_text, expected in test_cases:
            result = self.formatter._escape_bibtex(input_text)
            assert result == expected
    
    def test_entry_key_generation(self):
        """Test BibTeX entry key generation."""
        citation = CitationRef(
            record_type=RecordType.WORK,
            record_id='123456789',
            creators=['Smith, John Q.'],
            publication_date='2020-01-15'
        )
        
        key = self.formatter._generate_entry_key(citation)
        assert key == 'smith_2020_12345678'
    
    def test_year_extraction(self):
        """Test year extraction from various date formats."""
        test_cases = [
            ('2020', '2020'),
            ('2020-01-15', '2020'),
            ('Published in 1995', '1995'),
            ('c. 1890', '1890'),
            (None, None),
            ('', None),
        ]
        
        for input_date, expected in test_cases:
            result = self.formatter._extract_year(input_date)
            assert result == expected


class TestCSLJSONFormatter:
    """Test CSL-JSON citation formatting."""
    
    def setup_method(self):
        self.formatter = CSLJSONFormatter()
    
    def test_format_work_citation(self):
        """Test CSL-JSON formatting for work citation."""
        citation = CitationRef(
            record_type=RecordType.WORK,
            record_id='123456',
            title='Australian Poetry Anthology',
            creators=['Smith, John'],
            publication_date='2020',
            publisher='University Press',
            place_of_publication='Melbourne',
            trove_url='https://trove.nla.gov.au/work/123456',
            pid='nla.obj-123456789'
        )
        
        csl_json = self.formatter.format(citation)
        
        assert csl_json['id'] == 'nla.obj-123456789'
        assert csl_json['type'] == 'document'
        assert csl_json['title'] == 'Australian Poetry Anthology'
        assert csl_json['author'] == [{'family': 'Smith', 'given': 'John'}]
        assert csl_json['issued'] == {'date-parts': [[2020]]}
        assert csl_json['publisher'] == 'University Press'
        assert csl_json['publisher-place'] == 'Melbourne'
        assert csl_json['URL'] == 'https://trove.nla.gov.au/work/123456'
        assert csl_json['note'] == 'Retrieved from Trove, National Library of Australia'
    
    def test_format_article_citation(self):
        """Test CSL-JSON formatting for article citation."""
        citation = CitationRef(
            record_type=RecordType.ARTICLE,
            record_id='18341291',
            title='Federation Celebrations in Sydney',
            newspaper_title='The Sydney Morning Herald',
            publication_date='1901-01-01',
            page='1',
            trove_url='https://nla.gov.au/nla.news-article18341291'
        )
        
        csl_json = self.formatter.format(citation)
        
        assert csl_json['type'] == 'article-newspaper'
        assert csl_json['title'] == 'Federation Celebrations in Sydney'
        assert csl_json['container-title'] == 'The Sydney Morning Herald'
        assert csl_json['issued'] == {'date-parts': [[1901, 1, 1]]}
        assert csl_json['page'] == '1'
    
    def test_author_name_parsing(self):
        """Test author name parsing for CSL format."""
        test_cases = [
            ('Smith, John', {'family': 'Smith', 'given': 'John'}),
            ('John Smith', {'given': 'John', 'family': 'Smith'}),
            ('SingleName', {'literal': 'SingleName'}),
            ('van der Berg, Johannes', {'family': 'van der Berg', 'given': 'Johannes'}),
        ]
        
        for input_name, expected in test_cases:
            result = self.formatter._parse_author_name(input_name)
            assert result == expected
    
    def test_csl_date_parsing(self):
        """Test date parsing for CSL format."""
        test_cases = [
            ('2020', {'date-parts': [[2020]]}),
            ('2020-01-15', {'date-parts': [[2020, 1, 15]]}),
            ('1995', {'date-parts': [[1995]]}),
            ('', {}),
            ('invalid-date', {}),
        ]
        
        for input_date, expected in test_cases:
            result = self.formatter._parse_csl_date(input_date)
            assert result == expected


class TestCitationFormatter:
    """Test main citation formatter interface."""
    
    def setup_method(self):
        self.formatter = CitationFormatter()
        self.citation = CitationRef(
            record_type=RecordType.WORK,
            record_id='123456',
            title='Test Work',
            creators=['Smith, John'],
            publication_date='2020'
        )
    
    def test_format_bibtex(self):
        """Test BibTeX formatting through main interface."""
        bibtex = self.formatter.format_bibtex(self.citation)
        
        assert '@misc{' in bibtex
        assert 'title = {Test Work}' in bibtex
        assert 'author = {Smith, John}' in bibtex
    
    def test_format_csl_json(self):
        """Test CSL-JSON formatting through main interface."""
        csl_json = self.formatter.format_csl_json(self.citation)
        
        assert csl_json['type'] == 'document'
        assert csl_json['title'] == 'Test Work'
        assert csl_json['author'] == [{'family': 'Smith', 'given': 'John'}]
    
    def test_format_multiple_bibtex(self):
        """Test multiple BibTeX formatting."""
        citations = [self.citation, self.citation]
        bibtex = self.formatter.format_multiple_bibtex(citations)
        
        # Should have two entries separated by double newline
        entries = bibtex.split('\n\n')
        assert len(entries) == 2
        assert '@misc{' in entries[0]
        assert '@misc{' in entries[1]
    
    def test_format_multiple_csl_json(self):
        """Test multiple CSL-JSON formatting."""
        citations = [self.citation, self.citation]
        csl_json_list = self.formatter.format_multiple_csl_json(citations)
        
        assert len(csl_json_list) == 2
        assert all('title' in item for item in csl_json_list)
        assert all(item['title'] == 'Test Work' for item in csl_json_list)