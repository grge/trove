# Trove API v3 Core Schemas

This document describes the primary data structures returned by the Trove API: Work, Article, People, and List schemas.

## Work Schema

Represents a work (book, image, map, music, sound, video, archive, or journal article).

### Properties

#### Basic Identification
- **id** (string): The Trove work id (XML attribute)
  - Example: `123456789`
- **url** (string): A link to view this article in the Trove API (XML attribute)
- **troveUrl** (string): A link to view this article in the Trove web interface

#### Core Metadata
- **title** (string): The title or name of the work
  - Example: `"Tangled : the essential guide to Rapunzel's world / written by Barbara Bazaldua"`
- **contributor** (array of strings): The main creator of this work. Some works have multiple creators listed, others have only one even if multiple creators exist
  - Example: `['Bazaldua, Barbara']`
- **issued** (string): The year/s this work was issued, created or published. May also include month and day. May be a range
  - Example: `2011`, `2001-2011`
- **type** (array of formats): The format of this work. There may be more than one type element
- **abstract** (string): A description, summary, abstract, or first few words of this work, if available
  - Example: `"Damaged rainforest trees in a backyard in Babinda."`

#### Content Information
- **subject** (array of strings): Subjects describe what a work is about
  - Example: `["Global warming - Health aspects"]`
- **audience** (array of strings): The target audience of the work
- **rights** (array of strings): The terms of use of the work
- **format** (array of strings): The physical format of the item
- **extent** (string): The extent of the work
- **tableOfContents** (string): A table of contents for this work, if available. Where possible, each item is listed on a separate line within the same tableOfContents element

#### Geographic and Language
- **spatial** (array of spatial objects): The spatial topic of the item. e.g. the location a photograph was taken
- **placeOfPublication** (array of strings): The place of publication of this work
  - Example: `['Australia/New South Wales']`
- **language** (array of language objects): The language/s this work is available in. More than one language element may be present

#### Relationships and References
- **isPartOf** (array of isPartOf objects): For articles, the journal or periodical this article belongs to (if known). The url may include the API access point to get more information about this periodical e.g. /work/13110632
- **identifier** (array of identifier objects): Additional identifiers for the work
- **snippet** (array of strings): A small amount of text containing one or more of the search terms. The matching term/s are enclosed in a `<B>` element
  - Example: `['...blue-green plumage holding the <B>tangled</B> loops. A very useful dress it composed of a plaided material...']`

#### Enrichment Data
- **wikipedia** (string): Links to any known associated wikipedia articles. Includes markup
  - Example: `'Read associated articles: <a href="http://en.wikipedia.org/wiki/Golomb_coding"> Golomb coding</a>, <a href="http://en.wikipedia.org/wiki/Incremental_encoding"> Incremental encoding</a>'`
- **hasCorrections** (enum): Does the work have any text corrections?
  - Values: `Y`, `N`
- **lastUpdated** (string): The date of the most recent text correction (UTC timezone)
  - Example: `2011-12-09T09:43:00Z`

#### Quantitative Data
- **holdingsCount** (integer): The number of organisations (libraries, archives, etc) who have a copy of this work
- **versionCount** (integer): A work is made up of one or more versions. This is the number of versions that are grouped together to make up this work
- **listCount** (integer): The number of public lists this work is in

#### User-Generated Content
- **tagCount** (array of itemCount objects): Tags can be placed on the work as a whole, or on a particular version that is part of the work. This element shows the number of public tags on this work or any of its versions
- **commentCount** (array of itemCount objects): Comments can be placed on the work as a whole, or on a particular version that is part of the work. This element shows the number of public comments on this work or any of its versions
- **tag** (array of tag objects): A public tag added to the work. There may be more than one tag element
- **comment** (array of comment objects): A public comment added to the work. There may be more than one comment element
- **list** (array of list objects): The name of a public, user-created list this work belongs to. There may be more than one list element

#### Cultural Sensitivity
- **culturallySensitive** (string): An indicator of cultural sensitivity, particularly in respect to First Australians
- **firstAustralians** (string): Whether the item pertains to First Australians

#### Structure
- **holding** (array of holding objects): A container element for information about a copy of this work held by a particular organisation (library, archive, etc)
- **version** (array of version objects): A container element for a version/edition that is part of this work. Versions usually contain one record but can sometimes contain several
- **relevance** (relevance object): Relevance scoring information

