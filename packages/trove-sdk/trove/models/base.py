"""Base model classes for Trove API responses."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr


class TroveBaseModel(BaseModel):
    """Base model for all Trove data structures.
    
    This model provides both Pydantic validation and backward compatibility
    with dict-like access patterns. Raw API data is always preserved.
    """
    
    model_config = ConfigDict(
        extra='allow',  # Allow extra fields for future API changes
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,  # Allow both field names and aliases
    )
    
    # Store raw data as private attribute
    _raw_data: Dict[str, Any] = PrivateAttr()
    
    def __init__(self, **data):
        # Store raw data before Pydantic processes it
        super().__init__(**data)
        self._raw_data = data.copy()
    
    @property
    def raw(self) -> Dict[str, Any]:
        """Access to raw API response data."""
        return self._raw_data
    
    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access for backward compatibility."""
        return self._raw_data.get(key)
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator for backward compatibility."""
        return key in self._raw_data
    
    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get method for backward compatibility."""
        return self._raw_data.get(key, default)
    
    def keys(self):
        """Get all keys from raw data."""
        return self._raw_data.keys()
    
    def items(self):
        """Get all items from raw data."""
        return self._raw_data.items()
    
    def values(self):
        """Get all values from raw data."""
        return self._raw_data.values()