"""Cache backend implementations for Trove SDK.

This module provides different cache backend implementations to store
API responses and reduce network requests. Supports in-memory and
persistent SQLite caching.
"""

import json
import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .exceptions import CacheError


class CacheBackend(ABC):
    """Abstract cache backend interface.
    
    Defines the interface that all cache backends must implement,
    supporting both synchronous and asynchronous operations.
    """

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """Get value from cache.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int) -> None:
        """Set value in cache with TTL.
        
        Args:
            key: Cache key to store
            value: Value to cache (must be JSON-serializable for persistent backends)
            ttl: Time-to-live in seconds
        """
        pass

    @abstractmethod
    async def aget(self, key: str) -> Any | None:
        """Async get value from cache.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        pass

    @abstractmethod
    async def aset(self, key: str, value: Any, ttl: int) -> None:
        """Async set value in cache with TTL.
        
        Args:
            key: Cache key to store
            value: Value to cache (must be JSON-serializable for persistent backends)
            ttl: Time-to-live in seconds
        """
        pass


class MemoryCache(CacheBackend):
    """In-memory cache with TTL support.
    
    Provides fast caching using Python dictionaries. Cache is not persistent
    across process restarts but offers the fastest performance.
    
    Example:
        >>> cache = MemoryCache()
        >>> cache.set("key1", {"data": "value"}, ttl=300)
        >>> result = cache.get("key1")
        >>> print(result)
        {'data': 'value'}
    """

    def __init__(self):
        self._cache: dict[str, tuple] = {}  # key -> (value, expiry_time)
        self._lock = threading.RLock()

    def _is_expired(self, expiry_time: float) -> bool:
        """Check if cache entry is expired."""
        return time.time() > expiry_time

    def _cleanup_expired(self) -> None:
        """Remove expired entries from cache.
        
        This method is called periodically to clean up expired entries
        and prevent the cache from growing indefinitely.
        """
        now = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if now > expiry
        ]
        for key in expired_keys:
            self._cache.pop(key, None)

    def get(self, key: str) -> Any | None:
        """Get value from memory cache.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self._lock:
            if key not in self._cache:
                return None

            value, expiry_time = self._cache[key]
            if self._is_expired(expiry_time):
                del self._cache[key]
                return None

            return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        """Set value in memory cache.
        
        Args:
            key: Cache key to store
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        expiry_time = time.time() + ttl
        with self._lock:
            self._cache[key] = (value, expiry_time)

            # Periodic cleanup (every 100 sets)
            if len(self._cache) % 100 == 0:
                self._cleanup_expired()

    async def aget(self, key: str) -> Any | None:
        """Async get (same as sync for memory cache)."""
        return self.get(key)

    async def aset(self, key: str, value: Any, ttl: int) -> None:
        """Async set (same as sync for memory cache)."""
        self.set(key, value, ttl)

    def clear(self) -> None:
        """Clear all cached items."""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Get number of items in cache."""
        with self._lock:
            return len(self._cache)


class SqliteCache(CacheBackend):
    """SQLite-based persistent cache.
    
    Provides persistent caching using SQLite database. Cache survives
    process restarts but has slightly higher overhead than memory cache.
    
    Args:
        db_path: Path to SQLite database file (default: ~/.trove/cache.db)
        
    Example:
        >>> cache = SqliteCache()
        >>> cache.set("key1", {"data": "value"}, ttl=300)
        >>> result = cache.get("key1")
        >>> print(result)
        {'data': 'value'}
    """

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or Path.home() / '.trove' / 'cache.db'
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        expiry_time REAL
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_expiry_time 
                    ON cache_entries(expiry_time)
                """)
                conn.commit()
        except sqlite3.Error as e:
            raise CacheError(f"Failed to initialize cache database: {e}") from e

    def _cleanup_expired(self, conn: sqlite3.Connection) -> None:
        """Remove expired entries from database."""
        now = time.time()
        conn.execute("DELETE FROM cache_entries WHERE expiry_time < ?", (now,))

    def get(self, key: str) -> Any | None:
        """Get value from SQLite cache.
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Cached value if found and not expired, None otherwise
            
        Raises:
            CacheError: If database operation fails
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT value, expiry_time FROM cache_entries WHERE key = ?",
                        (key,)
                    )
                    row = cursor.fetchone()

                    if row is None:
                        return None

                    value_json, expiry_time = row
                    if time.time() > expiry_time:
                        # Clean up expired entry
                        conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                        conn.commit()
                        return None

                    return json.loads(value_json)

            except (sqlite3.Error, json.JSONDecodeError) as e:
                raise CacheError(f"Failed to get cache entry: {e}") from e

    def set(self, key: str, value: Any, ttl: int) -> None:
        """Set value in SQLite cache.
        
        Args:
            key: Cache key to store
            value: Value to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds
            
        Raises:
            CacheError: If database operation fails or value is not serializable
        """
        expiry_time = time.time() + ttl

        try:
            value_json = json.dumps(value)
        except (TypeError, ValueError) as e:
            raise CacheError(f"Value is not JSON-serializable: {e}") from e

        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO cache_entries (key, value, expiry_time)
                        VALUES (?, ?, ?)
                    """, (key, value_json, expiry_time))

                    # Periodic cleanup (every 100 sets based on key hash)
                    if hash(key) % 100 == 0:
                        self._cleanup_expired(conn)

                    conn.commit()

            except sqlite3.Error as e:
                raise CacheError(f"Failed to set cache entry: {e}") from e

    async def aget(self, key: str) -> Any | None:
        """Async get (uses sync implementation)."""
        return self.get(key)

    async def aset(self, key: str, value: Any, ttl: int) -> None:
        """Async set (uses sync implementation)."""
        self.set(key, value, ttl)

    def clear(self) -> None:
        """Clear all cached items.
        
        Raises:
            CacheError: If database operation fails
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM cache_entries")
                    conn.commit()
            except sqlite3.Error as e:
                raise CacheError(f"Failed to clear cache: {e}") from e

    def size(self) -> int:
        """Get number of items in cache.
        
        Returns:
            Number of cached items
            
        Raises:
            CacheError: If database operation fails
        """
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("SELECT COUNT(*) FROM cache_entries")
                    return cursor.fetchone()[0]
            except sqlite3.Error as e:
                raise CacheError(f"Failed to get cache size: {e}") from e


class NoCache(CacheBackend):
    """No-op cache backend that doesn't cache anything.
    
    Useful for disabling caching entirely while maintaining the same interface.
    All operations are no-ops and get() always returns None.
    
    Example:
        >>> cache = NoCache()
        >>> cache.set("key1", "value", ttl=300)  # Does nothing
        >>> result = cache.get("key1")          # Always returns None
        >>> print(result)
        None
    """

    def get(self, key: str) -> Any | None:
        """Always returns None."""
        return None

    def set(self, key: str, value: Any, ttl: int) -> None:
        """Does nothing."""
        pass

    async def aget(self, key: str) -> Any | None:
        """Always returns None."""
        return None

    async def aset(self, key: str, value: Any, ttl: int) -> None:
        """Does nothing."""
        pass


class SearchCacheBackend(CacheBackend):
    """Enhanced cache backend with search-specific TTL logic and statistics."""
    
    def __init__(self, backend: CacheBackend):
        """Initialize search cache wrapper.
        
        Args:
            backend: Underlying cache backend to wrap
        """
        self._backend = backend
        self._stats = {
            'hits': 0,
            'misses': 0, 
            'sets': 0,
            'search_requests': 0,
            'cache_savings_seconds': 0.0
        }
        self._route_ttl = {
            '/result': 900,  # 15 minutes default for search results
            '/work': 3600,   # 1 hour for individual works
            '/article': 3600,  # 1 hour for articles
            '/people': 86400,  # 24 hours for people records (more stable)
            '/list': 1800,     # 30 minutes for lists
        }
        
    def get_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dictionary containing cache hit/miss rates and other metrics
        """
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total_requests) if total_requests > 0 else 0.0
        
        return {
            **self._stats,
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'miss_rate': 1.0 - hit_rate
        }
        
    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0, 
            'search_requests': 0,
            'cache_savings_seconds': 0.0
        }
        
    def set_route_ttl(self, route: str, ttl: int) -> None:
        """Set TTL for a specific API route.
        
        Args:
            route: API route path (e.g., '/result', '/work')
            ttl: Time-to-live in seconds
        """
        self._route_ttl[route] = ttl
        
    def _determine_search_ttl(self, params: dict, response: dict, route: str = '/result') -> int:
        """Determine TTL based on search characteristics.
        
        Args:
            params: Search parameters used
            response: API response data
            route: API route being cached
            
        Returns:
            TTL in seconds
        """
        base_ttl = self._route_ttl.get(route, 900)  # 15 minutes default
        
        # For search results, analyze content for dynamic TTL
        if route == '/result':
            categories = response.get('category', [])
            total_results = sum(cat.get('records', {}).get('total', 0) for cat in categories)
            
            # Shorter TTL for small result sets (more likely to change)
            if total_results < 10:
                return base_ttl // 3  # 5 minutes for small result sets
                
            # Check for "coming soon" or recently added content
            for category in categories:
                records = category.get('records', {})
                for record_type in ['work', 'article', 'people', 'list']:
                    for record in records.get(record_type, []):
                        # Check for recent additions or "coming soon" status
                        if (record.get('status') == 'coming soon' or 
                            'recently added' in str(record.get('notes', '')).lower()):
                            return 300  # 5 minutes for dynamic content
                            
            # Longer TTL for bulk harvest (more stable)
            if params.get('bulkHarvest') == 'true':
                return base_ttl * 4  # 1 hour for bulk harvest
                
            # Check for date-based searches (historical data is more stable)  
            if any(param.startswith('l-decade') for param in params.keys()):
                decades = [d for k, v in params.items() 
                          if k.startswith('l-decade') for d in v.split(',')]
                if decades and all(int(d) < 200 for d in decades if d.isdigit()):
                    # Historical data (before 2000s) - very stable
                    return base_ttl * 8  # 2 hours
                    
        return base_ttl
        
    def get(self, key: str) -> Any | None:
        """Get value from cache with statistics tracking."""
        start_time = time.time()
        result = self._backend.get(key)
        
        if result is not None:
            self._stats['hits'] += 1
            # Estimate time saved by cache hit (typical API response time)
            self._stats['cache_savings_seconds'] += 1.5  
        else:
            self._stats['misses'] += 1
            
        return result
        
    async def aget(self, key: str) -> Any | None:
        """Async get value from cache with statistics tracking."""
        start_time = time.time()
        result = await self._backend.aget(key)
        
        if result is not None:
            self._stats['hits'] += 1
            self._stats['cache_savings_seconds'] += 1.5
        else:
            self._stats['misses'] += 1
            
        return result
        
    def set(self, key: str, value: Any, ttl: int = None, 
           search_params: dict = None, route: str = '/result') -> None:
        """Set value in cache with dynamic TTL calculation.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional explicit TTL (seconds)
            search_params: Search parameters for dynamic TTL calculation
            route: API route for TTL calculation
        """
        # Determine TTL dynamically if not provided
        if ttl is None and search_params and route == '/result':
            ttl = self._determine_search_ttl(search_params, value, route)
        elif ttl is None:
            ttl = self._route_ttl.get(route, 900)
            
        self._backend.set(key, value, ttl)
        self._stats['sets'] += 1
        
        if route == '/result':
            self._stats['search_requests'] += 1
        
    async def aset(self, key: str, value: Any, ttl: int = None,
                  search_params: dict = None, route: str = '/result') -> None:
        """Async set value in cache with dynamic TTL calculation."""
        if ttl is None and search_params and route == '/result':
            ttl = self._determine_search_ttl(search_params, value, route)
        elif ttl is None:
            ttl = self._route_ttl.get(route, 900)
            
        await self._backend.aset(key, value, ttl)
        self._stats['sets'] += 1
        
        if route == '/result':
            self._stats['search_requests'] += 1


