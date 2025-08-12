#!/usr/bin/env python3
"""Performance benchmarks and quality assurance tests."""

import time
import os
import sys
from typing import List, Dict, Any
import statistics
from contextlib import contextmanager

# Add the trove package to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

try:
    from trove import TroveClient
    from trove.models import Work, Article
    from trove.performance import get_performance_monitor, BatchProcessor
    from trove.production import get_production_client, monitor_performance
except ImportError as e:
    print(f"Could not import trove modules: {e}")
    sys.exit(1)


@contextmanager
def benchmark_timer():
    """Context manager for timing operations."""
    start_time = time.time()
    yield lambda: time.time() - start_time
    

class BenchmarkSuite:
    """Performance benchmark suite."""
    
    def __init__(self, client=None):
        self.client = client
        self.results = {}
    
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmarks and return results."""
        print("Running performance benchmarks...")
        
        # Memory and CPU benchmarks (no API required)
        self.benchmark_model_creation()
        self.benchmark_batch_processing()
        self.benchmark_performance_monitoring()
        
        # API benchmarks (require API key)
        if self.client and os.environ.get('TROVE_API_KEY'):
            self.benchmark_client_creation()
            self.benchmark_search_performance()
            self.benchmark_resource_access()
            self.benchmark_connection_reuse()
        else:
            print("Skipping API benchmarks (no client/API key)")
        
        return self.results
    
    def benchmark_model_creation(self):
        """Benchmark model creation and access."""
        print("  - Model creation and access...")
        
        # Test data
        work_data = {
            'id': '123456',
            'title': 'Test Work Title',
            'contributor': ['Author, Test', 'Another, Author'],
            'issued': '2020',
            'type': ['Book'],
            'subject': ['History', 'Australia']
        }
        
        # Benchmark model creation
        times = []
        for _ in range(1000):
            with benchmark_timer() as timer:
                work = Work(**work_data)
                # Access some properties
                _ = work.primary_title
                _ = work.publication_year
                _ = work.primary_contributor
            times.append(timer())
        
        self.results['model_creation'] = {
            'iterations': 1000,
            'avg_time_ms': statistics.mean(times) * 1000,
            'min_time_ms': min(times) * 1000,
            'max_time_ms': max(times) * 1000,
            'std_dev_ms': statistics.stdev(times) * 1000 if len(times) > 1 else 0
        }
    
    def benchmark_batch_processing(self):
        """Benchmark batch processing performance."""
        print("  - Batch processing...")
        
        processor = BatchProcessor(max_workers=3)
        
        def dummy_task(item):
            time.sleep(0.001)  # Simulate 1ms of work
            return item * 2
        
        items = list(range(50))
        
        with benchmark_timer() as timer:
            results = processor.process_batch_sync(items, dummy_task)
        
        batch_time = timer()
        
        self.results['batch_processing'] = {
            'items_processed': len(items),
            'total_time_ms': batch_time * 1000,
            'items_per_second': len(items) / batch_time,
            'results_count': len(results)
        }
    
    def benchmark_performance_monitoring(self):
        """Benchmark performance monitoring overhead."""
        print("  - Performance monitoring overhead...")
        
        monitor = get_performance_monitor()
        
        # Benchmark without monitoring
        times_without = []
        for i in range(100):
            with benchmark_timer() as timer:
                # Simulate some work
                _ = sum(range(100))
            times_without.append(timer())
        
        # Benchmark with monitoring
        times_with = []
        for i in range(100):
            request_id = f"test_request_{i}"
            with benchmark_timer() as timer:
                monitor.start_request(request_id)
                # Simulate some work
                _ = sum(range(100))
                monitor.end_request(request_id)
            times_with.append(timer())
        
        avg_without = statistics.mean(times_without)
        avg_with = statistics.mean(times_with)
        overhead = ((avg_with - avg_without) / avg_without) * 100 if avg_without > 0 else 0
        
        self.results['monitoring_overhead'] = {
            'avg_time_without_ms': avg_without * 1000,
            'avg_time_with_ms': avg_with * 1000,
            'overhead_percent': overhead
        }
    
    def benchmark_client_creation(self):
        """Benchmark client creation time."""
        print("  - Client creation...")
        
        times = []
        for _ in range(10):
            with benchmark_timer() as timer:
                client = TroveClient.from_env()
                client.close()
            times.append(timer())
        
        self.results['client_creation'] = {
            'iterations': 10,
            'avg_time_ms': statistics.mean(times) * 1000,
            'min_time_ms': min(times) * 1000,
            'max_time_ms': max(times) * 1000
        }
    
    def benchmark_search_performance(self):
        """Benchmark search performance."""
        print("  - Search performance...")
        
        times = []
        result_counts = []
        
        for i in range(5):  # 5 searches to avoid rate limiting
            with benchmark_timer() as timer:
                result = (self.client.search()
                         .text(f"test {i}")
                         .in_("book")
                         .page_size(10)
                         .first_page())
                result_counts.append(result.total_results)
            times.append(timer())
            
            # Small delay to avoid rate limiting
            time.sleep(0.6)
        
        self.results['search_performance'] = {
            'iterations': len(times),
            'avg_time_ms': statistics.mean(times) * 1000,
            'min_time_ms': min(times) * 1000,
            'max_time_ms': max(times) * 1000,
            'avg_results_returned': statistics.mean(result_counts)
        }
    
    def benchmark_resource_access(self):
        """Benchmark direct resource access."""
        print("  - Resource access...")
        
        # Test with a known work ID (using a common test ID)
        test_work_id = "123456789"  # This might not exist, but we'll measure the attempt
        
        times = []
        success_count = 0
        
        for _ in range(3):  # Limited to avoid rate limiting
            with benchmark_timer() as timer:
                try:
                    work = self.client.work.get(test_work_id)
                    success_count += 1
                except Exception:
                    pass  # We're just measuring timing
            times.append(timer())
            
            time.sleep(0.6)  # Rate limit delay
        
        self.results['resource_access'] = {
            'iterations': len(times),
            'avg_time_ms': statistics.mean(times) * 1000,
            'success_rate': success_count / len(times),
            'min_time_ms': min(times) * 1000,
            'max_time_ms': max(times) * 1000
        }
    
    def benchmark_connection_reuse(self):
        """Benchmark connection reuse efficiency."""
        print("  - Connection reuse...")
        
        # Multiple requests with same client (should reuse connections)
        with benchmark_timer() as timer:
            for i in range(5):
                try:
                    result = (self.client.search()
                             .text("poetry")
                             .in_("book")
                             .page_size(5)
                             .first_page())
                except Exception:
                    pass
                time.sleep(0.6)  # Rate limit delay
        
        total_time = timer()
        
        self.results['connection_reuse'] = {
            'total_requests': 5,
            'total_time_ms': total_time * 1000,
            'avg_time_per_request_ms': (total_time / 5) * 1000
        }


class QualityAssuranceTests:
    """Quality assurance tests for production readiness."""
    
    def __init__(self, client=None):
        self.client = client
        self.test_results = {}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all QA tests."""
        print("Running quality assurance tests...")
        
        self.test_memory_usage()
        self.test_error_handling_robustness()
        self.test_model_backward_compatibility()
        
        if self.client and os.environ.get('TROVE_API_KEY'):
            self.test_api_error_recovery()
            self.test_rate_limiting()
        
        return self.test_results
    
    def test_memory_usage(self):
        """Test memory usage patterns."""
        print("  - Memory usage...")
        
        import gc
        import sys
        
        # Force garbage collection
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Create many model instances
        works = []
        for i in range(1000):
            work_data = {
                'id': f'work_{i}',
                'title': f'Test Work {i}',
                'contributor': [f'Author {i}'],
                'issued': '2020'
            }
            works.append(Work(**work_data))
        
        # Check object count
        gc.collect()
        peak_objects = len(gc.get_objects())
        
        # Clear references
        works.clear()
        del works
        
        # Force cleanup
        gc.collect()
        final_objects = len(gc.get_objects())
        
        self.test_results['memory_usage'] = {
            'initial_objects': initial_objects,
            'peak_objects': peak_objects,
            'final_objects': final_objects,
            'objects_created': peak_objects - initial_objects,
            'objects_cleaned': peak_objects - final_objects,
            'cleanup_efficiency': ((peak_objects - final_objects) / (peak_objects - initial_objects)) * 100
        }
    
    def test_error_handling_robustness(self):
        """Test error handling robustness."""
        print("  - Error handling...")
        
        from trove.exceptions import ValidationError
        from trove.errors import ErrorRecovery
        
        test_cases = [
            ValidationError("Invalid parameter 'test'"),
            ValidationError("Invalid categories: invalid_category"),
            Exception("Generic error"),
        ]
        
        successful_suggestions = 0
        
        for error in test_cases:
            suggestions = ErrorRecovery.suggest_fixes_for_error(error)
            if suggestions:
                successful_suggestions += 1
        
        self.test_results['error_handling'] = {
            'test_cases': len(test_cases),
            'successful_suggestions': successful_suggestions,
            'suggestion_rate': (successful_suggestions / len(test_cases)) * 100
        }
    
    def test_model_backward_compatibility(self):
        """Test model backward compatibility."""
        print("  - Model backward compatibility...")
        
        work_data = {
            'id': '123456',
            'title': 'Test Work',
            'contributor': ['Author, Test'],
            'issued': '2020',
            'newField': 'This is a new field added to the API'
        }
        
        work = Work(**work_data)
        
        # Test both access methods work
        compatibility_tests = [
            # Dict-like access
            work['title'] == 'Test Work',
            work.get('issued') == '2020',
            'newField' in work,
            work['newField'] == 'This is a new field added to the API',
            
            # Model access
            work.primary_title == 'Test Work',
            work.publication_year == 2020,
            
            # Raw access
            'newField' in work.raw,
            work.raw['newField'] == 'This is a new field added to the API'
        ]
        
        passed_tests = sum(compatibility_tests)
        
        self.test_results['backward_compatibility'] = {
            'total_tests': len(compatibility_tests),
            'passed_tests': passed_tests,
            'success_rate': (passed_tests / len(compatibility_tests)) * 100
        }
    
    def test_api_error_recovery(self):
        """Test API error recovery."""
        print("  - API error recovery...")
        
        recovery_attempts = 0
        successful_recoveries = 0
        
        # Test with invalid resource ID
        try:
            self.client.work.get("definitely_nonexistent_id_12345")
        except Exception as e:
            recovery_attempts += 1
            
            # Check if error has suggestions
            if hasattr(e, 'response_data') and e.response_data:
                suggestions = e.response_data.get('suggestions', [])
                if suggestions:
                    successful_recoveries += 1
        
        self.test_results['api_error_recovery'] = {
            'recovery_attempts': recovery_attempts,
            'successful_recoveries': successful_recoveries,
            'recovery_rate': (successful_recoveries / recovery_attempts * 100) if recovery_attempts > 0 else 0
        }
    
    def test_rate_limiting(self):
        """Test rate limiting behavior."""
        print("  - Rate limiting...")
        
        # Get rate limiter stats before
        monitor = get_performance_monitor()
        initial_delays = monitor.metrics.rate_limit_delays
        
        # Make several rapid requests (should trigger rate limiting)
        requests_made = 0
        for i in range(3):
            try:
                result = (self.client.search()
                         .text("test")
                         .in_("book")
                         .page_size(1)
                         .first_page())
                requests_made += 1
            except Exception:
                pass
            # No delay between requests to test rate limiting
        
        final_delays = monitor.metrics.rate_limit_delays
        rate_limit_triggered = final_delays > initial_delays
        
        self.test_results['rate_limiting'] = {
            'requests_made': requests_made,
            'rate_limit_delays': final_delays - initial_delays,
            'rate_limiting_active': rate_limit_triggered
        }


