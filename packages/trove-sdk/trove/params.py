"""Comprehensive search parameters for the Trove API v3."""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import warnings


class SortBy(Enum):
    """Sort order options for search results."""
    RELEVANCE = "relevance"
    DATE_DESC = "datedesc" 
    DATE_ASC = "dateasc"


class RecLevel(Enum):
    """Record detail level options."""
    BRIEF = "brief"
    FULL = "full"


class Encoding(Enum):
    """Response encoding format options."""
    JSON = "json"
    XML = "xml"


class ArticleType(Enum):
    """Article type filters for limiting searches within categories."""
    # For newspaper category
    NEWSPAPER = "newspaper"
    GAZETTE = "gazette"
    
    # For image category
    IMAGES_AND_ARTEFACTS = "images and artefacts"
    MAPS = "maps"
    
    # For people category
    PERSON = "person"
    ORGANISATION = "organisation"


class Availability(Enum):
    """Online availability options."""
    ONLINE = "y"
    FREE_ONLINE = "y/f"
    PAYMENT_REQUIRED = "y/r"  
    SUBSCRIPTION_REQUIRED = "y/s"
    POSSIBLY_ONLINE = "y/u"


class Audience(Enum):
    """Target audience options (Gale articles only)."""
    TRADE = "Trade"
    GENERAL = "General"
    ACADEMIC = "Academic"
    PROFESSIONAL = "Professional"
    CHILDRENS = "Children's"
    CHILDRENS_UPPER = "Children's - Upper elementary"
    CHILDRENS_LOWER = "Children's - Lower elementary"


class WordCount(Enum):
    """Article word count ranges."""
    SHORT = "<100 Words"
    MEDIUM = "100 - 1000 Words"
    LONG = "1000+ Words"


