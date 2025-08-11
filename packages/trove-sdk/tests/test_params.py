"""Tests for search parameter functionality."""

import pytest
from trove.params import (
    SearchParameters, ParameterBuilder, build_limits,
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
        params = SearchParameters(category=['book'], n=0)
        with pytest.raises(ValueError, match="Page size .* must be between 1 and 100"):
            params.validate()
            
        params = SearchParameters(category=['book'], n=101)
        with pytest.raises(ValueError, match="Page size .* must be between 1 and 100"):
            params.validate()
            
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


class TestParameterBuilder:
    """Test ParameterBuilder fluent interface."""
    
    def test_basic_builder(self):
        """Test basic parameter building."""
        params = (ParameterBuilder()
                 .categories('book', 'image')
                 .query('Australian history')
                 .page_size(50)
                 .build())
        
        assert params.category == ['book', 'image']
        assert params.q == 'Australian history'
        assert params.n == 50
        
    def test_builder_with_enums(self):
        """Test builder with enum parameters."""
        params = (ParameterBuilder()
                 .categories('book')
                 .sort(SortBy.DATE_DESC)
                 .record_level(RecLevel.FULL)
                 .build())
        
        assert params.sortby == SortBy.DATE_DESC
        assert params.reclevel == RecLevel.FULL
        
    def test_builder_with_string_enums(self):
        """Test builder with string enum values."""
        params = (ParameterBuilder()
                 .categories('book')
                 .sort('datedesc')
                 .record_level('full')
                 .build())
        
        assert params.sortby == SortBy.DATE_DESC
        assert params.reclevel == RecLevel.FULL
        
    def test_builder_date_filters(self):
        """Test builder date filter methods."""
        params = (ParameterBuilder()
                 .categories('newspaper')
                 .decade('200')
                 .year('2015')
                 .month('03')
                 .build())
        
        assert params.l_decade == ['200']
        assert params.l_year == ['2015']
        assert params.l_month == ['03']
        
    def test_builder_multiple_values(self):
        """Test builder methods with multiple values."""
        params = (ParameterBuilder()
                 .categories('book')
                 .decade('190', '200')
                 .format('Book', 'Map')
                 .build())
        
        assert params.l_decade == ['190', '200']
        assert params.l_format == ['Book', 'Map']
        
    def test_builder_boolean_flags(self):
        """Test builder boolean flag methods."""
        params = (ParameterBuilder()
                 .categories('book')
                 .first_australians()
                 .australian_content()
                 .bulk_harvest()
                 .build())
        
        assert params.l_firstAustralians == 'y'
        assert params.l_australian == 'y'
        assert params.bulkHarvest == True
        
    def test_builder_complex_filters(self):
        """Test builder with complex filter combinations."""
        params = (ParameterBuilder()
                 .categories('book')
                 .query('literature')
                 .decade('200')
                 .availability(Availability.FREE_ONLINE)
                 .audience(Audience.ACADEMIC, Audience.GENERAL)
                 .facets('decade', 'format', 'language')
                 .include_fields('tags', 'comments')
                 .build())
        
        assert params.q == 'literature'
        assert params.l_decade == ['200']
        assert params.l_availability == ['y/f']
        assert params.l_audience == ['Academic', 'General']
        assert params.facet == ['decade', 'format', 'language']
        assert params.include == ['tags', 'comments']
        
    def test_builder_validation_error(self):
        """Test that builder validation catches errors."""
        with pytest.raises(ValueError):
            (ParameterBuilder()
             .page_size(101)  # Invalid page size
             .build())
             
    def test_builder_article_types(self):
        """Test article type builder methods."""
        params = (ParameterBuilder()
                 .categories('newspaper')
                 .article_type(ArticleType.NEWSPAPER, ArticleType.GAZETTE)
                 .build())
        
        assert params.l_artType == ['newspaper', 'gazette']
        
    def test_builder_people_filters(self):
        """Test people-specific filter methods."""
        params = (ParameterBuilder()
                 .categories('people')
                 .occupation('Author', 'Journalist')
                 .birth_year('1850')
                 .death_year('1920')
                 .place('Sydney', 'Melbourne')
                 .build())
        
        assert params.l_occupation == ['Author', 'Journalist']
        assert params.l_birth == ['1850']
        assert params.l_death == ['1920']
        assert params.l_place == ['Sydney', 'Melbourne']
        
    def test_builder_content_filters(self):
        """Test content-specific filter methods."""
        params = (ParameterBuilder()
                 .categories('newspaper')
                 .illustrated(True)
                 .word_count(WordCount.LONG)
                 .category_filter('Article', 'Literature')
                 .build())
        
        assert params.l_illustrated == True
        assert params.l_wordCount == ['1000+ Words']
        assert params.l_category == ['Article', 'Literature']
        
    def test_builder_arbitrary_limits(self):
        """Test arbitrary limit parameter method."""
        params = (ParameterBuilder()
                 .categories('book')
                 .limit('l-custom', 'value1', 'value2')
                 .build())
        
        assert params.otherLimits['l-custom'] == 'value1,value2'


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