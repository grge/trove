# Trove API v3 Error Handling Guide

This guide covers error responses, common error scenarios, troubleshooting steps, and best practices for handling errors in the Trove API.

## Error Response Schema

All error responses follow a consistent structure regardless of the response format (JSON or XML).

### Error Object Properties

- **statusCode** (integer): The HTTP status code
- **statusText** (string): The HTTP status reason phrase  
- **description** (string): A brief description of the error

### JSON Error Format

```json
{
  "statusCode": 404,
  "statusText": "Not Found",
  "description": "A matching record could not be found."
}
```

### XML Error Format

```xml
<error>
  <statusCode>404</statusCode>
  <statusText>Not Found</statusText>
  <description>A matching record could not be found.</description>
</error>
```

## HTTP Status Codes

### 400 Bad Request

**Meaning**: The request was malformed or contains invalid parameters.

**Common Causes**:
- Missing required `category` parameter
- Invalid parameter values
- Malformed query strings
- Invalid facet names

**Example Response**:
```json
{
  "statusCode": 400,
  "statusText": "Bad Request",
  "description": "The category parameter is required."
}
```

**Solutions**:
- Verify all required parameters are included
- Check parameter values against documentation
- Validate URL encoding of parameters
- Test with minimal parameter sets first

### 401 Unauthorized

**Meaning**: Authentication failed - invalid or missing API key.

**Common Causes**:
- Missing `X-API-KEY` header
- Invalid API key
- Expired API key
- API key not properly formatted

**Example Response**:
```json
{
  "statusCode": 401,
  "statusText": "Unauthorized",
  "description": "Invalid or missing API key."
}
```

**Solutions**:
- Verify API key is included in request
- Check API key format and validity
- Ensure using correct header name: `X-API-KEY`
- Request new API key if expired

### 403 Forbidden

**Meaning**: Valid API key but access is denied.

**Common Causes**:
- API key doesn't have required permissions
- Terms of service violations
- Rate limiting restrictions
- Geographic restrictions

**Example Response**:
```json
{
  "statusCode": 403,
  "statusText": "Forbidden", 
  "description": "Access denied. Please check your API key permissions."
}
```

**Solutions**:
- Review API key permissions
- Check compliance with terms of service
- Verify account status
- Contact Trove support if needed

### 404 Not Found

**Meaning**: The requested resource could not be found.

**Common Causes**:
- Invalid record ID
- Deleted or removed content
- Incorrect endpoint URL
- Resource doesn't exist in specified category

**Example Response**:
```json
{
  "statusCode": 404,
  "statusText": "Not Found",
  "description": "A matching record could not be found."
}
```

**Solutions**:
- Verify record ID is correct
- Check if record exists in different category
- Use search to locate similar records
- Verify endpoint URL is correct

### 429 Too Many Requests

**Meaning**: Rate limit exceeded.

**Common Causes**:
- Too many requests in short time period
- Bulk operations without delays
- Multiple concurrent requests
- Exceeding daily/hourly quotas

**Example Response**:
```json
{
  "statusCode": 429,
  "statusText": "Too Many Requests",
  "description": "Rate limit exceeded. Please slow down your requests."
}
```

**Solutions**:
- Implement request throttling
- Add delays between requests
- Use bulk harvest mode for large datasets
- Monitor rate limit headers (if provided)

### 500 Internal Server Error

**Meaning**: Server-side error occurred.

**Common Causes**:
- Temporary server issues
- Database connectivity problems
- Service maintenance
- Unexpected server errors

**Example Response**:
```json
{
  "statusCode": 500,
  "statusText": "Internal Server Error",
  "description": "An internal server error occurred. Please try again later."
}
```

**Solutions**:
- Retry request after delay
- Check Trove status page
- Simplify request if complex
- Contact support if persistent

### 502 Bad Gateway

**Meaning**: Gateway or proxy server error.

**Common Causes**:
- Temporary gateway issues
- Load balancer problems
- Upstream server unavailable

**Solutions**:
- Retry request after delay
- Check network connectivity
- Try different endpoint if available

