# Trove API v3 Search Parameters Guide

This comprehensive guide provides detailed usage information, examples, and best practices for all search parameters in the Trove API.

## Quick Start Example

```
https://api.trove.nla.gov.au/v3/result?key=YOUR_API_KEY&category=book&q=Australian+history
```

## Core Search Parameters

### Query Parameter (q)

**Purpose**: The main search query with support for indexed fields.

**Basic Usage**:
```
q=Australian history
q="Prime Ministers"  # Exact phrase
```

**Indexed Fields**: Your query can use indexes to search specific fields:
- `title:` - Search in titles only
- `creator:` - Search in creator/author fields
- `subject:` - Search in subject fields
- `fulltext:` - Search in full text (where available)

**Advanced Examples**:
```
q=title:"Australian history" AND creator:Smith
q=fulltext:democracy NOT fulltext:monarchy
q=subject:politics AND decade:199*
```

**External Documentation**: [Supported indexes](https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#list-of-supported-indexes)

### Category Parameter

**Purpose**: Specify which Trove categories to search.
**Required**: Yes
**Type**: Array (comma-separated)

**Available Categories**:
- `all` - All categories (fastest for broad searches)
- `book` - Books & Libraries
- `diary` - Diaries, Letters & Archives
- `image` - Images, Maps & Artefacts
- `list` - Lists
- `magazine` - Magazines & Newsletters
- `music` - Music, Audio & Video
- `newspaper` - Newspapers & Gazettes
- `people` - People & Organisations
- `research` - Research & Reports

**Examples**:
```
category=book                    # Single category
category=book,image             # Multiple categories
category=all                    # All categories
```

**Best Practice**: Search only the categories you need for faster responses.

## Pagination and Result Control

### Start Parameter (s)

**Purpose**: Cursor-based pagination starting point.
**Default**: `*`

**Usage**:
```
s=*                             # First page
s=AoIIPyteOSlzdTczOTQ2MjQ%3D     # Next page (URL encoded)
```

**Important**: 
- Use the `nextStart` value from previous responses
- Always URL encode the cursor value
- Don't construct cursor values manually

### Number of Results (n)

**Purpose**: Results per page per category.
**Default**: 20
**Maximum**: 100

**Examples**:
```
n=10                            # 10 results per category
n=100                           # Maximum results per category
```

### Sort Order (sortby)

**Purpose**: Control result ordering.
**Default**: `relevance`

**Options**:
- `relevance` - Most relevant first
- `datedesc` - Newest first
- `dateasc` - Oldest first

**Examples**:
```
sortby=datedesc                 # Latest publications first
sortby=relevance                # Most relevant first
```

### Bulk Harvest (bulkHarvest)

**Purpose**: Optimize for systematic harvesting.
**Default**: `false`
**Type**: Boolean

**Usage**:
```
bulkHarvest=true                # Sort by identifier for consistent ordering
bulkHarvest=false               # Sort by relevance (default)
```

**When to Use**: Set to `true` when harvesting large datasets to ensure consistent record order and complete coverage.

## Record Detail Control

### Record Level (reclevel)

**Purpose**: Control metadata detail level.
**Default**: `brief`

**Options**:
- `brief` - Essential metadata only
- `full` - Complete metadata including Dublin Core records

**Examples**:
```
reclevel=brief                  # Fast, minimal metadata
reclevel=full                   # Complete metadata
```

### Include Parameter

**Purpose**: Add optional information to results.
**Type**: Array (comma-separated)

**Options** (varies by endpoint):
- `all` - Include all available optional information
- `comments` - User comments
- `tags` - User tags  
- `holdings` - Library holdings information
- `links` - Additional links
- `lists` - User lists containing the item
- `workversions` - Work version information
- `articletext` - Full article text (newspapers)
- `listitems` - Items within lists
- `subscribinglibs` - Libraries with subscriptions
- `raweaccpf` - Raw EAC-CPF XML (people records)

**Examples**:
```
include=tags,comments           # Include user-generated content
include=all                     # Include everything available
include=articletext             # Include full newspaper article text
```

**Performance Note**: Only request the information you need to optimize response time.

## Date and Time Filters

### Decade Filter (l-decade)

**Purpose**: Filter by publication decade.
**Format**: YYY (e.g., 199 for 1990-1999)
**Categories**: book, image, magazine, music, diary, newspaper, list

**Examples**:
```
l-decade=195                    # 1950s
l-decade=200                    # 2000s
l-decade=195,196               # 1950s and 1960s
```

### Year Filter (l-year)

**Purpose**: Filter by publication year.
**Format**: YYYY
**Categories**: book, image, magazine, music, diary, newspaper, list
**Dependency**: For newspapers, decade filter must also be applied

**Examples**:
```
l-year=1995                     # Year 1995
l-decade=199&l-year=1995       # Required for newspapers
```

### Month Filter (l-month)

**Purpose**: Filter by publication month.
**Categories**: newspaper only
**Dependency**: Year filter must also be applied

**Examples**:
```
l-decade=201&l-year=2015&l-month=03  # March 2015
```

## Geographic Filters

### Geographic Coverage (l-geocoverage)

**Purpose**: Filter by geographic region the item is about.
**Categories**: magazine, image, research, book, diary, music

**Examples**:
```
l-geocoverage=Australia
l-geocoverage=New%20South%20Wales   # URL encoded
```

### Place (l-place)

**Purpose**: Place of birth (people) or establishment (organisations).
**Categories**: people

**Examples**:
```
l-place=Sydney
l-place=Melbourne,Brisbane
```

### State (l-state)

**Purpose**: State of publication for newspapers/gazettes.
**Categories**: newspaper

**Examples**:
```
l-state=NSW
l-state=VIC,QLD
```

## Language and Cultural Filters

### Language (l-language)

**Purpose**: Filter by language(s) the work is available in.
**Categories**: book, image, magazine, music, diary

**Examples**:
```
l-language=English
l-language=French,German
```

### Aboriginal and Torres Strait Islander Language (l-austlanguage)

**Purpose**: Filter by Aboriginal and Torres Strait Islander languages.
**Categories**: book, image, magazine, music, diary, research

**Examples**:
```
l-austlanguage=Yolngu%20Matha
```

### First Australians (l-firstAustralians)

**Purpose**: Filter items pertaining to First Australians.
**Categories**: book, diary, image, magazine, music, people
**Value**: `y` only

**Examples**:
```
l-firstAustralians=y
```

### Cultural Sensitivity (l-culturalSensitivity)

**Purpose**: Filter culturally sensitive items.
**Categories**: book, diary, image, magazine, music, people
**Value**: `y` only

**Examples**:
```
l-culturalSensitivity=y
```

## Content Type Filters

### Format (l-format)

**Purpose**: Filter by resource format.
**Categories**: book, image, magazine, newspaper, music, diary

**Examples**:
```
l-format=Book
l-format=Map,Photograph
```

### Article Type (l-artType)

**Purpose**: Narrow searches within categories.
**Categories**: newspaper, image, people

**Options**:
- `newspaper` / `gazette` (for newspaper category)
- `images and artefacts` / `maps` (for image category)
- `person` / `organisation` (for people category)

**Examples**:
```
l-artType=newspaper             # Only newspapers, not gazettes
l-artType=person               # Only people, not organisations
```

## Availability Filters

### Availability (l-availability)

**Purpose**: Filter by online availability.
**Categories**: book, image, magazine, music, diary

**Options**:
- `y` - Online
- `y%2Ff` - Freely accessible online (URL encoded)
- `y%2Fr` - Payment/subscription required
- `y%2Fs` - Subscription required
- `y%2Fu` - Possibly online

**Examples**:
```
l-availability=y%2Ff             # Free online access
l-availability=y                # Any online access
```

**Important**: Replace "/" with "%2F" (URL encoding).

### Australian Content (l-australian)

**Purpose**: Filter for Australian published or authored works.
**Categories**: book, image, magazine, music, diary, people
**Value**: `y` only

**Examples**:
```
l-australian=y
```

## People-Specific Filters

### Occupation (l-occupation)

**Purpose**: Filter by occupation.
**Categories**: diary, people

**Examples**:
```
l-occupation=Teacher
l-occupation=Author,Journalist
```

### Birth Year (l-birth)

**Purpose**: Filter by birth/establishment year.
**Categories**: people
**Format**: YYYY

**Examples**:
```
l-birth=1850
l-birth=1850,1851
```

### Death Year (l-death)

**Purpose**: Filter by death/dissolution year.
**Categories**: people
**Format**: YYYY

**Examples**:
```
l-death=1920
l-death=1920,1921
```

## Content-Specific Filters

### Title (l-title)

**Purpose**: Filter by publication title ID.
**Categories**: newspaper, magazine, research

**Examples**:
```
l-title=123                     # Specific newspaper/magazine
l-title=123,456                # Multiple publications
```

### Category (Article) (l-category)

**Purpose**: Filter by article category.
**Categories**: magazine, newspaper

**Common Values**:
- `Article`
- `Advertising`
- `Family notices`
- `Government Gazette Notices`
- `Literature`

**Examples**:
```
l-category=Article
l-category=Article,Literature
```

### Illustrated (l-illustrated)

**Purpose**: Filter by illustration presence.
**Categories**: magazine, newspaper, research
**Type**: Boolean

**Examples**:
```
l-illustrated=true              # Only illustrated articles
l-illustrated=false             # Only non-illustrated articles
```

### Word Count (l-wordCount)

**Purpose**: Filter by article length.
**Categories**: newspaper, magazine, research

**Options**:
- `<100 Words`
- `100 - 1000 Words`  
- `1000+ Words`

**Examples**:
```
l-wordCount=1000%2B%20Words     # Long articles (URL encoded)
l-wordCount=%3C100%20Words      # Short articles (URL encoded)
```

### Map Scale (l-zoom)

**Purpose**: Filter by map scale.
**Categories**: image

**Examples**:
```
l-zoom=1:50000
```

### Audience (l-audience)

**Purpose**: Filter by target audience (Gale articles only).
**Categories**: book, music, research, image

**Options**:
- `Trade`
- `General`
- `Academic`
- `Professional`
- `Children's`

**Examples**:
```
l-audience=Academic
l-audience=General,Trade
```

## Contributor and Collection Filters

### Contributing Collection (l-contribcollection)

**Purpose**: Filter by collection.
**Categories**: book, image, magazine, music, diary, research

**Examples**:
```
l-contribcollection=Australian%20War%20Memorial
```

### Partner NUC (l-partnerNuc)

**Purpose**: Filter by contributing partner's NUC code.
**Categories**: book, image, magazine, music, diary, research

**Examples**:
```
l-partnerNuc=ANL
l-partnerNuc=ANL,VSL
```

## Advanced Parameter Usage

### Other Limits (otherLimits)

**Purpose**: Apply additional limits not covered by specific parameters.
**Format**: URL query string style

**Examples**:
```
otherLimits=l-availability%3DY%26l-year%3D1881
```

**Use Case**: For facet values or limits discovered through faceting that aren't available as dedicated parameters.

## Response Format Control

### Encoding (encoding)

**Purpose**: Choose response format.
**Default**: `xml`

**Options**:
- `json` - JSON format
- `xml` - XML format

**Examples**:
```
encoding=json                   # JSON response
encoding=xml                    # XML response (default)
```

**Alternative**: Use HTTP Accept header:
```
Accept: application/json
Accept: application/xml
```

## Faceting Parameters

### Facet Parameter

**Purpose**: Request facet information for filtering.
**Type**: Array (comma-separated)

**Common Facets**:
- `decade` - Publication decades
- `year` - Publication years
- `format` - Content formats
- `language` - Languages
- `state` - States/territories
- `availability` - Online availability

**Examples**:
```
facet=decade,format             # Request decade and format facets
facet=year                      # Request year facets
```

**External Documentation**: [Supported facets](https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#facetValues)

## Best Practices

### Performance Optimization

1. **Minimal Categories**: Search only needed categories
2. **Brief Records**: Use `reclevel=brief` unless full metadata needed
3. **Selective Includes**: Only include necessary optional information
4. **Appropriate Page Size**: Balance between efficiency and requests

### Search Strategy

1. **Start Broad**: Begin with general terms, then refine
2. **Use Facets**: Let facets guide your filtering choices
3. **Combine Filters**: Use multiple limit parameters for precision
4. **Case Sensitivity**: Facet values are often case-sensitive

### Error Avoidance

1. **Required Category**: Always include category parameter
2. **URL Encoding**: Properly encode special characters
3. **Valid Values**: Use exact facet values from facet responses
4. **Parameter Dependencies**: Respect parameter dependencies (e.g., year requires decade for newspapers)

## Common Search Patterns

### Basic Search
```
https://api.trove.nla.gov.au/v3/result?
  key=YOUR_KEY&
  category=book&
  q=Australian+history&
  n=20&
  encoding=json
```

### Filtered Search
```
https://api.trove.nla.gov.au/v3/result?
  key=YOUR_KEY&
  category=newspaper&
  q=federation&
  l-decade=190&
  l-state=NSW&
  l-illustrated=true&
  sortby=datedesc
```

### Faceted Search
```
https://api.trove.nla.gov.au/v3/result?
  key=YOUR_KEY&
  category=book&
  q=Australian+literature&
  facet=decade,language,format&
  n=0
```

### Bulk Harvesting
```
https://api.trove.nla.gov.au/v3/result?
  key=YOUR_KEY&
  category=book&
  q=*&
  l-australian=y&
  bulkHarvest=true&
  n=100&
  reclevel=full
```

## Related Documentation

- [Parameters Reference](./trove-api-parameters.md) - Complete parameter specifications
- [Faceting Guide](./trove-faceting.md) - Detailed faceting information  
- [Categories & Formats](./trove-api-categories.md) - Available categories and formats
- [Endpoints Reference](./trove-api-endpoints.md) - API endpoint details
- [Response Formats](./trove-response-formats.md) - Response format examples