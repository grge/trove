# Trove API v3 Response Formats Guide

This guide demonstrates the JSON and XML response formats for all Trove API endpoints, including complete examples from the original specification.

## Format Selection

### Default Format
- **Default**: XML
- **Alternative**: JSON

### Specifying Format

#### Method 1: encoding Parameter
```
encoding=json                   # JSON response
encoding=xml                    # XML response (default)
```

#### Method 2: HTTP Accept Header
```
Accept: application/json        # JSON response
Accept: application/xml         # XML response
```

## Search Results Format

### JSON Response Example

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
        "next": "https://api.trove.nla.gov.au/v3/result?key=####&category=book&q=Australian%20Prime%20Ministers&s=%2A&n=1&sortBy=relevance&bulkHarvest=false&reclevel=brief&encoding=json?s=AoIIRPXGZypzdTMyNDExODI5",
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

### XML Response Example

```xml
<response>
  <query>Australian Prime Ministers</query>
  <category code="book" name="Books &amp; Libraries">
    <records s="*" n="1" total="219185" next="https://api.trove.nla.gov.au/v3/result?key=####&amp;category=book&amp;q=Australian%20Prime%20Ministers&amp;s=%252A&amp;n=1&amp;sortBy=relevance&amp;bulkHarvest=false&amp;reclevel=brief&amp;encoding=xml?s=AoIIRPXGZypzdTMyNDExODI5" nextStart="AoIIRPXGZypzdTMyNDExODI5">
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

## Work Record Format

### JSON Response Example

```json
{
  "id": "32411829",
  "url": "https://api.trove.nla.gov.au/v3/work/32411829",
  "troveUrl": "https://trove.nla.gov.au/work/32411829",
  "title": "Australian prime ministers / edited by Michelle Grattan",
  "contributor": ["Grattan, Michelle"],
  "issued": "1900-2020",
  "type": ["Book", "Book/Illustrated", "Object"],
  "hasCorrections": "N",
  "holdingsCount": 224,
  "versionCount": 17
}
```

### XML Response Example

```xml
<work id="32411829" url="https://api.trove.nla.gov.au/v3/work/32411829">
  <troveUrl>https://trove.nla.gov.au/work/32411829</troveUrl>
  <title>Australian prime ministers / edited by Michelle Grattan</title>
  <contributor>Grattan, Michelle</contributor>
  <issued>1900-2020</issued>
  <type>Book</type>
  <type>Book/Illustrated</type>
  <type>Object</type>
  <hasCorrections>N</hasCorrections>
  <holdingsCount>224</holdingsCount>
  <versionCount>17</versionCount>
</work>
```

## People Record Format

### JSON Response Example

```json
{
  "id": "551057",
  "url": "https://api.trove.nla.gov.au/v3/people/551057",
  "troveUrl": "https://trove.nla.gov.au/people/551057",
  "type": "person",
  "primaryName": "Barton, Edmund, (Sir) (1849-1920)",
  "primaryDisplayName": "Edmund Barton",
  "title": ["Sir"],
  "occupation": ["Federationist", "Prime Minister", "Judge"]
}
```

### XML Response Example

```xml
<people id="551057" url="https://api.trove.nla.gov.au/v3/people/551057">
  <troveUrl>https://trove.nla.gov.au/people/551057</troveUrl>
  <type>person</type>
  <primaryName>Barton, Edmund, (Sir) (1849-1920)</primaryName>
  <primaryDisplayName>Edmund Barton</primaryDisplayName>
  <title>Sir</title>
  <occupation>Federationist</occupation>
  <occupation>Prime Minister</occupation>
  <occupation>Judge</occupation>
</people>
```

## List Record Format

### JSON Response Example

```json
{
  "id": "32141",
  "url": "https://api.trove.nla.gov.au/v3/list/32141",
  "troveUrl": "https://trove.nla.gov.au/list?id=32141",
  "title": "Australian Prime Ministers",
  "description": "particularly births, marriages (and children) and deaths",
  "creator": "public:Drewy",
  "listItemCount": 21
}
```

### XML Response Example

```xml
<list id="32141" url="https://api.trove.nla.gov.au/v3/list/32141">
  <troveUrl>https://trove.nla.gov.au/list?id=32141</troveUrl>
  <title>Australian Prime Ministers</title>
  <description>particularly births, marriages (and children) and deaths</description>
  <creator>public:Drewy</creator>
  <listItemCount>21</listItemCount>