### 503 Service Unavailable

**Meaning**: Service temporarily unavailable.

**Common Causes**:
- Scheduled maintenance
- Server overload
- Temporary service disruption

**Solutions**:
- Check Trove announcements
- Wait and retry later
- Implement exponential backoff

## Common Error Scenarios

### Missing API Key

**Request**:
```bash
curl "https://api.trove.nla.gov.au/v3/result?category=book&q=australia"
```

**Error**:
```json
{
  "statusCode": 401,
  "statusText": "Unauthorized",
  "description": "API key is required."
}
```

**Solution**:
```bash
curl -H "X-API-KEY: your_api_key_here" \
     "https://api.trove.nla.gov.au/v3/result?category=book&q=australia"
```

### Missing Category Parameter

**Request**:
```bash
curl -H "X-API-KEY: your_key" \
     "https://api.trove.nla.gov.au/v3/result?q=australia"
```

**Error**:
```json
{
  "statusCode": 400,
  "statusText": "Bad Request",
  "description": "The category parameter is required."
}
```

**Solution**:
```bash
curl -H "X-API-KEY: your_key" \
     "https://api.trove.nla.gov.au/v3/result?category=book&q=australia"
```

### Invalid Record ID

**Request**:
```bash
curl -H "X-API-KEY: your_key" \
     "https://api.trove.nla.gov.au/v3/work/invalid_id"
```

**Error**:
```json
{
  "statusCode": 404,
  "statusText": "Not Found", 
  "description": "Work with ID 'invalid_id' could not be found."
}
```

**Solution**:
- Verify the record ID is correct
- Search for the record first to get valid ID

### Invalid Parameter Values

**Request**:
```bash
curl -H "X-API-KEY: your_key" \
     "https://api.trove.nla.gov.au/v3/result?category=invalid&q=australia"
```

**Error**:
```json
{
  "statusCode": 400,
  "statusText": "Bad Request",
  "description": "Invalid category 'invalid'. Valid categories are: all, book, diary, image, list, magazine, music, newspaper, people, research."
}
```

**Solution**:
- Use valid category codes from documentation
- Check parameter documentation for valid values

## Error Handling Best Practices

### 1. Implement Proper Status Code Handling

```python
import requests

def call_trove_api(url, headers):
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code == 404:
            raise ResourceNotFoundError("Resource not found")
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        else:
            error_data = response.json()
            raise APIError(f"API Error: {error_data['description']}")
            
    except requests.RequestException as e:
        raise NetworkError(f"Network error: {e}")
```

### 2. Implement Retry Logic

```python
import time
import random

def call_api_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code in [429, 502, 503]:
                # Exponential backoff with jitter
                delay = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(delay)
                continue
            else:
                # Don't retry for client errors
                break
                
        except requests.RequestException:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    
    # Handle final error
    if response.status_code != 200:
        error_data = response.json()
        raise APIError(error_data['description'])
```

### 3. Validate Parameters Before Requests

```python
def validate_search_params(category, query, **kwargs):
    valid_categories = [
        'all', 'book', 'diary', 'image', 'list', 
        'magazine', 'music', 'newspaper', 'people', 'research'
    ]
    
    if category not in valid_categories:
        raise ValueError(f"Invalid category. Must be one of: {valid_categories}")
    
    if 'n' in kwargs and (kwargs['n'] < 1 or kwargs['n'] > 100):
        raise ValueError("Parameter 'n' must be between 1 and 100")
    
    # Add more validation as needed
```

### 4. Handle Different Response Formats

```python
def parse_error_response(response):
    content_type = response.headers.get('content-type', '')
    
    try:
        if 'application/json' in content_type:
            error_data = response.json()
            return {
                'status_code': error_data.get('statusCode'),
                'status_text': error_data.get('statusText'),
                'description': error_data.get('description')
            }
        elif 'application/xml' in content_type:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            return {
                'status_code': int(root.find('statusCode').text),
                'status_text': root.find('statusText').text,
                'description': root.find('description').text
            }
        else:
            return {
                'status_code': response.status_code,
                'status_text': response.reason,
                'description': 'Unknown error format'
            }
    except Exception:
        return {
            'status_code': response.status_code,
            'status_text': response.reason,
            'description': 'Error parsing error response'
        }
```

