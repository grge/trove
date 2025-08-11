"""Unit tests for resource implementations."""

import pytest
from unittest.mock import Mock, AsyncMock

from trove.resources import (
    ResourceFactory, WorkResource, NewspaperResource, GazetteResource,
    PeopleResource, ListResource, NewspaperTitleResource, MagazineTitleResource,
    GazetteTitleResource, RecLevel, Encoding
)
from trove.exceptions import ResourceNotFoundError, ValidationError, TroveAPIError


class TestBaseResource:
    """Test base resource functionality."""

    def test_reclevel_normalization(self):
        """Test reclevel parameter normalization."""
        mock_transport = Mock()
        mock_transport.get.return_value = {'work': {'title': 'Test Work'}}
        
        work_resource = WorkResource(mock_transport)
        
        # Test string normalization
        work_resource.get('123', reclevel='full')
        mock_transport.get.assert_called_with('/work/123', {'reclevel': 'full', 'encoding': 'json'})
        
        # Test enum value
        work_resource.get('123', reclevel=RecLevel.BRIEF)
        mock_transport.get.assert_called_with('/work/123', {'reclevel': 'brief', 'encoding': 'json'})

    def test_encoding_normalization(self):
        """Test encoding parameter normalization."""
        mock_transport = Mock()
        mock_transport.get.return_value = {'work': {'title': 'Test Work'}}
        
        work_resource = WorkResource(mock_transport)
        
        # Test string normalization
        work_resource.get('123', encoding='xml')
        mock_transport.get.assert_called_with('/work/123', {'reclevel': 'brief', 'encoding': 'xml'})
        
        # Test enum value
        work_resource.get('123', encoding=Encoding.JSON)
        mock_transport.get.assert_called_with('/work/123', {'reclevel': 'brief', 'encoding': 'json'})

    def test_invalid_reclevel_raises_error(self):
        """Test that invalid reclevel raises ValidationError."""
        mock_transport = Mock()
        work_resource = WorkResource(mock_transport)
        
        with pytest.raises(ValidationError, match="Invalid reclevel"):
            work_resource.get('123', reclevel='invalid')

    def test_invalid_encoding_raises_error(self):
        """Test that invalid encoding raises ValidationError."""
        mock_transport = Mock()
        work_resource = WorkResource(mock_transport)
        
        with pytest.raises(ValidationError, match="Invalid encoding"):
            work_resource.get('123', encoding='invalid')

    def test_include_parameter_validation(self):
        """Test include parameter validation."""
        mock_transport = Mock()
        mock_transport.get.return_value = {'work': {'title': 'Test Work'}}
        
        work_resource = WorkResource(mock_transport)
        
        # Valid include options should work
        work_resource.get('123', include=['tags', 'comments'])
        mock_transport.get.assert_called_with(
            '/work/123', 
            {'reclevel': 'brief', 'encoding': 'json', 'include': 'tags,comments'}
        )
        
        # Invalid include options should raise error
        with pytest.raises(ValidationError, match="Invalid include options"):
            work_resource.get('123', include=['invalid_option'])

    def test_404_handling(self):
        """Test that 404 responses raise ResourceNotFoundError."""
        mock_transport = Mock()
        mock_transport.get.side_effect = TroveAPIError("Not found", status_code=404)
        
        work_resource = WorkResource(mock_transport)
        
        with pytest.raises(ResourceNotFoundError, match="Resource 999999 not found"):
            work_resource.get('999999')


class TestWorkResource:
    """Test WorkResource functionality."""

    def test_work_resource_basic_get(self):
        """Test basic work resource get."""
        mock_transport = Mock()
        mock_transport.get.return_value = {
            'work': {
                'title': 'Test Book',
                'contributor': ['Test Author']
            }
        }
        
        work_resource = WorkResource(mock_transport)
        result = work_resource.get('123456')
        
        assert result['title'] == 'Test Book'
        assert result['id'] == '123456'  # Added by post-processing
        mock_transport.get.assert_called_once_with(
            '/work/123456',
            {'reclevel': 'brief', 'encoding': 'json'}
        )

    def test_work_versions(self):
        """Test getting work versions."""
        mock_transport = Mock()
        mock_transport.get.return_value = {
            'work': {
                'version': [
                    {'id': 'v1', 'title': 'Version 1'},
                    {'id': 'v2', 'title': 'Version 2'}
                ]
            }
        }
        
        work_resource = WorkResource(mock_transport)
        versions = work_resource.get_versions('123456')
        
        assert len(versions) == 2
        assert versions[0]['id'] == 'v1'
        assert versions[1]['id'] == 'v2'
        
        mock_transport.get.assert_called_once_with(
            '/work/123456',
            {'reclevel': 'full', 'encoding': 'json', 'include': 'workversions'}
        )

    def test_work_holdings(self):
        """Test getting work holdings."""
        mock_transport = Mock()
        mock_transport.get.return_value = {
            'work': {
                'holding': [
                    {'nuc': 'NUC1', 'callNumber': 'ABC123'},
                    {'nuc': 'NUC2', 'callNumber': 'DEF456'}
                ]
            }
        }
        
        work_resource = WorkResource(mock_transport)
        holdings = work_resource.get_holdings('123456')
        
        assert len(holdings) == 2
        assert holdings[0]['nuc'] == 'NUC1'
        assert holdings[1]['nuc'] == 'NUC2'

    @pytest.mark.asyncio
    async def test_async_work_resource(self):
        """Test async work resource operations."""
        mock_transport = Mock()
        mock_transport.aget = AsyncMock(return_value={
            'work': {
                'title': 'Async Test Book',
                'contributor': ['Async Author']
            }
        })
        
        work_resource = WorkResource(mock_transport)
        result = await work_resource.aget('123456')
        
        assert result['title'] == 'Async Test Book'
        assert result['id'] == '123456'
        mock_transport.aget.assert_called_once_with(
            '/work/123456',
            {'reclevel': 'brief', 'encoding': 'json'}
        )


