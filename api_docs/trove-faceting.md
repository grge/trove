# Trove API v3 Faceting Guide

This guide provides comprehensive information about the faceting system in the Trove API, including how to request facets, interpret facet responses, and use facet values for filtering.

## Overview

Facets are categories that describe all the records in a particular result set. They provide a way to:

- Understand the composition of your search results
- Enable filtering and refinement of searches  
- Build faceted search interfaces
- Discover available filter options

For example, if you request the decade facet, the response will include a list of decades your results span across, and how many results are found in each decade.

## Requesting Facets

### Facet Parameter

Use the `facet` parameter to request specific facets:

```
facet=decade                    # Single facet
facet=decade,format,language    # Multiple facets  
facet=year,state               # Category-specific facets
```

### Facet-Only Searches

To get only facet information without results, set `n=0`:

```
https://api.trove.nla.gov.au/v3/result?
  key=YOUR_KEY&
  category=book&
  q=Australian+history&
  facet=decade,format&
  n=0
```

## Facet Response Structure

### In Search Results

Facets appear within each category in search results:

```json
{
  \"category\": [
    {
      \"code\": \"book\",
      \"name\": \"Books & Libraries\",
      \"records\": { ... },
      \"facets\": {
        \"facet\": [
          {
            \"name\": \"decade\",
            \"displayname\": \"Decade\",
            \"term\": [
              {
                \"count\": 1234,
                \"search\": \"200\",
                \"display\": \"2000s\",
                \"url\": \"https://api.trove.nla.gov.au/v3/result?...\",
                \"term\": [ /* nested terms if hierarchical */ ]
              }
            ]
          }
        ]
      }
    }
  ]
}
```

### Facet Object Properties

#### Facet Level
- **name** (string): The unique system name of the facet (XML attribute)
  - Example: `\"publicationplace\"`
- **displayname** (string): The human-readable name of the facet (XML attribute)
  - Example: `\"Place of Publication\"`
- **term** (array): The list of possible values for the facet

#### Facet Term Properties  
- **count** (integer): The number of records matching this facet term (XML attribute)
- **search** (string): The facet value used in limit parameters (e.g., `l-decade=200`)
- **display** (string): The facet value for display (usually same as search value)
- **url** (string): Ready-to-use API URL with this facet filter applied (XML attribute)
- **term** (array): Nested facet terms for hierarchical facets

## Using Facet Values for Filtering

### Basic Filtering

Use the **search** value from facet terms in limit parameters:

```
# From facet response: \"search\": \"200\"
l-decade=200

# From facet response: \"search\": \"Book\"  
l-format=Book
```

### Important Notes

- **Case Sensitivity**: Facet values are often case-sensitive
- **Exact Match**: Use the exact search value from the facet response
- **URL Encoding**: Properly encode special characters in URLs

### Multiple Values

Combine multiple facet values with commas:

```
l-decade=199,200               # 1990s and 2000s
l-format=Book,Article          # Books and Articles
```

## Common Facets by Category

### Universal Facets (Available for Most Categories)