## Article Schema

Represents a newspaper or gazette article.

### Properties

#### Basic Identification
- **id** (string): Trove newspaper article id (XML attribute)
  - Example: `18341291`
- **url** (string): Trove newspaper url (XML attribute)
  - Example: `18341291`
- **identifier** (string): The article identifier. This URL leads to the article view on the Trove web interface
  - Example: `https://nla.gov.au/nla.news-article18341291`
- **troveUrl** (string): A link to view this article in the Trove web interface. If this record was retrieved in response to a search, the search terms will be included in the URL which allows them to be highlighted when viewing in the article. This is not available for articles with a status of "coming soon"
  - Example: `https://trove.nla.gov.au/ndp/del/article/18342701?searchTerm=tangled`
- **trovePageUrl** (string): A link to view the first page of this article, in the Trove web interface. This is not available for articles with a status of "coming soon"
  - Example: `https://trove.nla.gov.au/ndp/del/page/2243685`

#### Content Information
- **heading** (string): The article heading
  - Example: `"Agriculture around Kelvin Grove and Kedron Brook. [BY OUR AGRICULTURAL REPORTER.]"`
- **category** (enum): The type of article. Displayed on the Trove web interface as "Category"
  - Values: `Article`, `Advertising`, `'Detailed lists, results, guides'`, `Family Notices`, `Literature`, `Government Gazette Notices`, `Government Gazette Tenders and Contracts`, `Government Gazette Proclamations And Legislation`, `Government Gazette Private Notices`, `Government Gazette Budgetary Papers`, `Government Gazette Index And Contents`, `Government Gazette Appointments And Employment`, `Government Gazette Freedom Of Information`
- **articleText** (string): The full text of the article, including all corrections. Article paragraphs are enclosed in a `<p>` element. Lines are enclosed by `<span>`. Article text is not available for some articles, such as those from the Australian Women's Weekly, and articles with a status of "coming soon". For these articles, there will be no articleText element present
  - Example: `'<p><span>  SHIPPING  INTELLIGENCE.</span></p> <p><span>  Lying  in  Owen's  Anchorage.-II.M.S.  Pelorus,</span><span>  and  Champion»</span></p>'`

#### Publication Information
- **title** (articleTitle object): The name of the newspaper or periodical this article is found in
- **edition** (string): If this article appeared in a special newspaper/periodical edition, the name of that edition is included here. In the Trove web interface, this is shown on the page view
  - Example: `'2, SPECIAL EDITION TO THE QUEANBEYAN AGE'`
- **date** (string): When the issue this article belongs to was published. YYYY-MM-DD
  - Example: `1876-05-27`
- **page** (string): Determine the sequence of delivery of the pages in an issue
  - Example: `1`
- **pageSequence** (string): In addition to the page sequence number, indicates if the article is part of a supplement/section (displayed in the Trove web interface)
  - Example: `1 S`
- **pageLabel** (string): Sometimes used to indicate what is printed on the page, or perhaps the page number within a section/supplement. Not displayed in the Trove web interface. Sometimes numeric and sometimes not
  - Example: `Front cover`

#### Article Characteristics
- **supplement** (string): The newspaper/periodical section this article appeared in. In the Trove web interface, this is shown on the page view. A supplement is part of an issue
  - Example: `Something to do`
- **section** (string): The newspaper/periodical section this article appeared in. In the Trove web interface, this is shown on the page view. A section is part of an issue
  - Example: `1, Special Home Feature`
- **illustrated** (enum): Flags whether the article is illustrated or not
  - Values: `Y`, `N`
- **wordCount** (string): The number of words in the full text of the article
  - Example: `1514`

#### Status and Corrections
- **status** (enum): Included if the article is not currently available. Not included for normal articles. New articles are included before they are fully approved. These articles have a status of "coming soon". They don't include the full text or a link to view the article in Trove. They may be deleted from Trove. If you want to harvest newspaper articles into your own system, you may prefer to only harvest those added more than a month ago, as most articles which are "coming soon" will be approved within this timeframe. If you do harvest any articles which are "coming soon" you will need to check back later to find out whether they still exist/have been approved/get the Trove link and full text
  - Values: `coming soon`, `withdrawn`, `currently unavailable`
- **correctionCount** (string): The number of corrections made to the article. Each correction may involve many lines
  - Example: `1`