class TestArticleResource:
    """Test article resource functionality."""

    def test_newspaper_resource_basic_get(self):
        """Test basic newspaper article get."""
        mock_transport = Mock()
        mock_transport.get.return_value = {
            'article': {
                'heading': 'Test Article',
                'date': '1876-05-27'
            }
        }
        
        newspaper_resource = NewspaperResource(mock_transport)
        result = newspaper_resource.get('12345')
        
        assert result['heading'] == 'Test Article'
        assert result['id'] == '12345'  # Added by post-processing
        mock_transport.get.assert_called_once_with(
            '/newspaper/12345',
            {'reclevel': 'brief', 'encoding': 'json'}
        )

    def test_article_full_text(self):
        """Test getting article full text."""
        mock_transport = Mock()
        mock_transport.get.return_value = {
            'article': {
                'heading': 'Test Article',
                'articleText': '<p>Article content</p>'
            }
        }
        
        newspaper_resource = NewspaperResource(mock_transport)
        full_text = newspaper_resource.get_full_text('12345')
        
        assert full_text == '<p>Article content</p>'
        mock_transport.get.assert_called_once_with(
            '/newspaper/12345',
            {'reclevel': 'brief', 'encoding': 'json', 'include': 'articletext'}
        )

    def test_article_status_checks(self):
        """Test article status checking methods."""
        mock_transport = Mock()
        
        # Test coming soon status
        mock_transport.get.return_value = {
            'article': {'status': 'coming soon'}
        }
        newspaper_resource = NewspaperResource(mock_transport)
        assert newspaper_resource.is_coming_soon('12345') is True
        assert newspaper_resource.is_withdrawn('12345') is False
        
        # Test withdrawn status
        mock_transport.get.return_value = {
            'article': {'status': 'withdrawn'}
        }
        assert newspaper_resource.is_coming_soon('12345') is False
        assert newspaper_resource.is_withdrawn('12345') is True

    def test_gazette_resource(self):
        """Test gazette resource uses correct endpoint."""
        mock_transport = Mock()
        mock_transport.get.return_value = {
            'article': {
                'heading': 'Gazette Notice',
                'category': 'Government Gazette Notices'
            }
        }
        
        gazette_resource = GazetteResource(mock_transport)
        result = gazette_resource.get('67890')
        
        assert result['heading'] == 'Gazette Notice'
        mock_transport.get.assert_called_once_with(
            '/gazette/67890',
            {'reclevel': 'brief', 'encoding': 'json'}
        )


class TestPeopleResource:
    """Test people resource functionality."""

    def test_people_resource_basic_get(self):
        """Test basic people resource get."""
        mock_transport = Mock()
        mock_transport.get.return_value = {
            'people': {
                'primaryName': 'John Smith',
                'type': 'person'
            }
        }
        
        people_resource = PeopleResource(mock_transport)
        result = people_resource.get('1234')
        
        assert result['primaryName'] == 'John Smith'
        assert result['id'] == '1234'  # Added by post-processing

    def test_person_type_checks(self):
        """Test person/organization type checking."""
        mock_transport = Mock()
        people_resource = PeopleResource(mock_transport)
        
        # Test person type
        mock_transport.get.return_value = {
            'people': {'type': 'person'}
        }
        assert people_resource.is_person('1234') is True
        assert people_resource.is_organization('1234') is False
        
        # Test organization type
        mock_transport.get.return_value = {
            'people': {'type': 'corporatebody'}
        }
        assert people_resource.is_person('1234') is False
        assert people_resource.is_organization('1234') is True

    def test_get_occupations(self):
        """Test getting occupations."""
        mock_transport = Mock()
        people_resource = PeopleResource(mock_transport)
        
        # Test single occupation
        mock_transport.get.return_value = {
            'people': {'occupation': 'Writer'}
        }
        occupations = people_resource.get_occupations('1234')
        assert occupations == ['Writer']
        
        # Test multiple occupations
        mock_transport.get.return_value = {
            'people': {'occupation': ['Writer', 'Teacher']}
        }
        occupations = people_resource.get_occupations('1234')
        assert occupations == ['Writer', 'Teacher']


class TestListResource:
    """Test list resource functionality."""

    def test_list_resource_basic_get(self):
        """Test basic list resource get."""
        mock_transport = Mock()
        mock_transport.get.return_value = {
            'list': {
                'title': 'My Reading List',
                'creator': 'user123',
                'listItemCount': 5
            }
        }
        
        list_resource = ListResource(mock_transport)
        result = list_resource.get('21922')
        
        assert result['title'] == 'My Reading List'
        assert result['id'] == '21922'  # Added by post-processing

    def test_list_metadata_methods(self):
        """Test list metadata retrieval methods."""
        mock_transport = Mock()
        mock_transport.get.return_value = {
            'list': {
                'title': 'Test List',
                'creator': 'testuser',
                'listItemCount': 10,
                'description': 'A test list',
                'lastupdated': '2023-01-01T12:00:00Z'
            }
        }
        
        list_resource = ListResource(mock_transport)
        
        assert list_resource.get_title('21922') == 'Test List'
        assert list_resource.get_creator('21922') == 'testuser'
        assert list_resource.get_item_count('21922') == 10
        assert list_resource.get_description('21922') == 'A test list'
        assert list_resource.get_last_updated('21922') == '2023-01-01T12:00:00Z'


class TestTitleResources:
    """Test title resource functionality."""

    def test_newspaper_title_search(self):
        """Test newspaper title search."""
        mock_transport = Mock()
        mock_transport.get.return_value = {
            'response': {
                'query': {},
                'total': 10,
                'titles': [{'id': 't1', 'title': 'Sydney Morning Herald'}]
            }
        }
        
        title_resource = NewspaperTitleResource(mock_transport)
        results = title_resource.search(state='nsw', limit=10)
        
        assert 'response' in results
        mock_transport.get.assert_called_once_with(
            '/newspaper/titles',
            {'offset': 0, 'limit': 10, 'encoding': 'json', 'state': 'nsw'}
        )

    def test_newspaper_title_state_validation(self):
        """Test newspaper title state validation."""
        mock_transport = Mock()
        title_resource = NewspaperTitleResource(mock_transport)
        
        with pytest.raises(ValueError, match="Invalid state"):
            title_resource.search(state='invalid_state')

    def test_gazette_title_state_validation(self):
        """Test gazette title state validation (more restrictive)."""
        mock_transport = Mock()
        title_resource = GazetteTitleResource(mock_transport)
        
        # Valid gazette states
        title_resource.search(state='nsw')  # Should not raise
        title_resource.search(state='national')  # Should not raise
        
        # Invalid gazette state (valid for newspapers but not gazettes)
        with pytest.raises(ValueError, match="Invalid state"):
            title_resource.search(state='vic')

    def test_title_get_with_years(self):
        """Test getting title with years included."""
        mock_transport = Mock()
        mock_transport.get.return_value = {
            'title': 'Test Newspaper',
            'year': [
                {'value': '2020', 'count': 365},
                {'value': '2021', 'count': 365}
            ]
        }
        
        title_resource = NewspaperTitleResource(mock_transport)
        result = title_resource.get('123', include=['years'])
        
        assert result['title'] == 'Test Newspaper'
        mock_transport.get.assert_called_once_with(
            '/newspaper/title/123',
            {'encoding': 'json', 'include': 'years'}
        )


class TestResourceFactory:
    """Test resource factory functionality."""

    def test_resource_factory_creates_resources(self):
        """Test that resource factory creates all resource types."""
        mock_transport = Mock()
        factory = ResourceFactory(mock_transport)
        
        # Test that all resource types can be created
        assert isinstance(factory.get_search_resource(), type(factory.get_search_resource()))
        assert isinstance(factory.get_work_resource(), WorkResource)
        assert isinstance(factory.get_newspaper_resource(), NewspaperResource)
        assert isinstance(factory.get_gazette_resource(), GazetteResource)
        assert isinstance(factory.get_people_resource(), PeopleResource)
        assert isinstance(factory.get_list_resource(), ListResource)
        assert isinstance(factory.get_newspaper_title_resource(), NewspaperTitleResource)
        assert isinstance(factory.get_magazine_title_resource(), MagazineTitleResource)
        assert isinstance(factory.get_gazette_title_resource(), GazetteTitleResource)

    def test_resource_factory_caches_instances(self):
        """Test that resource factory caches resource instances."""
        mock_transport = Mock()
        factory = ResourceFactory(mock_transport)
        
        # Get same resource twice
        work1 = factory.get_work_resource()
        work2 = factory.get_work_resource()
        
        # Should be the same instance
        assert work1 is work2