# Trove API v3 Categories and Formats

## Supported Categories

The following categories are supported for searching the Trove API:

| Category Code | Category Name | Description |
|---------------|---------------|-------------|
| `all` | Everything except the Web | All available categories |
| `book` | Books & Libraries | Books and library materials |
| `diary` | Diaries, Letters & Archives | Personal papers and archival materials |
| `image` | Images, Maps & Artefacts | Visual materials and objects |
| `list` | Lists | User-created lists |
| `magazine` | Magazines & Newsletters | Periodical publications |
| `music` | Music, Audio & Video | Audio and video materials |
| `newspaper` | Newspapers & Gazettes | Newspaper and gazette articles |
| `people` | People & Organisations | Person and organisation records |
| `research` | Research & Reports | Research publications and reports |

### Category Usage

- Use the category code (value in brackets) as the category identifier
- Multiple categories can be searched by separating them with a comma
- If no category is specified, an error occurs
- To get a faster response, search only the categories you need

### Category Examples

- All categories: `category=all`
- Only Books & Libraries: `category=book`
- Books & Libraries and Images: `category=book,image`

## Supported Formats

The API supports the following format types:

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

### Periodical Formats
- `Periodical`
- `Periodical/Journal, magazine, other`
- `Periodical/Newspaper`

### Music and Audio Formats
- `Printed music`
- `Sheet music`
- `Sound`
- `Sound/Interview, lecture, talk`
- `Sound/Other sound`
- `Sound/Recorded music`

### Video Formats
- `Video`
- `Video/Captioned`

### Conference Materials
- `Conference Proceedings`

## Art Type Enumeration

Used with the `l-artType` parameter:

| Value | Description | Applicable Categories |
|-------|-------------|----------------------|
| `newspaper` | Newspaper articles | newspaper |
| `gazette` | Gazette articles | newspaper |
| `images and artefacts` | Images and artefacts | image |
| `maps` | Maps | image |
| `person` | Person records | people |
| `organisation` | Organisation records | people |

## Audience Enumeration

Used with the `l-audience` parameter (applies to articles from Gale):

- `Trade`
- `General`
- `Academic`
- `Professional`
- `"Children's"`
- `"Children's - Upper elementary"`
- `"Children's - Lower elementary"`

## Availability Types

Used with the `l-availability` parameter:

| Code | Description |
|------|-------------|
| `y` | Online |
| `y/f` | Freely accessible online |
| `y/r` | Payment, subscription or membership required |
| `y/s` | Subscription required |
| `y/u` | Possibly online |

**Note**: Replace "/" with %2F (URL encoding) when using these values.

## Word Count Categories

Used with the `l-wordCount` parameter:

- `<100 Words`
- `100 - 1000 Words`
- `1000+ Words`

## Article Categories

Examples of newspaper or gazette article categories (used with `l-category` parameter):

- `Article`
- `Advertising`
- `Detailed Lists, Results, Guides`
- `Family notices`
- `Literature`
- `Government Gazette Notices`
- `Government Gazette Tenders and Contracts`
- `Government Gazette Proclamations And Legislation`
- `Government Gazette Private Notices`
- `Government Gazette Budgetary Papers`
- `Government Gazette Index And Contents`
- `Government Gazette Appointments And Employment`
- `Government Gazette Freedom Of Information`

## States and Territories

Used with various state-related parameters:

### Full State List (Newspaper Titles)
- `nsw` (New South Wales)
- `act` (Australian Capital Territory)
- `qld` (Queensland)
- `tas` (Tasmania)
- `sa` (South Australia)
- `nt` (Northern Territory)
- `wa` (Western Australia)
- `vic` (Victoria)
- `national` (National)
- `international` (International)

### Limited State List (Gazette Titles)
- `nsw` (New South Wales)
- `national` (National)
- `international` (International)

### Article Title States
- `International`
- `National`
- `ACT`
- `New South Wales`
- `Northern Territory`
- `Queensland`
- `South Australia`
- `Tasmania`
- `Victoria`
- `Western Australia`

## Related Documentation

- [Parameters Reference](./trove-api-parameters.md) - Complete parameter documentation
- [Search Parameters Guide](./trove-search-parameters.md) - Usage examples and best practices
- [Endpoints Reference](./trove-api-endpoints.md) - API endpoint information