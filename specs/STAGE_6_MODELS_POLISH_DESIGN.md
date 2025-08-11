# Stage 6 - Models & Polish Design Document

## Overview

Stage 6 adds optional Pydantic models for type safety, implements performance optimizations, enhances error handling, and prepares the SDK for production deployment. This stage also generates comprehensive API documentation and implements production-ready logging and monitoring.

## Design Goals

- **Optional Type Safety** - Pydantic models without breaking raw dict access
- **Production Ready** - Enhanced logging, monitoring, error handling
- **Performance Optimized** - Connection pooling, response streaming, batch operations
- **Complete Documentation** - Auto-generated API reference with examples
- **Developer Experience** - Better error messages, debugging tools, IDE support
- **Deployment Ready** - Package configuration, CI/CD integration

## Architecture Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Production Interface                           │
├─────────────────────────────────────────────────────────────────────┤
│   Models   │ Monitoring │ Enhanced Errors │ Performance │ Docs      │
├────────────┼────────────┼─────────────────┼─────────────┼───────────┤
│                    Core SDK (Stages 1-5)                           │
└─────────────────────────────────────────────────────────────────────┘
```

## Detailed Component Design

### 1. Optional Pydantic Models (`trove/models/`)

```python
# trove/models/base.py
from typing import Dict, Any, Optional, List, Union, get_type_hints
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime

