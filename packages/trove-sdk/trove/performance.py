"""Performance optimizations and monitoring for Trove SDK."""

import asyncio
import time
from typing import List, Dict, Any, Optional, Callable, Iterator, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics collection."""
    request_count: int = 0
    total_request_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    rate_limit_delays: int = 0
    errors: int = 0
    start_time: float = field(default_factory=time.time)
    
    @property
    def average_request_time(self) -> float:
        """Average request time in seconds."""
        return self.total_request_time / self.request_count if self.request_count > 0 else 0.0
    
    @property
    def cache_hit_rate(self) -> float:
        """Cache hit rate as percentage."""
        total_cache_requests = self.cache_hits + self.cache_misses
        return (self.cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0.0
    
    @property
    def uptime(self) -> float:
        """Uptime in seconds."""
        return time.time() - self.start_time


class PerformanceMonitor:
    """Monitors and reports performance metrics."""
    
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self._request_start_times: Dict[str, float] = {}
    
    def start_request(self, request_id: str) -> None:
        """Start timing a request."""
        self._request_start_times[request_id] = time.time()
    
    def end_request(self, request_id: str) -> None:
        """End timing a request and record the duration."""
        if request_id in self._request_start_times:
            duration = time.time() - self._request_start_times.pop(request_id)
            self.record_request(duration)
    
    def record_request(self, duration: float) -> None:
        """Record a request completion."""
        self.metrics.request_count += 1
        self.metrics.total_request_time += duration
    
    def record_cache_hit(self) -> None:
        """Record cache hit."""
        self.metrics.cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """Record cache miss."""
        self.metrics.cache_misses += 1
    
    def record_rate_limit_delay(self) -> None:
        """Record rate limit delay."""
        self.metrics.rate_limit_delays += 1
    
    def record_error(self) -> None:
        """Record error."""
        self.metrics.errors += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            'uptime_seconds': self.metrics.uptime,
            'total_requests': self.metrics.request_count,
            'requests_per_second': self.metrics.request_count / self.metrics.uptime if self.metrics.uptime > 0 else 0,
            'average_request_time': self.metrics.average_request_time,
            'cache_hit_rate': self.metrics.cache_hit_rate,
            'rate_limit_delays': self.metrics.rate_limit_delays,
            'error_count': self.metrics.errors,
            'error_rate': self.metrics.errors / self.metrics.request_count * 100 if self.metrics.request_count > 0 else 0
        }
    
    def log_stats(self, level: int = logging.INFO) -> None:
        """Log performance statistics."""
        stats = self.get_stats()
        logger.log(level, f"Performance Stats: {stats}")
    
    def reset_stats(self) -> None:
        """Reset all statistics."""
        self.metrics = PerformanceMetrics()
        self._request_start_times.clear()


class BatchProcessor:
    """Process multiple operations in batches for better performance."""
    
    def __init__(self, max_workers: int = 5, batch_size: int = 10):
        self.max_workers = max_workers
        self.batch_size = batch_size
    
    def process_batch_sync(self, items: List[Any], processor_func: Callable, 
                          progress_callback: Optional[Callable] = None) -> List[Any]:
        """Process items in parallel batches synchronously.
        
        Args:
            items: Items to process
            processor_func: Function to process each item
            progress_callback: Optional callback for progress updates (current, total)
            
        Returns:
            List of processing results
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(processor_func, item): item 
                for item in items
            }
            
            # Collect results as they complete
            for i, future in enumerate(as_completed(future_to_item)):
                try:
                    result = future.result()
                    results.append(result)
                    
                    if progress_callback:
                        progress_callback(i + 1, len(items))
                        
                except Exception as e:
                    logger.error(f"Batch processing error for item {future_to_item[future]}: {e}")
                    results.append(None)  # Placeholder for failed item
        
        return results
    
    async def process_batch_async(self, items: List[Any], async_processor_func: Callable,
                                 progress_callback: Optional[Callable] = None) -> List[Any]:
        """Process items in parallel batches asynchronously.
        
        Args:
            items: Items to process
            async_processor_func: Async function to process each item
            progress_callback: Optional callback for progress updates (current, total)
            
        Returns:
            List of processing results
        """
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def bounded_processor(item):
            async with semaphore:
                return await async_processor_func(item)
        
        tasks = [bounded_processor(item) for item in items]
        results = []
        
        for i, task in enumerate(asyncio.as_completed(tasks)):
            try:
                result = await task
                results.append(result)
                
                if progress_callback:
                    progress_callback(i + 1, len(items))
                    
            except Exception as e:
                logger.error(f"Async batch processing error: {e}")
                results.append(None)
        
        return results


