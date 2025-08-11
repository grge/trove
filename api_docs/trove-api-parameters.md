# Trove API v3 Parameters Reference

## Query Parameters

### Core Search Parameters

#### q (Query)
- **Name**: `q`
- **Type**: string
- **Required**: false
- **Location**: query
- **Description**: The search query. Your query can use indexes which let you do things like search for words in the title, or limit your search to items tagged recently. Supported indexes are described here: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#list-of-supported-indexes.

#### category
- **Name**: `category`
- **Type**: array of categories
- **Required**: true
- **Location**: query
- **Description**: Allows searching in a particular category. Available categories are: "All" (all), "Books & Libraries" (book), "Diaries, Letters & Archives" (diary), "Images, Maps & Artefacts" (image), "Lists" (list), "Magazines & Newsletters" (magazine), "Music, Audio & Video" (music), "Newspapers & Gazettes" (newspaper), "People & Organisations" (people), and "Research & Reports" (research). Use the value in brackets as the category identifier. Multiple categories can be searched by separating them with a comma. If no category is specified, an error occurs. To get a faster response, search only the categories you need.
- **Examples**:
  - "All categories": `[all]`
  - "Only the 'Books & Libraries' category": `[book]`
  - "'Books & Libraries' and 'Images, Maps & Artefacts'": `[book,image]`

### Pagination Parameters

#### s (Start)
- **Name**: `s`
- **Type**: string
- **Required**: false
- **Location**: query
- **Default**: `*`
- **Description**: The default value to start from i.e. s=*. You will receive a CursorMark value called 'nextStart' in your results if there are more pages of results. Use this 'nextStart' value with the 's' parameter to get to the next page of results and page through a long list of results i.e. s=AoIIPyteOSlzdTczOTQ2MjQ=. Please note: the 's' parameter must be URL encoded.

#### n (Number of Results)
- **Name**: `n`
- **Type**: integer (int32)
- **Required**: false
- **Location**: query
- **Default**: 20
- **Description**: The number of results to return per category. Maximum is 100.

### Result Control Parameters

#### sortby
- **Name**: `sortby`
- **Type**: string
- **Required**: false
- **Location**: query
- **Default**: `relevance`
- **Enum**: [`datedesc`, `dateasc`, `relevance`]
- **Description**: The sort order for the results. Both date of publication and relevance are supported.

#### bulkHarvest
- **Name**: `bulkHarvest`
- **Type**: boolean
- **Required**: false
- **Location**: query
- **Default**: false
- **Description**: Include this parameter if you intend to harvest a set of records for further processing in your own system. The results will be sorted by identifier, rather than relevance. This will prevent your results set order changing while you harvest, and ensure you obtain every record once. If the value is 'true', article/work identifier is used to sort. If the value is 'false' relevance score is used to sort.

#### reclevel
- **Name**: `reclevel`
- **Type**: string
- **Required**: false
- **Location**: query
- **Default**: `brief`
- **Enum**: [`full`, `brief`]
- **Description**: Indicates whether to return a full or brief metadata record.

#### encoding
- **Name**: `encoding`
- **Type**: string
- **Required**: false
- **Location**: query
- **Default**: `xml`
- **Enum**: [`json`, `xml`]
- **Description**: Get the response in xml (default) or json. Alternately, specify a HTTP accept content type of application/xml or application/json.

### Faceting Parameters

#### facet
- **Name**: `facet`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: Facets are categories that describe the results for your search. For example, if you ask for the decade facet, the response will include the list of decades your results span across, and how many results are found in each decade. You can separate multiple values with commas. Some facets only apply to certain categories. A maximum number of values will be returned, which varies per facet.
- **External Docs**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#facetValues

## Limit Parameters (Search Filters)

### Format and Content Type

#### l-format
- **Name**: `l-format`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: The format of the resource. For example, is it a book or a piece of sheet music? Applicable categories: book, image, magazine, newspaper, music, diary.

#### l-artType
- **Name**: `l-artType`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Enum**: [`newspaper`, `gazette`, `images and artefacts`, `maps`, `person`, `organisation`]
- **Description**: The type limit to narrow a search in newspaper category to either "Newspaper" or "Gazette", in the people category to "Person" or "Organisation", and in image category to either "Images and artefacts" or "Maps". Applicable categories: newspaper, image, people.

### Date and Time Filters

#### l-decade
- **Name**: `l-decade`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: Publication decade in the format YYY: e.g 199 represents 1990 – 1999. Applicable categories: book, image, magazine, music, diary, newspaper, list.

#### l-year
- **Name**: `l-year`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: Publication year in the format YYYY. For newspapers, only available if the decade facet is also applied. Applicable categories: book, image, magazine, music, diary, newspaper, list.

#### l-month
- **Name**: `l-month`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: Publication month. Only available if the year facet is also applied. Applicable categories: newspaper.

### Language and Cultural Parameters

#### l-language
- **Name**: `l-language`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: The language(s) the work is available in. Applicable categories: book, image, magazine, music, diary.

#### l-austlanguage
- **Name**: `l-austlanguage`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: Aboriginal and Torres Strait Islander Language. Applicable categories: book, image, magazine, music, diary, research.

#### l-firstAustralians
- **Name**: `l-firstAustralians`
- **Type**: string
- **Required**: false
- **Location**: query
- **Enum**: [`y`]
- **Description**: Whether the item pertains to First Australians. Applicable categories: book, diary, image, magazine, music, people.

#### l-culturalSensitivity
- **Name**: `l-culturalSensitivity`
- **Type**: string
- **Required**: false
- **Location**: query
- **Enum**: [`y`]
- **Description**: An indicator of cultural sensitivity, particularly in respect to First Australians. Applicable categories: book, diary, image, magazine, music, people.

### Geographic Parameters

#### l-geocoverage
- **Name**: `l-geocoverage`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: Place is the geographic region the item is about (geographic coverage) and includes Australian states and territories and a number of Australia's closest International neighbours. Applicable categories: magazine, image, research, book, diary, music.

#### l-place
- **Name**: `l-place`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: The place of birth (for people) or establishment (for organisations). Applicable categories: people.

#### l-state
- **Name**: `l-state`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: State of publication for newspaper or gazette article. Applicable categories: newspaper.

### Contributor and Collection Parameters

#### l-contribcollection
- **Name**: `l-contribcollection`
- **Type**: string
- **Required**: false
- **Location**: query
- **Description**: The collection the work is available in. Applicable categories: book, image, magazine, music, diary, research.

#### l-partnerNuc
- **Name**: `l-partnerNuc`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: The NUC of the contributing partner. Applicable categories: book, image, magazine, music, diary, research.

### Availability Parameters

#### l-availability
- **Name**: `l-availability`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Enum**: [`y`, `y/f`, `y/r`, `y/s`, `y/u`]
- **Description**: Whether the item is online or not: y – online; y/f – freely accessible online; y/r – payment, subscription or membership required; y/s – subscription required; y/u – possibly online. Replace "/" with %2F (URL encoding). Applicable categories: book, image, magazine, music, diary.

#### l-australian
- **Name**: `l-australian`
- **Type**: string
- **Required**: false
- **Location**: query
- **Enum**: [`y`]
- **Description**: Works identified as published primarily in Australia, or written by Australians. Applicable categories: book, image, magazine, music, diary, people.

### People-Specific Parameters

#### l-occupation
- **Name**: `l-occupation`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: Applicable categories: diary, people.

#### l-birth
- **Name**: `l-birth`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: Year of Birth/Establishment in the format YYYY. Applicable categories: people.

#### l-death
- **Name**: `l-death`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: Year of Death/Dissolution in the format YYYY. Applicable categories: people.

### Content Specific Parameters

#### l-zoom
- **Name**: `l-zoom`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: Map scale. Applicable categories: image.

#### l-audience
- **Name**: `l-audience`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Enum**: [`Trade`, `General`, `Academic`, `Professional`, `"Children's"`, `"Children's - Upper elementary"`, `"Children's - Lower elementary"`]
- **Description**: Only applies to articles from Gale. Applicable categories: book, music, research and image.

#### l-title
- **Name**: `l-title`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: The newspaper or gazette title id; or the magazine, newsletter, research or report title. Applicable categories: newspaper, magazine, research.

#### l-category
- **Name**: `l-category`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: Newspaper or gazette article category. Examples include: "Article", "Advertising","Detailed Lists, Results, Guides", "Family notices", "Literature", "Government Gazette Notices", "Government Gazette Tenders and Contracts", "Government Gazette Proclamations And Legislation", "Government Gazette Private Notices", "Government Gazette Budgetary Papers", "Government Gazette Index And Contents", "Government Gazette Appointments And Employment", "Government Gazette Freedom Of Information". Applicable categories: magazine, newspaper.

