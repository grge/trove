# Citing Trove Resources Guide

This guide explains how to properly cite resources from Trove using the Trove SDK's citation functionality. The SDK automatically extracts bibliographic information and formats citations in standard academic formats.

## Quick Start

```python
from trove import TroveClient
from trove.citations import RecordType

# Create client
client = TroveClient.from_env()

# Extract citation from search result
search = client.search().text("Australian literature").in_("book")
for record in search.records():
    citation = client.citations.extract_from_record(record, RecordType.WORK)
    
    # Generate BibTeX
    bibtex = client.citations.cite_bibtex(citation)
    print(bibtex)
    break
```

## Citation Types

The SDK supports citation extraction and formatting for all major Trove resource types:

### Books and Works (`RecordType.WORK`)

Used for books, manuscripts, images, maps, music, and other creative works.

```python
citation = client.citations.extract_from_record(work_data, RecordType.WORK)

# BibTeX format
bibtex = client.citations.cite_bibtex(citation)
print(bibtex)
```

Example output:
```bibtex
@book{wilde_1980_6790891,
  title = {The Oxford companion to Australian literature},
  author = {Wilde, W. H. (William Henry) and Hooton, Joy and Andrews, Barry},
  year = {1980},
  publisher = {Oxford University Press},
  address = {Melbourne},
  url = {https://trove.nla.gov.au/work/6790891},
  urldate = {2025-08-12},
  note = {Retrieved from Trove, National Library of Australia}
}
```

### Newspaper Articles (`RecordType.ARTICLE`)

Used for newspaper and gazette articles.

```python
citation = client.citations.extract_from_record(article_data, RecordType.ARTICLE)

# CSL-JSON format
csl_json = client.citations.cite_csl_json(citation)
```

Example output:
```json
{
  "id": "nla.news-article18341291",
  "type": "article-newspaper",
  "title": "Federation Celebrations in Sydney",
  "container-title": "The Sydney Morning Herald",
  "issued": {"date-parts": [[1901, 1, 1]]},
  "page": "1",
  "URL": "https://nla.gov.au/nla.news-article18341291",
  "accessed": {"date-parts": [[2025, 8, 12]]},
  "note": "Retrieved from Trove, National Library of Australia"
}
```

### People and Organizations (`RecordType.PEOPLE`)

Used for biographical records.

```python
citation = client.citations.extract_from_record(people_data, RecordType.PEOPLE)
```

### User Lists (`RecordType.LIST`)

Used for user-created resource collections.

```python
citation = client.citations.extract_from_record(list_data, RecordType.LIST)
```

### Publication Titles (`RecordType.TITLE`)

Used for newspaper, magazine, and gazette titles.

```python
citation = client.citations.extract_from_record(title_data, RecordType.TITLE)
```

## Persistent Identifiers (PIDs)

Trove uses persistent identifiers to provide stable links to resources. The SDK automatically extracts and validates PIDs.

### Work PIDs

Works use National Library of Australia identifiers:

- `nla.obj-123456789` - General objects
- `nla.pic-an24009937` - Pictures  
- `nla.mus-vn3630286` - Music
- `nla.map-gmod7-st` - Maps

### Article PIDs

Articles use news-article identifiers:

- `nla.news-article18341291` - Newspaper articles
- `nla.gazette-article12345` - Government gazette articles

### URL Patterns

The SDK recognizes these URL patterns:

```python
# Work URLs
"https://nla.gov.au/nla.obj-123456789"
"https://trove.nla.gov.au/work/123456"
"https://api.trove.nla.gov.au/v3/work/123456"

# Article URLs  
"https://nla.gov.au/nla.news-article18341291"
"https://trove.nla.gov.au/ndp/del/article/18341291"
"https://api.trove.nla.gov.au/v3/newspaper/18341291"

# People URLs
"https://api.trove.nla.gov.au/v3/people/123456"

# List URLs
"https://api.trove.nla.gov.au/v3/list/123456"
```

## PID Resolution

You can resolve PIDs or URLs directly to citations:

```python
# Resolve by PID
citation = client.citations.resolve_identifier("nla.obj-123456789")

# Resolve by URL
citation = client.citations.resolve_identifier("https://nla.gov.au/nla.news-article18341291")

# Resolve by numeric ID (tries multiple record types)
citation = client.citations.resolve_identifier("123456")

if citation:
    print(f"Resolved: {citation.display_title}")
```

## Citation Formats

### BibTeX Format

BibTeX is widely used in academic writing and reference management software.

```python
bibtex = client.citations.cite_bibtex(citation)
```

The SDK automatically selects appropriate BibTeX entry types:
- `@book{}` for books and monographs
- `@article{}` for newspaper articles
- `@periodical{}` for publication titles  
- `@misc{}` for other resources

### CSL-JSON Format

Citation Style Language JSON format is used by modern reference managers like Zotero.

```python
csl_json = client.citations.cite_csl_json(citation)
```

