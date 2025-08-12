"""Production configuration and deployment utilities."""

import os
from typing import Dict, Any, Optional
from .config import TroveConfig
from .logging import configure_production_logging, configure_development_logging
from .performance import get_performance_monitor


class ProductionConfig:
    """Production-ready configuration management."""
    
    @staticmethod
    def create_config(environment: str = "production") -> TroveConfig:
        """Create production configuration.
        
        Args:
            environment: Target environment ('production', 'development', 'testing')
            
        Returns:
            Configured TroveConfig instance
        """
        
        config_overrides = {}
        
        if environment == "production":
            config_overrides.update({
                'rate_limit': 1.5,  # Conservative rate limiting
                'max_retries': 5,
                'cache_backend': 'sqlite',
                'log_requests': False,  # Disable request logging in prod
                'redact_credentials': True
            })
        elif environment == "development":
            config_overrides.update({
                'rate_limit': 0.5,  # Very conservative for development
                'cache_backend': 'memory',
                'log_requests': True
            })
        elif environment == "testing":
            config_overrides.update({
                'rate_limit': 10.0,  # Higher limits for testing
                'cache_backend': 'memory',
                'log_requests': False
            })
        
        # Override with environment variables
        env_config = {
            'api_key': os.environ.get('TROVE_API_KEY'),
            'base_url': os.environ.get('TROVE_BASE_URL', 'https://api.trove.nla.gov.au'),
            'rate_limit': float(os.environ.get('TROVE_RATE_LIMIT', config_overrides.get('rate_limit', 2.0))),
            'cache_backend': os.environ.get('TROVE_CACHE_BACKEND', config_overrides.get('cache_backend', 'memory'))
        }
        
        # Remove None values
        env_config = {k: v for k, v in env_config.items() if v is not None}
        
        # Merge configurations
        final_config = {**config_overrides, **env_config}
        
        return TroveConfig(**final_config)


def setup_production_environment(environment: str = "production") -> Dict[str, Any]:
    """Set up production environment with monitoring and logging.
    
    Args:
        environment: Target environment ('production', 'development', 'testing')
        
    Returns:
        Dictionary containing setup components
    """
    
    # Configure logging based on environment
    if environment == "production":
        log_level = os.environ.get('TROVE_LOG_LEVEL', 'INFO')
        log_file = os.environ.get('TROVE_LOG_FILE')
        logger = configure_production_logging(
            log_level=log_level,
            log_file=log_file,
            enable_performance_logs=True
        )
    else:
        log_level = os.environ.get('TROVE_LOG_LEVEL', 'DEBUG')
        logger = configure_development_logging(log_level=log_level)
    
    # Set up performance monitoring
    monitor = get_performance_monitor()
    
    # Create production config
    config = ProductionConfig.create_config(environment)
    
    # Log environment setup
    logger.info(f"Trove SDK environment configured: {environment}")
    
    return {
        'config': config,
        'monitor': monitor,
        'environment': environment,
        'logger': logger
    }


def validate_production_setup() -> Dict[str, bool]:
    """Validate production setup and return status.
    
    Returns:
        Dictionary with validation results
    """
    
    validation_results = {}
    
    # Check API key
    api_key = os.environ.get('TROVE_API_KEY')
    validation_results['api_key_present'] = bool(api_key)
    validation_results['api_key_valid_format'] = bool(api_key and len(api_key) > 10)
    
    # Check logging configuration
    log_file = os.environ.get('TROVE_LOG_FILE')
    if log_file:
        try:
            # Test write access to log file
            with open(log_file, 'a') as f:
                pass
            validation_results['log_file_writable'] = True
        except (IOError, OSError):
            validation_results['log_file_writable'] = False
    else:
        validation_results['log_file_writable'] = True  # Using stdout
    
    # Check cache directory for SQLite backend
    cache_backend = os.environ.get('TROVE_CACHE_BACKEND', 'memory')
    if cache_backend == 'sqlite':
        cache_dir = os.environ.get('TROVE_CACHE_DIR', './cache')
        try:
            os.makedirs(cache_dir, exist_ok=True)
            validation_results['cache_directory_accessible'] = True
        except (IOError, OSError):
            validation_results['cache_directory_accessible'] = False
    else:
        validation_results['cache_directory_accessible'] = True
    
    # Check rate limiting configuration
    try:
        rate_limit = float(os.environ.get('TROVE_RATE_LIMIT', 2.0))
        validation_results['rate_limit_valid'] = 0.1 <= rate_limit <= 10.0
    except (ValueError, TypeError):
        validation_results['rate_limit_valid'] = False
    
    return validation_results


