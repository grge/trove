"""Base resource class for all Trove API endpoints."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import logging

from ..transport import TroveTransport
from ..exceptions import ResourceNotFoundError, ValidationError, TroveAPIError

logger = logging.getLogger(__name__)


class RecLevel(Enum):
    """Record level enumeration."""
    BRIEF = "brief"
    FULL = "full"


class Encoding(Enum):
    """Response encoding enumeration."""
    JSON = "json"
    XML = "xml"


class BaseResource(ABC):
    """Base class for all resource types with common functionality."""
    
    def __init__(self, transport: TroveTransport):
        """Initialize resource with transport layer.
        
        Args:
            transport: Transport layer for API communication
        """
        self.transport = transport
        
    @property
    @abstractmethod
    def endpoint_path(self) -> str:
        """The API endpoint path for this resource type."""
        pass
        
    @property
    @abstractmethod  
    def valid_include_options(self) -> List[str]:
        """Valid include options for this resource type."""
        pass
        
    def get(self, resource_id: Union[str, int], 
           include: Optional[List[str]] = None,
           reclevel: Union[str, RecLevel] = RecLevel.BRIEF,
           encoding: Union[str, Encoding] = Encoding.JSON) -> Dict[str, Any]:
        """Get a single resource by ID.
        
        Args:
            resource_id: The resource identifier
            include: Optional fields to include in response
            reclevel: Level of detail (brief or full)  
            encoding: Response format (json or xml)
            
        Returns:
            Resource data as dictionary
            
        Raises:
            ResourceNotFoundError: Resource doesn't exist
            ValidationError: Invalid parameters
            TroveAPIError: Other API errors
        """
        # Validate and normalize parameters
        include = self._validate_include_params(include or [])
        reclevel = self._normalize_reclevel(reclevel)
        encoding = self._normalize_encoding(encoding)
        
        # Build request parameters
        params = {
            'reclevel': reclevel.value,
            'encoding': encoding.value
        }
        
        if include:
            params['include'] = ','.join(include)
            
        # Construct endpoint URL
        endpoint = f"{self.endpoint_path}/{resource_id}"
        
        try:
            logger.info(f"Fetching {self.__class__.__name__} {resource_id} with reclevel={reclevel.value}")
            
            response = self.transport.get(endpoint, params)
            
            # Post-process response if needed
            return self._post_process_response(response, resource_id)
            
        except TroveAPIError as e:
            if e.status_code == 404:
                raise ResourceNotFoundError(f"Resource {resource_id} not found") from e
            raise
            
    async def aget(self, resource_id: Union[str, int],
                  include: Optional[List[str]] = None, 
                  reclevel: Union[str, RecLevel] = RecLevel.BRIEF,
                  encoding: Union[str, Encoding] = Encoding.JSON) -> Dict[str, Any]:
        """Async version of get method.
        
        Args:
            resource_id: The resource identifier
            include: Optional fields to include in response
            reclevel: Level of detail (brief or full)  
            encoding: Response format (json or xml)
            
        Returns:
            Resource data as dictionary
            
        Raises:
            ResourceNotFoundError: Resource doesn't exist
            ValidationError: Invalid parameters
            TroveAPIError: Other API errors
        """
        # Validate and normalize parameters
        include = self._validate_include_params(include or [])
        reclevel = self._normalize_reclevel(reclevel)
        encoding = self._normalize_encoding(encoding)
        
        params = {
            'reclevel': reclevel.value,
            'encoding': encoding.value
        }
        
        if include:
            params['include'] = ','.join(include)
            
        endpoint = f"{self.endpoint_path}/{resource_id}"
        
        try:
            logger.info(f"Async fetching {self.__class__.__name__} {resource_id} with reclevel={reclevel.value}")
            
            response = await self.transport.aget(endpoint, params)
            return self._post_process_response(response, resource_id)
            
        except TroveAPIError as e:
            if e.status_code == 404:
                raise ResourceNotFoundError(f"Resource {resource_id} not found") from e
            raise
    
    def _validate_include_params(self, include: List[str]) -> List[str]:
        """Validate include parameters against valid options.
        
        Args:
            include: List of include parameters to validate
            
        Returns:
            Validated include parameters
            
        Raises:
            ValidationError: If invalid include options are provided
        """
        valid_options = set(self.valid_include_options)
        invalid_options = set(include) - valid_options
        
        if invalid_options:
            valid_str = ', '.join(sorted(valid_options))
            invalid_str = ', '.join(sorted(invalid_options))
            raise ValidationError(
                f"Invalid include options: {invalid_str}. "
                f"Valid options for {self.__class__.__name__}: {valid_str}"
            )
            
        return include
        
    def _normalize_reclevel(self, reclevel: Union[str, RecLevel]) -> RecLevel:
        """Normalize reclevel parameter to enum.
        
        Args:
            reclevel: String or enum value for record level
            
        Returns:
            RecLevel enum value
            
        Raises:
            ValidationError: If invalid reclevel is provided
        """
        if isinstance(reclevel, str):
            try:
                return RecLevel(reclevel.lower())
            except ValueError:
                raise ValidationError(f"Invalid reclevel: {reclevel}. Must be 'brief' or 'full'")
        return reclevel
        
    def _normalize_encoding(self, encoding: Union[str, Encoding]) -> Encoding:
        """Normalize encoding parameter to enum.
        
        Args:
            encoding: String or enum value for encoding
            
        Returns:
            Encoding enum value
            
        Raises:
            ValidationError: If invalid encoding is provided
        """
        if isinstance(encoding, str):
            try:
                return Encoding(encoding.lower())
            except ValueError:
                raise ValidationError(f"Invalid encoding: {encoding}. Must be 'json' or 'xml'")
        return encoding
        
    def _post_process_response(self, response: Dict[str, Any], resource_id: Union[str, int]) -> Dict[str, Any]:
        """Post-process response data. Override in subclasses if needed.
        
        Args:
            response: Raw response from API
            resource_id: The resource ID that was requested
            
        Returns:
            Post-processed response data
        """
        return response