The SDK maps to appropriate CSL types:
- `book` for books
- `article-newspaper` for newspaper articles
- `article-journal` for journal articles
- `map` for maps
- `document` for general works
- `dataset` for user lists
- `periodical` for publication titles

## Bibliographies

Generate bibliographies for multiple resources:

```python
# Collect citations from search results
citations = []
for record in client.search().text("Australian poetry").in_("book").records():
    citation = client.citations.extract_from_record(record, RecordType.WORK)
    citations.append(citation)
    if len(citations) >= 10:  # Limit for example
        break

# Generate BibTeX bibliography
bibtex_bib = client.citations.bibliography_bibtex(citations)

# Generate CSL-JSON bibliography
csl_json_bib = client.citations.bibliography_csl_json(citations)
```

## Best Practices

### 1. Use Appropriate Record Types

Always specify the correct record type when extracting citations:

```python
# For works (books, images, maps, etc.)
citation = client.citations.extract_from_record(record, RecordType.WORK)

# For newspaper/gazette articles
citation = client.citations.extract_from_record(record, RecordType.ARTICLE)

# For people/organizations
citation = client.citations.extract_from_record(record, RecordType.PEOPLE)
```

### 2. Include Access Dates

The SDK automatically includes access dates in citations, which is important for web resources:

```python
citation.access_date  # Automatically set to current time
```

### 3. Preserve PIDs

Always include the canonical PID when available for long-term citation stability:

```python
if citation.canonical_pid:
    print(f"Canonical PID: {citation.canonical_pid}")
```

### 4. Handle Missing Data Gracefully

The SDK handles missing bibliographic data gracefully:

```python
citation = client.citations.extract_from_record(incomplete_record, RecordType.WORK)
# Will still generate valid citations with available information
```

## Citation Examples

### Australian Book

```bibtex
@book{lawson_1896_12345,
  title = {While the Billy Boils},
  author = {Lawson, Henry},
  year = {1896},
  publisher = {Angus and Robertson},
  address = {Sydney},
  url = {https://trove.nla.gov.au/work/12345},
  urldate = {2025-08-12},
  note = {Retrieved from Trove, National Library of Australia}
}
```

### Historical Newspaper Article

```bibtex
@article{1901_18341291,
  title = {Federation Celebrations in Sydney},
  journal = {The Sydney Morning Herald},
  year = {1901},
  pages = {1},
  url = {https://nla.gov.au/nla.news-article18341291},
  urldate = {2025-08-12},
  note = {Retrieved from Trove, National Library of Australia}
}
```

### Historical Photograph

```bibtex
@misc{cazneaux_1930_pic123,
  title = {Sydney Harbour Bridge under construction},
  author = {Cazneaux, Harold},
  year = {1930},
  url = {https://nla.gov.au/nla.pic-an123456},
  urldate = {2025-08-12},
  note = {Retrieved from Trove, National Library of Australia}
}
```

## Integration with Reference Managers

### Zotero

Export CSL-JSON for Zotero import:

```python
import json

csl_data = client.citations.cite_csl_json(citation)
with open('trove_citation.json', 'w') as f:
    json.dump(csl_data, f, indent=2)
```

### Mendeley/EndNote

Export BibTeX for traditional reference managers:

```python
bibtex = client.citations.cite_bibtex(citation)
with open('trove_citation.bib', 'w') as f:
    f.write(bibtex)
```

## Error Handling

The citation system handles various error conditions gracefully:

```python
try:
    citation = client.citations.resolve_identifier("invalid-id")
    if citation is None:
        print("Could not resolve identifier")
except Exception as e:
    print(f"Error resolving citation: {e}")
```

## Advanced Usage

### Custom Citation Processing

Access raw citation data for custom processing:

```python
citation = client.citations.extract_from_record(record, RecordType.WORK)

# Access raw record data
raw_data = citation.raw_data

# Access structured fields
print(f"Title: {citation.title}")
print(f"Creators: {citation.creators}")
print(f"Publication Date: {citation.publication_date}")
print(f"PID: {citation.canonical_pid}")
```

### Bulk Citation Processing

Process multiple identifiers efficiently:

```python
identifiers = ["nla.obj-123", "nla.news-article456", "789"]
results = client.citations.resolver.bulk_resolve(identifiers)

for identifier, citation in results.items():
    if citation:
        print(f"{identifier}: {citation.display_title}")
    else:
        print(f"{identifier}: Could not resolve")
```

## Compliance and Ethics

### Attribution Requirements

When using Trove resources in research or publications:

1. Always cite the original source (creator, publication, date)
2. Include the Trove URL for digital access
3. Acknowledge Trove and the National Library of Australia
4. Include access date for web citations

### Copyright Considerations

- Respect copyright restrictions on Trove materials
- Check usage rights before republishing content
- Cite properly to support fair dealing/fair use claims
- Consider seeking permission for substantial use

The SDK automatically includes appropriate attribution text:
```
"Retrieved from Trove, National Library of Australia"
```

This guide should help you create proper citations for all types of Trove resources using the SDK's comprehensive citation functionality.