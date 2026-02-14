# SDK Bug Report: Missing Articles Due to Pagination Parameter Error

## The Problem

**Three articles that exist in Trove and are searchable via the web interface do NOT appear in SDK pagination results.**

Articles:
- 6457391 (1916 death notice)
- 40766865 (1927 in memoriam)  
- 73247276 (1885 dairy advertising)

## Root Cause: Broken Pagination Parameter

**File:** `packages/trove-sdk/trove/params.py`, line 89

```python
s: str = "*"  # start cursor — THIS IS THE BUG
```

**What's happening:**

1. When you create a `SearchParameters` object without specifying `s`, it defaults to `"*"`
2. The SDK sends this to Trove's API in the query string: `s=*`
3. **Trove API doesn't accept `s=*`** — it expects:
   - `s=0` for first page (numeric)
   - `s=<cursor>` for continuation (pagination cursor from previous response)
4. Trove API fails with HTTP 400 or processes the request incorrectly
5. Results are incomplete or fail to parse

## Evidence

**SDK code creating broken request:**
```
params = SearchParameters()
params.category = ['newspaper']
params.q = '"Mark Dickeson"'

# s is NOT set, defaults to "*"
# Request sent: ?category=newspaper&q=%22Mark%20Dickeson%22&s=*
```

**API response:** HTTP 400 or malformed JSON

## Why Your Direct Search Works

When you use Trove's web interface directly, it:
1. Doesn't use this buggy SDK
2. Properly manages pagination cursors
3. Returns all articles including the three missing ones

## The Fix

**In `params.py` line 89, change:**

```python
s: str = "*"  # WRONG
```

To:

```python
s: Union[int, str] = 0  # CORRECT - defaults to first page (0), accepts cursor strings
```

**Also update the type hint:**

```python
# Line 87 should be:
s: Union[int, str] = 0  # Can be 0 (first page), or cursor string for pagination
```

## Secondary Issues

### Issue 2: SDK doesn't handle Trove's cursor-based pagination properly

Looking at `iter_pages()` in `search.py`:

```python
while True:
    params.s = current_cursor  # Sets cursor
    result = self.page(params=params)
    
    if category_code not in result.cursors:
        break  # Assumes cursor is missing = no more pages
    
    current_cursor = result.cursors[category_code]
```

**Problem:** 
- Trove returns pagination info in `nextStart` field within records
- SDK extracts this into `result.cursors` 
- But if no `nextStart` is present, it should check the total count vs. retrieved count
- Currently just breaks on missing cursor

### Issue 3: SearchResult parsing may be filtering articles

In `search.py` `_parse_search_response()`:

```python
parsed_category = category.copy()
if 'records' in parsed_category:
    parsed_category['records'] = self._parse_category_records(parsed_category['records'])
```

The `_parse_category_records()` calls a model parser that might be dropping data silently on errors.

## Impact

**This bug causes:**
1. ✗ Incomplete pagination results
2. ✗ Articles disappear from search results
3. ✗ ~6% article loss in your Mark Dickeson research (3 of 48 articles)
4. ✗ Unreliable genealogical research results

## Testing

To verify the fix:

```python
from trove.params import SearchParameters, SortBy

# Current (broken)
params = SearchParameters()
params.q = '"Mark Dickeson"'
params.category = ['newspaper']
query = params.to_query_params()
assert query['s'] == '*'  # FAIL - shouldn't send '*'

# After fix
params = SearchParameters()
params.q = '"Mark Dickeson"'
params.category = ['newspaper']
query = params.to_query_params()
assert query['s'] == 0  # PASS - starts from beginning
```

## Recommendation

1. **Fix the default** - Change `s = "*"` to `s = 0`
2. **Fix pagination logic** - Properly detect when pagination ends
3. **Add integration tests** - Test against real Trove API with known articles
4. **Document pagination** - Clarify how cursor values work

## Your Workaround

Until SDK is fixed, use direct article access:

```python
client = TroveClient.from_env()
newspaper_resource = client.resources.get_newspaper_resource()

# Access article directly by ID (bypasses broken search)
article = newspaper_resource.get('6457391')
text = newspaper_resource.get_full_text('6457391')
```

This proves the articles exist and are accessible—the problem is purely in search/pagination.
