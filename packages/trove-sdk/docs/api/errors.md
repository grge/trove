# Error Handling

The Trove SDK provides comprehensive error handling with context-aware messages and recovery suggestions.

## Exception Hierarchy

All SDK exceptions inherit from `TroveError`:

```python
from trove.exceptions import (
    TroveError,              # Base exception
    ConfigurationError,       # Configuration issues
    AuthenticationError,      # Invalid API key (HTTP 401)
    AuthorizationError,       # Access forbidden (HTTP 403)
    ResourceNotFoundError,    # Resource not found (HTTP 404)
    RateLimitError,          # Rate limit exceeded (HTTP 429)
    TroveAPIError,           # General API errors
    NetworkError,            # Network connectivity issues
    ValidationError,         # Parameter validation errors
    CacheError               # Cache operation errors
)
```

## Basic Error Handling

```python
from trove import TroveClient
from trove.exceptions import TroveError, ResourceNotFoundError

try:
    client = TroveClient.from_env()
    work = client.work.get("123456789")
    print(work.primary_title)
    
except ResourceNotFoundError:
    print("Work not found")
except TroveError as e:
    print(f"Trove SDK error: {e}")
```

## Enhanced Error Information

Errors include context and suggestions:

```python
try:
    client.work.get("nonexistent123")
except ResourceNotFoundError as e:
    print(f"Error: {e}")
    
    # Enhanced errors include suggestions
    if hasattr(e, 'response_data') and e.response_data:
        suggestions = e.response_data.get('suggestions', [])
        if suggestions:
            print("Suggestions:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")
```

## Rate Limiting

```python
from trove.exceptions import RateLimitError
import time

try:
    # Bulk operation that might hit rate limits
    for work_id in work_ids:
        work = client.work.get(work_id)
        process_work(work)
        
except RateLimitError as e:
    print(f"Rate limited: {e}")
    
    # Check for retry-after header
    if hasattr(e, 'retry_after') and e.retry_after:
        print(f"Retry after {e.retry_after} seconds")
        time.sleep(float(e.retry_after))
```

## Validation Errors

```python
from trove.exceptions import ValidationError

try:
    # Invalid search parameters
    results = client.search().in_("invalid_category").first_page()
    
except ValidationError as e:
    print(f"Validation error: {e}")
    # Error message includes valid options
```

## Network Errors

```python
from trove.exceptions import NetworkError

try:
    results = client.search().text("test").in_("book").first_page()
    
except NetworkError as e:
    print(f"Network error: {e}")
    # Could indicate connectivity issues, timeouts, etc.
```

## Retry Logic

Check if an error is retryable:

```python
from trove.exceptions import is_retryable_error
import time

for attempt in range(3):
    try:
        work = client.work.get("123456789")
        break  # Success
        
    except TroveError as e:
        if is_retryable_error(e) and attempt < 2:
            print(f"Retrying after error: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
            continue
        else:
            raise  # Non-retryable or final attempt
```

## Debug Mode

Enable debug mode for detailed error information:

```python
from trove.errors import set_debug_mode

# Enable debug mode for development
set_debug_mode(True)

try:
    work = client.work.get("nonexistent")
except TroveError as e:
    # Error will include traceback and context in debug mode
    print(f"Debug error: {e}")
    if hasattr(e, 'response_data') and 'traceback' in e.response_data:
        print("Traceback available for debugging")
```

## Best Practices

### Specific Exception Handling

```python
try:
    work = client.work.get(work_id)
    
except ResourceNotFoundError:
    # Handle missing resources specifically
    print(f"Work {work_id} not found")
    
except AuthenticationError:
    # Handle API key issues
    print("Check your API key configuration")
    
except RateLimitError as e:
    # Handle rate limiting with backoff
    wait_time = getattr(e, 'retry_after', 30)
    time.sleep(float(wait_time))
    
except TroveError as e:
    # Handle other SDK errors
    print(f"SDK error: {e}")
```

### Graceful Degradation

```python
def get_work_safely(work_id: str) -> Optional[Dict]:
    try:
        return client.work.get(work_id)
    except ResourceNotFoundError:
        return None
    except TroveError as e:
        print(f"Warning: Could not retrieve work {work_id}: {e}")
        return None

# Use in batch operations
works = []
for work_id in work_ids:
    work = get_work_safely(work_id)
    if work:
        works.append(work)
```

### Logging Errors

```python
import logging
from trove.exceptions import TroveError

logger = logging.getLogger(__name__)

try:
    results = client.search().text("test").first_page()
    
except TroveError as e:
    # Log errors for monitoring
    logger.error(f"Trove API error: {e}", extra={
        'error_type': type(e).__name__,
        'operation': 'search'
    })
    raise
```
