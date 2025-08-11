# Trove API v3 Metadata Schemas

This document describes the metadata record structures, Dublin Core schemas, and EAC-CPF (Encoded Archival Context - Corporate bodies, Persons, and Families) schemas used in the Trove API.

## Record Schema

Container for metadata records contributed to Trove.

### Properties

#### Header Information
- **header** (object): Record header information
  - **identifier** (string): Unique identifier number or value for contributors for each record contributed to Trove
  - **datestamp** (string): Datestamp for each record indicating the date of creation, modification or deletion of the record in Trove
  - **setSpec** (string): Optional unique value for contributors to group records contributed to Trove as a set

#### Metadata Content
- **metadata** (object): The actual metadata content
  - **dc** (dcRecord object): Dublin Core record
  - **eac-cpf** (object): The EAC-CPF record, processed into a structure compatible with the OpenAPI specification. See https://eac.staatsbibliothek-berlin.de/ for details of the EAC-CPF schema
    - **additionalProperties**: true (allows for flexible EAC-CPF structure)
  - **rawXml** (string): When the "raweaccpf" Include option has been selected, this field will contain the original, unprocessed and unformatted EAC-CPF record that corresponds to the above processed eac-cpf element. Applicable categories: people

#### Source Information
- **metadataSource** (object): Information about the record source
  - **value** (string): The name of the organisation or aggregating service who contributed this record to Trove (e.g. Libraries Australia)
  - **type** (string): The NUC symbol of the organisation who contributed this record to Trove (XML attribute)

### Description

A related resource from which the described resource is derived, for example the print book from which an image was scanned.

### External Documentation

