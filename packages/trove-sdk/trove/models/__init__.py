"""Trove API response models."""

from typing import Dict, Any, Optional, Union
import logging

from .work import Work, WorkVersion, WorkHolding
from .article import Article, ArticleTitle
from .people import People, Biography
from .list import TroveList, ListItem
from .common import Identifier, Language, Spatial, ItemCount, Tag, Comment, Relevance

logger = logging.getLogger(__name__)

# Model registry for automatic conversion
MODEL_REGISTRY = {
    'work': Work,
    'article': Article, 
    'people': People,
    'list': TroveList
}

def parse_record(record_data: Dict[str, Any], record_type: str) -> Optional[Union[Work, Article, People, TroveList]]:
    """Parse raw record data into appropriate model.
    
    Args:
        record_data: Raw record data from API
        record_type: Type of record ('work', 'article', 'people', 'list')
        
    Returns:
        Parsed model instance or None if parsing fails
    """
    model_class = MODEL_REGISTRY.get(record_type.lower())
    if model_class:
        try:
            return model_class(**record_data)
        except Exception as e:
            # Log error but don't fail - return None for raw access
            logger.warning(f"Failed to parse {record_type} record: {e}")
    return None

def parse_records(records_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a collection of records from search results.
    
    Args:
        records_data: Records data from search results
        
    Returns:
        Dict with both raw data and parsed models where available
    """
    parsed = {}
    
    # Map record container names to record types
    record_containers = {
        'work': 'work',
        'article': 'article', 
        'people': 'people',
        'list': 'list'
    }
    
    for container_name, record_type in record_containers.items():
        if container_name in records_data:
            raw_records = records_data[container_name]
            
            # Handle both single record and list of records
            if isinstance(raw_records, dict):
                raw_records = [raw_records]
            elif not isinstance(raw_records, list):
                raw_records = []
            
            parsed_records = []
            for record_data in raw_records:
                if isinstance(record_data, dict):
                    parsed_record = parse_record(record_data, record_type)
                    if parsed_record:
                        parsed_records.append(parsed_record)
                    else:
                        # Keep raw data as fallback
                        parsed_records.append(record_data)
                else:
                    parsed_records.append(record_data)
            
            parsed[container_name] = parsed_records
    
    return parsed

__all__ = [
    'Work', 'WorkVersion', 'WorkHolding',
    'Article', 'ArticleTitle', 
    'People', 'Biography',
    'TroveList', 'ListItem',
    'Identifier', 'Language', 'Spatial', 'ItemCount', 'Tag', 'Comment', 'Relevance',
    'parse_record', 'parse_records', 'MODEL_REGISTRY'
]