</list>
```

## Newspaper Article Format

### JSON Response Example

```json
{
  "id": "152471373",
  "url": "https://api.trove.nla.gov.au/v3/newspaper/152471373",
  "heading": "AUSTRALIAN PRIME MINISTERS VIEWS",
  "category": "Article",
  "title": {
    "id": "742",
    "title": "Daily Telegraph (Launceston, Tas. : 1883 - 1928)"
  },
  "date": "1912-09-27",
  "page": "5",
  "pageSequence": "5",
  "troveUrl": "https://trove.nla.gov.au/ndp/del/article/152471373"
}
```

### XML Response Example

```xml
<article id="152471373" url="https://api.trove.nla.gov.au/v3/newspaper/152471373">
  <heading>AUSTRALIAN PRIME MINISTERS VIEWS</heading>
  <category>Article</category>
  <title id="742">
    <title>Daily Telegraph (Launceston, Tas. : 1883 - 1928)</title>
  </title>
  <date>1912-09-27</date>
  <page>5</page>
  <pageSequence>5</pageSequence>
  <troveUrl>https://trove.nla.gov.au/ndp/del/article/152471373</troveUrl>
</article>
```

## Magazine Title Search Format

### JSON Response Example

```json
{
  "total": 2492,
  "magazine": [
    {
      "id": "nla.obj-2526944948",
      "title": "... Annual report of the Canned Fruits Control Board for the year ...",
      "troveUrl": "https://nla.gov.au/work/nla.obj-2526944948",
      "startDate": "1927-01-01 00:00:00.0"
    },
    {
      "id": "nla.obj-244631375",
      "title": "..."
    }
  ]
}
```

### XML Response Example

```xml
<response total="2492">
  <magazine id="nla.obj-2526944948">
    <title>... Annual report of the Canned Fruits Control Board for the year ...</title>
    <troveUrl>https://nla.gov.au/work/nla.obj-2526944948</troveUrl>
    <startDate>1927-01-01 00:00:00.0</startDate>
  </magazine>
  <magazine id="nla.obj-244631375">
    <title>......</title>
  </magazine>
</response>
```

## Format Differences

### Key Differences Between JSON and XML

#### Attributes vs Properties
- **XML**: Uses attributes for IDs and metadata
- **JSON**: All data as object properties

```xml
<!-- XML: id as attribute -->
<work id="123456" url="https://api.example.com">
```

```json
// JSON: id as property
{
  "id": "123456",
  "url": "https://api.example.com"
}
```

#### Repeated Elements
- **XML**: Multiple elements with same name
- **JSON**: Arrays for multiple values

```xml
<!-- XML: Multiple type elements -->
<type>Book</type>
<type>Illustrated</type>
```

```json
// JSON: Array of types
"type": ["Book", "Illustrated"]
```

#### Nested Structures
- **XML**: Hierarchical element structure
- **JSON**: Nested objects

```xml
<!-- XML: Nested elements -->
<relevance score="1966.2">
  <value>very relevant</value>
</relevance>
```

```json
// JSON: Nested object
"relevance": {
  "score": 1966.2,
  "value": "very relevant"
}
```

### Encoding Considerations

#### XML Encoding
- HTML entities: `&amp;`, `&lt;`, `&gt;`
- CDATA sections for complex content
- Namespace declarations when needed

#### JSON Encoding
- UTF-8 character encoding
- Escaped quotes and backslashes
- No HTML entity encoding needed

### Content Type Headers

#### XML Response
```
Content-Type: application/xml; charset=utf-8
```

#### JSON Response
```
Content-Type: application/json; charset=utf-8
```

## Error Response Formats

### JSON Error Example

```json
{
  "statusCode": 404,
  "statusText": "Not Found",
  "description": "A matching record could not be found."
}
```

### XML Error Example

```xml
<error>
  <statusCode>404</statusCode>
  <statusText>Not Found</statusText>
  <description>A matching record could not be found.</description>