class HealthCheck:
    """Health check utilities for production monitoring."""
    
    def __init__(self, client):
        self.client = client
        
    def basic_health_check(self) -> Dict[str, Any]:
        """Perform basic health check.
        
        Returns:
            Health check results
        """
        
        health_status = {
            'timestamp': None,
            'status': 'unknown',
            'checks': {}
        }
        
        from datetime import datetime
        health_status['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        try:
            # Test basic API connectivity
            test_result = self.client.raw_search.page(
                category=['book'],
                q='test',
                n=1
            )
            
            health_status['checks']['api_connectivity'] = {
                'status': 'pass',
                'response_time_ms': None,  # Would need timing
                'total_results': test_result.total_results
            }
            
            # Test cache functionality
            cache_key = 'health_check_test'
            self.client._transport.cache.set(cache_key, 'test_value', ttl=10)
            cached_value = self.client._transport.cache.get(cache_key)
            
            health_status['checks']['cache'] = {
                'status': 'pass' if cached_value == 'test_value' else 'fail'
            }
            
            # Test rate limiter
            rate_limiter_healthy = self.client._transport.rate_limiter.acquire(timeout=0.1)
            if rate_limiter_healthy:
                self.client._transport.rate_limiter.release()
            
            health_status['checks']['rate_limiter'] = {
                'status': 'pass' if rate_limiter_healthy else 'fail'
            }
            
            # Overall status
            all_pass = all(
                check['status'] == 'pass' 
                for check in health_status['checks'].values()
            )
            health_status['status'] = 'pass' if all_pass else 'fail'
            
        except Exception as e:
            health_status['status'] = 'fail'
            health_status['error'] = str(e)
            health_status['checks']['api_connectivity'] = {
                'status': 'fail',
                'error': str(e)
            }
        
        return health_status
    
    def detailed_health_check(self) -> Dict[str, Any]:
        """Perform detailed health check with performance metrics.
        
        Returns:
            Detailed health check results
        """
        
        basic_health = self.basic_health_check()
        
        # Add performance metrics
        monitor = get_performance_monitor()
        performance_stats = monitor.get_stats()
        
        basic_health['performance'] = performance_stats
        
        # Add configuration validation
        validation_results = validate_production_setup()
        basic_health['configuration'] = validation_results
        
        return basic_health


def create_deployment_manifest() -> Dict[str, Any]:
    """Create deployment manifest with version and configuration info.
    
    Returns:
        Deployment manifest
    """
    
    from . import __version__
    from datetime import datetime
    
    manifest = {
        'name': 'trove-sdk',
        'version': __version__,
        'build_time': datetime.utcnow().isoformat() + 'Z',
        'python_version': None,
        'dependencies': {},
        'environment_variables': {
            'required': [
                'TROVE_API_KEY'
            ],
            'optional': [
                'TROVE_RATE_LIMIT',
                'TROVE_CACHE_BACKEND',
                'TROVE_LOG_LEVEL',
                'TROVE_LOG_FILE',
                'TROVE_CACHE_DIR'
            ]
        },
        'endpoints': [
            'https://api.trove.nla.gov.au/v3/result',
            'https://api.trove.nla.gov.au/v3/work',
            'https://api.trove.nla.gov.au/v3/newspaper',
            'https://api.trove.nla.gov.au/v3/gazette',
            'https://api.trove.nla.gov.au/v3/people',
            'https://api.trove.nla.gov.au/v3/list'
        ]
    }
    
    # Add Python version
    import sys
    manifest['python_version'] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    # Add key dependencies (would normally read from requirements)
    try:
        import httpx
        manifest['dependencies']['httpx'] = httpx.__version__
    except (ImportError, AttributeError):
        pass
    
    try:
        import pydantic
        manifest['dependencies']['pydantic'] = pydantic.__version__
    except (ImportError, AttributeError):
        pass
    
    return manifest


# Production utilities
def get_production_client():
    """Get a production-ready TroveClient instance."""
    from .client import TroveClient
    
    setup_result = setup_production_environment()
    return TroveClient(setup_result['config'])


def monitor_performance(client, operation_name: str):
    """Context manager for monitoring operation performance."""
    
    class PerformanceMonitor:
        def __init__(self, client, operation_name):
            self.client = client
            self.operation_name = operation_name
            self.start_time = None
        
        def __enter__(self):
            import time
            from .logging import performance_logger
            
            self.start_time = time.time()
            performance_logger.info(f"Starting operation: {self.operation_name}")
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            import time
            from .logging import performance_logger
            
            duration = time.time() - self.start_time
            
            if exc_type is None:
                performance_logger.log_performance(
                    f"Operation completed: {self.operation_name}",
                    {'duration_seconds': duration, 'status': 'success'}
                )
            else:
                performance_logger.log_performance(
                    f"Operation failed: {self.operation_name}",
                    {'duration_seconds': duration, 'status': 'error', 'error': str(exc_val)}
                )
    
    return PerformanceMonitor(client, operation_name)