- **lastCorrection** (object): Further information about the most recent correction to this article. The correction itself is not included
  - Properties:
    - **by** (string): The username of the person who made the most recent correction to this article, or "anonymous"
    - **lastupdated** (string): When the most recent correction was made to this article (UTC timezone)
      - Example: `2011-12-06T18:05:17Z`

#### User-Generated Content
- **tagCount** (string): The number of public tags added to this article by Trove users
- **commentCount** (string): The number of public comments added to this article by Trove users
- **listCount** (string): The number of public Trove user created lists this article has been added to
- **tag** (array of tag objects): A public tag added to the article. There may be more than one tag element
- **comment** (array of comment objects): A public comment added to the article. There may be more than one comment element
- **list** (array of list objects): The name of a public, user created list this article belongs to. There may be more than one list element

#### Resources
- **pdf** (array of strings): A link leading to the pdf for the page this article appears on. There may be more than one pdf element if the article appears over multiple pages. PDFs are not available for some articles, such as the Australian Women's Weekly, and articles with a status of "coming soon"
  - Example: `https://trove.nla.gov.au/ndp/imageservice/nla.news-page2243325/print`

#### Search and Relevance
- **relevance** (relevance object): Relevance scoring information
- **snippet** (string): A small amount of article text containing one or more of the search terms. The matching term/s are enclosed in a `<B>` element
  - Example: `'...blue-green plumage holding the <B>tangled</B> loops. A very useful dress it composed of a plaided material...'`

#### System Information
- **warning** (string): A message to indicate if a newspaper article is not present in the newspaper database, but exists in the Trove index

## People Schema

Represents a person or organisation record.

### Properties

#### Basic Identification
- **id** (string): The unique identifier for this person/organisation (XML attribute)
- **url** (string): A link to view this article in the Trove API (XML attribute)
- **troveUrl** (string): A link to view this article in the Trove web interface
- **type** (enum): Type of entity
  - Values: `person`, `corporatebody`, `family`

#### Names
- **primaryName** (string): The person/organisation's primary name with, life dates (where applicable)
- **primaryDisplayName** (string): The person/organisation's primary name without life dates
- **alternateName** (array of strings): Other name(s) that the person/organisation's is/are known by, with life dates (where applicable)
- **alternateDisplayName** (array of strings): Other name(s) that the person/organisation's is/are known by, without life dates

#### Disambiguation
- **disambiguation** (boolean): Disambiguation information for a person or organisation, to help distinguish people or organisations with the same or similar name
- **disambiguationName** (array of objects): Disambiguation names and relation (e.g. 'is not')
  - Properties:
    - **name** (string): The related disambiguation name
    - **url** (string): A link to the related person/organisation record
    - **reltype** (string): The type of relationship between the two person/organisation records (e.g. may refer to, is not, etc)
    - **reldesc** (string): More information about the relationship between the records

#### Person-Specific Information
- **title** (array of strings): Title associated with the person or organization including post-nominals and titles of status to show the awards and honours a person has (not available for organisations)
- **occupation** (array of strings): One or more occupations describing the person (not available for organisations)

#### Sources and Contributors
- **contributor** (array of objects): The name of the contributor of this person or organisation record to Trove
  - Properties:
    - **id** (string): The Trove contributor id (XML attribute)
    - **nuc** (string): The Trove contributor Nuc. Nuc (id) of the contributor of the person or organisation record to Trove (XML attribute)
    - **name** (string): The Trove contributor name. Name of the contributor of the person or organisation record to Trove
    - **url** (string): The Trove contributor Url. A link to access the person or organisation record through the contributing organisation's external website

#### Biographical Information
- **biography** (array of objects): A written account of the persons life or brief history of the organisation. Some Trove people and organisation records include multiple biographies contributed by various Trove partners/contributors
  - Properties:
    - **contributor** (string): The Trove contributor name. Name of the contributor of the person or organisation biography to Trove
    - **contributorId** (string): The Trove contributorId. Id of the contributor of the person or organisation biography to Trove (XML attribute)
    - **id** (string): The URL id for the biography. URL identifier for the person or organization biography on the contributors website
    - **biography** (string): Container element for the biography record for each person or organization biography contributed to Trove

#### Metadata Records
- **record** (array of record objects): Container element for a Dublin Core or EAC-CPF record. These records are contributed to Trove from various sources and have often been converted by Trove or the original contributor to Dublin Core from other formats
- **identifier** (array of identifier objects): Additional identifiers for the person/organisation