class ResponseStreamer:
    """Stream large responses to reduce memory usage."""
    
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
    
    def stream_search_results(self, search_func: Callable, search_params: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """Stream search results in chunks.
        
        Args:
            search_func: Function to call for search requests
            search_params: Base search parameters
            
        Yields:
            Individual records from the search results
        """
        current_cursor = search_params.get('s', '*')
        total_processed = 0
        
        while True:
            # Update cursor for this chunk
            chunk_params = search_params.copy()
            chunk_params['s'] = current_cursor
            chunk_params['n'] = min(self.chunk_size, chunk_params.get('n', self.chunk_size))
            
            try:
                result = search_func(**chunk_params)
                
                # Yield individual records
                for category in result.categories:
                    records = self._extract_records_from_category(category)
                    for record in records:
                        yield record
                        total_processed += 1
                
                # Check for next page
                if not result.cursors:
                    break
                    
                # Use cursor from first category (assuming single category for streaming)
                next_cursor = list(result.cursors.values())[0] if result.cursors else None
                if not next_cursor or next_cursor == current_cursor:
                    break  # No more results
                    
                current_cursor = next_cursor
                
            except Exception as e:
                logger.error(f"Error streaming results after {total_processed} records: {e}")
                break
                
        logger.info(f"Streamed {total_processed} total records")
    
    def _extract_records_from_category(self, category_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract records from category data."""
        records_data = category_data.get('records', {})
        category_code = category_data.get('code', '')
        
        # Different categories store records differently
        record_containers = {
            'book': 'work', 'image': 'work', 'magazine': 'work',
            'music': 'work', 'diary': 'work', 'research': 'work',
            'newspaper': 'article', 'gazette': 'article',
            'people': 'people', 'list': 'list'
        }
        
        container = record_containers.get(category_code, 'work')
        records = records_data.get(container, [])
        
        if isinstance(records, dict):
            records = [records]
        elif not isinstance(records, list):
            records = []
            
        return records


class ConnectionPool:
    """Manage HTTP connection pooling for better performance."""
    
    def __init__(self, pool_connections: int = 10, pool_maxsize: int = 10):
        self.pool_connections = pool_connections
        self.pool_maxsize = pool_maxsize
    
    def configure_httpx_limits(self) -> Dict[str, Any]:
        """Configure httpx client limits for optimal connection pooling.
        
        Returns:
            Dictionary of httpx limits configuration
        """
        return {
            'max_connections': self.pool_connections,
            'max_keepalive_connections': self.pool_maxsize,
            'keepalive_expiry': 30.0  # Keep connections alive for 30 seconds
        }


class RequestOptimizer:
    """Optimize request patterns for better performance."""
    
    @staticmethod
    def optimize_search_params(params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize search parameters for better performance.
        
        Args:
            params: Original search parameters
            
        Returns:
            Optimized search parameters
        """
        optimized = params.copy()
        
        # Use bulk harvest for large requests
        if optimized.get('n', 0) > 100:
            optimized['bulkHarvest'] = True
            logger.info("Enabled bulk harvest for large request")
        
        # Optimize facet requests
        if 'facet' in optimized:
            facets = optimized['facet']
            if isinstance(facets, list) and len(facets) > 5:
                # Limit facets for performance
                optimized['facet'] = facets[:5]
                logger.info(f"Limited facets to first 5 for performance: {optimized['facet']}")
        
        return optimized
    
    @staticmethod
    def should_use_cache(params: Dict[str, Any]) -> bool:
        """Determine if a request should use caching.
        
        Args:
            params: Request parameters
            
        Returns:
            True if the request should be cached
        """
        # Don't cache bulk harvest requests
        if params.get('bulkHarvest'):
            return False
            
        # Don't cache requests with cursors (pagination)
        if params.get('s') and params['s'] != '*':
            return False
            
        return True


class MemoryOptimizer:
    """Optimize memory usage for large operations."""
    
    @staticmethod
    def should_stream_response(params: Dict[str, Any], estimated_size: Optional[int] = None) -> bool:
        """Determine if response should be streamed to save memory.
        
        Args:
            params: Request parameters
            estimated_size: Estimated response size in records
            
        Returns:
            True if response should be streamed
        """
        # Stream large page sizes
        if params.get('n', 0) > 1000:
            return True
            
        # Stream if estimated size is large
        if estimated_size and estimated_size > 5000:
            return True
            
        return False
    
    @staticmethod
    def cleanup_cache_entry(entry: Any) -> None:
        """Clean up a cache entry to free memory.
        
        Args:
            entry: Cache entry to clean up
        """
        # For large responses, we could implement selective cleanup
        # This is a placeholder for more sophisticated memory management
        pass


# Global performance monitor
_global_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return _global_monitor


def log_performance_stats() -> None:
    """Log current performance statistics."""
    _global_monitor.log_stats()