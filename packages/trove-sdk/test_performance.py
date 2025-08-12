#!/usr/bin/env python3
"""Test performance optimizations and monitoring."""

import time
from trove.performance import (
    PerformanceMonitor, 
    BatchProcessor, 
    RequestOptimizer,
    ConnectionPool,
    get_performance_monitor
)

def test_performance_monitor():
    """Test performance monitoring functionality."""
    print("=== Performance Monitor Test ===")
    
    monitor = PerformanceMonitor()
    
    # Simulate some requests
    for i in range(5):
        request_id = f"test_request_{i}"
        monitor.start_request(request_id)
        time.sleep(0.01)  # Simulate request time
        monitor.end_request(request_id)
    
    # Simulate cache hits and misses
    for _ in range(3):
        monitor.record_cache_hit()
    for _ in range(2):
        monitor.record_cache_miss()
    
    # Get stats
    stats = monitor.get_stats()
    print(f"Total requests: {stats['total_requests']}")
    print(f"Average request time: {stats['average_request_time']:.4f}s")
    print(f"Cache hit rate: {stats['cache_hit_rate']:.1f}%")
    print(f"Requests per second: {stats['requests_per_second']:.2f}")
    print()

def test_batch_processor():
    """Test batch processing functionality."""
    print("=== Batch Processor Test ===")
    
    processor = BatchProcessor(max_workers=3)
    
    def dummy_task(item):
        """Simulate processing work."""
        time.sleep(0.01)
        return item * 2
    
    items = list(range(10))
    start_time = time.time()
    
    results = processor.process_batch_sync(
        items, 
        dummy_task,
        progress_callback=lambda current, total: print(f"Progress: {current}/{total}")
    )
    
    end_time = time.time()
    print(f"Processed {len(results)} items in {end_time - start_time:.2f}s")
    print(f"Results: {results}")
    print()

def test_request_optimizer():
    """Test request optimization."""
    print("=== Request Optimizer Test ===")
    
    # Test optimization of large requests
    large_params = {
        'category': ['book'],
        'q': 'test',
        'n': 200,  # Large page size
        'facet': ['decade', 'format', 'language', 'subject', 'creator', 'publisher']  # Many facets
    }
    
    optimized = RequestOptimizer.optimize_search_params(large_params)
    
    print("Original params:")
    for key, value in large_params.items():
        print(f"  {key}: {value}")
    
    print("Optimized params:")
    for key, value in optimized.items():
        print(f"  {key}: {value}")
    
    print(f"Bulk harvest enabled: {optimized.get('bulkHarvest', False)}")
    print(f"Facets limited: {len(optimized.get('facet', []))} facets")
    print()

def test_connection_pool():
    """Test connection pool configuration."""
    print("=== Connection Pool Test ===")
    
    pool = ConnectionPool(pool_connections=15, pool_maxsize=15)
    limits = pool.configure_httpx_limits()
    
    print("Connection pool limits:")
    for key, value in limits.items():
        print(f"  {key}: {value}")
    print()

def test_global_monitor():
    """Test global performance monitor."""
    print("=== Global Monitor Test ===")
    
    monitor = get_performance_monitor()
    
    # Simulate some activity
    monitor.record_request(0.05)  # 50ms request
    monitor.record_cache_hit()
    monitor.record_error()
    
    stats = monitor.get_stats()
    print("Global monitor stats:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    print()

if __name__ == "__main__":
    print("Testing performance optimizations...")
    test_performance_monitor()
    test_batch_processor() 
    test_request_optimizer()
    test_connection_pool()
    test_global_monitor()
    print("Performance optimization tests completed!")