@dataclass
class SearchParameters:
    """Comprehensive search parameters based on Trove API v3 specification."""
    
    # Required parameters
    category: List[str] = field(default_factory=list)
    
    # Core search parameters  
    q: Optional[str] = None
    
    # Pagination and results
    s: str = "*"  # start cursor
    n: int = 20   # number of results
    sortby: SortBy = SortBy.RELEVANCE
    bulkHarvest: bool = False
    
    # Response control
    reclevel: RecLevel = RecLevel.BRIEF
    encoding: Encoding = Encoding.JSON
    include: List[str] = field(default_factory=list)
    facet: List[str] = field(default_factory=list)
    
    # Date and time filters
    l_decade: List[str] = field(default_factory=list)
    l_year: List[str] = field(default_factory=list) 
    l_month: List[str] = field(default_factory=list)
    
    # Format and content type
    l_format: List[str] = field(default_factory=list)
    l_artType: List[str] = field(default_factory=list)
    
    # Language and cultural
    l_language: List[str] = field(default_factory=list)
    l_austlanguage: List[str] = field(default_factory=list)
    l_firstAustralians: Optional[str] = None  # "y" only
    l_culturalSensitivity: Optional[str] = None  # "y" only
    
    # Geographic
    l_geocoverage: List[str] = field(default_factory=list)
    l_place: List[str] = field(default_factory=list)
    l_state: List[str] = field(default_factory=list)
    
    # Contributor and collection
    l_contribcollection: Optional[str] = None
    l_partnerNuc: List[str] = field(default_factory=list)
    
    # Availability
    l_availability: List[str] = field(default_factory=list)
    l_australian: Optional[str] = None  # "y" only
    
    # People-specific
    l_occupation: List[str] = field(default_factory=list)
    l_birth: List[str] = field(default_factory=list)
    l_death: List[str] = field(default_factory=list)
    
    # Content specific  
    l_zoom: List[str] = field(default_factory=list)
    l_audience: List[str] = field(default_factory=list)
    l_title: List[str] = field(default_factory=list)
    l_category: List[str] = field(default_factory=list)
    l_illustrated: Optional[bool] = None
    l_illustrationType: List[str] = field(default_factory=list)
    l_wordCount: List[str] = field(default_factory=list)
    
    # Additional limits (for extensibility)
    otherLimits: Dict[str, Any] = field(default_factory=dict)
    
    def to_query_params(self) -> Dict[str, Any]:
        """Convert to query parameters for API request."""
        params = {}
        
        # Required category parameter
        if not self.category:
            raise ValueError("At least one category is required")
        params['category'] = ','.join(self.category)
        
        # Optional query
        if self.q is not None:
            params['q'] = self.q
            
        # Pagination
        params['s'] = self.s
        params['n'] = self.n
        params['sortby'] = self.sortby.value
        if self.bulkHarvest:
            params['bulkHarvest'] = 'true'
            
        # Response control
        params['reclevel'] = self.reclevel.value if hasattr(self.reclevel, 'value') else self.reclevel
        params['encoding'] = self.encoding.value if hasattr(self.encoding, 'value') else self.encoding
        
        if self.include:
            params['include'] = ','.join(self.include)
        if self.facet:
            params['facet'] = ','.join(self.facet)
            
        # Add limit parameters (l-*)
        limit_fields = [f for f in dir(self) if f.startswith('l_')]
        for field_name in limit_fields:
            api_name = field_name.replace('_', '-')
            value = getattr(self, field_name)
            
            if value is None:
                continue
            elif isinstance(value, list) and value:
                params[api_name] = ','.join(str(v) for v in value)
            elif isinstance(value, bool):
                params[api_name] = str(value).lower()
            elif isinstance(value, str):
                params[api_name] = value
                
        # Add other limits
        params.update(self.otherLimits)
        
        return params
        
    def validate(self) -> None:
        """Validate parameter combinations and dependencies."""
        if not self.category:
            raise ValueError("At least one category is required")
            
        # Validate category values
        valid_categories = {
            'all', 'book', 'diary', 'image', 'list', 
            'magazine', 'music', 'newspaper', 'people', 'research'
        }
        invalid_categories = set(self.category) - valid_categories
        if invalid_categories:
            raise ValueError(f"Invalid categories: {invalid_categories}")
            
        # Check parameter dependencies
        if self.l_month and not self.l_year:
            raise ValueError("l-month requires l-year to also be specified")
            
        if 'newspaper' in self.category and self.l_year and not self.l_decade:
            raise ValueError("For newspapers, l-year requires l-decade to also be specified")
            
        # Check boolean-only fields
        boolean_only_fields = ['l_firstAustralians', 'l_culturalSensitivity', 'l_australian']
        for field_name in boolean_only_fields:
            value = getattr(self, field_name)
            if value is not None and value != 'y':
                raise ValueError(f"{field_name} can only be 'y' or None")
                
        # Validate availability values  
        if self.l_availability:
            valid_availability = {'y', 'y/f', 'y/r', 'y/s', 'y/u'}
            invalid_availability = set(self.l_availability) - valid_availability
            if invalid_availability:
                raise ValueError(f"Invalid availability values: {invalid_availability}")
        
        # Validate page size
        if self.n < 1 or self.n > 100:
            raise ValueError("Page size (n) must be between 1 and 100")
            
        # Validate article type values
        if self.l_artType:
            valid_art_types = {e.value for e in ArticleType}
            invalid_art_types = set(self.l_artType) - valid_art_types
            if invalid_art_types:
                raise ValueError(f"Invalid article types: {invalid_art_types}")
                
        # Validate audience values
        if self.l_audience:
            valid_audiences = {e.value for e in Audience}
            invalid_audiences = set(self.l_audience) - valid_audiences
            if invalid_audiences:
                raise ValueError(f"Invalid audience values: {invalid_audiences}")
                
        # Validate word count values
        if self.l_wordCount:
            valid_word_counts = {e.value for e in WordCount}
            invalid_word_counts = set(self.l_wordCount) - valid_word_counts
            if invalid_word_counts:
                raise ValueError(f"Invalid word count values: {invalid_word_counts}")


