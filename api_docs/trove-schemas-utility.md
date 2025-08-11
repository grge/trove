# Trove API v3 Utility Schemas

This document describes the supporting utility schemas used throughout the Trove API, including common structures for identifiers, languages, spatial information, user-generated content, and other shared components.

## Language Schema

Represents language information for resources.

### Properties

- **value** (string): Language name or code of the item
- **type** (string): Language code or standard used to describe the item (XML attribute)

### Usage Examples

- ISO 639-2 (3-letter codes): `{"value": "eng", "type": "iso639-2"}`
- Plain text: `{"value": "English", "type": "text"}`
- Austlang codes: `{"value": "A1", "type": "austlang"}`

### External Documentation

- [Austlang Codes](https://trove.nla.gov.au/austlang-codes)

## Spatial Schema

Represents geographic information for resources.

### Properties

- **value** (string): Geographic place name or code for the item
- **scheme** (string): Geographic place code or standard used to describe the item (XML attribute)

### Description

The spatial topic of the item, e.g. the location a photograph was taken.

### Usage Examples

- Place name: `{"value": "Sydney, NSW", "scheme": "text"}`
- Coordinates: `{"value": "-33.8688,151.2093", "scheme": "coordinates"}`
- Geographic codes: `{"value": "u-at-ne", "scheme": "marc-gac"}`

## Identifier Schema

Represents various types of identifiers and links for resources.

### Properties

#### Core Properties
- **type** (enum): The type of the identifier
  - Values: `url`, `isbn`, `ismn`, `issn`, `control number`
  - Example: `"url"`
- **value** (string): The value of the identifier. Will vary depending on the type and linktype properties

#### URL-Specific Properties (when type='url')
- **linktype** (enum): Describes the type of content available at the url, for type='url' identifiers
  - Values: `fulltext`, `restricted`, `subscription`, `unknown`, `notonline`, `thumbnail`, `viewcopy`, `'searchable resource'`, `'metadata record'`, `mediated`
- **url** (string): Depending on the linktype: The best known link to this work is included automatically in the brief record (if available); or A link to access this work through a particular organisation's subscription; or A link to a thumbnail-sized image representing this item (if available) (XML attribute)
  - Example: `"http://bishop.slq.qld.gov.au/webclient/DeliveryManager?pid=282557"`
- **linktext** (string): Link label, for type='url' identifiers (XML attribute)
  - Example: `"View online"`

#### Subscription-Specific Properties (when linktype='subscription')
- **nuc** (string): The NUC symbol for the organisation that has the subscription, for linktype='subscription' identifiers (XML attribute)
  - Example: `"NWU"`
- **library** (string): In future will be the API access point for more information about the organisation that has the subscription (XML attribute)
  - Example: `"/library/ABS"`

#### Control Number Properties (when type='control number')
- **source** (string): The source of the identifier, for type='control number' identifiers (XML attribute)
  - Example: `"AuCNLKIN"`

### External Documentation

Additional information on possible linktypes: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#list-of-possible-linktype-values

### Usage Examples

```json
// URL identifier with fulltext access
{
  "type": "url",
  "linktype": "fulltext", 
  "url": "https://example.org/fulltext/123456",
  "linktext": "View full text"
}

// ISBN identifier
{
  "type": "isbn",
  "value": "9780123456789"
}

// Subscription access
{
  "type": "url",
  "linktype": "subscription",
  "url": "https://database.example.com/article/123",
  "nuc": "NLA",
  "library": "/library/NLA"
}
```

## Relevance Schema

Represents relevance scoring for search results.

### Properties

- **score** (number): A numeric representation of how relevant this record is to the search. This number can be compared to other search results in this category, but not to results from other categories (XML attribute)
  - Example: `0.009942865`
- **value** (enum): How relevant the record is to the search
  - Values: `very relevant`, `likely to be relevant`, `may have relevance`, `limited relevance`, `vaguely relevant`

### Usage

Relevance scores are only meaningful within the same category and should not be compared across different categories (book vs newspaper, etc.).

## Comment Schema

Represents user comments on resources.

### Properties

- **lastupdated** (string): When the comment was most recently added/edited (UTC timezone) (XML attribute)
  - Example: `"2011-12-09T09:43:00Z"`
- **by** (string): The username of the person who added the comment (XML attribute)
  - Examples:
    - `"public:bobbyfamilytree"`
    - `"rholley"` (NLA staff accounts do not include the 'public' prefix)
    - `"anonymous"` (no user account identified)
- **rating** (string): An optional rating of the item from 0 to 5 (XML attribute)
  - Example: `"5"`
- **value** (string): A public comment added to the work. There may be more than one comment element. Comments can also be added to a version (the version/comment element)
  - Example: `"Have any names been listed as to who is in the photo?"`

## Tag Schema

Represents user tags on resources.

### Properties

- **lastupdated** (string): When the tag was added (UTC timezone) (XML attribute)
  - Example: `"2011-12-12T15:44:01Z"`
- **value** (string): A public tag added to the work. There may be more than one tag element. Tags can also be added to a version (the version/tag element)
  - Example: `"lightning"`

## Item Count Schema

Generic object representing a structure with a count and an optional level attribute.

### Properties

- **level** (enum): The record level that encapsulates the counted items (either 'work' or 'version') (XML attribute)
  - Values: `work`, `version`
- **value** (integer): The count

### Description

Used for counting tags, comments, and other user-generated content at different levels (work level vs version level).

### Usage Examples

```json
// Work-level tag count
{
  "level": "work",
  "value": 15
}

// Version-level comment count  
{
  "level": "version",
  "value": 3
}
```

## IsPartOf Schema

Represents relationships where a resource is part of a larger collection or series.

### Properties

- **value** (string): The related resource
- **url** (string): The Trove API URL to the related resource (XML attribute)
- **type** (string): The type of related resource (e.g. series) (XML attribute)

### Description

A related resource in which the described resource is physically or logically included, e.g. a photograph or manuscript collection. For articles, the journal or periodical the article belongs to (if known).

### Usage Examples

```json
{
  "value": "Australian Historical Studies",
  "url": "/work/12345",
  "type": "series"
}
```

## Error Schema

Represents error responses from the API.

### Properties

- **statusCode** (integer): The HTTP status code
  - Example: `404`
- **statusText** (string): The HTTP status reason phrase
  - Example: `"Not Found"`
- **description** (string): A brief description of the error
  - Example: `"A matching record could not be found."`

### XML Structure
```xml
<error>
  <statusCode>404</statusCode>
  <statusText>Not Found</statusText>
  <description>A matching record could not be found.</description>
</error>
```

### Common Error Codes

- **400 Bad Request**: Invalid parameters or malformed request
- **401 Unauthorized**: Invalid or missing API key
- **403 Forbidden**: Access denied
- **404 Not Found**: Resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

## Record Level Enumeration

Used to specify the detail level of returned records.

### Values

- **brief** (default): Brief metadata record
- **full**: Full metadata record

### Usage

Used with the `reclevel` parameter to control response detail level across various endpoints.

## Categories Enumeration

Supported categories for searching the Trove API.

### Values

- `all` - Everything except the Web
- `book` - Books & Libraries  
- `diary` - Diaries, Letters & Archives
- `image` - Images, Maps & Artefacts
- `list` - Lists
- `magazine` - Magazines & Newsletters
- `music` - Music, Audio & Video
- `newspaper` - Newspapers & Gazettes
- `people` - People & Organisations
- `research` - Research & Reports

## Formats Enumeration

Complete list of supported format types used throughout the API.

### General Formats

- `Archived website`
- `Art work`
- `Data set`
- `Government publication`
- `Microform`
- `Object`
- `Photograph`
- `Poster, chart, other`
- `Published`
- `Thesis`
- `Unpublished`

### Article Formats

- `Article`
- `Article/Abstract`
- `Article/Book chapter`
- `Article/Conference paper`
- `Article/Journal or magazine article`
- `Article/Other article`
- `Article/Report`
- `Article/Review`
- `Article/Working paper`

### Book Formats

- `Book`
- `Book/Braille`
- `Book/Illustrated`
- `Book/Large print`
- `Audio book`

### Conference Materials

- `Conference Proceedings`

### Map Formats

- `Map`
- `Map/Aerial photograph`
- `Map/Atlas`
- `Map/Braille`
- `Map/Electronic`
- `Map/Globe or object`
- `Map/Large print`
- `Map/Map series`
- `Map/Microform`
- `Map/Single map`

### Music and Audio Formats

- `Printed music`
- `Sheet music`
- `Sound`
- `Sound/Interview, lecture, talk`
- `Sound/Other sound`
- `Sound/Recorded music`

### Periodical Formats

- `Periodical`
- `Periodical/Journal, magazine, other`
- `Periodical/Newspaper`

### Video Formats

- `Video`
- `Video/Captioned`

## Usage in Core Schemas

These utility schemas are referenced throughout the core schemas:

- **Language**: Used in work, article, and Dublin Core records
- **Spatial**: Used in work and Dublin Core records for geographic information
- **Identifier**: Used across all record types for various identifiers and URLs
- **Relevance**: Used in search results for all record types
- **Comment/Tag**: Used in work, article, people, and list records
- **ItemCount**: Used for counting user-generated content
- **IsPartOf**: Used in work records for series/collection relationships

## Related Documentation

- [Core Schemas](./trove-schemas-core.md) - Main record types that use these utilities
- [Search Schemas](./trove-schemas-search.md) - Search-specific schema usage
- [Metadata Schemas](./trove-schemas-metadata.md) - Dublin Core usage of utilities
- [Parameters Reference](./trove-api-parameters.md) - Parameter usage for these schema types