def print_benchmark_results(results: Dict[str, Any]):
    """Print benchmark results in a readable format."""
    print("\n=== Benchmark Results ===")
    
    for test_name, metrics in results.items():
        print(f"\n{test_name.replace('_', ' ').title()}:")
        for metric, value in metrics.items():
            if isinstance(value, float):
                if 'ms' in metric:
                    print(f"  {metric}: {value:.3f}ms")
                elif 'percent' in metric:
                    print(f"  {metric}: {value:.2f}%")
                else:
                    print(f"  {metric}: {value:.3f}")
            else:
                print(f"  {metric}: {value}")


def print_qa_results(results: Dict[str, Any]):
    """Print QA test results."""
    print("\n=== Quality Assurance Results ===")
    
    for test_name, metrics in results.items():
        print(f"\n{test_name.replace('_', ' ').title()}:")
        for metric, value in metrics.items():
            if isinstance(value, float) and 'rate' in metric:
                status = "✓" if value >= 80 else "⚠" if value >= 60 else "✗"
                print(f"  {status} {metric}: {value:.1f}%")
            else:
                print(f"  {metric}: {value}")


def main():
    """Run all benchmarks and QA tests."""
    print("Trove SDK Performance Benchmarks and Quality Assurance")
    print("=" * 60)
    
    # Create client if API key available
    client = None
    if os.environ.get('TROVE_API_KEY'):
        client = TroveClient.from_env()
    
    try:
        # Run benchmarks
        benchmark_suite = BenchmarkSuite(client)
        benchmark_results = benchmark_suite.run_all_benchmarks()
        
        # Run QA tests
        qa_suite = QualityAssuranceTests(client)
        qa_results = qa_suite.run_all_tests()
        
        # Print results
        print_benchmark_results(benchmark_results)
        print_qa_results(qa_results)
        
        # Summary
        print(f"\n=== Summary ===")
        print(f"Benchmarks completed: {len(benchmark_results)}")
        print(f"QA tests completed: {len(qa_results)}")
        
        # Check if all QA tests passed
        qa_scores = []
        for test_results in qa_results.values():
            for metric, value in test_results.items():
                if 'rate' in metric and isinstance(value, (int, float)):
                    qa_scores.append(value)
        
        if qa_scores:
            avg_qa_score = sum(qa_scores) / len(qa_scores)
            print(f"Average QA score: {avg_qa_score:.1f}%")
            
            if avg_qa_score >= 90:
                print("🎉 Excellent quality! Production ready.")
            elif avg_qa_score >= 80:
                print("✅ Good quality. Minor improvements recommended.")
            elif avg_qa_score >= 70:
                print("⚠️  Acceptable quality. Some improvements needed.")
            else:
                print("❌ Quality improvements required before production.")
        
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    main()