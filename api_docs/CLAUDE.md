# Trove API v3 Documentation for AI Agents

This directory contains comprehensive, fragmented documentation for the Trove API v3, specifically designed for AI agent consumption and efficient information retrieval.

## Documentation Structure

### Main Index
- **[trove-api-index.md](./trove-api-index.md)** - Master reference document with links to all fragments

### Core API Information
- **[trove-api-overview.md](./trove-api-overview.md)** - Basic API info, version, terms of service
- **[trove-api-authentication.md](./trove-api-authentication.md)** - API key requirements and security schemes
- **[trove-api-endpoints.md](./trove-api-endpoints.md)** - Complete endpoint reference with operation IDs
- **[trove-api-parameters.md](./trove-api-parameters.md)** - All parameters with types and descriptions
- **[trove-api-categories.md](./trove-api-categories.md)** - Supported categories and format enumerations

### Schema Documentation
- **[trove-schemas-core.md](./trove-schemas-core.md)** - Primary schemas: Work, Article, People, List
- **[trove-schemas-search.md](./trove-schemas-search.md)** - Search result structures and facets
- **[trove-schemas-contributor.md](./trove-schemas-contributor.md)** - Contributor and title schemas
- **[trove-schemas-metadata.md](./trove-schemas-metadata.md)** - Dublin Core and EAC-CPF records
- **[trove-schemas-utility.md](./trove-schemas-utility.md)** - Supporting schemas (identifiers, language, spatial, etc.)

### Comprehensive Guides
- **[trove-search-parameters.md](./trove-search-parameters.md)** - Complete search guide with examples
- **[trove-faceting.md](./trove-faceting.md)** - Faceting system usage and patterns
- **[trove-response-formats.md](./trove-response-formats.md)** - JSON vs XML format examples
- **[trove-error-handling.md](./trove-error-handling.md)** - Error schemas and troubleshooting

### Original Specification  
- **[trove-api-v3.yaml](./trove-api-v3.yaml)** - Complete OpenAPI 3.0.3 specification (2730+ lines)

## AI Agent Usage Patterns

### Quick Start Sequence
1. **Authentication**: Read [trove-api-authentication.md](./trove-api-authentication.md) for API key setup
2. **Basic Search**: Use [trove-search-parameters.md](./trove-search-parameters.md) for search patterns
3. **Data Understanding**: Reference [trove-schemas-core.md](./trove-schemas-core.md) for response structure
4. **Error Handling**: Implement patterns from [trove-error-handling.md](./trove-error-handling.md)

### Common Tasks
- **Parameter Lookup**: Use [trove-api-parameters.md](./trove-api-parameters.md) for exact parameter specifications
- **Category Research**: Check [trove-api-categories.md](./trove-api-categories.md) for valid category codes and formats
- **Faceted Search**: Reference [trove-faceting.md](./trove-faceting.md) for faceting implementation
- **Response Parsing**: Use [trove-response-formats.md](./trove-response-formats.md) for JSON/XML examples

### Advanced Usage
- **Bulk Operations**: See search parameters guide for bulkHarvest patterns
- **Metadata Analysis**: Use Dublin Core schemas for detailed record structure
- **Custom Applications**: Reference utility schemas for identifier and linking patterns

## Documentation Features

### AI-Optimized Design
- **Self-Contained**: Each document contains complete information about its topic area
- **Cross-Referenced**: Strategic links to related documents without circular dependencies
- **Searchable Structure**: Clear hierarchical headings and consistent formatting
- **Example-Rich**: Real examples from the original OpenAPI specification

### Faithful to Original
- **Complete Coverage**: All information from the 2730-line YAML preserved
- **Exact Parameters**: Parameter names, types, and constraints match original specification
- **Preserved Examples**: All original JSON/XML examples included
- **External Links**: All original documentation URLs maintained

### Efficient Context Usage
- **Focused Fragments**: Find specific information without loading entire specification
- **Logical Grouping**: Related concepts grouped together (e.g., all schemas, all parameters)
- **Minimal Redundancy**: Information appears once in its most logical location
- **Quick Reference**: Index provides rapid navigation to any topic

## Usage Recommendations

### For Search Implementation
1. Start with [trove-search-parameters.md](./trove-search-parameters.md) - comprehensive guide with examples
2. Reference [trove-api-parameters.md](./trove-api-parameters.md) for exact parameter specifications
3. Use [trove-faceting.md](./trove-faceting.md) for advanced filtering

### For Data Processing
1. Use [trove-schemas-core.md](./trove-schemas-core.md) for primary record types
2. Reference [trove-schemas-utility.md](./trove-schemas-utility.md) for supporting structures
3. Check [trove-response-formats.md](./trove-response-formats.md) for format-specific parsing

### For Error Handling
1. Implement patterns from [trove-error-handling.md](./trove-error-handling.md)
2. Reference HTTP status codes and retry strategies
3. Use authentication guide for API key troubleshooting

### For Complete Reference
- Use [trove-api-index.md](./trove-api-index.md) as starting point
- Fall back to [trove-api-v3.yaml](./trove-api-v3.yaml) for edge cases not covered in fragments

## Best Practices for AI Agents

1. **Start Narrow**: Read only the fragment you need for the current task
2. **Follow Links**: Use cross-references to find related information efficiently  
3. **Validate Against Examples**: Use provided examples to validate your implementation
4. **Check Dependencies**: Some parameters require others (e.g., year requires decade for newspapers)
5. **Handle Errors Gracefully**: Implement retry patterns and proper error responses

## External Resources

- **Official Documentation**: https://trove.nla.gov.au/about/create-something/using-api
- **API Key Registration**: https://trove.nla.gov.au/about/create-something/using-api#getting-an-api-key
- **Terms of Service**: https://trove.nla.gov.au/about/create-something/using-api/trove-api-terms-use
- **Technical Guide**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide