# Trove API v3 Endpoints Reference

## Complete Endpoint List

### Search Endpoint
- **Path**: `/v3/result`
- **Method**: GET
- **Operation ID**: `search`
- **Tag**: Search
- **Description**: Search Trove newspaper, gazette and magazine articles, people, lists and works. Works are made up of "versions". They can be books, images, maps, music, sound, video, archives, or journal articles. Archived websites have not been included at this point.

A simple search request looks basically like this: `https://api.trove.nla.gov.au/v3/result?key=<**INSERT KEY**>&category=<**CATEGORY NAME**>&q=<**YOUR SEARCH TERMS**>`

By default, you will only get a brief metadata record that does NOT include information like tags, comments, full text, library holdings, links etc. If you want this information, you will need to use the "reclevel" and "include" parameters which are described below. If you don't want this information for every record in your results, you can retrieve metadata for individual records instead.

As a general principle, it is better to only ask the API for the information you need – this will give you and all the other Trove users a more responsive service. Also note that the various limit fields are often case-sensitive: the best way to determine the correct value is to first perform a facet search for that field.

Note: the current best method for finding records with certain licences is a search with the licence URL, e.g. q=https://creativecommons.org

- **External Docs**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#api-search

### Work Endpoints

#### Get Work
- **Path**: `/v3/work/{workId}`
- **Method**: GET
- **Operation ID**: `getWork`
- **Tag**: Work
- **Description**: Retrieves a specific Work record
- **External Docs**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#api-get-metadata-records

### Magazine Endpoints

#### Find Magazine Titles
- **Path**: `/v3/magazine/titles`
- **Method**: GET
- **Operation ID**: `findMagazineTitles`
- **Tag**: Work
- **Description**: Search for Magazine and Newsletter titles
- **External Docs**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#get-a-list-of-magazines-and-newsletters-titles

#### Get Magazine Title
- **Path**: `/v3/magazine/title/{id}`
- **Method**: GET
- **Operation ID**: `getMagazineTitle`
- **Tag**: Work
- **Description**: Retrieves a specific magazine or newsletter title
- **External Docs**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#get-information-about-one-magazine-or-newsletter-title

### People Endpoints

#### Get Person or Organisation
- **Path**: `/v3/people/{id}`
- **Method**: GET
- **Operation ID**: `getPersonOrOrg`
- **Tag**: People
- **Description**: Retrieves a specific Person or Organisation record
- **External Docs**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#api-people-and-organisation-record-structure

### List Endpoints

#### Get List
- **Path**: `/v3/list/{id}`
- **Method**: GET
- **Operation ID**: `getList`
- **Tag**: List
- **Description**: Retrieves a specific List
- **External Docs**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#api-list-record-structure

### Newspaper Endpoints

#### Get Newspaper Article
- **Path**: `/v3/newspaper/{id}`
- **Method**: GET
- **Operation ID**: `getNewspaperArticle`
- **Tag**: Newspaper
- **Description**: Retrieves a specific Newspaper article
- **External Docs**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#api-newspaper-and-gazette-article-record-structure

#### Find Newspaper Titles
- **Path**: `/v3/newspaper/titles`
- **Method**: GET
- **Operation ID**: `findNewspaperTitles`
- **Tag**: Newspaper
- **Description**: Search for Newspaper titles
- **External Docs**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#listTitles

#### Get Newspaper Title
- **Path**: `/v3/newspaper/title/{id}`
- **Method**: GET
- **Operation ID**: `getNewspaperTitle`
- **Tag**: Newspaper
- **Description**: Retrieves a specific newspaper title
- **External Docs**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#get-information-about-one-newspaper-or-gazette-title

### Gazette Endpoints

#### Get Gazette Article
- **Path**: `/v3/gazette/{id}`
- **Method**: GET
- **Operation ID**: `getGazetteArticle`
- **Tag**: Newspaper
- **Description**: Retrieves a specific Gazette article
- **External Docs**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#api-newspaper-and-gazette-article-record-structure

#### Find Gazette Titles
- **Path**: `/v3/gazette/titles`
- **Method**: GET
- **Operation ID**: `findGazetteTitles`
- **Tag**: Newspaper
- **Description**: Search for Gazette titles
- **External Docs**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#listTitles

#### Get Gazette Title
- **Path**: `/v3/gazette/title/{id}`
- **Method**: GET
- **Operation ID**: `getGazetteTitle`
- **Tag**: Newspaper
- **Description**: Retrieves a specific gazette title
- **External Docs**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#get-information-about-one-newspaper-or-gazette-title

### Contributor Endpoints

#### Find Contributors
- **Path**: `/v3/contributor`
- **Method**: GET
- **Operation ID**: `findContributors`
- **Tag**: Contributor
- **Description**: Search for Contributors
- **External Docs**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#contrib

#### Get Contributor
- **Path**: `/v3/contributor/{id}`
- **Method**: GET
- **Operation ID**: `getContributor`
- **Tag**: Contributor
- **Description**: Retrieves a specific Contributor
- **External Docs**: https://trove.nla.gov.au/about/create-something/using-api/v3/api-technical-guide#get-information-about-one-contributor

## Tags Summary

- **Search**: Search operations
- **Work**: Work-related operations (including magazines)
- **People**: People and organisation operations
- **List**: List operations
- **Newspaper**: Newspaper and gazette operations
- **Contributor**: Contributor operations

## Related Documentation

- [Parameters Reference](./trove-api-parameters.md) - Detailed parameter information for each endpoint
- [Search Parameters Guide](./trove-search-parameters.md) - Comprehensive search parameter guide
- [Response Formats](./trove-response-formats.md) - Response format examples for each endpoint