"""Tests for search parameter functionality."""

import pytest
from trove.params import (
    SearchParameters, build_limits,
    SortBy, RecLevel, Encoding, ArticleType, Availability, Audience, WordCount
)
from trove.exceptions import ValidationError


class TestSearchParameters:
    """Test SearchParameters dataclass."""
    
    def test_basic_initialization(self):
        """Test basic parameter initialization."""
        params = SearchParameters(category=['book'], q='test')
        assert params.category == ['book']
        assert params.q == 'test'
        assert params.n == 20  # default
        assert params.sortby == SortBy.RELEVANCE  # default
        
    def test_to_query_params_basic(self):
        """Test conversion to query parameters."""
        params = SearchParameters(category=['book'], q='Australian history')
        query_params = params.to_query_params()
        
        expected = {
            'category': 'book',
            'q': 'Australian history',
            's': '*',
            'n': 20,
            'sortby': 'relevance',
            'reclevel': 'brief',
            'encoding': 'json'
        }
        
        assert query_params == expected
        
    def test_to_query_params_with_limits(self):
        """Test query parameter conversion with limit parameters."""
        params = SearchParameters(
            category=['book', 'image'],
            q='Sydney',
            l_decade=['200'],
            l_availability=['y/f'],
            l_firstAustralians='y'
        )
        query_params = params.to_query_params()
        
        assert query_params['category'] == 'book,image'
        assert query_params['l-decade'] == '200'
        assert query_params['l-availability'] == 'y/f'
        assert query_params['l-firstAustralians'] == 'y'
        
    def test_to_query_params_with_lists(self):
        """Test query parameter conversion with list parameters."""
        params = SearchParameters(
            category=['book'],
            l_decade=['190', '200'],
            l_format=['Book', 'Map'],
            include=['tags', 'comments'],
            facet=['decade', 'format']
        )
        query_params = params.to_query_params()
        
        assert query_params['l-decade'] == '190,200'
        assert query_params['l-format'] == 'Book,Map'
        assert query_params['include'] == 'tags,comments'
        assert query_params['facet'] == 'decade,format'
        
    def test_to_query_params_with_boolean_fields(self):
        """Test boolean field conversion."""
        params = SearchParameters(
            category=['newspaper'],
            l_illustrated=True,
            bulkHarvest=True
        )
        query_params = params.to_query_params()
        
        assert query_params['l-illustrated'] == 'true'
        assert query_params['bulkHarvest'] == 'true'
        
    def test_to_query_params_with_other_limits(self):
        """Test other limits parameter handling."""
        params = SearchParameters(
            category=['book'],
            otherLimits={'l-custom': 'value', 'extra-param': 'test'}
        )
        query_params = params.to_query_params()
        
        assert query_params['l-custom'] == 'value'
        assert query_params['extra-param'] == 'test'


