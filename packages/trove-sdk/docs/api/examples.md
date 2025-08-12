# Examples

Practical examples showing how to use the Trove SDK for common tasks.

## Basic Search Examples

### Search for Books

```python
from trove import TroveClient

client = TroveClient.from_env()

# Find books about Australian history
results = (client.search()
          .text("Australian history")
          .in_("book")
          .decade("200")  # 2000s
          .page_size(20)
          .first_page())

print(f"Found {results.total_results} books")

# Process results
works = results.categories[0]['records']['work']
for work in works:
    print(f"- {work.primary_title}")
    print(f"  Author: {work.primary_contributor or 'Unknown'}")
    print(f"  Year: {work.publication_year or 'Unknown'}")
    print()
```

### Search Newspapers

```python
# Find newspaper articles about federation
results = (client.search()
          .text("federation")
          .in_("newspaper")
          .state("NSW")
          .decade("190", "191")  # 1900s-1910s
          .illustrated()
          .first_page())

articles = results.categories[0]['records']['article']
for article in articles:
    print(f"- {article.display_title}")
    print(f"  {article.newspaper_title}, {article.date}")
    print()
```

## Resource Access Examples

### Get Work Details

```python
# Get a specific work with full details
work = client.work.get("123456789", include=['workversions', 'holdings'], reclevel='full')

print(f"Title: {work.primary_title}")
print(f"Contributors: {', '.join(work.contributor)}")

# Check versions
versions = client.work.get_versions("123456789") 
print(f"Available in {len(versions)} versions")

# Check library holdings
holdings = client.work.get_holdings("123456789")
for holding in holdings:
    print(f"Held by: {holding.get('name', 'Unknown library')}")
```

### Get Article with Full Text

```python
# Get newspaper article with full text
article = client.newspaper.get("18341291", include=['articletext'])

print(f"Headline: {article.display_title}")
print(f"Newspaper: {article.newspaper_title}")
print(f"Date: {article.date}")

if article.has_full_text:
    print(f"Article text ({article.word_count} words):")
    print(article.article_text[:500] + "...")
```

## Advanced Search Examples

### Faceted Browsing

```python
# Search with facets for exploration
results = (client.search()
          .text("women's suffrage")
          .in_("newspaper")
          .with_facets("decade", "state", "title")
          .first_page())

print(f"Found {results.total_results} articles")

# Explore facets
facets = results.categories[0]['facets']['facet']
for facet in facets:
    print(f"\n{facet['name'].title()} breakdown:")
    
    terms = facet['term']
    for term in terms[:10]:  # Show top 10
        print(f"  {term['display']}: {term['count']} articles")
```

### Pagination Example

```python
# Process all results page by page
search = (client.search()
         .text("Australian poetry")
         .in_("book")
         .page_size(50))

total_processed = 0
for page_num, page in enumerate(search.pages(), 1):
    works = page.categories[0]['records']['work']
    
    print(f"Page {page_num}: {len(works)} works")
    total_processed += len(works)
    
    # Process works
    for work in works:
        print(f"  - {work.primary_title}")
    
    # Stop after 5 pages for demo
    if page_num >= 5:
        break

print(f"Processed {total_processed} total works")
```

### Bulk Data Collection

```python
# Collect large datasets efficiently
search = (client.search()
         .text("bushfire")
         .in_("newspaper")
         .year("2019", "2020")  # Black Summer fires
         .harvest()  # Enable bulk mode
         .page_size(100))

articles = []
for article in search.records():
    articles.append({
        'title': article.display_title,
        'newspaper': article.newspaper_title,
        'date': article.date,
        'url': article.trove_url,
        'text': article.article_text if article.has_full_text else None
    })
    
    # Progress indicator
    if len(articles) % 100 == 0:
        print(f"Collected {len(articles)} articles...")
    
    # Limit for demo
    if len(articles) >= 1000:
        break

print(f"Final dataset: {len(articles)} articles")
```

## Analysis Examples

### Publication Timeline

