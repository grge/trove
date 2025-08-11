"""Unit tests for ergonomic search interface."""

import pytest
from unittest.mock import Mock

from trove.search import Search, SearchSpec, SearchFilter, search
from trove.params import SortBy, RecLevel
from trove.exceptions import ValidationError


def test_immutable_builder():
    """Test that search builder is immutable."""
    mock_resource = Mock()
    
    search1 = Search(mock_resource)
    search2 = search1.text("test")
    search3 = search2.in_("book")
    
    # Each operation should return a new instance
    assert search1 is not search2
    assert search2 is not search3
    
    # Original should be unchanged
    assert search1._spec.query is None
    assert search2._spec.query == "test"
    assert search3._spec.query == "test"
    assert search3._spec.categories == ["book"]


def test_method_chaining():
    """Test fluent method chaining."""
    mock_resource = Mock()
    
    search_obj = (Search(mock_resource)
                 .text("Australian history")
                 .in_("book", "image")
                 .decade("200", "199")
                 .page_size(50)
                 .sort_by("date_desc")
                 .with_facets("format", "language")
                 .illustrated()
                 .australian_content())
                 
    spec = search_obj._spec
    assert spec.query == "Australian history"
    assert spec.categories == ["book", "image"]
    assert spec.page_size == 50
    assert spec.sort_by == SortBy.DATE_DESC
    assert spec.facets == ["format", "language"]
    
    # Check filters
    filter_names = {f.param_name for f in spec.filters}
    assert "l-decade" in filter_names
    assert "l-illustrated" in filter_names
    assert "l-australian" in filter_names


def test_parameter_validation():
    """Test parameter validation in builder."""
    mock_resource = Mock()
    search_obj = Search(mock_resource)
    
    # Invalid category should raise error
    with pytest.raises(ValidationError, match="Invalid categories"):
        search_obj.in_("invalid_category")
        
    # Invalid page size should raise error
    with pytest.raises(ValidationError, match="Page size must be"):
        search_obj.page_size(-1)
        
    with pytest.raises(ValidationError, match="Page size must be"):
        search_obj.page_size(101)
        
    # Invalid sort order should raise error  
    with pytest.raises(ValidationError, match="Invalid sort order"):
        search_obj.sort_by("invalid_sort")


def test_single_category_validation():
    """Test single category validation for iteration methods."""
    mock_resource = Mock()
    
    # Single category should work
    single_cat_search = Search(mock_resource).in_("book")
    # Should not raise error when checking spec
    assert len(single_cat_search._spec.categories) == 1
    
    # Multi-category should raise error for pages()  
    multi_cat_search = Search(mock_resource).in_("book", "image")
    with pytest.raises(ValidationError, match="only supports single-category"):
        list(multi_cat_search.pages())
        
    with pytest.raises(ValidationError, match="only supports single-category"):
        list(multi_cat_search.records())


def test_parameter_compilation():
    """Test conversion to raw SearchParameters."""
    mock_resource = Mock()
    
    search_obj = (Search(mock_resource)
                 .text("test query")
                 .in_("book")
                 .decade("200")
                 .format("Book")
                 .page_size(25)
                 .harvest())
                 
    params = search_obj._spec.to_parameters()
    
    assert params.category == ["book"]
    assert params.q == "test query"
    assert params.n == 25
    assert params.bulkHarvest == True
    assert params.l_decade == ["200"]
    assert params.l_format == ["Book"]


def test_convenience_filters():
    """Test convenience filter methods."""
    mock_resource = Mock()
    
    search_obj = (Search(mock_resource)
                 .online()
                 .free_online()
                 .first_australians()
                 .australian_content()
                 .culturally_sensitive()
                 .illustrated())
                 
    filters = {f.param_name: f.values for f in search_obj._spec.filters}
    
    # Multiple calls to availability should create multiple filters
    availability_filters = [f for f in search_obj._spec.filters if f.param_name == "l-availability"]
    assert len(availability_filters) == 2  # online() and free_online()
    assert any(f.values == ["y"] for f in availability_filters)
    assert any(f.values == ["y/f"] for f in availability_filters)
    
    assert filters["l-firstAustralians"] == ["y"]
    assert filters["l-australian"] == ["y"]
    assert filters["l-culturalSensitivity"] == ["y"]
    assert filters["l-illustrated"] == ["true"]


def test_explain_method():
    """Test search explanation for debugging."""
    mock_resource = Mock()
    
    search_obj = (Search(mock_resource)
                 .text("test")
                 .in_("book")
                 .decade("200")
                 .page_size(10))
                 
    explanation = search_obj.explain()
    
    assert explanation['categories'] == ["book"]
    assert explanation['query'] == "test"
    assert explanation['page_size'] == 10
    assert len(explanation['filters']) == 1
    assert explanation['filters'][0]['param'] == "l-decade"
    assert 'compiled_params' in explanation


