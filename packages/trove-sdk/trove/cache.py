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


def create_cache(backend_type: str, **kwargs: Any) -> CacheBackend:
    """Factory function for creating cache backends.
    
    Provides a convenient way to create cache backends by name with
    appropriate parameters.
    
    Args:
        backend_type: Type of cache backend ("memory", "sqlite", "none")
        **kwargs: Additional keyword arguments for cache backend constructor
        
    Returns:
        Appropriate cache backend instance
        
    Raises:
        ValueError: If backend_type is not supported
        
    Example:
        >>> # Create memory cache
        >>> cache = create_cache("memory")
        >>> 
        >>> # Create SQLite cache with custom path
        >>> from pathlib import Path
        >>> cache = create_cache("sqlite", db_path=Path("/tmp/cache.db"))
        >>> 
        >>> # Create no-op cache
        >>> cache = create_cache("none")
    """
    if backend_type == "memory":
        return MemoryCache(**kwargs)
    elif backend_type == "sqlite":
        return SqliteCache(**kwargs)
    elif backend_type == "none":
        return NoCache(**kwargs)
    else:
        raise ValueError(
            f"Unknown cache backend: {backend_type}. "
            f"Supported backends: memory, sqlite, none"
        )
