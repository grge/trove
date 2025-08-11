# Trove API v3 Contributor and Title Schemas

This document describes the schemas for contributors, newspaper titles, magazine titles, and related structures.

## Contributor Schema

Represents an institution or organisation that contributes content to Trove.

### Properties

#### Basic Identification
- **id** (string): Either the contributor's NUC or a numeric id (XML attribute)
  - Example: `"ANL"`
- **url** (string): The contributor's Trove API url (XML attribute)
  - Example: `"https://api.trove.nla.gov.au/v3/contributor/ANL"`
- **name** (string): The contributor's name
  - Example: `"National Library of Australia"`
- **nuc** (string): The contributor's NUC
  - Example: `"ANL"`
- **shortname** (string): A shorter version of the contributor's name
  - Example: `"NLA"`

#### Organisation Details
- **totalholdings** (integer): The total number of holders the contributor has
  - Example: `123`
- **accesspolicy** (string): The contributor's access conditions
  - Example: `"Open to the public"`
- **homepage** (string): The contributor's web page
  - Example: `"https://nla.gov.au"`
- **algentry** (string): The url to contributor's ALG entry

#### Hierarchical Relationships

##### Parent Institution
- **parent** (object): The contributor's parent institution, if there is one
  - **id** (string): The identifier of the parent institution (XML attribute)
  - **url** (string): The parent institution's Trove API url (XML attribute)
  - **name** (string): The parent institution's name

##### Child Institutions
- **children** (array of contributor objects): The contributor's child institutions, if there are any

## Article Title Schema (Newspaper/Gazette)

Represents a newspaper or gazette publication title.

### Properties

#### Basic Information
- **id** (string): ID of the newspaper or gazette title (XML attribute)
- **title** (string): Name of the newspaper (or magazine, gazette)
  - Example: `"The Canberra Times (ACT : 1926-1954)"`
- **troveUrl** (string): A link to view this newspaper or gazette title in Trove
  - Example: `"https://trove.nla.gov.au/ndp/del/title/11"`

#### Publication Details
- **state** (enum): The state the newspaper or gazette was primarily published in
  - Values: `International`, `National`, `ACT`, `New South Wales`, `Northern Territory`, `Queensland`, `South Australia`, `Tasmania`, `Victoria`, `Western Australia`
- **publisher** (string): The name of the publisher, where available
- **place** (array of strings): Place is the geographic region the item is about (geographic coverage) and includes Australian states and territories and a number of Australia's closest International neighbours
  - Example: `["New South Wales"]`

#### Identifiers and Alternative Names
- **issn** (string): International Standard Serial Number
  - Example: `"01576925"`
- **alternateTitles** (array of strings): Other names for this title

#### Publication Dates
- **startDate** (string): The publication date of the earliest issue of this newspaper available in Trove, in the format YYYY-MM-DD
  - Example: `"1926-09-03"`
- **endDate** (string): The publication date of the most recent issue of this newspaper or gazette available in Trove, in the format YYYY-MM-DD
  - Example: `"1954-12-31"`

#### Year-by-Year Information
- **year** (array of year objects): A list of the publication years for this newspaper or gazette that are included in Trove
  - **date** (string): A year this newspaper or gazette title was published, in the format YYYY (XML attribute)
    - Example: `"1926"`
  - **issuecount** (integer): The number of issues published in this year (XML attribute)
    - Example: `18`
  - **issue** (array of issue objects): Information about a particular issue of this newspaper or gazette
    - **id** (string): Issue id (XML attribute)
      - Example: `"3863"`
    - **date** (string): Date this issue was published, in the format YYYY-MM-DD (XML attribute)
      - Example: `"1926-09-03"`
    - **url** (string): URL to view this issue in Trove (XML attribute)
      - Example: `"https://trove.nla.gov.au/ndp/del/issue/3863"`

### XML Structure Example

```xml
<newspaper id="11">
  <title>The Canberra Times (ACT : 1926-1954)</title>
  <state>ACT</state>
  <issn>01576925</issn>
  <publisher>Publisher Name</publisher>
  <place>Australian Capital Territory</place>
  <troveUrl>https://trove.nla.gov.au/ndp/del/title/11</troveUrl>
  <startDate>1926-09-03</startDate>
  <endDate>1954-12-31</endDate>
  <year date="1926" issuecount="18">
    <issue id="3863" date="1926-09-03" url="https://trove.nla.gov.au/ndp/del/issue/3863"/>
  </year>
</newspaper>
```