def test_repr_method():
    """Test string representation."""
    mock_resource = Mock()
    
    search_obj = (Search(mock_resource)
                 .text("test")
                 .in_("book")
                 .page_size(50))
                 
    repr_str = repr(search_obj)
    assert "text='test'" in repr_str
    assert "categories=['book']" in repr_str
    assert "page_size=50" in repr_str


def test_factory_function():
    """Test the search factory function."""
    mock_resource = Mock()
    
    search_obj = search(mock_resource)
    assert isinstance(search_obj, Search)
    assert search_obj._search_resource is mock_resource


def test_search_filter():
    """Test SearchFilter dataclass."""
    filter_obj = SearchFilter("l-decade", ["200", "199"])
    assert filter_obj.param_name == "l-decade"
    assert filter_obj.values == ["200", "199"]
    assert filter_obj.operator == "eq"  # default


def test_search_spec():
    """Test SearchSpec dataclass."""
    spec = SearchSpec(
        categories=["book"],
        query="test",
        page_size=10,
        sort_by=SortBy.DATE_DESC
    )
    
    assert spec.categories == ["book"]
    assert spec.query == "test"
    assert spec.page_size == 10
    assert spec.sort_by == SortBy.DATE_DESC
    
    # Test defaults
    default_spec = SearchSpec()
    assert default_spec.page_size == 20
    assert default_spec.sort_by == SortBy.RELEVANCE
    assert default_spec.record_level == RecLevel.BRIEF


def test_where_method():
    """Test the generic where method."""
    mock_resource = Mock()
    search_obj = Search(mock_resource)
    
    # Test with l- prefix
    search1 = search_obj.where("l-decade", "200")
    assert len(search1._spec.filters) == 1
    assert search1._spec.filters[0].param_name == "l-decade"
    assert search1._spec.filters[0].values == ["200"]
    
    # Test without l- prefix (should be added)
    search2 = search_obj.where("decade", "200")
    assert len(search2._spec.filters) == 1
    assert search2._spec.filters[0].param_name == "l-decade"
    assert search2._spec.filters[0].values == ["200"]
    
    # Test multiple values
    search3 = search_obj.where("format", "Book", "Map")
    assert len(search3._spec.filters) == 1
    assert search3._spec.filters[0].param_name == "l-format"
    assert search3._spec.filters[0].values == ["Book", "Map"]


def test_sort_by_mapping():
    """Test sort by string mapping."""
    mock_resource = Mock()
    search_obj = Search(mock_resource)
    
    # Test string mappings
    assert search_obj.sort_by("relevance")._spec.sort_by == SortBy.RELEVANCE
    assert search_obj.sort_by("date_desc")._spec.sort_by == SortBy.DATE_DESC
    assert search_obj.sort_by("date_asc")._spec.sort_by == SortBy.DATE_ASC
    assert search_obj.sort_by("newest")._spec.sort_by == SortBy.DATE_DESC
    assert search_obj.sort_by("oldest")._spec.sort_by == SortBy.DATE_ASC
    
    # Test enum directly
    assert search_obj.sort_by(SortBy.RELEVANCE)._spec.sort_by == SortBy.RELEVANCE


def test_reclevel_mapping():
    """Test record level string mapping."""
    mock_resource = Mock()
    search_obj = Search(mock_resource)
    
    # Test string mappings
    assert search_obj.with_reclevel("brief")._spec.record_level == RecLevel.BRIEF
    assert search_obj.with_reclevel("full")._spec.record_level == RecLevel.FULL
    assert search_obj.with_reclevel("BRIEF")._spec.record_level == RecLevel.BRIEF  # case insensitive
    
    # Test enum directly
    assert search_obj.with_reclevel(RecLevel.FULL)._spec.record_level == RecLevel.FULL


def test_execution_method_validation():
    """Test that execution methods require categories."""
    mock_resource = Mock()
    search_obj = Search(mock_resource)  # No categories set
    
    with pytest.raises(ValidationError, match="At least one category must be specified"):
        search_obj.first_page()
        
    # Test that the underlying SearchParameters validation works
    params = search_obj._spec.to_parameters()
    with pytest.raises(ValueError, match="At least one category is required"):
        params.validate()


def test_count_method_logic():
    """Test count method uses page_size(0)."""
    mock_resource = Mock()
    mock_result = Mock()
    mock_result.total_results = 42
    mock_resource.page.return_value = mock_result
    
    search_obj = Search(mock_resource).in_("book").text("test")
    
    # Test that page_size(0) is allowed for count operations
    count_search = search_obj.page_size(0)
    assert count_search._spec.page_size == 0
    
    # Test the count method indirectly by checking it builds the right search
    # The count method calls page_size(0).first_page() internally
    count_result = count_search.count()
    assert mock_resource.page.called
    assert count_result == 42