class TestParameterValidation:
    """Test parameter validation logic."""
    
    def test_validation_requires_category(self):
        """Test that category is required."""
        params = SearchParameters()
        
        with pytest.raises(ValueError, match="At least one category is required"):
            params.validate()
            
    def test_validation_invalid_category(self):
        """Test validation of category values."""
        params = SearchParameters(category=['invalid_category'])
        
        with pytest.raises(ValueError, match="Invalid categories"):
            params.validate()
            
    def test_validation_valid_categories(self):
        """Test validation passes for valid categories."""
        params = SearchParameters(category=['book', 'image', 'newspaper'])
        params.validate()  # Should not raise
        
    def test_validation_month_requires_year(self):
        """Test that month parameter requires year."""
        params = SearchParameters(
            category=['newspaper'],
            l_month=['03']
        )
        
        with pytest.raises(ValueError, match="l-month requires l-year"):
            params.validate()
            
    def test_validation_newspaper_year_requires_decade(self):
        """Test that newspaper year requires decade."""
        params = SearchParameters(
            category=['newspaper'],
            l_year=['2015']
        )
        
        with pytest.raises(ValueError, match="l-year requires l-decade"):
            params.validate()
            
    def test_validation_boolean_only_fields(self):
        """Test validation of boolean-only fields."""
        params = SearchParameters(
            category=['book'],
            l_firstAustralians='invalid'
        )
        
        with pytest.raises(ValueError, match="can only be 'y' or None"):
            params.validate()
            
    def test_validation_availability_values(self):
        """Test validation of availability values."""
        params = SearchParameters(
            category=['book'],
            l_availability=['invalid']
        )
        
        with pytest.raises(ValueError, match="Invalid availability values"):
            params.validate()
            
    def test_validation_page_size(self):
        """Test validation of page size limits."""
        params = SearchParameters(category=['book'], n=-1)
        with pytest.raises(ValueError, match="Page size .* must be between 0 and 100"):
            params.validate()
            
        params = SearchParameters(category=['book'], n=101)
        with pytest.raises(ValueError, match="Page size .* must be between 0 and 100"):
            params.validate()
            
        # n=0 should be valid (for count operations)
        params = SearchParameters(category=['book'], n=0)
        params.validate()  # Should not raise
            
    def test_validation_article_type_values(self):
        """Test validation of article type values."""
        params = SearchParameters(
            category=['newspaper'],
            l_artType=['invalid']
        )
        
        with pytest.raises(ValueError, match="Invalid article types"):
            params.validate()
            
    def test_validation_audience_values(self):
        """Test validation of audience values."""
        params = SearchParameters(
            category=['book'],
            l_audience=['Invalid']
        )
        
        with pytest.raises(ValueError, match="Invalid audience values"):
            params.validate()
            
    def test_validation_word_count_values(self):
        """Test validation of word count values."""
        params = SearchParameters(
            category=['newspaper'],
            l_wordCount=['Invalid range']
        )
        
        with pytest.raises(ValueError, match="Invalid word count values"):
            params.validate()


class TestBuildLimitsUtility:
    """Test build_limits utility function."""
    
    def test_build_limits_basic(self):
        """Test basic limit parameter building."""
        limits = build_limits(decade=['200'], availability=['y/f'])
        
        expected = {
            'l-decade': '200',
            'l-availability': 'y/f'
        }
        assert limits == expected
        
    def test_build_limits_with_prefix(self):
        """Test limit building with different prefix formats."""
        limits = build_limits(
            decade=['200'],  # No prefix
            l_year=['2015'],  # Underscore prefix
            **{'l-month': ['03']}  # Hyphen prefix
        )
        
        expected = {
            'l-decade': '200',
            'l-year': '2015',
            'l-month': '03'
        }
        assert limits == expected
        
    def test_build_limits_multiple_values(self):
        """Test limit building with multiple values."""
        limits = build_limits(
            format=['Book', 'Map'],
            state=['NSW', 'VIC']
        )
        
        assert limits['l-format'] == 'Book,Map'
        assert limits['l-state'] == 'NSW,VIC'
        
    def test_build_limits_boolean_values(self):
        """Test limit building with boolean values."""
        limits = build_limits(
            illustrated=True,
            australian='y'
        )
        
        assert limits['l-illustrated'] == 'true'
        assert limits['l-australian'] == 'y'


@pytest.mark.parametrize("category,params,should_pass", [
    # Valid combinations
    (['book'], {'l_decade': ['200'], 'l_availability': ['y']}, True),
    (['newspaper'], {'l_decade': ['200'], 'l_year': ['2015']}, True),
    (['newspaper'], {'l_decade': ['200'], 'l_year': ['2015'], 'l_month': ['03']}, True),
    
    # Invalid combinations
    (['newspaper'], {'l_year': ['2015']}, False),  # newspaper year without decade
    (['book'], {'l_month': ['03']}, False),  # month without year
])
def test_parameter_dependencies(category, params, should_pass):
    """Test parameter dependency validation."""
    search_params = SearchParameters(category=category, **params)
    
    if should_pass:
        search_params.validate()  # Should not raise
    else:
        with pytest.raises(ValueError):
            search_params.validate()