class TroveBaseModel(BaseModel):
    """Base model for all Trove data structures."""
    
    model_config = ConfigDict(
        extra='allow',  # Allow extra fields for future API changes
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    def __init__(self, **data):
        # Store raw data for direct access
        self._raw_data = data.copy()
        super().__init__(**data)
    
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

# trove/models/work.py
from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator
from .base import TroveBaseModel
from .common import Contributor, Identifier, Language, Subject

class WorkVersion(TroveBaseModel):
    """Represents a version/edition within a work."""
    id: Optional[str] = None
    title: Optional[str] = None
    contributor: List[str] = Field(default_factory=list)
    publisher: Optional[str] = None
    date: Optional[str] = None
    format: List[str] = Field(default_factory=list)
    isbn: List[str] = Field(default_factory=list)
    
class WorkHolding(TroveBaseModel):
    """Represents library holding information."""
    library: Optional[str] = None
    call_number: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None

class Work(TroveBaseModel):
    """
    Represents a Trove work record with optional type safety.
    
    Always provides raw dict access via .raw property and dict-like methods
    for backward compatibility and future API changes.
    """
    
    # Core identification
    id: str
    title: Optional[str] = None
    url: Optional[str] = None
    trove_url: Optional[str] = Field(None, alias='troveUrl')
    
    # Content metadata
    contributor: List[str] = Field(default_factory=list)
    issued: Optional[str] = None
    type: List[str] = Field(default_factory=list)
    format: List[str] = Field(default_factory=list)
    subject: List[str] = Field(default_factory=list)
    abstract: Optional[str] = None
    
    # Publication info
    publisher: List[str] = Field(default_factory=list)
    place_of_publication: List[str] = Field(default_factory=list, alias='placeOfPublication')
    extent: Optional[str] = None
    language: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Relationships
    is_part_of: List[Dict[str, Any]] = Field(default_factory=list, alias='isPartOf')
    identifier: List[Dict[str, Any]] = Field(default_factory=list)
    
    # User-generated content
    tag_count: List[Dict[str, Any]] = Field(default_factory=list, alias='tagCount')
    comment_count: List[Dict[str, Any]] = Field(default_factory=list, alias='commentCount')
    list_count: Optional[int] = Field(None, alias='listCount')
    
    # Quantitative data
    holdings_count: Optional[int] = Field(None, alias='holdingsCount')
    version_count: Optional[int] = Field(None, alias='versionCount')
    
    # Cultural sensitivity
    culturally_sensitive: Optional[str] = Field(None, alias='culturallySensitive')
    first_australians: Optional[str] = Field(None, alias='firstAustralians')
    
    # Complex nested objects (when includes are used)
    version: List[WorkVersion] = Field(default_factory=list)
    holding: List[WorkHolding] = Field(default_factory=list)
    
    @field_validator('contributor', 'type', 'format', 'subject', 'publisher', 'place_of_publication', mode='before')
    @classmethod
    def ensure_list(cls, v):
        """Ensure certain fields are always lists."""
        if v is None:
            return []
        elif isinstance(v, (str, dict)):
            return [v]
        elif isinstance(v, list):
            return v
        return []
    
    @property
    def primary_title(self) -> str:
        """Get the primary title, with fallback."""
        return self.title or "Untitled Work"
    
    @property
    def primary_contributor(self) -> Optional[str]:
        """Get the first contributor."""
        return self.contributor[0] if self.contributor else None
    
    @property
    def publication_year(self) -> Optional[int]:
        """Extract publication year from issued date."""
        if not self.issued:
            return None
        import re
        match = re.search(r'(\d{4})', self.issued)
        return int(match.group(1)) if match else None
    
    @property
    def is_online(self) -> bool:
        """Check if work has online availability."""
        # This would check various fields to determine online availability
        return any('online' in str(item).lower() for item in self.identifier)

# trove/models/article.py
class ArticleTitle(TroveBaseModel):
    """Represents newspaper/gazette title information."""
    id: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None

class Article(TroveBaseModel):
    """
    Represents a Trove newspaper/gazette article with optional type safety.
    """
    
    # Core identification
    id: str
    url: Optional[str] = None
    identifier: Optional[str] = None
    trove_url: Optional[str] = Field(None, alias='troveUrl')
    trove_page_url: Optional[str] = Field(None, alias='trovePageUrl')
    
    # Content
    heading: Optional[str] = None
    category: Optional[str] = None
    article_text: Optional[str] = Field(None, alias='articleText')
    
    # Publication info
    title: Optional[ArticleTitle] = None
    date: Optional[str] = None
    page: Optional[str] = None
    page_sequence: Optional[str] = Field(None, alias='pageSequence')
    page_label: Optional[str] = Field(None, alias='pageLabel')
    edition: Optional[str] = None
    supplement: Optional[str] = None
    section: Optional[str] = None
    
    # Article characteristics
    illustrated: Optional[str] = None
    word_count: Optional[str] = Field(None, alias='wordCount')
    
    # Status and corrections
    status: Optional[str] = None
    correction_count: Optional[str] = Field(None, alias='correctionCount')
    last_correction: Optional[Dict[str, Any]] = Field(None, alias='lastCorrection')
    
    # User content
    tag_count: Optional[str] = Field(None, alias='tagCount')
    comment_count: Optional[str] = Field(None, alias='commentCount')
    list_count: Optional[str] = Field(None, alias='listCount')
    
    # Resources
    pdf: List[str] = Field(default_factory=list)
    
    @property
    def display_title(self) -> str:
        """Get displayable title/heading."""
        return self.heading or "Untitled Article"
    
    @property
    def newspaper_title(self) -> Optional[str]:
        """Get newspaper title."""
        if isinstance(self.title, dict):
            return self.title.get('title')
        return str(self.title) if self.title else None
    
    @property
    def has_full_text(self) -> bool:
        """Check if article has full text available."""
        return bool(self.article_text and self.article_text.strip())
    
    @property
    def is_illustrated(self) -> bool:
        """Check if article is illustrated."""
        return self.illustrated == 'Y'

# trove/models/people.py  
class Biography(TroveBaseModel):
    """Biographical information."""
    contributor: Optional[str] = None
    contributor_id: Optional[str] = Field(None, alias='contributorId')
    biography: Optional[str] = None

class People(TroveBaseModel):
    """
    Represents a Trove people/organisation record with optional type safety.
    """
    
    # Core identification
    id: str
    url: Optional[str] = None
    trove_url: Optional[str] = Field(None, alias='troveUrl')
    type: Optional[str] = None  # person, corporatebody, family
    
    # Names
    primary_name: Optional[str] = Field(None, alias='primaryName')
    primary_display_name: Optional[str] = Field(None, alias='primaryDisplayName')
    alternate_name: List[str] = Field(default_factory=list, alias='alternateName')
    alternate_display_name: List[str] = Field(default_factory=list, alias='alternateDisplayName')
    
    # Disambiguation
    disambiguation: Optional[bool] = None
    disambiguation_name: List[Dict[str, Any]] = Field(default_factory=list, alias='disambiguationName')
    
    # Person-specific
    title: List[str] = Field(default_factory=list)
    occupation: List[str] = Field(default_factory=list)
    
    # Biography
    biography: List[Biography] = Field(default_factory=list)
    
    # Metadata
    contributor: List[Dict[str, Any]] = Field(default_factory=list)
    identifier: List[Dict[str, Any]] = Field(default_factory=list)
    
    # User content
    tag_count: Optional[int] = Field(None, alias='tagCount')
    comment_count: Optional[int] = Field(None, alias='commentCount')
    list_count: Optional[int] = Field(None, alias='listCount')
    
    # Cultural sensitivity
    culturally_sensitive: Optional[str] = Field(None, alias='culturallySensitive')
    first_australians: Optional[str] = Field(None, alias='firstAustralians')
    
    @property
    def display_name(self) -> str:
        """Get primary display name with fallback."""
        return (self.primary_display_name or 
                self.primary_name or 
                "Unnamed Entity")
    
    @property
    def is_person(self) -> bool:
        """Check if record represents a person."""
        return self.type == 'person'
    
    @property
    def is_organization(self) -> bool:
        """Check if record represents an organization."""
        return self.type in ['corporatebody', 'family']

# trove/models/list.py
class ListItem(TroveBaseModel):
    """Represents an item within a list."""
    # Structure depends on item type (work, article, etc.)
    pass

class List(TroveBaseModel):
    """
    Represents a Trove user list with optional type safety.
    """
    
    # Core identification
    id: str
    url: Optional[str] = None
    trove_url: Optional[str] = Field(None, alias='troveUrl')
    
    # Content
    title: Optional[str] = None
    description: Optional[str] = None
    
    # Creator info
    creator: Optional[str] = None
    by: Optional[str] = None  # Alternative creator field
    
    # List properties
    list_item_count: Optional[int] = Field(None, alias='listItemCount')
    
    # Timestamps
    last_updated: Optional[str] = Field(None, alias='lastupdated')
    date: Optional[Dict[str, str]] = None
    
    # User content
    tag_count: Optional[Dict[str, Any]] = Field(None, alias='tagCount')
    comment_count: Optional[Dict[str, Any]] = Field(None, alias='commentCount')
    
    # List contents (when included)
    list_item: List[ListItem] = Field(default_factory=list, alias='listItem')
    
    @property
    def display_title(self) -> str:
        """Get displayable title."""
        return self.title or "Untitled List"
    
    @property
    def creator_name(self) -> str:
        """Get creator name with fallback."""
        return self.creator or self.by or "Anonymous"
    
    @property
    def item_count(self) -> int:
        """Get number of items in list."""
        return self.list_item_count or len(self.list_item)

# trove/models/__init__.py
from .work import Work, WorkVersion, WorkHolding
from .article import Article, ArticleTitle
from .people import People, Biography
from .list import List, ListItem
from .common import *

# Model registry for automatic conversion
MODEL_REGISTRY = {
    'work': Work,
    'article': Article, 
    'people': People,
    'list': List
}

def parse_record(record_data: Dict[str, Any], record_type: str) -> Optional[TroveBaseModel]:
    """Parse raw record data into appropriate model."""
    model_class = MODEL_REGISTRY.get(record_type.lower())
    if model_class:
        try:
            return model_class(**record_data)
        except Exception as e:
            # Log error but don't fail - return None for raw access
            import logging
            logging.warning(f"Failed to parse {record_type} record: {e}")
    return None

__all__ = ['Work', 'Article', 'People', 'List', 'parse_record', 'MODEL_REGISTRY']
```

### 2. Enhanced Error Handling (`trove/errors.py`)

```python
import traceback
from typing import Dict, Any, Optional, List
import logging
from .exceptions import TroveError, TroveAPIError

logger = logging.getLogger(__name__)

class EnhancedErrorHandler:
    """Enhanced error handling with context and debugging info."""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
    
    def wrap_api_error(self, error: Exception, context: Dict[str, Any]) -> TroveAPIError:
        """Wrap any error with context and debugging information."""
        
        # Extract meaningful error message
        if isinstance(error, TroveAPIError):
            base_message = str(error)
            status_code = error.status_code
        else:
            base_message = str(error)
            status_code = None
        
        # Build context information
        context_parts = []
        if context.get('endpoint'):
            context_parts.append(f"endpoint: {context['endpoint']}")
        if context.get('params'):
            # Redact sensitive info
            safe_params = self._redact_params(context['params'])
            context_parts.append(f"params: {safe_params}")
        if context.get('operation'):
            context_parts.append(f"operation: {context['operation']}")
            
        context_str = ", ".join(context_parts)
        
        # Build enhanced error message
        enhanced_message = base_message
        if context_str:
            enhanced_message = f"{base_message} ({context_str})"
            
        # Add debugging information in debug mode
        debug_info = {}
        if self.debug_mode:
            debug_info = {
                'original_error_type': type(error).__name__,
                'traceback': traceback.format_exc(),
                'context': context
            }
            
        return TroveAPIError(
            message=enhanced_message,
            status_code=status_code,
            response_data=debug_info if debug_info else None
        )
    
    def _redact_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive parameters for logging."""
        redacted = params.copy()
        sensitive_keys = ['key', 'api_key', 'token', 'password']
        
        for key in sensitive_keys:
            if key in redacted:
                redacted[key] = '***redacted***'
                
        return redacted
    
    def log_error(self, error: Exception, context: Dict[str, Any], level: int = logging.ERROR):
        """Log error with context."""
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        logger.log(level, f"Error: {error} | Context: {context_str}")
        
        if self.debug_mode:
            logger.debug(f"Full traceback: {traceback.format_exc()}")

class ErrorRecovery:
    """Implements error recovery strategies."""
    
    @staticmethod
    def suggest_fixes(error: TroveAPIError) -> List[str]:
        """Suggest fixes based on error type."""
        suggestions = []
        
        if error.status_code == 401:
            suggestions.extend([
                "Check that your API key is valid and properly set",
                "Verify the X-API-KEY header is included",
                "Ensure your API key hasn't expired"
            ])
        elif error.status_code == 404:
            suggestions.extend([
                "Verify the record ID is correct",
                "Check if the record exists in the specified category",
                "Try searching for the record first"
            ])
        elif error.status_code == 429:
            suggestions.extend([
                "Reduce request rate (current default: 2 req/sec)",
                "Add delays between requests",
                "Use bulk harvest mode for large datasets"
            ])
        elif error.status_code and error.status_code >= 500:
            suggestions.extend([
                "Try the request again (temporary server issue)",
                "Check Trove service status",
                "Simplify the request if complex"
            ])
        elif "Invalid categories" in str(error):
            suggestions.extend([
                "Use valid category codes: book, newspaper, image, people, list, etc.",
                "Check the API documentation for current category codes"
            ])
        elif "parameter" in str(error).lower():
            suggestions.extend([
                "Check parameter spelling and values",
                "Verify parameter dependencies (e.g., year requires decade for newspapers)",
                "Consult the API documentation for valid parameter values"
            ])
            
        return suggestions
    
    @staticmethod
    def is_retryable(error: Exception) -> bool:
        """Determine if an error is worth retrying."""
        if isinstance(error, TroveAPIError):
            # Retry server errors and rate limits, but not client errors
            if error.status_code:
                return error.status_code in [429, 502, 503, 504] or error.status_code >= 500
        
        # Retry network-related errors
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True
            
        return False

def enhance_exception_message(error: Exception, operation: str) -> str:
    """Enhance exception messages with operation context."""
    base_message = str(error)
    
    if isinstance(error, TroveAPIError) and error.status_code:
        status_info = f" (HTTP {error.status_code})"
    else:
        status_info = ""
        
    return f"Failed to {operation}: {base_message}{status_info}"
```

### 3. Performance Optimizations (`trove/performance.py`)

```python
import asyncio
import time
from typing import List, Dict, Any, Optional, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics collection."""
    request_count: int = 0
    total_request_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    rate_limit_delays: int = 0
    errors: int = 0
    
    @property
    def average_request_time(self) -> float:
        """Average request time in seconds."""
        return self.total_request_time / self.request_count if self.request_count > 0 else 0.0
    
    @property
    def cache_hit_rate(self) -> float:
        """Cache hit rate as percentage."""
        total_cache_requests = self.cache_hits + self.cache_misses
        return (self.cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0.0

class PerformanceMonitor:
    """Monitors and reports performance metrics."""
    
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self._start_time = time.time()
    
    def record_request(self, duration: float):
        """Record a request completion."""
        self.metrics.request_count += 1
        self.metrics.total_request_time += duration
    
    def record_cache_hit(self):
        """Record cache hit."""
        self.metrics.cache_hits += 1
    
    def record_cache_miss(self):
        """Record cache miss."""
        self.metrics.cache_misses += 1
    
    def record_rate_limit_delay(self):
        """Record rate limit delay."""
        self.metrics.rate_limit_delays += 1
    
    def record_error(self):
        """Record error."""
        self.metrics.errors += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        uptime = time.time() - self._start_time
        
        return {
            'uptime_seconds': uptime,
            'total_requests': self.metrics.request_count,
            'requests_per_second': self.metrics.request_count / uptime if uptime > 0 else 0,
            'average_request_time': self.metrics.average_request_time,
            'cache_hit_rate': self.metrics.cache_hit_rate,
            'rate_limit_delays': self.metrics.rate_limit_delays,
            'error_count': self.metrics.errors,
            'error_rate': self.metrics.errors / self.metrics.request_count * 100 if self.metrics.request_count > 0 else 0
        }
    
    def log_stats(self, level: int = logging.INFO):
        """Log performance statistics."""
        stats = self.get_stats()
        logger.log(level, f"Performance Stats: {stats}")

class BatchProcessor:
    """Process multiple operations in batches for better performance."""
    
    def __init__(self, max_workers: int = 5, batch_size: int = 10):
        self.max_workers = max_workers
        self.batch_size = batch_size
    
    def process_batch_sync(self, items: List[Any], processor_func: Callable, 
                          progress_callback: Optional[Callable] = None) -> List[Any]:
        """Process items in parallel batches synchronously."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(processor_func, item): item 
                for item in items
            }
            
            # Collect results as they complete
            for i, future in enumerate(as_completed(future_to_item)):
                try:
                    result = future.result()
                    results.append(result)
                    
                    if progress_callback:
                        progress_callback(i + 1, len(items))
                        
                except Exception as e:
                    logger.error(f"Batch processing error for item {future_to_item[future]}: {e}")
                    results.append(None)  # Placeholder for failed item
        
        return results
    
    async def process_batch_async(self, items: List[Any], async_processor_func: Callable,
                                 progress_callback: Optional[Callable] = None) -> List[Any]:
        """Process items in parallel batches asynchronously."""
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def bounded_processor(item):
            async with semaphore:
                return await async_processor_func(item)
        
        tasks = [bounded_processor(item) for item in items]
        results = []
        
        for i, task in enumerate(asyncio.as_completed(tasks)):
            try:
                result = await task
                results.append(result)
                
                if progress_callback:
                    progress_callback(i + 1, len(items))
                    
            except Exception as e:
                logger.error(f"Async batch processing error: {e}")
                results.append(None)
        
        return results

class ResponseStreamer:
    """Stream large responses to reduce memory usage."""
    
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
    
    def stream_search_results(self, search_func: Callable, search_params: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """Stream search results in chunks.""" 
        current_cursor = search_params.get('s', '*')
        total_processed = 0
        
        while True:
            # Update cursor for this chunk
            chunk_params = search_params.copy()
            chunk_params['s'] = current_cursor
            chunk_params['n'] = min(self.chunk_size, chunk_params.get('n', self.chunk_size))
            
            try:
                result = search_func(**chunk_params)
                
                # Yield individual records
                for category in result.categories:
                    records = self._extract_records_from_category(category)
                    for record in records:
                        yield record
                        total_processed += 1
                
                # Check for next page
                if not result.cursors:
                    break
                    
                # Use cursor from first category (assuming single category for streaming)
                next_cursor = list(result.cursors.values())[0]
                if next_cursor == current_cursor:
                    break  # No more results
                    
                current_cursor = next_cursor
                
            except Exception as e:
                logger.error(f"Error streaming results after {total_processed} records: {e}")
                break
                
        logger.info(f"Streamed {total_processed} total records")
    
    def _extract_records_from_category(self, category_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract records from category data."""
        records_data = category_data.get('records', {})
        category_code = category_data.get('code', '')
        
        # Different categories store records differently
        record_containers = {
            'book': 'work', 'image': 'work', 'magazine': 'work',
            'music': 'work', 'diary': 'work', 'research': 'work',
            'newspaper': 'article', 'people': 'people', 'list': 'list'
        }
        
        container = record_containers.get(category_code, 'work')
        records = records_data.get(container, [])
        
        if isinstance(records, dict):
            records = [records]
            
        return records

class ConnectionPool:
    """Manage HTTP connection pooling for better performance."""
    
    def __init__(self, pool_connections: int = 10, pool_maxsize: int = 10):
        self.pool_connections = pool_connections
        self.pool_maxsize = pool_maxsize
    
    def configure_httpx_client(self, client_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Configure httpx client for optimal connection pooling."""
        limits = client_kwargs.get('limits', {})
        
        # Set connection pool limits
        limits.update({
            'max_connections': self.pool_connections,
            'max_keepalive_connections': self.pool_maxsize,
            'keepalive_expiry': 30.0  # Keep connections alive for 30 seconds
        })
        
        client_kwargs['limits'] = limits
        return client_kwargs
```

### 4. Enhanced Logging (`trove/logging.py`)

```python
import logging
import sys
import json
from typing import Dict, Any, Optional
from datetime import datetime
import traceback

class TroveFormatter(logging.Formatter):
    """Custom formatter for Trove SDK logs."""
    
    def __init__(self, include_context: bool = True):
        self.include_context = include_context
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        # Build log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage()
        }
        
        # Add context if available
        if self.include_context and hasattr(record, 'trove_context'):
            log_entry['context'] = record.trove_context
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_entry, ensure_ascii=False)

class ContextualLogger:
    """Logger that maintains context across operations."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context: Dict[str, Any] = {}
    
    def set_context(self, **context):
        """Set context for subsequent log messages."""
        self.context.update(context)
    
    def clear_context(self):
        """Clear all context."""
        self.context.clear()
    
    def _log_with_context(self, level: int, message: str, **extra_context):
        """Log message with context."""
        # Merge context
        full_context = {**self.context, **extra_context}
        
        # Create log record
        record = self.logger.makeRecord(
            self.logger.name, level, __file__, 0, message, (), None
        )
        record.trove_context = full_context
        
        self.logger.handle(record)
    
    def debug(self, message: str, **context):
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, **context)
    
    def info(self, message: str, **context):
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, **context)
    
    def warning(self, message: str, **context):
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, message, **context)
    
    def error(self, message: str, **context):
        """Log error message with context."""
        self._log_with_context(logging.ERROR, message, **context)