</error>
```

## Complex Response Examples

### Search with Facets (JSON)

```json
{
  "query": "Australian history",
  "category": [
    {
      "code": "book",
      "name": "Books & Libraries",
      "records": {
        "s": "*",
        "n": 5,
        "total": 45678,
        "work": [
          {
            "id": "12345678",
            "title": "A History of Australia",
            "contributor": ["Manning Clark"]
          }
        ]
      },
      "facets": {
        "facet": [
          {
            "name": "decade",
            "displayname": "Decade",
            "term": [
              {
                "count": 8901,
                "search": "200",
                "display": "2000s",
                "url": "https://api.trove.nla.gov.au/v3/result?..."
              }
            ]
          }
        ]
      }
    }
  ]
}
```

### Search with Facets (XML)

```xml
<response>
  <query>Australian history</query>
  <category code="book" name="Books &amp; Libraries">
    <records s="*" n="5" total="45678">
      <work id="12345678">
        <title>A History of Australia</title>
        <contributor>Manning Clark</contributor>
      </work>
    </records>
    <facets>
      <facet name="decade" displayname="Decade">
        <term count="8901" search="200" display="2000s" url="https://api.trove.nla.gov.au/v3/result?..."/>
      </facet>
    </facets>
  </category>
</response>
```

### Full Work Record with Holdings (JSON)

```json
{
  "id": "32411829",
  "url": "https://api.trove.nla.gov.au/v3/work/32411829",
  "title": "Australian prime ministers",
  "contributor": ["Grattan, Michelle"],
  "issued": "2000",
  "type": ["Book"],
  "holding": [
    {
      "nuc": "ANL",
      "url": {
        "type": "deepLink",
        "value": "https://catalogue.nla.gov.au/Record/123456"
      },
      "callNumber": [
        {
          "value": "994.06 AUS"
        }
      ]
    }
  ],
  "version": [
    {
      "id": "123456789",
      "type": ["Book"],
      "issued": ["2000"],
      "record": [
        {
          "metadata": {
            "dc": {
              "title": ["Australian prime ministers"],
              "creator": [
                {
                  "name": "Grattan, Michelle",
                  "type": "editor"
                }
              ]
            }
          }
        }
      ]
    }
  ]
}
```

## Choosing the Right Format

### JSON Advantages
- **Web Development**: Native JavaScript support
- **APIs**: Standard for REST APIs
- **Parsing**: Faster parsing in most languages
- **Size**: Generally more compact

### XML Advantages
- **Standards**: Strong schema validation support
- **Namespaces**: Better namespace handling
- **Metadata**: Rich attribute support
- **Legacy**: Better for older systems

### Performance Considerations

#### JSON
- Smaller payload size (typically 10-20% smaller)
- Faster parsing in most programming languages
- Better for mobile and bandwidth-constrained environments

#### XML
- Self-describing structure
- Better for complex hierarchical data
- More metadata through attributes
- Better validation and schema support

## Best Practices

### Format Selection
1. **Use JSON** for web applications and modern APIs
2. **Use XML** when you need strong validation or working with legacy systems
3. **Consider bandwidth** - JSON is more compact
4. **Test both formats** to see which works better for your use case

### Processing Tips
1. **Consistent Handling**: Handle both formats if supporting multiple clients
2. **Error Handling**: Both formats use the same error structure
3. **Attribute Mapping**: Plan for XML attributes vs JSON properties
4. **Array Handling**: XML multiple elements become JSON arrays

### Development Guidelines
1. **Content Negotiation**: Use Accept headers when possible
2. **Default Handling**: Be prepared for XML as the default
3. **Validation**: Validate structure regardless of format
4. **Documentation**: Document which format your application expects

## Related Documentation

- [Core Schemas](./trove-schemas-core.md) - Structure definitions for all record types
- [Search Schemas](./trove-schemas-search.md) - Search result structures  
- [Utility Schemas](./trove-schemas-utility.md) - Common utility schemas
- [Error Handling](./trove-error-handling.md) - Error response handling