# Trove API v3 Authentication

## Overview

The Trove API requires authentication using an API key for all requests. Authentication is implemented using a custom API key scheme.

## Security Scheme

- **Type**: API Key
- **Name**: `X-API-KEY`
- **Location**: Header
- **Description**: Enter your Trove API key to execute a call

## Obtaining an API Key

Use of the Trove API requires an active API key.

**How to Get an API Key**: See [Getting an API key](https://trove.nla.gov.au/about/create-something/using-api#getting-an-api-key) for instructions on how to obtain a key.

## Using Your API Key

### Header Method (Recommended)

Include your API key in the request header:

```
X-API-KEY: your_api_key_here
```

### Query Parameter Method

Alternatively, you can include your API key as a query parameter (though header method is preferred):

```
https://api.trove.nla.gov.au/v3/result?key=your_api_key_here&category=book&q=search_terms
```

## Authentication Requirements

- **All Endpoints**: Require valid API key
- **Rate Limiting**: API keys may be subject to rate limiting (check current terms of service)
- **Usage Monitoring**: API usage is tracked and monitored

## Terms of Service

By using any Trove API functionality, you agree to the [Trove API Terms of Use](https://trove.nla.gov.au/about/create-something/using-api/trove-api-terms-use).

## Best Practices

1. **Secure Storage**: Store your API key securely and never expose it in client-side code
2. **Environment Variables**: Use environment variables or secure configuration files to store API keys
3. **Header Usage**: Prefer using the `X-API-KEY` header over query parameters for security
4. **Monitor Usage**: Keep track of your API usage to avoid hitting any limits
5. **Respect Terms**: Follow the terms of service and usage guidelines

## Example Request

```bash
curl -H "X-API-KEY: your_api_key_here" \
     "https://api.trove.nla.gov.au/v3/result?category=book&q=Australian+history"
```

## Troubleshooting

### Common Authentication Issues

1. **401 Unauthorized**: Invalid or missing API key
2. **403 Forbidden**: API key valid but access denied (check terms compliance)
3. **429 Too Many Requests**: Rate limit exceeded

### Error Response Format

Authentication errors will be returned in the standard error format:

```json
{
  "statusCode": 401,
  "statusText": "Unauthorized", 
  "description": "Invalid or missing API key"
}
```

## Related Documentation

- [API Overview](./trove-api-overview.md) - General API information and terms
- [Endpoints Reference](./trove-api-endpoints.md) - All available endpoints
- [Error Handling](./trove-error-handling.md) - Complete error handling information