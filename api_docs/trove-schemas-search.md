# Trove API v3 Search Result Schemas

This document describes the schemas used for search results, facets, and search-related structures in the Trove API.

## Search Result Schema

The main container for search results returned by the `/v3/result` endpoint.

### Properties

- **query** (string): The original search term
- **category** (array of searchResultCategory objects): Array of categories with their results

### XML Structure
```xml
<response>
  <query>search terms</query>
  <category code="book" name="Books & Libraries">
    <!-- category content -->
  </category>
</response>
```

## Search Result Category Schema

Represents a single category within the search results.

### Properties

- **code** (string): The unique system identifier for the category (corresponds to the 'category' search parameter; e.g. book) (XML attribute)
- **name** (string): The human-readable name of the category (e.g. Books & Libraries) (XML attribute)
- **records** (searchResultRecords object): The records container for this category
- **facets** (object): Faceting information
  - **facet** (array of searchResultFacet objects): Individual facet information

## Search Result Records Schema

Container for the actual records and pagination information within a category.

### Properties

#### Pagination
- **s** (string): The current page's cursor mark (XML attribute)
- **n** (number): The current page size (XML attribute)
- **total** (number): The total number of results (XML attribute)
- **next** (string): The complete URL to retrieve the next page of results (XML attribute)
- **nextStart** (string): The cursorMark for the next page of results (XML attribute)

#### Result Arrays
- **work** (array of work objects): The list of Work results (where applicable)
- **article** (array of article objects): The list of Article results (where applicable)
- **people** (array of people objects): The list of Person/Organisation results (where applicable)
- **list** (array of list objects): The list of List results (where applicable)
- **item** (array of item objects): A container entity to be used when bulkHarvest = true and category = all

## Bulk Harvest Item Schema

Used when `bulkHarvest = true` and `category = all`.

### Properties

Contains one of the following:
- **work** (work object): A work record
- **article** (article object): An article record  
- **people** (people object): A person/organisation record
- **list** (list object): A list record

## Search Result Facet Schema

Represents facet information for filtering search results.

### Properties

- **name** (string): The unique system name of the facet (e.g. publicationplace) (XML attribute)
- **displayname** (string): The human-readable name of the facet (e.g. Place of Publication) (XML attribute)
- **term** (array of searchResultFacetTerm objects): The list of possible values for the facet

### Description

Facets are categories that describe all the records in a particular result set. For example, if you request the decade facet, the response will include a list of decades your results span across, and how many results are found in each decade.

### External Documentation

Supported facets are described at: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#facetValues

## Search Result Facet Term Schema

Represents a particular value for a given facet.

### Properties

- **count** (integer, int64): The number of records in the search result that match this facet term (XML attribute)
- **url** (string): The Trove API URL to perform a search using this facet term (XML attribute)
- **search** (string): The facet value used in the corresponding limit field i.e. l-<limit>. Facet values are often case-sensitive, so be sure to use the value exactly as provided
- **display** (string): The facet value used for display (usually same as 'Search' value)
- **term** (array of searchResultFacetTerm objects): Nested facet terms for hierarchical facets

### Usage Notes

- Facet values are often case-sensitive
- Use the `search` value exactly as provided when constructing limit parameters
- The `url` property provides a ready-to-use API URL for applying this facet filter

## Images Result Schema

Represents image information for a work.

### Properties

- **workId** (string): The requested parent work object id
- **count** (integer): The number of images available for this resource
- **images** (array of image objects): The ordered list of images available for this resource

### Image Object Properties

- **imageId** (string): The NLA Object Identifier of the image
- **culturallySensitive** (string): An indicator of cultural sensitivity, particularly in respect to First Australians
- **title** (string): The title of the image, where available
- **order** (integer): The order of the image within the parent work, where applicable

### XML Structure
```xml
<images>
  <workId>123456</workId>
  <count>5</count>
  <images>
    <imageId>nla.obj-123456789</imageId>
    <title>Image Title</title>
    <order>1</order>
  </images>
</images>
```

## List Item Schema

Represents an item within a user-created list.

### Properties

- **note** (string): A note the creator of the list wrote about this item, such as why they decided to include it, or extra description of the item
  - Example: `"Henry Thomas Byrnes Death Notice"`

### Content Types

The list item will contain one of the following:

