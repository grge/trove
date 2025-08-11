"""Title resource implementations for newspaper, magazine, and gazette titles."""

from typing import Dict, Any, List, Union, Optional

from .base import BaseResource


class BaseTitleResource(BaseResource):
    """Base class for title resources (newspaper, magazine, gazette)."""
    
    def __init__(self, transport, title_type: str):
        """Initialize title resource.
        
        Args:
            transport: Transport layer
            title_type: 'newspaper', 'magazine', or 'gazette'
        """
        super().__init__(transport)
        self.title_type = title_type
        
    @property
    def endpoint_path(self) -> str:
        """API endpoint path for title resources."""
        return f"/{self.title_type}/title"
        
    @property
    def valid_include_options(self) -> List[str]:
        """Valid include options for title resources."""
        # Title endpoints have different include patterns than other resources
        return ['years']  # Main include option for titles
        
    def search(self, offset: int = 0, limit: int = 20,
               state: Optional[str] = None,
               place: Optional[Union[str, List[str]]] = None,
               range_param: Optional[str] = None) -> Dict[str, Any]:
        """Search for titles.
        
        Args:
            offset: Starting index for results
            limit: Number of results to return (max 100)
            state: Filter by state (newspapers/gazettes only)
            place: Filter by place (string or list of strings)
            range_param: Date range for issue information
            
        Returns:
            Search results containing titles
        """
        params = {
            'offset': offset,
            'limit': min(limit, 100),  # API maximum
            'encoding': 'json'
        }
        
        if state:
            params['state'] = state
        if place:
            if isinstance(place, list):
                params['place'] = ','.join(place)
            else:
                params['place'] = place
        if range_param:
            params['range'] = range_param
            
        endpoint = f"/{self.title_type}/titles"
        return self.transport.get(endpoint, params)
        
    async def asearch(self, offset: int = 0, limit: int = 20,
                     state: Optional[str] = None,
                     place: Optional[Union[str, List[str]]] = None,
                     range_param: Optional[str] = None) -> Dict[str, Any]:
        """Async version of search.
        
        Args:
            offset: Starting index for results
            limit: Number of results to return (max 100)
            state: Filter by state (newspapers/gazettes only)
            place: Filter by place (string or list of strings)
            range_param: Date range for issue information
            
        Returns:
            Search results containing titles
        """
        params = {
            'offset': offset,
            'limit': min(limit, 100),  # API maximum
            'encoding': 'json'
        }
        
        if state:
            params['state'] = state
        if place:
            if isinstance(place, list):
                params['place'] = ','.join(place)
            else:
                params['place'] = place
        if range_param:
            params['range'] = range_param
            
        endpoint = f"/{self.title_type}/titles"
        return await self.transport.aget(endpoint, params)
        
    def get(self, title_id: Union[str, int],
           include: Optional[List[str]] = None,
           range_param: Optional[str] = None) -> Dict[str, Any]:
        """Get a specific title by ID.
        
        Args:
            title_id: Title identifier
            include: Include options (e.g., 'years')
            range_param: Date range for issue information
            
        Returns:
            Title information
        """
        params = {'encoding': 'json'}
        
        if include and 'years' in include:
            params['include'] = 'years'
        if range_param:
            params['range'] = range_param
            
        endpoint = f"{self.endpoint_path}/{title_id}"
        return self.transport.get(endpoint, params)
        
    async def aget(self, title_id: Union[str, int],
                  include: Optional[List[str]] = None,
                  range_param: Optional[str] = None) -> Dict[str, Any]:
        """Async version of get.
        
        Args:
            title_id: Title identifier
            include: Include options (e.g., 'years')
            range_param: Date range for issue information
            
        Returns:
            Title information
        """
        params = {'encoding': 'json'}
        
        if include and 'years' in include:
            params['include'] = 'years'
        if range_param:
            params['range'] = range_param
            
        endpoint = f"{self.endpoint_path}/{title_id}"
        return await self.transport.aget(endpoint, params)
        
    def get_publication_years(self, title_id: Union[str, int], 
                             date_range: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get publication years for a title.
        
        Args:
            title_id: Title identifier
            date_range: Optional date range in format YYYYMMDD-YYYYMMDD
            
        Returns:
            List of year information dictionaries
        """
        title_data = self.get(title_id, include=['years'], range_param=date_range)
        
        years = []
        if 'year' in title_data:
            year_data = title_data['year']
            if isinstance(year_data, dict):
                years = [year_data]
            elif isinstance(year_data, list):
                years = year_data
                
        return years
        
    async def aget_publication_years(self, title_id: Union[str, int], 
                                    date_range: Optional[str] = None) -> List[Dict[str, Any]]:
        """Async version of get_publication_years.
        
        Args:
            title_id: Title identifier
            date_range: Optional date range in format YYYYMMDD-YYYYMMDD
            
        Returns:
            List of year information dictionaries
        """
        title_data = await self.aget(title_id, include=['years'], range_param=date_range)
        
        years = []
        if 'year' in title_data:
            year_data = title_data['year']
            if isinstance(year_data, dict):
                years = [year_data]
            elif isinstance(year_data, list):
                years = year_data
                
        return years


class NewspaperTitleResource(BaseTitleResource):
    """Resource for newspaper title information."""
    
    def __init__(self, transport):
        """Initialize newspaper title resource."""
        super().__init__(transport, 'newspaper')
        
    def search(self, offset: int = 0, limit: int = 20,
               state: Optional[str] = None,
               place: Optional[Union[str, List[str]]] = None) -> Dict[str, Any]:
        """Search newspaper titles.
        
        Args:
            offset: Starting index for results
            limit: Number of results to return (max 100)
            state: Filter by state ('nsw', 'act', 'qld', 'tas', 'sa', 'nt', 'wa', 'vic', 'national', 'international')
            place: Filter by place (string or list of strings)
            
        Returns:
            Search results containing newspaper titles
        """
        # Valid states for newspapers
        valid_states = ['nsw', 'act', 'qld', 'tas', 'sa', 'nt', 'wa', 'vic', 'national', 'international']
        if state and state not in valid_states:
            raise ValueError(f"Invalid state '{state}'. Valid states: {valid_states}")
            
        return super().search(offset, limit, state, place)
        
    async def asearch(self, offset: int = 0, limit: int = 20,
                     state: Optional[str] = None,
                     place: Optional[Union[str, List[str]]] = None) -> Dict[str, Any]:
        """Async version of search.
        
        Args:
            offset: Starting index for results
            limit: Number of results to return (max 100)
            state: Filter by state ('nsw', 'act', 'qld', 'tas', 'sa', 'nt', 'wa', 'vic', 'national', 'international')
            place: Filter by place (string or list of strings)
            
        Returns:
            Search results containing newspaper titles
        """
        # Valid states for newspapers
        valid_states = ['nsw', 'act', 'qld', 'tas', 'sa', 'nt', 'wa', 'vic', 'national', 'international']
        if state and state not in valid_states:
            raise ValueError(f"Invalid state '{state}'. Valid states: {valid_states}")
            
        return await super().asearch(offset, limit, state, place)


class MagazineTitleResource(BaseTitleResource):
    """Resource for magazine title information."""
    
    def __init__(self, transport):
        """Initialize magazine title resource."""
        super().__init__(transport, 'magazine')


class GazetteTitleResource(BaseTitleResource):
    """Resource for gazette title information."""
    
    def __init__(self, transport):
        """Initialize gazette title resource."""
        super().__init__(transport, 'gazette')
        
    def search(self, offset: int = 0, limit: int = 20,
               state: Optional[str] = None,
               place: Optional[Union[str, List[str]]] = None) -> Dict[str, Any]:
        """Search gazette titles.
        
        Args:
            offset: Starting index for results
            limit: Number of results to return (max 100)
            state: Filter by state ('nsw', 'national', 'international')
            place: Filter by place (string or list of strings)
            
        Returns:
            Search results containing gazette titles
        """
        # Valid states for gazettes (more limited than newspapers)
        valid_states = ['nsw', 'national', 'international']
        if state and state not in valid_states:
            raise ValueError(f"Invalid state '{state}'. Valid states: {valid_states}")
            
        return super().search(offset, limit, state, place)
        
    async def asearch(self, offset: int = 0, limit: int = 20,
                     state: Optional[str] = None,
                     place: Optional[Union[str, List[str]]] = None) -> Dict[str, Any]:
        """Async version of search.
        
        Args:
            offset: Starting index for results
            limit: Number of results to return (max 100)
            state: Filter by state ('nsw', 'national', 'international')
            place: Filter by place (string or list of strings)
            
        Returns:
            Search results containing gazette titles
        """
        # Valid states for gazettes (more limited than newspapers)
        valid_states = ['nsw', 'national', 'international']
        if state and state not in valid_states:
            raise ValueError(f"Invalid state '{state}'. Valid states: {valid_states}")
            
        return await super().asearch(offset, limit, state, place)