## Magazine Title Schema

Inherits all properties from articleTitle schema. Used specifically for magazine and newsletter titles.

### Properties

All properties from articleTitle schema apply, with magazine-specific usage contexts.

### XML Structure
```xml
<magazine id="nla.obj-2526944948">
  <title>... Annual report of the Canned Fruits Control Board for the year ...</title>
  <troveUrl>https://nla.gov.au/work/nla.obj-2526944948</troveUrl>
  <startDate>1927-01-01 00:00:00.0</startDate>
  <!-- additional magazine properties -->
</magazine>
```

## Version Schema

Represents a version/edition that is part of a work.

### Properties

#### Basic Information
- **id** (string): A string of internal Trove ids for any records that make up this version (XML attribute)
- **type** (array of format objects): The format of this version. There may be more than one type element
  - Example: `"Book/Illustrated"`
- **issued** (array of strings): The date this version was issued/published/created. Either YYYY or YYYY-MM or YYYY-MM-DD
  - Example: `"1980-01-31"`

#### Records
- **record** (array of record objects): Container element for a Dublin Core record. These records are contributed to Trove from various sources and have often been converted by Trove or the original contributor to Dublin Core from other formats

#### Holdings
- **holdingsCount** (integer): The number of institutions (libraries, archives, etc) who have or control a copy of this work
- **holding** (array of holding objects): A container element for information about a copy of this version held by a particular organisation (library, archive, etc)

#### User-Generated Content
- **tagCount** (itemCount object): The number of public tags on this version (not including tags placed at the work level)
- **commentCount** (itemCount object): The number of public comments on this version (not including comments placed at the work level)
- **tag** (array of tag objects): A public tag added to the version. There may be more than one tag element. Tags can also be added to a version (the version/tag element)
- **comment** (array of comment objects): A public comment added to the version. There may be more than one comment element. Comments can also be added to a version (the version/comment element)

#### Additional Information
- **identifier** (array of identifier objects): Additional identifiers for the version
- **culturallySensitive** (string): An indicator of cultural sensitivity, particularly in respect to First Australians
- **firstAustralians** (string): Whether the item pertains to First Australians

## Holding Schema

Represents information about a copy of a work held by an institution.

### Properties

#### Institution Information
- **nuc** (string): The NUC symbol of an organisation with a copy of this work (XML attribute)
  - Example: `"NWU"`
- **contributor** (string): The Trove API URL to the Contributor who owns this holding (XML attribute)
  - Example: `"/contributor/VSL"`
- **name** (string): The name of an organisation which controls a copy of this work. Provided instead of a NUC symbol for organisations which do not have one assigned (XML attribute)
  - Example: `"Internet Archive"`
- **library** (string): In future, this will be the API access point to look up more information about this organisation (XML attribute)
  - Example: `"/library/NWU"`

#### Access Information
- **url** (object): The best available link is shown
  - **type** (enum): The type of link (XML attribute)
    - Values: `deepLink`, `homepage`, `catalogue`
    - Descriptions:
      - `"deepLink"`: a link to view this item in the holding institution's catalogue/website
      - `"catalogue"`: a link to the holding institution's catalogue home page
      - `"homepage"`: a link to the organisation's homepage
  - **value** (string): The url

#### Call Numbers
- **callNumber** (array of objects): The institution's call number for their copy of the work
  - **localIdentifier** (string): Also provided if available. From Libraries Australia MARC records, this is extracted from 850$b (XML attribute)
  - **value** (string): The call number

### Example
```xml
<holding nuc="NWU" contributor="/contributor/VSL">
  <url type="deepLink">https://example.org/catalogue/item/123</url>
  <callNumber localIdentifier="LOC123">
    <value>794.1 SMI</value>
  </callNumber>
</holding>
```

## Record Level Enumeration

Used to specify the level of detail in record responses.

### Values

- **brief** (default): Brief metadata record
- **full**: Full metadata record with complete information

### Usage

Used with the `reclevel` parameter to control the amount of detail returned in API responses.

## Related Documentation

- [Core Schemas](./trove-schemas-core.md) - Work, Article, People, and List schemas  
- [Utility Schemas](./trove-schemas-utility.md) - Supporting utility schemas
- [Metadata Schemas](./trove-schemas-metadata.md) - Dublin Core and record structures
- [Parameters Reference](./trove-api-parameters.md) - Complete parameter documentation