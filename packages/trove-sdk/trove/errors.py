"""Enhanced error handling with context and debugging information."""

import traceback
from typing import Dict, Any, Optional, List
import logging

from .exceptions import TroveError, TroveAPIError, ValidationError, RateLimitError

logger = logging.getLogger(__name__)


class EnhancedErrorHandler:
    """Enhanced error handling with context and debugging info."""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
    
    def wrap_api_error(self, error: Exception, context: Dict[str, Any]) -> Exception:
        """Wrap any error with context and debugging information.
        
        Args:
            error: Original exception
            context: Context information about the operation
            
        Returns:
            Enhanced exception with context and debugging info
        """
        
        # For TroveError types, preserve the original type but enhance the message
        from .exceptions import TroveError, AuthenticationError, AuthorizationError, ResourceNotFoundError, RateLimitError, NetworkError
        
        # Build context information
        context_parts = []
        if context.get('endpoint'):
            context_parts.append(f"endpoint: {context['endpoint']}")
        if context.get('params'):
            # Redact sensitive info
            safe_params = self._redact_params(context['params'])
            context_parts.append(f"params: {safe_params}")
        if context.get('operation'):
            context_parts.append(f"operation: {context['operation']}")
        if context.get('resource_id'):
            context_parts.append(f"resource_id: {context['resource_id']}")
            
        context_str = ", ".join(context_parts)
        
        # Build enhanced error message
        base_message = str(error)
        enhanced_message = base_message
        if context_str:
            enhanced_message = f"{base_message} ({context_str})"
        
        # Preserve original exception type for backward compatibility
        if isinstance(error, TroveError):
            # Create a new instance of the same type with enhanced message
            error_class = type(error)
            if isinstance(error, (AuthenticationError, AuthorizationError, ResourceNotFoundError)):
                # These don't have status_code parameters
                enhanced_error = error_class(enhanced_message)
            elif isinstance(error, RateLimitError):
                # Preserve retry_after if present
                retry_after = getattr(error, 'retry_after', None)
                enhanced_error = error_class(enhanced_message, retry_after=retry_after)
            elif isinstance(error, TroveAPIError):
                # Preserve status_code and response_data
                enhanced_error = error_class(
                    enhanced_message, 
                    status_code=error.status_code,
                    response_data=error.response_data
                )
            else:
                # Generic TroveError
                enhanced_error = error_class(enhanced_message)
                
            # Add debugging information in debug mode
            if self.debug_mode and hasattr(enhanced_error, 'response_data'):
                debug_info = enhanced_error.response_data or {}
                debug_info.update({
                    'original_error_type': type(error).__name__,
                    'traceback': traceback.format_exc(),
                    'context': context,
                    'suggestions': ErrorRecovery.suggest_fixes_for_error(error, context)
                })
                enhanced_error.response_data = debug_info
                
            return enhanced_error
        else:
            # For non-TroveError exceptions, wrap in TroveAPIError
            debug_info = {}
            if self.debug_mode:
                debug_info.update({
                    'original_error_type': type(error).__name__,
                    'traceback': traceback.format_exc(),
                    'context': context,
                    'suggestions': ErrorRecovery.suggest_fixes_for_error(error, context)
                })
                
            return TroveAPIError(
                message=enhanced_message,
                status_code=None,
                response_data=debug_info if debug_info else None
            )
    
    def _redact_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive parameters for logging.
        
        Args:
            params: Parameters to redact
            
        Returns:
            Parameters with sensitive values redacted
        """
        redacted = params.copy()
        sensitive_keys = ['key', 'api_key', 'token', 'password']
        
        for key in list(redacted.keys()):
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                redacted[key] = '***redacted***'
                
        return redacted
    
    def log_error(self, error: Exception, context: Dict[str, Any], level: int = logging.ERROR):
        """Log error with context.
        
        Args:
            error: Exception to log
            context: Context information
            level: Logging level to use
        """
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        logger.log(level, f"Error: {error} | Context: {context_str}")
        
        if self.debug_mode:
            logger.debug(f"Full traceback: {traceback.format_exc()}")


class ErrorRecovery:
    """Implements error recovery strategies and suggestions."""
    
    @staticmethod
    def suggest_fixes_for_error(error: Exception, context: Dict[str, Any] = None) -> List[str]:
        """Suggest fixes based on error type and context.
        
        Args:
            error: Exception to analyze
            context: Optional context information
            
        Returns:
            List of suggested fixes
        """
        suggestions = []
        context = context or {}
        
        if isinstance(error, TroveAPIError):
            suggestions.extend(ErrorRecovery._suggest_api_error_fixes(error, context))
        elif isinstance(error, ValidationError):
            suggestions.extend(ErrorRecovery._suggest_validation_error_fixes(error, context))
        elif isinstance(error, RateLimitError):
            suggestions.extend(ErrorRecovery._suggest_rate_limit_fixes(error, context))
        else:
            suggestions.extend(ErrorRecovery._suggest_general_fixes(error, context))
            
        return suggestions
    
    @staticmethod
    def _suggest_api_error_fixes(error: TroveAPIError, context: Dict[str, Any]) -> List[str]:
        """Suggest fixes for API errors."""
        suggestions = []
        
        if error.status_code == 401:
            suggestions.extend([
                "Check that your API key is valid and properly set",
                "Verify the X-API-KEY header is included",
                "Ensure your API key hasn't expired",
                "Get a new API key from https://trove.nla.gov.au/about/create-something/using-api#getting-an-api-key"
            ])
        elif error.status_code == 404:
            suggestions.extend([
                "Verify the record ID is correct",
                "Check if the record exists in the specified category",
                "Try searching for the record first",
                "Ensure the resource hasn't been removed from Trove"
            ])
        elif error.status_code == 429:
            suggestions.extend([
                "Reduce request rate (current default: 2 req/sec)",
                "Add delays between requests",
                "Use bulk harvest mode for large datasets",
                "Check if your application is making too many concurrent requests"
            ])
        elif error.status_code and error.status_code >= 500:
            suggestions.extend([
                "Try the request again (temporary server issue)",
                "Check Trove service status at https://trove.nla.gov.au/",
                "Simplify the request if complex",
                "Wait a few minutes before retrying"
            ])
        elif error.status_code == 400:
            suggestions.extend([
                "Check parameter spelling and values",
                "Verify parameter dependencies (e.g., year requires decade for newspapers)",
                "Consult the API documentation for valid parameter values",
                "Ensure all required parameters are provided"
            ])
            
        return suggestions
    
    @staticmethod
    def _suggest_validation_error_fixes(error: ValidationError, context: Dict[str, Any]) -> List[str]:
        """Suggest fixes for validation errors."""
        suggestions = []
        error_msg = str(error).lower()
        
        if "category" in error_msg:
            suggestions.extend([
                "Use valid category codes: book, newspaper, image, people, list, etc.",
                "Check the API documentation for current category codes",
                "Ensure category names are spelled correctly"
            ])
        elif "parameter" in error_msg:
            suggestions.extend([
                "Check parameter spelling and values",
                "Verify parameter dependencies (e.g., year requires decade for newspapers)",
                "Consult the API documentation for valid parameter values"
            ])
        elif "include" in error_msg:
            suggestions.extend([
                "Check valid include options for the resource type",
                "Verify include parameter spelling",
                "See resource documentation for supported include values"
            ])
        else:
            suggestions.extend([
                "Check input parameter values",
                "Verify parameter types match expectations",
                "Consult SDK documentation for parameter requirements"
            ])
            
        return suggestions
    
    @staticmethod
    def _suggest_rate_limit_fixes(error: RateLimitError, context: Dict[str, Any]) -> List[str]:
        """Suggest fixes for rate limit errors."""
        suggestions = [
            "Reduce request rate (current default: 2 req/sec)",
            "Add delays between requests",
            "Use bulk harvest mode for large datasets",
            "Implement exponential backoff for retries"
        ]
        
        if hasattr(error, 'retry_after') and error.retry_after:
            suggestions.insert(0, f"Wait {error.retry_after} seconds before retrying")
            
        return suggestions
    
    @staticmethod
    def _suggest_general_fixes(error: Exception, context: Dict[str, Any]) -> List[str]:
        """Suggest fixes for general errors."""
        suggestions = [
            "Check your network connection",
            "Verify API service is available",
            "Try the operation again in a few moments"
        ]
        
        if "timeout" in str(error).lower():
            suggestions.extend([
                "Increase timeout values",
                "Check for network connectivity issues",
                "Try smaller batch sizes if processing bulk data"
            ])
        elif "connection" in str(error).lower():
            suggestions.extend([
                "Check internet connection",
                "Verify firewall settings allow HTTPS requests",
                "Check if you're behind a corporate proxy"
            ])
            
        return suggestions
    
    @staticmethod
    def is_retryable(error: Exception) -> bool:
        """Determine if an error is worth retrying.
        
        Args:
            error: Exception to analyze
            
        Returns:
            True if the error is potentially retryable
        """
        from .exceptions import is_retryable_error
        return is_retryable_error(error)
    
    @staticmethod
    def get_retry_delay(error: Exception, attempt: int) -> float:
        """Calculate retry delay for an error.
        
        Args:
            error: Exception that occurred
            attempt: Current retry attempt number (1-based)
            
        Returns:
            Delay in seconds before retrying
        """
        base_delay = 1.0
        
        if isinstance(error, RateLimitError) and hasattr(error, 'retry_after') and error.retry_after:
            try:
                return float(error.retry_after)
            except (ValueError, TypeError):
                pass
        
        # Exponential backoff with jitter
        import random
        delay = base_delay * (2 ** (attempt - 1))
        jitter = random.uniform(0.1, 0.5)
        return delay + jitter


def enhance_exception_message(error: Exception, operation: str, context: Dict[str, Any] = None) -> str:
    """Enhance exception messages with operation context.
    
    Args:
        error: Original exception
        operation: Description of the operation that failed
        context: Optional context information
        
    Returns:
        Enhanced error message
    """
    base_message = str(error)
    context = context or {}
    
    if isinstance(error, TroveAPIError) and error.status_code:
        status_info = f" (HTTP {error.status_code})"
    else:
        status_info = ""
    
    # Add suggestions if available
    suggestions = ErrorRecovery.suggest_fixes_for_error(error, context)
    suggestion_text = ""
    if suggestions:
        suggestion_text = f" | Suggestions: {'; '.join(suggestions[:3])}"
        
    return f"Failed to {operation}: {base_message}{status_info}{suggestion_text}"


# Global error handler instance
_default_error_handler = EnhancedErrorHandler(debug_mode=False)


def get_error_handler() -> EnhancedErrorHandler:
    """Get the global error handler instance."""
    return _default_error_handler


def set_debug_mode(enabled: bool) -> None:
    """Enable or disable debug mode for error handling."""
    _default_error_handler.debug_mode = enabled