- **work** (work object): A brief record for a work that belongs to this list
- **article** (article object): A brief record for a digitised newspaper article that belongs to this list
- **people** (people object): A very brief record for a person or organisation that belongs to this list
- **externalWebsite** (object): Information about a link to page outside of Trove that has been included in this list
  - **title** (string): The name of the webpage
    - Example: `"Google"`
  - **identifier** (array of identifier objects): The URL of the webpage
  - **relevance** (relevance object): Relevance information

### Status Information

- **deleted** (object): Indicator to show whether the item has been recently deleted from Trove
  - **deleted** (string): The status of the linked record ('deleted')
  - **value** (string): The reason the linked record is not available ('The resource described by this item has been deleted from Trove')

### Cultural Sensitivity

- **culturallySensitive** (string): An indicator of cultural sensitivity, particularly in respect to First Australians
- **firstAustralians** (string): Whether the item pertains to First Australians

## Title Search Result Schema

Used for newspaper and magazine title search results.

### Properties

- **total** (integer): The number of matching titles (XML attribute)
- **newspaper** (array of articleTitle objects): The list of matching Newspaper or Gazette titles (where applicable)
- **magazine** (array of magazineTitle objects): The list of matching Magazine or Newsletter titles (where applicable)

### XML Structure
```xml
<response total="1234">
  <newspaper id="123">
    <title>Newspaper Title</title>
    <!-- additional newspaper properties -->
  </newspaper>
  <magazine id="456">
    <title>Magazine Title</title>
    <!-- additional magazine properties -->
  </magazine>
</response>
```

## Contributor Search Result Schema

Used for contributor search results.

### Properties

- **total** (integer): The number of matching Contributors (XML attribute)
- **contributor** (array of contributor objects): The list of matching Contributors

### XML Structure
```xml
<response total="50">
  <contributor id="ANL">
    <name>National Library of Australia</name>
    <!-- additional contributor properties -->
  </contributor>
</response>
```

## Search Examples

### Basic Search Response (JSON)

```json
{
  "query": "Australian Prime Ministers",
  "category": [
    {
      "code": "book",
      "name": "Books & Libraries",
      "records": {
        "s": "*",
        "n": 1,
        "total": 219185,
        "next": "https://api.trove.nla.gov.au/v3/result?...",
        "nextStart": "AoIIRPXGZypzdTMyNDExODI5",
        "work": [
          {
            "id": "32411829",
            "url": "https://api.trove.nla.gov.au/v3/work/32411829",
            "troveUrl": "https://trove.nla.gov.au/work/32411829",
            "title": "Australian prime ministers / edited by Michelle Grattan",
            "contributor": ["Grattan, Michelle"],
            "issued": "1900-2020",
            "type": ["Book", "Book/Illustrated", "Object"],
            "hasCorrections": "N",
            "relevance": {
              "score": 1966.2000732421875,
              "value": "very relevant"
            },
            "holdingsCount": 224,
            "versionCount": 17
          }
        ]
      }
    }
  ]
}
```

### Basic Search Response (XML)

```xml
<response>
  <query>Australian Prime Ministers</query>
  <category code="book" name="Books &amp; Libraries">
    <records s="*" n="1" total="219185" next="https://api.trove.nla.gov.au/v3/result?..." nextStart="AoIIRPXGZypzdTMyNDExODI5">
      <work id="32411829" url="https://api.trove.nla.gov.au/v3/work/32411829">
        <troveUrl>https://trove.nla.gov.au/work/32411829</troveUrl>
        <title>Australian prime ministers / edited by Michelle Grattan</title>
        <contributor>Grattan, Michelle</contributor>
        <issued>1900-2020</issued>
        <type>Book</type>
        <type>Book/Illustrated</type>
        <type>Object</type>
        <hasCorrections>N</hasCorrections>
        <relevance score="1966.2000732421875">
          <value>very relevant</value>
        </relevance>
        <holdingsCount>224</holdingsCount>
        <versionCount>17</versionCount>
      </work>
    </records>
  </category>
</response>
```

## Related Documentation

- [Core Schemas](./trove-schemas-core.md) - Work, Article, People, and List schemas
- [Utility Schemas](./trove-schemas-utility.md) - Supporting utility schemas
- [Faceting Guide](./trove-faceting.md) - Detailed faceting information
- [Parameters Reference](./trove-api-parameters.md) - Search parameters and faceting options