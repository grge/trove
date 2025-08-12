# Data Models

The Trove SDK provides optional Pydantic models for type-safe access to API responses while maintaining backward compatibility with dict-like access.

## Overview

Models provide:
- **Type safety** - IDE autocompletion and static type checking
- **Computed properties** - Convenient access to derived data
- **Data validation** - Automatic validation of API responses
- **Backward compatibility** - All dict-like access patterns still work

## Available Models

### Work Model

Represents books, images, maps, music, and other published works.

```python
from trove.models import Work

# Get a work (returns Work model automatically)
work = client.work.get("123456789")

# Type-safe property access
print(work.primary_title)      # "The Title of the Work"
print(work.primary_contributor) # "Author, Name"  
print(work.publication_year)   # 2020

# Dict-like access (backward compatible)
print(work['title'])           # "The Title of the Work"
print(work.get('issued'))      # "2020"

# Access raw data
print(work.raw['title'])       # Original API response data
```

**Key Properties:**
- `primary_title` - Main title with fallback
- `primary_contributor` - First contributor/author
- `publication_year` - Parsed publication year as integer
- `is_online` - Whether work is available online
- `has_corrections` - Whether work has text corrections

### Article Model  

Represents newspaper and gazette articles.

```python
from trove.models import Article

# Get an article
article = client.newspaper.get("18341291")

# Type-safe access
print(article.display_title)    # Article heading with fallback
print(article.newspaper_title)  # Newspaper name
print(article.has_full_text)    # Boolean - full text available
print(article.is_illustrated)   # Boolean - has illustrations
print(article.word_count)       # Integer word count

# Dict-like access still works
print(article['heading'])       # Raw heading
print(article.get('articleText')) # Full article text
```

**Key Properties:**
- `display_title` - Article heading with fallback
- `newspaper_title` - Name of the newspaper/publication
- `has_full_text` - Whether full article text is available
- `is_illustrated` - Whether article contains illustrations
- `has_corrections` - Whether article has user corrections

### People Model

Represents people and organization records.

```python
from trove.models import People

# Get a person record
person = client.people.get("123456")

# Type-safe access
print(person.display_name)     # Primary display name
print(person.is_person)        # True if person, False if organization
print(person.is_organization)  # True if organization/family
print(person.primary_biography) # First biographical text

# Access alternate names
for name in person.alternate_name:
    print(f"Also known as: {name}")
```

**Key Properties:**
- `display_name` - Primary display name with fallback
- `is_person` - Whether record represents a person
- `is_organization` - Whether record represents an organization
- `primary_biography` - First available biographical text

### List Model

Represents user-created lists.

```python
from trove.models import TroveList

# Get a list
trove_list = client.list.get("123456")

# Type-safe access  
print(trove_list.display_title)   # List title with fallback
print(trove_list.creator_name)    # Creator name with fallback
print(trove_list.item_count)      # Number of items in list

# Access list items
for item in trove_list.list_item:
    print(f"- {item.title}")
```

**Key Properties:**
- `display_title` - List title with fallback
- `creator_name` - List creator with fallback
- `item_count` - Number of items in the list

## Backward Compatibility

Models are designed to be drop-in replacements for dictionary access:

```python
# Both approaches work identically
work = client.work.get("123456")

# New model approach
title = work.primary_title
contributors = work.contributor

# Legacy dict approach (still works)
title = work['title'] or "Untitled Work"
contributors = work.get('contributor', [])

# Mixed approach
print(f"{work.primary_title} by {work['contributor'][0] if work['contributor'] else 'Unknown'}")
```

## Raw Data Access

Access the original API response data:

```python
work = client.work.get("123456")

# Access raw response
raw_data = work.raw
print(raw_data.keys())  # All original field names

# Useful for debugging or accessing new fields
if 'newField' in work.raw:
    print(f"New field: {work.raw['newField']}")
```

## Working with Search Results

Models are automatically used in search results:

```python
results = client.search().text("poetry").in_("book").first_page()

# Records are automatically parsed into models
works = results.categories[0]['records']['work']
for work in works:
    # work is a Work model instance
    print(f"{work.primary_title} ({work.publication_year})")
    
    # But dict access still works
    print(f"Raw title: {work['title']}")
```

## Error Handling

Models gracefully handle missing or malformed data:

```python
work = client.work.get("123456")

# Properties handle missing data gracefully
print(work.primary_title)      # Returns "Untitled Work" if title missing
print(work.publication_year)   # Returns None if year can't be parsed

# Raw access returns exactly what API provides
print(work.raw.get('title'))   # Returns None if missing
```

## Custom Model Usage

You can also manually parse data into models:

```python
from trove.models import parse_record

# Parse raw API data
raw_data = {'id': '123', 'title': 'Test Work'}
work = parse_record(raw_data, 'work')

if work:
    print(work.primary_title)  # Type-safe access
else:
    print(raw_data['title'])   # Fallback to dict access
```

## Type Hints

Models provide full type hint support:

```python
from trove.models import Work
from typing import Optional

def process_work(work: Work) -> Optional[str]:
    # Process a work and return its title
    if work.publication_year and work.publication_year > 2000:
        return work.primary_title
    return None

# IDE will provide autocompletion and type checking
work = client.work.get("123456")
title = process_work(work)  # Type: Optional[str]
```