```python
from collections import Counter

# Analyze publication years for a topic
search = client.search().text("climate change").in_("book").page_size(100)

years = []
for work in search.records():
    if work.publication_year:
        years.append(work.publication_year)
    
    if len(years) >= 500:  # Limit sample
        break

# Count by decade
decades = Counter(year // 10 * 10 for year in years)
print("Climate change books by decade:")
for decade in sorted(decades.keys()):
    print(f"  {decade}s: {decades[decade]} books")
```

### Geographic Distribution

```python
from collections import Counter

# Analyze newspaper coverage by state
search = (client.search()
         .text("mining boom")
         .in_("newspaper")
         .decade("200")  # 2000s
         .page_size(50))

states = []
for page in search.pages():
    articles = page.categories[0]['records']['article']
    for article in articles:
        # Extract state from newspaper title or other metadata
        title = article.newspaper_title or ""
        if "Sydney" in title or "NSW" in title:
            states.append("NSW")
        elif "Melbourne" in title or "VIC" in title:
            states.append("VIC")
        # ... more state detection logic
    
    if len(states) >= 200:  # Limit for demo
        break

state_counts = Counter(states)
print("Mining boom coverage by state:")
for state, count in state_counts.most_common():
    print(f"  {state}: {count} articles")
```

## Citation Examples

### Generate Citations

```python
from trove.citations import generate_citation

# Get work and generate citation
work = client.work.get("123456789")

# BibTeX format
bibtex = generate_citation(work, format='bibtex')
print("BibTeX citation:")
print(bibtex)

# CSL-JSON format
csl_json = generate_citation(work, format='csl-json')
print("\nCSL-JSON citation:")
print(json.dumps(csl_json, indent=2))
```

### PID Resolution

```python
from trove.citations import resolve_pid

# Resolve Trove URLs to records
urls = [
    "https://trove.nla.gov.au/work/123456789",
    "https://trove.nla.gov.au/newspaper/article/18341291"
]

for url in urls:
    record = resolve_pid(url, client)
    if record:
        if hasattr(record, 'primary_title'):  # Work
            print(f"Work: {record.primary_title}")
        elif hasattr(record, 'display_title'):  # Article
            print(f"Article: {record.display_title}")
```

## Error Handling Examples

### Robust Batch Processing

```python
from trove.exceptions import ResourceNotFoundError, RateLimitError
import time

def process_work_ids(work_ids):
    results = []
    failed = []
    
    for i, work_id in enumerate(work_ids):
        try:
            work = client.work.get(work_id)
            results.append(work)
            
        except ResourceNotFoundError:
            print(f"Work {work_id} not found")
            failed.append(work_id)
            
        except RateLimitError as e:
            print(f"Rate limited, waiting...")
            wait_time = getattr(e, 'retry_after', 30)
            time.sleep(float(wait_time))
            
            # Retry the same ID
            try:
                work = client.work.get(work_id)
                results.append(work)
            except Exception:
                failed.append(work_id)
        
        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(work_ids)} works")
    
    return results, failed

# Use the function
work_ids = ["123", "456", "789", "nonexistent"]
works, failed_ids = process_work_ids(work_ids)

print(f"Successfully processed: {len(works)} works")
print(f"Failed: {len(failed_ids)} works")
```

## Performance Examples

### Connection Reuse

```python
# Use client as context manager for automatic cleanup
with TroveClient.from_env() as client:
    # All requests reuse the same connection
    for query in ["poetry", "fiction", "history"]:
        results = client.search().text(query).in_("book").first_page()
        print(f"{query}: {results.total_results} results")
    
    # Client automatically closed here
```

### Async Processing

```python
import asyncio

async def search_multiple_terms(terms):
    client = TroveClient.from_env()
    
    # Process searches concurrently
    tasks = []
    for term in terms:
        task = client.search().text(term).in_("book").afirst_page()
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    for term, result in zip(terms, results):
        print(f"{term}: {result.total_results} results")
    
    await client.aclose()

# Run async example
terms = ["poetry", "fiction", "history", "science"]
asyncio.run(search_multiple_terms(terms))
```
