#!/usr/bin/env python3
"""Test production logging functionality."""

import json
import io
import sys
import logging
from contextlib import redirect_stdout, redirect_stderr

from trove.logging import (
    configure_logging,
    configure_production_logging,
    configure_development_logging,
    ContextualLogger,
    TroveFormatter,
    transport_logger,
    get_logger
)

def test_json_formatter():
    """Test JSON log formatting."""
    print("=== JSON Formatter Test ===")
    
    # Create a string buffer to capture logs
    log_buffer = io.StringIO()
    
    # Configure logger to write to buffer
    logger = logging.getLogger('test.json')
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    
    handler = logging.StreamHandler(log_buffer)
    handler.setFormatter(TroveFormatter(json_format=True))
    logger.addHandler(handler)
    
    # Create log record with context
    record = logger.makeRecord(
        'test.json', logging.INFO, __file__, 42, "Test message with context", (), None
    )
    record.trove_context = {"endpoint": "/test", "user_id": "12345"}
    record.request_id = "req_123"
    
    # Log the record
    logger.handle(record)
    
    # Parse the JSON output
    log_output = log_buffer.getvalue().strip()
    try:
        log_data = json.loads(log_output)
        print("JSON log parsed successfully:")
        print(f"  Level: {log_data['level']}")
        print(f"  Message: {log_data['message']}")
        print(f"  Context: {log_data.get('context', {})}")
        print(f"  Request ID: {log_data.get('request_id')}")
        print(f"  Timestamp: {log_data['timestamp']}")
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON log: {e}")
        print(f"Raw output: {log_output}")
    print()

def test_text_formatter():
    """Test text log formatting.""" 
    print("=== Text Formatter Test ===")
    
    # Create a string buffer to capture logs
    log_buffer = io.StringIO()
    
    # Configure logger to write to buffer
    logger = logging.getLogger('test.text')
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    
    handler = logging.StreamHandler(log_buffer)
    handler.setFormatter(TroveFormatter(json_format=False))
    logger.addHandler(handler)
    
    # Create log record with context
    record = logger.makeRecord(
        'test.text', logging.INFO, __file__, 42, "Test message with context", (), None
    )
    record.trove_context = {"endpoint": "/test", "user_id": "12345"}
    record.request_id = "req_123"
    
    # Log the record
    logger.handle(record)
    
    # Show the text output
    log_output = log_buffer.getvalue().strip()
    print("Text log output:")
    print(f"  {log_output}")
    print()

def test_contextual_logger():
    """Test contextual logger functionality."""
    print("=== Contextual Logger Test ===")
    
    # Create contextual logger
    ctx_logger = ContextualLogger('test.contextual')
    
    # Set global context
    ctx_logger.set_context(service="trove-sdk", version="1.0.0")
    ctx_logger.set_request_id("req_456")
    
    # Capture logs to buffer for testing
    log_buffer = io.StringIO()
    handler = logging.StreamHandler(log_buffer)
    handler.setFormatter(TroveFormatter(json_format=True))
    
    ctx_logger.logger.handlers.clear()
    ctx_logger.logger.addHandler(handler)
    ctx_logger.logger.setLevel(logging.INFO)
    
    # Log messages with additional context
    ctx_logger.info("Processing search request", query="Australian history", category="book")
    ctx_logger.warning("Rate limit approaching", remaining_requests=5)
    
    # Parse and display logs
    log_lines = log_buffer.getvalue().strip().split('\n')
    for i, line in enumerate(log_lines):
        if line:
            try:
                log_data = json.loads(line)
                print(f"Log {i+1}:")
                print(f"  Message: {log_data['message']}")
                print(f"  Context: {log_data.get('context', {})}")
                print(f"  Request ID: {log_data.get('request_id')}")
            except json.JSONDecodeError:
                print(f"Failed to parse log line: {line}")
    print()

def test_production_config():
    """Test production logging configuration."""
    print("=== Production Config Test ===")
    
    # Configure for production
    prod_logger = configure_production_logging(
        log_level="INFO",
        enable_performance_logs=True
    )
    
    print(f"Production logger level: {prod_logger.level}")
    print(f"Production logger handlers: {len(prod_logger.handlers)}")
    
    # Test structured logging
    transport_logger.info(
        "API request completed",
        endpoint="/result",
        duration_ms=150,
        cache_hit=True
    )
    print("Production log message sent successfully")
    print()

def test_development_config():
    """Test development logging configuration."""
    print("=== Development Config Test ===")
    
    # Configure for development
    dev_logger = configure_development_logging(log_level="DEBUG")
    
    print(f"Development logger level: {dev_logger.level}")
    print(f"Development logger handlers: {len(dev_logger.handlers)}")
    
    # Test that debug logs are captured
    debug_logger = get_logger('test.debug')
    debug_logger.debug("Debug message for development", step="initialization")
    print("Development debug log sent successfully")
    print()

def test_performance_logging():
    """Test performance logging."""
    print("=== Performance Logging Test ===")
    
    # Create performance logger
    perf_logger = get_logger('performance')
    
    # Log performance metrics
    metrics = {
        'request_count': 150,
        'average_response_time': 0.25,
        'cache_hit_rate': 85.5,
        'error_rate': 2.1
    }
    
    perf_logger.log_performance(
        "Hourly performance summary",
        metrics,
        service="trove-search"
    )
    
    print("Performance metrics logged successfully")
    print()

if __name__ == "__main__":
    print("Testing production logging functionality...")
    test_json_formatter()
    test_text_formatter() 
    test_contextual_logger()
    test_production_config()
    test_development_config()
    test_performance_logging()
    print("Production logging tests completed!")