#### l-illustrated
- **Name**: `l-illustrated`
- **Type**: boolean
- **Required**: false
- **Location**: query
- **Description**: Is an article illustrated? Applicable categories: magazine, newspaper, research.

#### l-illustrationType
- **Name**: `l-illustrationType`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: Type of illustration for an article. Applicable categories: magazine, newspaper, research.

#### l-wordCount
- **Name**: `l-wordCount`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Enum**: [`<100 Words`, `100 - 1000 Words`, `1000+ Words`]
- **Description**: The article word count. Applicable categories: newspaper, magazine, research. E.g. one of "<100 Words", "100 - 1000 Words", "1000+ Words".

### Additional Limits Parameter

#### otherLimits
- **Name**: `otherLimits`
- **Type**: object (additionalProperties: true)
- **Required**: false
- **Location**: query
- **Style**: simple
- **Explode**: true
- **Description**: Limit the search results using one or more limits/facets. e.g. l-availability=Y&l-year=1881. This field allows additional limits to those defined as individual parameters in this API specification (e.g. for use with faceting).

## Include Parameters (Different for Each Endpoint)

### Search Endpoint Include
- **Name**: `include`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Enum**: [`all`, `comments`, `holdings`, `links`, `listitems`, `lists`, `subscribinglibs`, `tags`, `workversions`]
- **Description**: Include optional pieces of information in the records returned.

### Work Endpoint Include
- **Name**: `include`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Enum**: [`all`, `comments`, `holdings`, `links`, `lists`, `subscribinglibs`, `tags`, `workversions`]
- **Description**: Include optional pieces of information in the records returned.

### People Endpoint Include
- **Name**: `include`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Enum**: [`all`, `comments`, `lists`, `raweaccpf`, `tags`]
- **Description**: Include optional pieces of information in the records returned.

### List Endpoint Include
- **Name**: `include`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Enum**: [`all`, `comments`, `listitems`, `tags`]
- **Description**: Include optional pieces of information in the records returned.

### Newspaper/Gazette Article Include
- **Name**: `include`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Enum**: [`all`, `articletext`, `comments`, `lists`, `tags`]
- **Description**: Include optional pieces of information in the records returned.

## Path Parameters

### workId
- **Name**: `workId`
- **Type**: string
- **Required**: true
- **Location**: path
- **Description**: The ID of the work to retrieve

### id (Generic)
- **Name**: `id`
- **Type**: string or integer (varies by endpoint)
- **Required**: true
- **Location**: path
- **Description**: The ID of the resource to retrieve (Person, Organisation, List, Article, etc.)

## Other Endpoint-Specific Parameters

### Magazine/Newspaper Title Parameters

#### place
- **Name**: `place`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: Place is the geographic region the item is about (geographic coverage) and includes Australian states and territories and a number of Australia's closest International neighbours.

#### offset
- **Name**: `offset`
- **Type**: integer
- **Required**: false
- **Location**: query
- **Default**: 0
- **Description**: The index to start retrieving results from. The first record is at index 0.

#### limit
- **Name**: `limit`
- **Type**: integer
- **Required**: false
- **Location**: query
- **Default**: 20
- **Description**: The number of records to retrieve. The default is 20, the maximum is 100.

#### range
- **Name**: `range`
- **Type**: array of strings
- **Required**: false
- **Location**: query
- **Description**: If include=years has also been used, then for the given date range, also return a list of dates an issue of this title was published. The range must be specified in the format YYYYMMDD-YYYYMMDD (url-encoded).

#### state (Newspaper/Gazette Titles)
- **Name**: `state`
- **Type**: string
- **Required**: false
- **Location**: query
- **Default**: `all`
- **Enum**: [`nsw`, `act`, `qld`, `tas`, `sa`, `nt`, `wa`, `vic`, `national`, `international`] (newspaper) or [`nsw`, `national`, `international`] (gazette)
- **Description**: Limit the title search to the specified state(s)

## Related Documentation

- [Search Parameters Guide](./trove-search-parameters.md) - Detailed usage examples and best practices
- [Categories & Formats](./trove-api-categories.md) - Complete category and format enumerations
- [Faceting Guide](./trove-faceting.md) - Faceting system details