## Debugging Tips

### 1. Start Simple

Begin with minimal requests and gradually add complexity:

```bash
# Start with basic search
curl -H "X-API-KEY: your_key" \
     "https://api.trove.nla.gov.au/v3/result?category=book&q=test"

# Add parameters one by one
curl -H "X-API-KEY: your_key" \
     "https://api.trove.nla.gov.au/v3/result?category=book&q=test&n=5"
```

### 2. Check URL Encoding

Ensure special characters are properly encoded:

```bash
# Wrong - spaces not encoded
curl "...result?q=Prime Ministers"

# Correct - spaces encoded
curl "...result?q=Prime%20Ministers"
```

### 3. Verify Headers

Check that headers are properly formatted:

```bash
# Check headers are included
curl -v -H "X-API-KEY: your_key" "...result?category=book"
```

### 4. Test with Different Tools

Use multiple tools to isolate issues:

- Browser for simple GET requests
- Postman for request building
- cURL for command line testing
- Programming language HTTP clients

### 5. Check Response Headers

Look for additional error information in headers:

```python
response = requests.get(url, headers=headers)
print("Status:", response.status_code)
print("Headers:", dict(response.headers))
print("Content:", response.text)
```

## Monitoring and Logging

### 1. Log API Requests and Responses

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_api_request(url, headers):
    logger.info(f"Making request to: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        logger.info(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"API Error: {response.text}")
        
        return response
    except Exception as e:
        logger.error(f"Request failed: {e}")
        raise
```

### 2. Track Error Patterns

Monitor common error types and patterns:

```python
class ErrorTracker:
    def __init__(self):
        self.error_counts = {}
    
    def record_error(self, status_code, description):
        key = f"{status_code}: {description}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
    
    def get_most_common_errors(self, limit=5):
        return sorted(
            self.error_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:limit]
```

### 3. Set Up Alerting

Monitor for critical errors:

```python
def should_alert(status_code, error_count):
    critical_errors = [500, 502, 503]
    
    if status_code in critical_errors and error_count > 5:
        return True
    
    if status_code == 429 and error_count > 10:
        return True
    
    return False
```

## Recovery Strategies

### 1. Graceful Degradation

When API is unavailable:

```python
def get_data_with_fallback(query):
    try:
        return fetch_from_trove_api(query)
    except APIError:
        # Fall back to cached data
        return get_cached_data(query)
    except NetworkError:
        # Return empty results with error message
        return {
            'results': [],
            'error': 'Service temporarily unavailable'
        }
```

### 2. Circuit Breaker Pattern

Prevent cascading failures:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerOpen()
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self):
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.reset_timeout
        )
```

## Getting Help

### Official Resources

1. **API Documentation**: https://trove.nla.gov.au/about/create-something/using-api
2. **Technical Guide**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide
3. **Terms of Use**: https://trove.nla.gov.au/about/create-something/using-api/trove-api-terms-use

### Support Channels

- Check official documentation first
- Review community forums and discussions
- Contact Trove support for persistent issues
- Report bugs through official channels

### Troubleshooting Checklist

1. ✅ **API Key**: Valid and properly included
2. ✅ **Parameters**: All required parameters present
3. ✅ **Values**: Parameter values are valid
4. ✅ **Encoding**: Special characters properly encoded
5. ✅ **Headers**: Correct content-type and accept headers
6. ✅ **Rate Limits**: Not exceeding request limits
7. ✅ **Network**: Stable internet connection
8. ✅ **Status**: Check Trove service status

## Related Documentation

- [Authentication Guide](./trove-api-authentication.md) - API key setup and usage
- [Parameters Reference](./trove-api-parameters.md) - Valid parameter values
- [Response Formats](./trove-response-formats.md) - Response structure information
- [API Overview](./trove-api-overview.md) - Terms of service and usage guidelines