#### User-Generated Content
- **tagCount** (integer): The number of public tags this person/organisation is in
- **commentCount** (integer): The number of public comments this person/organisation has
- **listCount** (integer): The number of public lists this person/organisation is in
- **tag** (array of tag objects): A public tag added to the person/organisation
- **comment** (array of comment objects): A public comment added to the person/organisation
- **list** (array of list objects): The name of a public list this person/organisation belongs to

#### Cultural Sensitivity
- **culturallySensitive** (string): An indicator of cultural sensitivity, particularly in respect to First Australians
- **firstAustralians** (string): Whether the item pertains to First Australians

#### Search Information
- **relevance** (relevance object): Relevance scoring information

## List Schema

Represents a user-created list.

### Properties

#### Basic Identification
- **id** (string): The Trove list id (XML attribute)
  - Example: `21922`
- **url** (string): A URL to retrieve more information about this list using the Trove API (XML attribute)
  - Example: `https://api.trove.nla.gov.au/v3/list/21922`
- **troveUrl** (string): A link to view this list in the Trove web interface
  - Example: `https://trove.nla.gov.au/list?id=1234`

#### Content Information
- **title** (string): The name of the list. List names are not unique. Display them in conjunction with the list creator's username
  - Example: `Adelaide Festival of the Arts (1960 – )`
- **description** (string): Brief record (truncated to 120 characters); Full record (full value)
  - Example: `<p><em>Furioso</em> premiered on 8 July 1993 at the Playhouse, Adelaide Festival Centre. It was choreographed by Meryl Tankard for Meryl Tankard Australian Dance Theatre. The original cast was Prue Lang, Mia Mason, Rachel Roberts, Tuula Roppola, Michelle Ryan, Vincent Crowley, Grayson Millwood, Shaun Parker, Gavin Webber and Steev Zane. It was danced to music by Arvo Part, Elliot Sharp and Henryk Gorecki, and had designs by Regis Lansac.</p>`

#### Creator Information
- **creator** (string): The username of the person who created the list. Anonymous lists are not allowed
- **by** (string): The username of the person who created the list (XML attribute)
  - Examples: 
    - `"public:bobbyfamilytree"`
    - `"dance"` (NLA staff accounts do not include the 'public' prefix)
    - `"anonymous"` (no user account identified)

#### List Properties
- **listItemCount** (integer): The number of items in the list
- **identifier** (identifier object): A link to a thumbnail image for the list

#### Timestamps
- **lastupdated** (string): When the list was most recently added/edited (UTC timezone) (XML attribute)
  - Example: `2011-12-09T09:43:00Z`
- **date** (object): Date information
  - Properties:
    - **created** (string): When the record was created (UTC timezone) (XML attribute)
      - Example: `2009-12-31T13:00:00Z`
    - **lastupdated** (string): When the record was last changed (UTC timezone) (XML attribute)
      - Example: `2010-09-06T05:07:41Z`

#### User-Generated Content
- **tagCount** (itemCount object): The number of tags on this list
- **commentCount** (itemCount object): The number of comments on this list
- **tag** (array of tag objects): A public tag added to the work. There may be more than one tag element
- **comment** (array of comment objects): A public comment on this list. There may be more than one comment element

#### List Contents
- **listItem** (array of listItem objects): An item that belongs to the list. This may be a work, a digitised newspaper article, a person/organisation, or a link to an external website. There may be more than one listItem element. A list item will contain one of the following elements: work, article, externalWebsite, people. It may also contain a note

#### Search Information
- **relevance** (relevance object): Relevance scoring information
- **snippet** (array of strings): A small amount of article text containing one or more of the search terms. The matching term/s are enclosed in a `<B>` element
  - Example: `['...blue-green plumage holding the <B>tangled</B> loops. A very useful dress it composed of a plaided material...']`

#### Cultural Sensitivity
- **culturallySensitive** (string): An indicator of cultural sensitivity, particularly in respect to First Australians
- **firstAustralians** (string): Whether the item pertains to First Australians

## Related Documentation

- [Utility Schemas](./trove-schemas-utility.md) - Supporting schemas used in these core schemas
- [Metadata Schemas](./trove-schemas-metadata.md) - Dublin Core and record structures
- [Search Schemas](./trove-schemas-search.md) - Search result and facet structures