class ParameterBuilder:
    """Builder for constructing search parameters with validation."""
    
    def __init__(self):
        self._params = SearchParameters()
        
    def categories(self, *categories: str) -> 'ParameterBuilder':
        """Set search categories."""
        self._params.category = list(categories)
        return self
        
    def query(self, q: str) -> 'ParameterBuilder':
        """Set search query."""
        self._params.q = q
        return self
        
    def page_size(self, n: int) -> 'ParameterBuilder':
        """Set number of results per page."""
        if n < 1 or n > 100:
            raise ValueError("Page size must be between 1 and 100")
        self._params.n = n
        return self
        
    def cursor(self, s: str) -> 'ParameterBuilder':
        """Set pagination cursor."""
        self._params.s = s
        return self
        
    def sort(self, sortby: Union[str, SortBy]) -> 'ParameterBuilder':
        """Set sort order."""
        if isinstance(sortby, str):
            sortby = SortBy(sortby)
        self._params.sortby = sortby
        return self
        
    def bulk_harvest(self, enabled: bool = True) -> 'ParameterBuilder':
        """Enable bulk harvest mode."""
        self._params.bulkHarvest = enabled
        return self
        
    def record_level(self, reclevel: Union[str, RecLevel]) -> 'ParameterBuilder':
        """Set record detail level."""
        if isinstance(reclevel, str):
            reclevel = RecLevel(reclevel)
        self._params.reclevel = reclevel
        return self
        
    def include_fields(self, *fields: str) -> 'ParameterBuilder':
        """Include optional fields in results."""
        self._params.include = list(fields)
        return self
        
    def facets(self, *facets: str) -> 'ParameterBuilder':
        """Request facet information."""
        self._params.facet = list(facets)
        return self
        
    def decade(self, *decades: str) -> 'ParameterBuilder':
        """Filter by publication decade(s)."""
        self._params.l_decade = list(decades)
        return self
        
    def year(self, *years: str) -> 'ParameterBuilder':
        """Filter by publication year(s)."""
        self._params.l_year = list(years)
        return self
        
    def month(self, *months: str) -> 'ParameterBuilder':
        """Filter by publication month(s)."""
        self._params.l_month = list(months)
        return self
        
    def format(self, *formats: str) -> 'ParameterBuilder':
        """Filter by format(s)."""
        self._params.l_format = list(formats)
        return self
        
    def article_type(self, *types: Union[str, ArticleType]) -> 'ParameterBuilder':
        """Filter by article type(s)."""
        type_values = []
        for t in types:
            if isinstance(t, ArticleType):
                type_values.append(t.value)
            else:
                type_values.append(t)
        self._params.l_artType = type_values
        return self
        
    def language(self, *languages: str) -> 'ParameterBuilder':
        """Filter by language(s)."""
        self._params.l_language = list(languages)
        return self
        
    def aboriginal_language(self, *languages: str) -> 'ParameterBuilder':
        """Filter by Aboriginal and Torres Strait Islander language(s)."""
        self._params.l_austlanguage = list(languages)
        return self
        
    def first_australians(self) -> 'ParameterBuilder':
        """Filter for First Australians content."""
        self._params.l_firstAustralians = 'y'
        return self
        
    def cultural_sensitivity(self) -> 'ParameterBuilder':
        """Filter for culturally sensitive content."""
        self._params.l_culturalSensitivity = 'y'
        return self
        
    def geographic_coverage(self, *regions: str) -> 'ParameterBuilder':
        """Filter by geographic coverage."""
        self._params.l_geocoverage = list(regions)
        return self
        
    def place(self, *places: str) -> 'ParameterBuilder':
        """Filter by place (people/organisations)."""
        self._params.l_place = list(places)
        return self
        
    def state(self, *states: str) -> 'ParameterBuilder':
        """Filter by state (newspapers).""" 
        self._params.l_state = list(states)
        return self
        
    def contributing_collection(self, collection: str) -> 'ParameterBuilder':
        """Filter by contributing collection."""
        self._params.l_contribcollection = collection
        return self
        
    def partner_nuc(self, *nucs: str) -> 'ParameterBuilder':
        """Filter by partner NUC codes."""
        self._params.l_partnerNuc = list(nucs)
        return self
        
    def availability(self, *availability: Union[str, Availability]) -> 'ParameterBuilder':
        """Filter by availability."""
        avail_values = []
        for a in availability:
            if isinstance(a, Availability):
                avail_values.append(a.value)
            else:
                avail_values.append(a)
        self._params.l_availability = avail_values
        return self
        
    def australian_content(self) -> 'ParameterBuilder':
        """Filter for Australian content."""
        self._params.l_australian = 'y'
        return self
        
    def occupation(self, *occupations: str) -> 'ParameterBuilder':
        """Filter by occupation(s)."""
        self._params.l_occupation = list(occupations)
        return self
        
    def birth_year(self, *years: str) -> 'ParameterBuilder':
        """Filter by birth/establishment year(s)."""
        self._params.l_birth = list(years)
        return self
        
    def death_year(self, *years: str) -> 'ParameterBuilder':
        """Filter by death/dissolution year(s)."""
        self._params.l_death = list(years)
        return self
        
    def map_scale(self, *scales: str) -> 'ParameterBuilder':
        """Filter by map scale(s)."""
        self._params.l_zoom = list(scales)
        return self
        
    def audience(self, *audiences: Union[str, Audience]) -> 'ParameterBuilder':
        """Filter by target audience(s)."""
        audience_values = []
        for a in audiences:
            if isinstance(a, Audience):
                audience_values.append(a.value)
            else:
                audience_values.append(a)
        self._params.l_audience = audience_values
        return self
        
    def title(self, *titles: str) -> 'ParameterBuilder':
        """Filter by publication title ID(s)."""
        self._params.l_title = list(titles)
        return self
        
    def category_filter(self, *categories: str) -> 'ParameterBuilder':
        """Filter by article category (different from main category)."""
        self._params.l_category = list(categories)
        return self
        
    def illustrated(self, illustrated: bool) -> 'ParameterBuilder':
        """Filter by illustration presence."""
        self._params.l_illustrated = illustrated
        return self
        
    def illustration_type(self, *types: str) -> 'ParameterBuilder':
        """Filter by illustration type(s)."""
        self._params.l_illustrationType = list(types)
        return self
        
    def word_count(self, *counts: Union[str, WordCount]) -> 'ParameterBuilder':
        """Filter by word count range(s)."""
        count_values = []
        for c in counts:
            if isinstance(c, WordCount):
                count_values.append(c.value)
            else:
                count_values.append(c)
        self._params.l_wordCount = count_values
        return self
        
    def limit(self, param: str, *values: str) -> 'ParameterBuilder':
        """Add arbitrary limit parameter."""
        self._params.otherLimits[param] = ','.join(values) if len(values) > 1 else values[0]
        return self
        
    def build(self) -> SearchParameters:
        """Build and validate parameters."""
        self._params.validate()
        return self._params


def build_limits(**limits) -> Dict[str, str]:
    """Utility function to build limit parameters from keyword arguments.
    
    Args:
        **limits: Limit parameters as keyword arguments
        
    Returns:
        Dictionary of formatted limit parameters
        
    Examples:
        build_limits(decade=['200'], availability=['y/f'], australian='y')
        # Returns: {'l-decade': '200', 'l-availability': 'y/f', 'l-australian': 'y'}
    """
    result = {}
    
    for key, value in limits.items():
        # Convert underscore to hyphen for API parameter format
        if key.startswith('l_'):
            api_key = key.replace('_', '-')
        elif not key.startswith('l-'):
            api_key = f'l-{key}'
        else:
            api_key = key
            
        # Format value appropriately
        if isinstance(value, list):
            result[api_key] = ','.join(str(v) for v in value)
        elif isinstance(value, bool):
            result[api_key] = str(value).lower()
        else:
            result[api_key] = str(value)
            
    return result