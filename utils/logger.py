"""
Secure logging configuration for GitCanvas
Prevents sensitive data exposure in logs
"""
import logging
import sys
from typing import Any


class SensitiveDataFilter(logging.Filter):
    """
    Filter to prevent sensitive data from being logged.
    Redacts tokens, API keys, and other sensitive information.
    """
    
    SENSITIVE_PATTERNS = [
        'token', 'password', 'api_key', 'secret', 'authorization',
        'bearer', 'ghp_', 'gho_', 'ghu_', 'ghs_', 'ghr_'
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and sanitize log records"""
        # Sanitize the message
        if hasattr(record, 'msg'):
            record.msg = self._sanitize(str(record.msg))
        
        # Sanitize arguments
        if hasattr(record, 'args') and record.args:
            record.args = tuple(self._sanitize(str(arg)) for arg in record.args)
        
        return True
    
    def _sanitize(self, text: str) -> str:
        """Remove or redact sensitive information from text"""
        text_lower = text.lower()
        
        # Check for sensitive patterns
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in text_lower:
                # Redact the sensitive part
                return "[REDACTED - Contains sensitive data]"
        
        # Redact GitHub tokens (ghp_, gho_, etc.)
        if any(prefix in text for prefix in ['ghp_', 'gho_', 'ghu_', 'ghs_', 'ghr_']):
            return "[REDACTED - GitHub token detected]"
        
        return text


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Setup a secure logger with sensitive data filtering.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add sensitive data filter
    console_handler.addFilter(SensitiveDataFilter())
    
    logger.addHandler(console_handler)
    
    return logger


def sanitize_error_response(response_text: str, max_length: int = 100) -> str:
    """
    Sanitize API error responses before logging.
    
    Args:
        response_text: Raw response text
        max_length: Maximum length to log
        
    Returns:
        Sanitized response text
    """
    if not response_text:
        return ""
    
    # Truncate
    sanitized = response_text[:max_length]
    
    # Remove potential sensitive data patterns
    sensitive_keys = ['token', 'password', 'api_key', 'secret', 'authorization']
    for key in sensitive_keys:
        if key in sanitized.lower():
            return "[Response contains sensitive data - not logged]"
    
    return sanitized


def log_api_call(logger: logging.Logger, endpoint: str, status_code: int, 
                 has_token: bool = False, error: Any = None) -> None:
    """
    Safely log API call information without exposing sensitive data.
    
    Args:
        logger: Logger instance
        endpoint: API endpoint (without query params)
        status_code: HTTP status code
        has_token: Whether request used authentication (boolean only)
        error: Error object if request failed
    """
    # Log success
    if status_code == 200:
        logger.info(f"API call successful: {endpoint} (authenticated: {has_token})")
    elif status_code == 429:
        logger.warning(f"Rate limit hit: {endpoint}")
    elif status_code >= 400:
        # Don't log full error response
        logger.error(f"API error: {endpoint} - Status {status_code}")
        if error:
            # Only log error type, not details
            logger.debug(f"Error type: {type(error).__name__}")
    else:
        logger.info(f"API call: {endpoint} - Status {status_code}")


# Default logger for the application
default_logger = setup_logger('gitcanvas', level='INFO')
