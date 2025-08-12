#!/usr/bin/env python3
"""Test enhanced error handling functionality."""

import os
from trove import TroveClient
from trove.exceptions import ValidationError, ResourceNotFoundError, TroveAPIError
from trove.errors import ErrorRecovery, enhance_exception_message, set_debug_mode

def test_validation_error_suggestions():
    """Test enhanced validation error suggestions."""
    print("=== Validation Error Suggestions Test ===")
    
    try:
        client = TroveClient.from_env()
        # Try invalid category to trigger validation error
        client.search().in_("invalid_category").first_page()
    except ValidationError as e:
        suggestions = ErrorRecovery.suggest_fixes_for_error(e)
        print(f"Validation Error: {e}")
        print("Suggestions:")
        for suggestion in suggestions:
            print(f"  - {suggestion}")
        print()

def test_not_found_error_suggestions():
    """Test resource not found error suggestions."""
    print("=== Resource Not Found Error Suggestions Test ===")
    
    try:
        client = TroveClient.from_env()
        # Try to get a non-existent work
        client.work.get("nonexistent123456789")
    except ResourceNotFoundError as e:
        suggestions = ErrorRecovery.suggest_fixes_for_error(e)
        print(f"Not Found Error: {e}")
        print("Suggestions:")
        for suggestion in suggestions:
            print(f"  - {suggestion}")
        print()

def test_enhanced_message():
    """Test enhanced exception messages."""
    print("=== Enhanced Exception Messages Test ===")
    
    try:
        raise ValidationError("Invalid parameter 'test'")
    except ValidationError as e:
        enhanced_msg = enhance_exception_message(
            e, 
            "validate search parameters", 
            context={"endpoint": "/result", "params": {"category": "invalid"}}
        )
        print(f"Original: {e}")
        print(f"Enhanced: {enhanced_msg}")
        print()

def test_debug_mode():
    """Test debug mode functionality."""
    print("=== Debug Mode Test ===")
    
    # Enable debug mode
    set_debug_mode(True)
    
    try:
        client = TroveClient.from_env()
        # This should trigger an enhanced error with debug info
        client.work.get("nonexistent123456789") 
    except TroveAPIError as e:
        print(f"Debug Error: {e}")
        if e.response_data:
            print("Debug Info:")
            for key, value in e.response_data.items():
                if key != 'traceback':  # Skip traceback for brevity
                    print(f"  {key}: {value}")
        print()
    
    # Disable debug mode
    set_debug_mode(False)

def test_retryable_errors():
    """Test retryable error detection."""
    print("=== Retryable Error Detection Test ===")
    
    from trove.exceptions import NetworkError, AuthenticationError, RateLimitError
    
    errors_to_test = [
        (NetworkError("Connection timeout"), True),
        (AuthenticationError("Invalid API key"), False),
        (RateLimitError("Too many requests"), True),
        (ValidationError("Invalid parameter"), False),
    ]
    
    for error, expected_retryable in errors_to_test:
        is_retryable = ErrorRecovery.is_retryable(error)
        status = "✓" if is_retryable == expected_retryable else "✗"
        print(f"{status} {error.__class__.__name__}: retryable={is_retryable}")
    print()

if __name__ == "__main__":
    # Only run tests that don't require API key if not available
    if not os.environ.get('TROVE_API_KEY'):
        print("No API key found. Running limited tests without network calls.")
        test_enhanced_message()
        test_retryable_errors()
    else:
        print("Running all enhanced error handling tests...")
        try:
            test_validation_error_suggestions()
            test_not_found_error_suggestions()
            test_debug_mode()
        except Exception as e:
            print(f"Test failed: {e}")
        
        test_enhanced_message()
        test_retryable_errors()
    
    print("Enhanced error handling tests completed!")