#### decade
- **System Name**: `decade`
- **Display Name**: \"Decade\"
- **Format**: YYY (e.g., \"199\" for 1990s)
- **Categories**: book, image, magazine, music, diary, newspaper, list

#### format
- **System Name**: `format`
- **Display Name**: \"Format\"
- **Examples**: \"Book\", \"Map\", \"Photograph\"
- **Categories**: book, image, magazine, music, diary

#### language
- **System Name**: `language`
- **Display Name**: \"Language\"
- **Examples**: \"English\", \"French\", \"German\"
- **Categories**: book, image, magazine, music, diary

#### availability
- **System Name**: `availability`
- **Display Name**: \"Availability\"
- **Values**: \"y\" (online), \"y/f\" (free), \"y/r\" (restricted), etc.
- **Categories**: book, image, magazine, music, diary

### Geographic Facets

#### state (Newspapers)
- **System Name**: `state`
- **Display Name**: \"State\"
- **Examples**: \"New South Wales\", \"Victoria\"
- **Categories**: newspaper

#### place
- **System Name**: `place` / `publicationplace`
- **Display Name**: \"Place of Publication\"
- **Examples**: \"Australia\", \"Sydney, NSW\"
- **Categories**: Various

#### geocoverage
- **System Name**: `geocoverage`
- **Display Name**: \"Place\"
- **Examples**: \"Australia\", \"New South Wales\"
- **Categories**: magazine, image, research, book, diary, music

### Content-Specific Facets

#### title (Newspapers/Magazines)
- **System Name**: `title`
- **Display Name**: \"Title\"
- **Format**: Title IDs for specific publications
- **Categories**: newspaper, magazine, research

#### category (Articles)
- **System Name**: `category`
- **Display Name**: \"Category\"
- **Examples**: \"Article\", \"Advertising\", \"Family notices\"
- **Categories**: magazine, newspaper

#### illustrated
- **System Name**: `illustrated`
- **Display Name**: \"Illustrated\"
- **Values**: \"Y\", \"N\"
- **Categories**: magazine, newspaper, research

#### wordcount
- **System Name**: `wordcount`
- **Display Name**: \"Word count\"
- **Values**: \"<100 Words\", \"100 - 1000 Words\", \"1000+ Words\"
- **Categories**: newspaper, magazine, research

### People-Specific Facets

#### occupation
- **System Name**: `occupation`
- **Display Name**: \"Occupation\"
- **Examples**: \"Author\", \"Politician\", \"Teacher\"
- **Categories**: diary, people

#### birth
- **System Name**: `birth`
- **Display Name**: \"Year of birth/establishment\"
- **Format**: YYYY
- **Categories**: people

#### death  
- **System Name**: `death`
- **Display Name**: \"Year of death/dissolution\"
- **Format**: YYYY
- **Categories**: people

### Collection and Source Facets

#### contributor
- **System Name**: `contributor`
- **Display Name**: \"Contributor\"
- **Examples**: \"National Library of Australia\"
- **Categories**: Various

#### partnernuc
- **System Name**: `partnernuc`
- **Display Name**: \"Partner\"
- **Format**: NUC codes
- **Categories**: book, image, magazine, music, diary, research

### Cultural Sensitivity Facets

#### firstAustralians
- **System Name**: `firstAustralians`
- **Display Name**: \"First Australians\"
- **Values**: \"y\"
- **Categories**: book, diary, image, magazine, music, people

#### culturalSensitivity
- **System Name**: `culturalSensitivity`
- **Display Name**: \"Cultural sensitivity\"
- **Values**: \"y\"
- **Categories**: book, diary, image, magazine, music, people

## Hierarchical Facets

Some facets have hierarchical structures with nested terms:

```json
{
  \"name\": \"subject\",
  \"displayname\": \"Subject\",
  \"term\": [
    {
      \"count\": 500,
      \"search\": \"History\",
      \"display\": \"History\",
      \"term\": [
        {
          \"count\": 150,
          \"search\": \"Australian history\",
          \"display\": \"Australian history\"
        },
        {
          \"count\": 100, 
          \"search\": \"European history\",
          \"display\": \"European history\"
        }
      ]
    }
  ]
}
```

## Facet Limitations

### Maximum Values

Each facet returns a maximum number of terms, which varies by facet type. The most frequent/relevant terms are returned first.

### Category Dependency

Some facets are only available for specific categories:

- `month` facet only works with `newspaper` category
- `zoom` facet only works with `image` category
- `occupation` facet only works with `people` and `diary` categories

### Parameter Dependencies

Some facets require other parameters:
- `year` facet for newspapers requires `decade` facet
- `month` facet requires `year` facet

## Advanced Faceting Strategies

### Progressive Refinement

1. Start with broad facets (decade, format)
2. Use results to identify more specific options
3. Apply additional filters based on facet values
4. Repeat to narrow results progressively

### Faceted Navigation

Build user interfaces that:
- Display facet counts to show result distribution
- Allow multiple selections within facet groups
- Show applied filters and allow removal
- Update facet counts when filters change

### Discovery Workflows

Use faceting to:
- Explore unknown collections
- Understand temporal distribution of content
- Identify available formats and languages
- Find unexpected related materials

## Example Requests and Responses

### Basic Facet Request

**Request**:
```
GET /v3/result?key=YOUR_KEY&category=book&q=Australia&facet=decade,format&n=5
```

**Response** (abbreviated):
```json
{
  \"query\": \"Australia\",
  \"category\": [
    {
      \"code\": \"book\",
      \"name\": \"Books & Libraries\", 
      \"records\": {
        \"total\": 45678,
        \"work\": [ /* 5 results */ ]
      },
      \"facets\": {
        \"facet\": [
          {
            \"name\": \"decade\",
            \"displayname\": \"Decade\",
            \"term\": [
              {
                \"count\": 8901,
                \"search\": \"200\",
                \"display\": \"2000s\",
                \"url\": \"https://api.trove.nla.gov.au/v3/result?key=YOUR_KEY&category=book&q=Australia&l-decade=200\"
              },
              {
                \"count\": 7234,
                \"search\": \"199\", 
                \"display\": \"1990s\",
                \"url\": \"https://api.trove.nla.gov.au/v3/result?key=YOUR_KEY&category=book&q=Australia&l-decade=199\"
              }
            ]
          },
          {
            \"name\": \"format\",
            \"displayname\": \"Format\",
            \"term\": [
              {
                \"count\": 30123,
                \"search\": \"Book\",
                \"display\": \"Book\",
                \"url\": \"https://api.trove.nla.gov.au/v3/result?key=YOUR_KEY&category=book&q=Australia&l-format=Book\"
              },
              {
                \"count\": 12456,
                \"search\": \"Book/Illustrated\", 
                \"display\": \"Book/Illustrated\",
                \"url\": \"https://api.trove.nla.gov.au/v3/result?key=YOUR_KEY&category=book&q=Australia&l-format=Book%2FIllustrated\"
              }
            ]
          }
        ]
      }
    }
  ]
}
```

### Applied Facet Filter Request

**Request**:
```
GET /v3/result?key=YOUR_KEY&category=newspaper&q=federation&l-decade=190&facet=state,category
```

This request:
- Searches newspapers for \"federation\"
- Filters to 1900s decade
- Requests state and category facets for further refinement

## Best Practices

### Performance

1. **Request Relevant Facets**: Only request facets you'll use
2. **Limit Result Count**: Use `n=0` for facet-only requests
3. **Cache Facet Values**: Cache common facet structures
4. **Batch Requests**: Combine faceting with initial searches

### User Experience

1. **Show Counts**: Display facet counts to indicate result sizes
2. **Clear Labels**: Use displayname values for user-facing labels  
3. **Applied Filters**: Show users what filters are active
4. **Reset Options**: Provide ways to clear filters

### Development

1. **Use Search Values**: Always use \"search\" values for filtering
2. **Handle Empty Facets**: Some facets may return no terms
3. **URL Encoding**: Properly encode facet values in URLs
4. **Error Handling**: Handle invalid facet names gracefully

## Common Faceting Patterns

### Exploration Interface
```javascript
// Request broad facets for exploration
facet=decade,format,language,availability
```

### Temporal Analysis
```javascript  
// Focus on time-based facets
facet=decade,year
// For newspapers: facet=decade,year,month
```

### Geographic Analysis
```javascript
// Focus on place-based facets  
facet=state,place,geocoverage
```

### Content Type Analysis
```javascript
// Focus on format and content facets
facet=format,category,illustrated,wordcount
```

## Troubleshooting

### Common Issues

1. **No Facet Results**: Check if facet is supported for the category
2. **Case Sensitivity**: Use exact search values from responses
3. **URL Encoding**: Properly encode special characters
4. **Category Limits**: Some facets only work with specific categories

### Debugging Tips

1. **Test Facet Names**: Try facet requests without other parameters
2. **Check Documentation**: Verify facet support for categories
3. **Examine Response**: Look at actual facet term structures
4. **URL Encode**: Test with properly encoded values

## External Documentation

- **Supported Facets**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#facetValues
- **Technical Guide**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide

## Related Documentation

- [Search Parameters Guide](./trove-search-parameters.md) - Complete search parameter usage
- [Parameters Reference](./trove-api-parameters.md) - Formal parameter specifications  
- [Categories & Formats](./trove-api-categories.md) - Available categories and their facets
- [Search Schemas](./trove-schemas-search.md) - Facet response structures