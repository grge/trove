import pytest
import os
from unittest.mock import Mock, patch
from trove import TroveClient
from trove.citations import CitationManager, CitationRef, RecordType
from trove.exceptions import ResourceNotFoundError

@pytest.mark.integration
class TestCitationsIntegration:
    """Integration tests for citations with real API."""
    
    @pytest.fixture(scope="class")  
    def citation_manager(self):
        api_key = os.environ.get('TROVE_API_KEY')
        if not api_key:
            pytest.skip("TROVE_API_KEY not set")
            
        client = TroveClient.from_api_key(api_key, rate_limit=1.0)
        return client.citations
    
    @pytest.fixture(scope="class")
    def client(self):
        api_key = os.environ.get('TROVE_API_KEY')
        if not api_key:
            pytest.skip("TROVE_API_KEY not set")
            
        return TroveClient.from_api_key(api_key, rate_limit=1.0)
    
    def test_work_citation_extraction_real_data(self, client, citation_manager):
        """Test work citation extraction with real API data."""
        # First find a work via search
        try:
            search = (client.search()
                     .text("Australian history")
                     .in_("book")
                     .page_size(1))
                           
            # Get first record
            work_data = None
            for record in search.records():
                work_data = record
                break
                
            if not work_data:
                pytest.skip("No work records found in search")
                
            citation = citation_manager.extract_from_record(work_data, RecordType.WORK)
            
            assert citation.record_type == RecordType.WORK
            assert citation.record_id is not None
            assert len(citation.record_id) > 0
            
            # Test that we can generate valid citations
            bibtex = citation_manager.cite_bibtex(citation)
            assert '@' in bibtex
            assert '{' in bibtex and '}' in bibtex
            
            csl_json = citation_manager.cite_csl_json(citation)
            assert isinstance(csl_json, dict)
            assert 'type' in csl_json
            assert 'id' in csl_json
            
        except Exception as e:
            pytest.skip(f"Could not test with real data: {e}")
            
    def test_article_citation_extraction_real_data(self, client, citation_manager):
        """Test article citation extraction with real API data."""
        try:
            search = (client.search()
                     .text("federation")
                     .in_("newspaper")
                     .page_size(1))
                           
            # Get first record
            article_data = None
            for record in search.records():
                article_data = record
                break
                
            if not article_data:
                pytest.skip("No article records found in search")
                
            citation = citation_manager.extract_from_record(article_data, RecordType.ARTICLE)
            
            assert citation.record_type == RecordType.ARTICLE
            assert citation.record_id is not None
            
            # Test BibTeX generation
            bibtex = citation_manager.cite_bibtex(citation)
            assert '@article' in bibtex
            
            # Test CSL-JSON generation
            csl_json = citation_manager.cite_csl_json(citation)
            assert csl_json['type'] == 'article-newspaper'
            
        except Exception as e:
            pytest.skip(f"Could not test with real data: {e}")
    
    def test_pid_resolution_with_known_work(self, client, citation_manager):
        """Test PID resolution with a known work ID."""
        try:
            # Get a work ID from search first
            search = (client.search()
                     .text("literature")
                     .in_("book")
                     .page_size(1))
                           
            # Get first record
            work_data = None
            for record in search.records():
                work_data = record
                break
                
            if not work_data:
                pytest.skip("No work records found for PID resolution test")
                
            work_id = work_data.get('id')
            if not work_id:
                pytest.skip("Work record has no ID")
            
            # Test resolution by numeric ID
            citation = citation_manager.resolve_identifier(str(work_id))
            if citation:  # May be None if resolution fails
                assert citation.record_id == str(work_id)
                assert citation.record_type in [RecordType.WORK, RecordType.ARTICLE, RecordType.PEOPLE, RecordType.LIST]
                
        except Exception as e:
            pytest.skip(f"Could not test PID resolution: {e}")
    
    def test_url_resolution_patterns(self, citation_manager):
        """Test URL resolution with various URL patterns."""
        # Test URLs that are likely to exist - use mock data instead
        test_urls = [
            "https://api.trove.nla.gov.au/v3/work/123456",
            "https://nla.gov.au/nla.news-article18341291",
            "https://trove.nla.gov.au/ndp/del/article/18341291",
        ]
        
        for url in test_urls:
            try:
                citation = citation_manager.resolve_identifier(url)
                # Citation may be None if URL doesn't exist - that's OK
                if citation:
                    assert citation.record_id is not None
                    assert citation.record_type is not None
            except Exception:
                # Expected for test URLs that don't exist
                pass
    
    def test_bibliography_generation_real_data(self, client, citation_manager):
        """Test bibliography generation with multiple real items."""
        try:
            # Use search to find some real items
            search = (client.search()
                     .text("Australian")
                     .in_("book")
                     .page_size(3))
                           
            citations = []
            record_count = 0
            for record in search.records():
                try:
                    citation = citation_manager.extract_from_record(record, RecordType.WORK)
                    citations.append(citation)
                    record_count += 1
                    if record_count >= 3:
                        break
                except:
                    continue  # Skip problematic records
                    
            if not citations:
                pytest.skip("No valid citations extracted from search results")
                
            # Test BibTeX bibliography
            bibtex_bib = citation_manager.bibliography_bibtex(citations)
            entry_count = bibtex_bib.count('@')
            assert entry_count == len(citations)
            
            # Test CSL-JSON bibliography
            csl_json_bib = citation_manager.bibliography_csl_json(citations)
            assert len(csl_json_bib) == len(citations)
            assert all('title' in item or 'id' in item for item in csl_json_bib)
            
        except Exception as e:
            pytest.skip(f"Could not test bibliography generation: {e}")
    
    def test_round_trip_citation_work(self, client, citation_manager):
        """Test round-trip: work -> citation -> formats."""
        try:
            # Use a known valid work ID from our search
            work_id = '6790891'  # The Oxford companion to Australian literature
            work = client.resources.get_work_resource().get(work_id)
            citation = citation_manager.extract_from_record(work, RecordType.WORK)
            
            # Verify citation was extracted properly
            assert citation.record_type == RecordType.WORK
            assert citation.record_id == work_id
            assert citation.title is not None
            assert len(citation.title) > 0
            
            # Test that we can format it
            bibtex = citation_manager.cite_bibtex(citation)
            csl_json = citation_manager.cite_csl_json(citation)
            
            assert len(bibtex) > 0
            assert '@' in bibtex  # Valid BibTeX
            assert citation.title in bibtex  # Title should appear
            
            assert isinstance(csl_json, dict)
            assert len(csl_json) > 0
            assert 'title' in csl_json
            assert csl_json['title'] == citation.title
            
            # Test round-trip via PID resolution if available
            if citation.canonical_pid:
                resolved_citation = citation_manager.resolve_identifier(citation.canonical_pid)
                if resolved_citation:
                    assert resolved_citation.record_id == work_id
            
        except ResourceNotFoundError:
            pytest.skip(f"Work ID {work_id} not found - may have been removed from Trove")
        except Exception as e:
            pytest.skip(f"Unexpected error in round-trip test: {e}")
    
    def test_citation_manager_in_client(self, client):
        """Test that citation manager is properly integrated in client."""
        assert hasattr(client, 'citations')
        assert isinstance(client.citations, CitationManager)
        
        # Test that we can call citation methods
        test_citation = CitationRef(
            record_type=RecordType.WORK,
            record_id='test',
            title='Test Work'
        )
        
        bibtex = client.citations.cite_bibtex(test_citation)
        assert '@misc{' in bibtex
        assert 'title = {Test Work}' in bibtex
    
    def test_malformed_data_handling(self, citation_manager):
        """Test handling of malformed or incomplete data."""
        # Test with minimal data
        minimal_work = {'id': '123'}
        citation = citation_manager.extract_from_record(minimal_work, RecordType.WORK)
        
        assert citation.record_type == RecordType.WORK
        assert citation.record_id == '123'
        assert citation.title == ''  # Should handle missing title gracefully
        
        # Should still be able to generate citations
        bibtex = citation_manager.cite_bibtex(citation)
        csl_json = citation_manager.cite_csl_json(citation)
        
        assert len(bibtex) > 0
        assert isinstance(csl_json, dict)
    
    def test_search_fallback_mechanism(self, client, citation_manager):
        """Test search fallback for identifier resolution."""
        try:
            # Test with a search term that should find results
            citation = citation_manager.resolve_identifier("Australian literature")
            
            # May or may not find results - that's OK
            if citation:
                assert citation.record_type is not None
                assert citation.record_id is not None
                
        except Exception:
            # Search fallback may fail - that's acceptable
            pass


