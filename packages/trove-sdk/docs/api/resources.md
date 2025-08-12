# Resource APIs

Direct access to specific Trove records by ID. All resource APIs support both sync and async operations.

## Work Resource

Access books, images, maps, music, and other published works.

```python
# Get a work
work = client.work.get("123456789")

# Get with additional details
work = client.work.get("123456789", include=['workversions'], reclevel='full')

# Get work versions
versions = client.work.get_versions("123456789")

# Get library holdings
holdings = client.work.get_holdings("123456789")
```

## Article Resources

Access newspaper and gazette articles.

```python
# Newspaper articles
article = client.newspaper.get("18341291")

# Gazette articles  
gazette = client.gazette.get("123456")

# Get with full text
article = client.newspaper.get("18341291", include=['articletext'])
```

## People Resource

Access people and organization records.

```python
# Get person/organization
person = client.people.get("123456")

# Get with biographical information
person = client.people.get("123456", include=['biography'], reclevel='full')
```

## List Resource

Access user-created lists.

```python
# Get list
trove_list = client.list.get("123456")

# Get with list items
trove_list = client.list.get("123456", include=['listItems'])
```

## Common Parameters

All resources support these parameters:

- `include` - Additional data to include
- `reclevel` - Detail level ('brief' or 'full')  
- `encoding` - Response format ('json' or 'xml')

## Error Handling

```python
from trove.exceptions import ResourceNotFoundError

try:
    work = client.work.get("nonexistent")
except ResourceNotFoundError:
    print("Work not found")
```