Dublin Core records follow the structure described in the [Trove Data Dictionary](https://trove.nla.gov.au/partners/partner-services/adding-collections-trove/trove-data-dictionary).

## Dublin Core Record Schema

Container element for a Dublin Core record, following Dublin Core metadata standards.

### Core Elements

#### Title Information
- **title** (array of strings): A name given to the resource
- **alternative** (array of strings): The alternate name (alternative title) for the item

#### Creator and Contributor Information
- **creator** (array of creator objects): An entity primarily responsible for making the resource. Examples of a Creator include a person, an organisation, or a service
  - **name** (string): The name of the entity
  - **type** (string): The type of entity (e.g. author, illustrator) (XML attribute)

- **contributor** (array of contributor objects): An entity responsible for making contributions to the resource. Examples of a Contributor include a person, an organisation, or a service
  - **value** (string): The name of the entity
  - **type** (string): The type of contributor. Examples include: conferenceOrganiser, owner, photographer (XML attribute)

#### Content Type and Format
- **type** (array of type objects): The nature or genre of the resource
  - **value** (string): The nature or genre of the resource
  - **type** (string): Used to identify which Trove category the item belongs in (e.g. book, thesis, audio, video, chart, diagram, etc.) (XML attribute)

- **format** (array of strings): The physical format of the item
- **medium** (array of strings): The material or physical carrier of the resource
- **extent** (array of strings): The size or duration of the resource, e.g. the number of pages, size of a computer file or length of a sound recording

#### Publication Information
- **publisher** (array of strings): An entity responsible for making the resource available. Examples of a publisher include a person, an organisation, or a service. Typically, the name of a publisher should be used to indicate the entity

- **issued** (array of issued objects): Date of formal issuance (e.g., publication) of the resource. ISO-8601 format dates are used, ie yyyy-mm-dd
  - **value** (string): The date
  - **type** (string): The type of issuance (XML attribute)

- **date** (array of strings): A point or period of time associated with an event in the lifecycle of the resource. ISO-8601 format dates are used, ie yyyy-mm-dd

#### Content Description
- **description** (array of description objects): An account of the resource. Description may include an abstract, a byline or a free-text account of the resource. When the fulltext of an article is available, include it in a description field with the additional attribute type="fulltext". Trove will index this text (return the record for a search on a word in the fulltext) but only display the first 200 characters. Users will need to visit your site to view the fulltext. Trove will only index the first 30,000 characters of a description field
  - **value** (string): The description text
  - **type** (string): The type of description. Examples include: byline, fulltext, open_fulltext, scale (XML attribute)

- **abstract** (array of strings): A description, summary, abstract, or first few words of this work, if available
- **tableOfContents** (string): A list of subunits of the resource, e.g. Book chapter headings. This field is split on "-- " and displayed as a list

#### Subject and Coverage
- **subject** (array of strings): The topic of the content of the resource. Use of a controlled vocabulary such as the Australian Pictorial Thesaurus, LCSH or the Australian Extension to LCSH is encouraged but not mandatory

- **coverage** (array of strings): The spatial or temporal topic of the resource, the spatial applicability of the resource, or the jurisdiction under which the resource is relevant. Spatial topic and spatial applicability may be a named place or a location specified by its geographic coordinates. Temporal topic may be a named period, date, or date range. A jurisdiction may be a named administrative entity or a geographic place to which the resource applies. Use of a controlled vocabulary is encouraged but not mandatory

- **spatial** (array of spatial objects): Spatial characteristics of the resource, e.g. the location a photograph was taken; can also be used to include MARC Geographic Area Codes (GAC) to apply place facets

- **temporal** (array of strings): Temporal characteristics of the resource. This can be a year, date range or named period

#### Language Information
- **language** (array of language objects): A language of the resource. ISO-639-2 is preferred (3 letter language codes). Plain text can also be used. If your system keeps ISO-639-1 language codes, combines a language with a country code (ISO-3166), or uses another standard please let the Trove team know at setup time. A special mapping will be applied to your data. Austlang (Aboriginal and Torres Strait Islander languages) codes may be added to this field

### External Documentation

For Austlang codes, see: [Austlang Codes](https://trove.nla.gov.au/austlang-codes)

#### Audience and Rights
- **audience** (array of strings): A class of entity for whom the resource is intended or useful, e.g. Academic, Professional

- **rights** (array of rights objects): Information about rights held in and over the resource. Copyright should be asserted if known. Free text or a URI is acceptable e.g. link to a Creative Commons licence. For better display in Trove a standard licence should be included in the Licence Ref element instead. Rights statements starting with a Creative Commons or RightsStatements.org URI will populate the rights facet with appropriate data
  - **value** (string): The rights statement
  - **type** (string): The type of rights statement (e.g. metadata) (XML attribute)

- **licenseRef** (array of license objects): A URL pointing to a licence – ideally human and machine readable – that explains the terms for use or re-use of the content. RightsStatements.org URLs need to point to the Persistant link to the statement. URLs from Creative Commons and RightsStatements.org are used to populate the rights facets in Trove
  - **value** (string): The licence URL
  - **startDate** (string): the date at which these licence conditions begin to apply (XML attribute)

- **freeToRead** (array of freeToRead objects): Indicates an Open Access item. Including the free_to_read element indicates any user can freely access the full item online without authenticating or having to pay. No content is required in this tag, its presence indicates an item is Open Access and its absence indicates an item is not Open Access
  - **value** (string): The free to read statement, if present
  - **startDate** (string): the date on which an item becomes free to read, for example when an embargo is lifted. This date should be in ISO-8601 format, ie yyyy-mm-dd (XML attribute)
  - **endDate** (string): the date on which the item ceases to be free to read, for example when a free trial period ends. This date should be in ISO-8601 format, ie yyyy-mm-dd (XML attribute)

#### Relationships and References
- **relation** (array of strings): A related resource; a version of the work, or a significant part of the work. Recommended best practice is to reference the resource by means of a string or number conforming to a formal identification system, for example a permanent URL. ARC or NHMRC grant numbers can also be entered as a permanent URL

- **references** (array of strings): The URL of a related resource that is referenced, cited, or otherwise pointed to by the described resource

- **isPartOf** (array of isPartOf objects): A related resource in which the described resource is physically or logically included, e.g. a photograph or manuscript collection

- **bibliographicCitation** (array of citation objects): A bibliographic reference for the resource. Recommended practice is to include sufficient bibliographic detail to identify the resource as unambiguously as possible
  - **value** (string): The citation text
  - **type** (string): The type of citation. Examples of bibliographic citation types include: publication, volume, issue, pagination, edition, eisbn, isbn, issn, dateIssues, placeOfPub, sourceCreator, dateIssued, yearIssued (XML attribute)

#### Identifiers
- **identifier** (array of identifier objects): A local system identifier OR A URL to the resource, a version of the resource, or a related item. For long-term viability of the record a permanent URL such as a handle or purl should be used, rather than a system-specific URL. Include the linktype attribute will give Trove further data about the nature of the resource available, and should be included with all URLs

#### Digital Resources
- **viewcopy** (array of strings): The URL of a medium sized version of the image hosted on your server

## EAC-CPF Schema Information

### Overview

EAC-CPF (Encoded Archival Context - Corporate bodies, Persons, and Families) is an XML standard for encoding contextual information about the creators of archival materials.

### Properties in Trove API

- **eac-cpf** (object): The processed EAC-CPF record structure
  - Flexible structure compatible with OpenAPI specification
  - Additional properties allowed to accommodate EAC-CPF complexity

- **rawXml** (string): Available when "raweaccpf" include option is selected
  - Contains original, unprocessed EAC-CPF XML
  - Only applicable to people category records

### External Documentation

For complete EAC-CPF schema details, see: https://eac.staatsbibliothek-berlin.de/

### Usage

EAC-CPF records are primarily used for people and organisation records to provide rich contextual and biographical information beyond basic Dublin Core metadata.

## Usage Examples

### Basic Dublin Core Record Structure

```xml
<record>
  <header>
    <identifier>oai:example.org:123456</identifier>
    <datestamp>2023-01-15T10:30:00Z</datestamp>
    <setSpec>books</setSpec>
  </header>
  <metadata>
    <dc>
      <title>Example Book Title</title>
      <creator type="author">
        <name>Smith, John</name>
      </creator>
      <issued type="publication">
        <value>2023</value>
      </issued>
      <description type="abstract">
        <value>This is an abstract of the book.</value>
      </description>
      <subject>History</subject>
      <language type="iso639-2">eng</language>
      <identifier type="url" linktype="fulltext">
        <value>https://example.org/books/123456</value>
      </identifier>
    </dc>
  </metadata>
  <metadataSource type="ABC">
    <value>Example Library</value>
  </metadataSource>
</record>
```

### Rights and Licensing Example

```xml
<dc>
  <rights type="copyright">
    <value>© 2023 Example Publisher</value>
  </rights>
  <licenseRef startDate="2023-01-01">
    <value>https://creativecommons.org/licenses/by/4.0/</value>
  </licenseRef>
  <freeToRead startDate="2023-01-01">
    <value>Open Access</value>
  </freeToRead>
</dc>
```

## Related Documentation

- [Core Schemas](./trove-schemas-core.md) - Work, Article, People, and List schemas
- [Utility Schemas](./trove-schemas-utility.md) - Supporting utility schemas
- [Contributor Schemas](./trove-schemas-contributor.md) - Contributor and title schemas
- [External: Trove Data Dictionary](https://trove.nla.gov.au/partners/partner-services/adding-collections-trove/trove-data-dictionary)
- [External: EAC-CPF Schema](https://eac.staatsbibliothek-berlin.de/)
- [External: Austlang Codes](https://trove.nla.gov.au/austlang-codes)