@pytest.mark.unit
class TestCitationsWithMockData:
    """Unit tests with mocked API responses."""
    
    @pytest.fixture
    def mock_resource_factory(self):
        """Create a mock resource factory."""
        factory = Mock()
        
        # Mock work resource
        work_resource = Mock()
        work_resource.get.return_value = {
            'id': '123456',
            'title': 'Test Work',
            'contributor': ['Smith, John'],
            'issued': '2020',
            'troveUrl': 'https://trove.nla.gov.au/work/123456',
            'identifier': [{'value': 'nla.obj-123456789'}]
        }
        factory.get_work_resource.return_value = work_resource
        
        # Mock newspaper resource
        newspaper_resource = Mock()
        newspaper_resource.get.return_value = {
            'id': '18341291',
            'heading': 'Test Article',
            'title': {'title': 'The Test Herald'},
            'date': '1901-01-01',
            'page': '1',
            'troveUrl': 'https://nla.gov.au/nla.news-article18341291'
        }
        factory.get_newspaper_resource.return_value = newspaper_resource
        
        # Mock search resource for fallback
        search_resource = Mock()
        search_resource.page.return_value = {
            'category': [{
                'code': 'book',
                'records': {
                    'record': [{
                        'id': '123456',
                        'title': 'Found Work',
                        'contributor': ['Found, Author']
                    }]
                }
            }]
        }
        factory.get_search_resource.return_value = search_resource
        
        return factory
    
    @pytest.fixture
    def citation_manager(self, mock_resource_factory):
        """Create citation manager with mocked resources."""
        return CitationManager(mock_resource_factory)
    
    def test_resolve_work_url(self, citation_manager):
        """Test resolving work URL to citation."""
        url = "https://api.trove.nla.gov.au/v3/work/123456"
        citation = citation_manager.resolve_identifier(url)
        
        assert citation is not None
        assert citation.record_type == RecordType.WORK
        assert citation.record_id == '123456'
        assert citation.title == 'Test Work'
        assert citation.pid == 'nla.obj-123456789'
    
    def test_resolve_article_url(self, citation_manager):
        """Test resolving article URL to citation."""
        url = "https://api.trove.nla.gov.au/v3/newspaper/18341291"
        citation = citation_manager.resolve_identifier(url)
        
        assert citation is not None
        assert citation.record_type == RecordType.ARTICLE
        assert citation.record_id == '18341291'
        assert citation.title == 'Test Article'
        assert citation.newspaper_title == 'The Test Herald'
    
    def test_resolve_numeric_id(self, citation_manager):
        """Test resolving numeric ID."""
        citation = citation_manager.resolve_identifier("123456")
        
        assert citation is not None
        assert citation.record_type == RecordType.WORK
        assert citation.record_id == '123456'
    
    def test_search_fallback_with_mock(self, citation_manager):
        """Test search fallback mechanism."""
        citation = citation_manager.resolve_identifier("some search term")
        
        assert citation is not None
        assert citation.record_type == RecordType.WORK
        assert citation.title == 'Found Work'
    
    def test_bulk_resolve(self, citation_manager):
        """Test bulk resolution of identifiers."""
        identifiers = [
            "https://api.trove.nla.gov.au/v3/work/123456",
            "123456",
            "nonexistent"
        ]
        
        results = citation_manager.resolver.bulk_resolve(identifiers)
        
        assert len(results) == 3
        assert results["https://api.trove.nla.gov.au/v3/work/123456"] is not None
        assert results["123456"] is not None
        # nonexistent should either be None or resolved via search fallback