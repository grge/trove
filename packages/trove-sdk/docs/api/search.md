# Search API

The Search API provides a fluent interface for querying Trove with method chaining and intelligent parameter handling.

## Creating Searches

Get a search builder from the client:

```python
search = client.search()
```

## Query Methods

### `text(query: str) -> Search`

Set the search query text.

```python
search = client.search().text("Australian federation")
```

### `in_(*categories: str) -> Search`

Specify categories to search within.

**Valid Categories:**
- `book` - Books and other published works
- `newspaper` - Newspaper articles
- `image` - Images and photographs
- `people` - People and organizations
- `list` - User-created lists
- `magazine` - Magazine and journal articles
- `music` - Musical works
- `map` - Maps and geographical materials

```python
# Single category
search = client.search().text("poetry").in_("book")

# Multiple categories  
search = client.search().text("Sydney").in_("book", "image", "newspaper")
```

## Filtering Methods

### `decade(*decades: str) -> Search`

Filter by decade (1790, 1800, 1810, etc.).

```python
search = client.search().text("federation").decade("190", "191")  # 1900s and 1910s
```

### `year(*years: str) -> Search`

Filter by specific years.

```python
search = client.search().text("election").year("2019", "2020", "2021")
```

### `state(*states: str) -> Search`

Filter by Australian state/territory.

**Valid States:**
- ACT, NSW, NT, QLD, SA, TAS, VIC, WA, National

```python
search = client.search().text("bushfire").state("NSW", "VIC")
```

### `title(*titles: str) -> Search`

Filter by publication title (newspapers, magazines).

```python
search = client.search().text("politics").title("The Sydney Morning Herald")
```

### `format(*formats: str) -> Search`

Filter by format/type.

```python
search = client.search().text("history").format("Book", "Thesis")
```

### `online() -> Search`

Filter for online-accessible items only.

```python
search = client.search().text("poetry").in_("book").online()
```

### `illustrated() -> Search`

Filter for illustrated items (newspapers/images).

```python
search = client.search().text("war").in_("newspaper").illustrated()
```

## Result Options

### `page_size(size: int) -> Search`

Set the number of results per page (max 100).

```python
search = client.search().text("test").page_size(50)
```

### `sort_by(sort_option: str) -> Search`

Set result sorting.

**Sort Options:**
- `relevance` (default)
- `date_asc` - Oldest first
- `date_desc` - Newest first  
- `title` - Alphabetical by title

```python
search = client.search().text("federation").sort_by("date_desc")
```

### `with_reclevel(level: str) -> Search`

Set record detail level.

- `brief` (default) - Basic metadata
- `full` - Complete metadata

```python
search = client.search().text("poetry").with_reclevel("full")
```

### `with_facets(*facets: str) -> Search`

Include facet information.

**Available Facets:**
- `format` - Item formats
- `decade` - Publication decades
- `year` - Publication years
- `language` - Languages
- `category` - Content categories

```python
search = client.search().text("history").with_facets("decade", "format")
```

### `harvest() -> Search`

Enable bulk harvest mode for large result sets.

```python
search = client.search().text("poetry").harvest()
```

## Execution Methods

### `first_page() -> SearchResult`

Execute search and get the first page of results.

```python
results = client.search().text("federation").in_("book").first_page()
print(f"Found {results.total_results} results")
```

### `pages() -> Iterator[SearchResult]`

Iterate through all pages of results (single category only).

```python
search = client.search().text("poetry").in_("book").page_size(20)

for page in search.pages():
    print(f"Page with {len(page.categories[0]['records']['work'])} works")
    if page_count > 10:  # Limit for example
        break
```

### `records() -> Iterator[Dict[str, Any]]`

Iterate through all individual records (single category only).

```python
search = client.search().text("federation").in_("newspaper")

for i, article in enumerate(search.records()):
    print(f"{i+1}. {article.display_title} ({article.date})")
    if i >= 100:  # Limit for example
        break
```

## Async Methods

All execution methods have async versions:

### `afirst_page() -> SearchResult`

```python
results = await client.search().text("test").in_("book").afirst_page()
```

### `apages() -> AsyncIterator[SearchResult]`

```python
async for page in client.search().text("poetry").in_("book").apages():
    print(f"Got {page.total_results} total results")
```

### `arecords() -> AsyncIterator[Dict[str, Any]]`

```python
async for record in client.search().text("history").in_("book").arecords():
    print(record.primary_title)
```

## Working with Results

### SearchResult Structure

```python
results = client.search().text("test").in_("book").first_page()

# Access metadata
print(f"Query: {results.query}")
print(f"Total results: {results.total_results}")

# Access categories
for category in results.categories:
    print(f"Category: {category['code']}")
    
    # Access records
    records = category['records']['work']  # 'work' for books
    for work in records:
        # Type-safe access (if using models)
        print(f"Title: {work.primary_title}")
        
        # Dict-like access (always available)
        print(f"Title: {work['title']}")
```

### Facet Information

```python
results = (client.search()
          .text("Australian history") 
          .in_("book")
          .with_facets("decade", "format")
          .first_page())

category = results.categories[0]
if 'facets' in category:
    facets = category['facets']['facet']
    for facet in facets:
        print(f"Facet: {facet['name']}")
        for term in facet['term'][:5]:  # Show top 5
            print(f"  {term['display']}: {term['count']}")
```

## Examples

### Basic Search

```python
# Find books about Australian poetry from the 2000s
results = (client.search()
          .text("Australian poetry")
          .in_("book")
          .decade("200")
          .page_size(20)
          .first_page())

works = results.categories[0]['records']['work']
for work in works:
    print(f"- {work.primary_title} ({work.publication_year})")
```

### Newspaper Search with Facets

```python
# Search newspapers with faceted browsing
results = (client.search()
          .text("federation")
          .in_("newspaper")
          .state("NSW")
          .decade("190", "191")
          .with_facets("year", "title")
          .first_page())

print(f"Found {results.total_results} articles")

# Explore facets
facets = results.categories[0]['facets']['facet']
for facet in facets:
    if facet['name'] == 'year':
        print("Articles by year:")
        for term in facet['term'][:10]:
            print(f"  {term['display']}: {term['count']} articles")
```

### Bulk Data Collection

```python
# Collect all articles about a topic
search = (client.search()
         .text("women's suffrage")
         .in_("newspaper")
         .decade("190", "191")
         .harvest()  # Enable bulk mode
         .page_size(50))

articles = []
for article in search.records():
    articles.append({
        'title': article.display_title,
        'newspaper': article.newspaper_title,
        'date': article.date,
        'url': article.trove_url
    })
    
    if len(articles) >= 1000:  # Collect up to 1000
        break

print(f"Collected {len(articles)} articles")
```