def create_cache(backend_type: str, enhanced: bool = False, **kwargs: Any) -> CacheBackend:
    """Factory function for creating cache backends.
    
    Provides a convenient way to create cache backends by name with
    appropriate parameters.
    
    Args:
        backend_type: Type of cache backend ("memory", "sqlite", "none")
        enhanced: Whether to wrap with SearchCacheBackend for search optimization
        **kwargs: Additional keyword arguments for cache backend constructor
        
    Returns:
        Appropriate cache backend instance
        
    Raises:
        ValueError: If backend_type is not supported
        
    Example:
        >>> # Create memory cache
        >>> cache = create_cache("memory")
        >>> 
        >>> # Create enhanced SQLite cache for search
        >>> cache = create_cache("sqlite", enhanced=True, db_path=Path("/tmp/cache.db"))
        >>> 
        >>> # Create no-op cache
        >>> cache = create_cache("none")
    """
    if backend_type == "memory":
        backend = MemoryCache(**kwargs)
    elif backend_type == "sqlite":
        backend = SqliteCache(**kwargs)
    elif backend_type == "none":
        backend = NoCache(**kwargs)
    else:
        raise ValueError(
            f"Unknown cache backend: {backend_type}. "
            f"Supported backends: memory, sqlite, none"
        )
        
    # Wrap with enhanced functionality if requested
    if enhanced:
        backend = SearchCacheBackend(backend)
        
    return backend
