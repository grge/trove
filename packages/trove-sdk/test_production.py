#!/usr/bin/env python3
"""Test production features and configuration."""

import os
import json
from trove.production import (
    ProductionConfig,
    setup_production_environment,
    validate_production_setup,
    create_deployment_manifest,
    get_production_client,
    monitor_performance
)

def test_production_config():
    """Test production configuration creation."""
    print("=== Production Config Test ===")
    
    # Set a test API key for configuration testing
    os.environ['TROVE_API_KEY'] = 'test_key_for_config_testing'
    
    try:
        # Test different environments
        environments = ["production", "development", "testing"]
        
        for env in environments:
            config = ProductionConfig.create_config(env)
            
            print(f"{env.title()} configuration:")
            print(f"  Rate limit: {config.rate_limit} req/sec")
            print(f"  Cache backend: {config.cache_backend}")
            print(f"  Max retries: {config.max_retries}")
            print()
    finally:
        # Clean up test key if it was set for testing
        if os.environ.get('TROVE_API_KEY') == 'test_key_for_config_testing':
            del os.environ['TROVE_API_KEY']

def test_environment_setup():
    """Test environment setup."""
    print("=== Environment Setup Test ===")
    
    # Set a test API key for environment setup testing
    os.environ['TROVE_API_KEY'] = 'test_key_for_setup_testing'
    
    try:
        # Test development setup
        setup_result = setup_production_environment("development")
        
        print("Development environment setup:")
        print(f"  Environment: {setup_result['environment']}")
        print(f"  Config rate limit: {setup_result['config'].rate_limit}")
        print(f"  Monitor class: {type(setup_result['monitor']).__name__}")
        print()
    finally:
        # Clean up test key
        if os.environ.get('TROVE_API_KEY') == 'test_key_for_setup_testing':
            del os.environ['TROVE_API_KEY']

def test_validation():
    """Test production setup validation."""
    print("=== Validation Test ===")
    
    validation_results = validate_production_setup()
    
    print("Production setup validation:")
    for check, result in validation_results.items():
        status = "✓" if result else "✗"
        print(f"  {status} {check}: {result}")
    print()

def test_deployment_manifest():
    """Test deployment manifest creation."""
    print("=== Deployment Manifest Test ===")
    
    manifest = create_deployment_manifest()
    
    print("Deployment manifest created:")
    print(f"  Name: {manifest['name']}")
    print(f"  Version: {manifest['version']}")
    print(f"  Python version: {manifest['python_version']}")
    print(f"  Required env vars: {len(manifest['environment_variables']['required'])}")
    print(f"  Optional env vars: {len(manifest['environment_variables']['optional'])}")
    print(f"  API endpoints: {len(manifest['endpoints'])}")
    print(f"  Dependencies: {list(manifest['dependencies'].keys())}")
    print()

def test_performance_monitoring():
    """Test performance monitoring context manager."""
    print("=== Performance Monitoring Test ===")
    
    # Mock client for testing
    class MockClient:
        pass
    
    client = MockClient()
    
    try:
        with monitor_performance(client, "test_operation"):
            # Simulate some work
            import time
            time.sleep(0.01)
            print("  Operation completed successfully")
    except Exception as e:
        print(f"  Operation failed: {e}")
    
    print()

def test_health_check():
    """Test health check functionality (if API key available)."""
    print("=== Health Check Test ===")
    
    if os.environ.get('TROVE_API_KEY'):
        try:
            from trove.production import HealthCheck
            client = get_production_client()
            health_checker = HealthCheck(client)
            
            # Basic health check
            basic_health = health_checker.basic_health_check()
            print(f"Health check status: {basic_health['status']}")
            print(f"Checks performed: {list(basic_health['checks'].keys())}")
            
            client.close()
        except Exception as e:
            print(f"Health check failed: {e}")
    else:
        print("Skipping health check (no API key)")
    
    print()

if __name__ == "__main__":
    print("Testing production features...")
    test_production_config()
    test_environment_setup()
    test_validation()
    test_deployment_manifest()
    test_performance_monitoring()
    test_health_check()
    print("Production feature tests completed!")