def configure_logging(level: str = "INFO", format_style: str = "json", 
                     log_file: Optional[str] = None) -> logging.Logger:
    """Configure logging for the Trove SDK."""
    
    # Convert level string to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create root logger
    logger = logging.getLogger('trove')
    logger.setLevel(numeric_level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create handler
    if log_file:
        handler = logging.FileHandler(log_file)
    else:
        handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter
    if format_style == "json":
        formatter = TroveFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# Create contextual loggers for different components
transport_logger = ContextualLogger('trove.transport')
search_logger = ContextualLogger('trove.search')
resources_logger = ContextualLogger('trove.resources')
citations_logger = ContextualLogger('trove.citations')
```

### 5. API Documentation Generation

```python
# docs/generate_api_docs.py
"""
Generate comprehensive API documentation from code and examples.
"""

import inspect
import json
from typing import Dict, Any, List
from pathlib import Path
import ast

class APIDocGenerator:
    """Generate API documentation from source code."""
    
    def __init__(self, source_dir: Path, output_dir: Path):
        self.source_dir = source_dir
        self.output_dir = output_dir
    
    def generate_docs(self):
        """Generate complete API documentation."""
        
        # Extract class and method documentation
        class_docs = self._extract_class_docs()
        
        # Generate markdown files
        self._generate_class_docs(class_docs)
        self._generate_examples_docs()
        self._generate_getting_started()
        
        print(f"API documentation generated in {self.output_dir}")
    
    def _extract_class_docs(self) -> Dict[str, Any]:
        """Extract documentation from Python classes."""
        docs = {}
        
        for py_file in self.source_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_info = self._extract_class_info(node, source)
                        if class_info:
                            docs[node.name] = class_info
                            
            except Exception as e:
                print(f"Error processing {py_file}: {e}")
        
        return docs
    
    def _extract_class_info(self, class_node: ast.ClassDef, source: str) -> Dict[str, Any]:
        """Extract information from a class node."""
        class_info = {
            'name': class_node.name,
            'docstring': ast.get_docstring(class_node),
            'methods': [],
            'properties': []
        }
        
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                method_info = {
                    'name': node.name,
                    'docstring': ast.get_docstring(node),
                    'is_property': any(isinstance(d, ast.Name) and d.id == 'property' 
                                     for d in node.decorator_list),
                    'args': [arg.arg for arg in node.args.args if arg.arg != 'self']
                }
                
                if method_info['is_property']:
                    class_info['properties'].append(method_info)
                else:
                    class_info['methods'].append(method_info)
        
        return class_info
    
    def _generate_class_docs(self, class_docs: Dict[str, Any]):
        """Generate markdown documentation for classes."""
        
        for class_name, class_info in class_docs.items():
            # Create markdown content
            lines = [
                f"# {class_name}",
                "",
                class_info.get('docstring', 'No description available.'),
                "",
                "## Methods",
                ""
            ]
            
            for method in class_info['methods']:
                lines.extend([
                    f"### {method['name']}",
                    "",
                    method.get('docstring', 'No description available.'),
                    "",
                    f"**Arguments**: {', '.join(method['args']) if method['args'] else 'None'}",
                    ""
                ])
            
            if class_info['properties']:
                lines.extend([
                    "## Properties",
                    ""
                ])
                
                for prop in class_info['properties']:
                    lines.extend([
                        f"### {prop['name']}",
                        "",
                        prop.get('docstring', 'No description available.'),
                        ""
                    ])
            
            # Write to file
            output_file = self.output_dir / f"{class_name}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
```

## Production Configuration

```python
# trove/production.py
"""Production configuration and deployment utilities."""

import os
from typing import Dict, Any, Optional
from .config import TroveConfig
from .logging import configure_logging
from .performance import PerformanceMonitor

class ProductionConfig:
    """Production-ready configuration management."""
    
    @staticmethod
    def create_config(environment: str = "production") -> TroveConfig:
        """Create production configuration."""
        
        config_overrides = {}
        
        if environment == "production":
            config_overrides.update({
                'rate_limit': 1.5,  # Conservative rate limiting
                'max_retries': 5,
                'cache_backend': 'sqlite',
                'log_level': 'INFO',
                'log_requests': False,  # Disable request logging in prod
                'redact_credentials': True
            })
        elif environment == "development":
            config_overrides.update({
                'rate_limit': 0.5,  # Very conservative for development
                'cache_backend': 'memory',
                'log_level': 'DEBUG',
                'log_requests': True
            })
        
        # Override with environment variables
        env_config = {
            'api_key': os.environ.get('TROVE_API_KEY'),
            'base_url': os.environ.get('TROVE_BASE_URL', TroveConfig.base_url),
            'rate_limit': float(os.environ.get('TROVE_RATE_LIMIT', config_overrides.get('rate_limit', 2.0))),
            'cache_backend': os.environ.get('TROVE_CACHE_BACKEND', config_overrides.get('cache_backend', 'memory')),
            'log_level': os.environ.get('TROVE_LOG_LEVEL', config_overrides.get('log_level', 'INFO'))
        }
        
        # Remove None values
        env_config = {k: v for k, v in env_config.items() if v is not None}
        
        # Merge configurations
        final_config = {**config_overrides, **env_config}
        
        return TroveConfig(**final_config)

def setup_production_environment(environment: str = "production") -> Dict[str, Any]:
    """Set up production environment with monitoring and logging."""
    
    # Configure logging
    log_level = os.environ.get('TROVE_LOG_LEVEL', 'INFO')
    log_file = os.environ.get('TROVE_LOG_FILE')
    configure_logging(level=log_level, log_file=log_file)
    
    # Set up performance monitoring
    monitor = PerformanceMonitor()
    
    # Create production config
    config = ProductionConfig.create_config(environment)
    
    return {
        'config': config,
        'monitor': monitor,
        'environment': environment
    }
```

## Testing Strategy

### Performance Benchmarks

```python
# test_performance_benchmarks.py
import pytest
import time
from trove import TroveClient
from trove.performance import PerformanceMonitor

@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Performance benchmark tests."""
    
    def test_cold_start_time(self, benchmark):
        """Benchmark cold start time."""
        def create_client():
            return TroveClient.from_env()
        
        result = benchmark(create_client)
        assert result is not None
    
    def test_search_performance(self, benchmark, trove_client):
        """Benchmark search performance.""" 
        def search_operation():
            return (trove_client.search()
                   .text("test")
                   .in_("book")
                   .page_size(10)
                   .first_page())
        
        result = benchmark(search_operation)
        assert result.total_results >= 0
    
    def test_model_parsing_performance(self, benchmark):
        """Benchmark model parsing performance."""
        from trove.models import Work
        
        work_data = {
            'id': '123456',
            'title': 'Test Work',
            'contributor': ['Author, Test'],
            'issued': '2020'
        }
        
        def parse_work():
            return Work(**work_data)
        
        result = benchmark(parse_work)
        assert result.id == '123456'
    
    def test_batch_processing_performance(self, benchmark, trove_client):
        """Benchmark batch processing."""
        from trove.performance import BatchProcessor
        
        processor = BatchProcessor(max_workers=3)
        
        def dummy_operation(item):
            time.sleep(0.01)  # Simulate small operation
            return item * 2
        
        items = list(range(20))
        
        def batch_operation():
            return processor.process_batch_sync(items, dummy_operation)
        
        result = benchmark(batch_operation)
        assert len(result) == 20
```

### Memory Usage Tests

```python
# test_memory_usage.py
import gc
import psutil
import os
from trove import TroveClient

def test_memory_usage_basic_operations():
    """Test memory usage for basic operations."""
    process = psutil.Process(os.getpid())
    
    # Baseline memory
    gc.collect()
    baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Create client and perform operations
    client = TroveClient.from_env()
    
    # Perform multiple searches
    for i in range(10):
        result = (client.search()
                 .text(f"test {i}")
                 .in_("book") 
                 .page_size(20)
                 .first_page())
    
    # Check memory usage
    gc.collect()
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - baseline_memory
    
    # Should not leak significant memory
    assert memory_increase < 100  # Less than 100MB increase
    
    client.close()
```

## Definition of Done

Stage 6 is complete when:

- ✅ **Optional models implemented** - Pydantic models with raw dict fallback
- ✅ **Enhanced error handling** - Context-aware errors with suggestions
- ✅ **Performance optimizations** - Connection pooling, batch processing, streaming
- ✅ **Production logging** - Structured logging with context
- ✅ **API documentation** - Auto-generated comprehensive docs
- ✅ **Type stubs** - Better IDE support and type checking
- ✅ **Performance monitoring** - Built-in metrics and monitoring
- ✅ **Memory optimization** - No memory leaks, efficient resource usage
- ✅ **Production config** - Environment-based configuration management
- ✅ **Benchmarks** - Performance benchmarks meet targets
- ✅ **Documentation** - Complete docs site with examples
- ✅ **Package ready** - Ready for PyPI publication

This polish stage transforms the SDK from a functional library into a production-ready, professionally polished package with comprehensive documentation and monitoring capabilities.