"""
Input validation and sanitization utilities for security
Prevents XSS, injection attacks, and invalid input
"""
import re
import html
from typing import Optional
from fastapi import HTTPException


def validate_username(username: str) -> str:
    """
    Validate GitHub username format.
    
    GitHub username rules:
    - 1-39 characters
    - Alphanumeric and hyphens only
    - Cannot start or end with hyphen
    - Cannot have consecutive hyphens
    
    Args:
        username: GitHub username to validate
        
    Returns:
        Validated username
        
    Raises:
        HTTPException: If username is invalid
    """
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    
    if len(username) > 39:
        raise HTTPException(status_code=400, detail="Username too long (max 39 characters)")
    
    # GitHub username pattern: alphanumeric and hyphens, no leading/trailing hyphens
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$', username):
        raise HTTPException(
            status_code=400, 
            detail="Invalid username format. Use only letters, numbers, and hyphens."
        )
    
    return username


def validate_theme(theme: str) -> str:
    """
    Validate theme name against whitelist.
    
    Args:
        theme: Theme name to validate
        
    Returns:
        Validated theme name
        
    Raises:
        HTTPException: If theme is invalid
    """
    # Import here to avoid circular dependency
    from themes.styles import THEMES, CUSTOM_THEMES
    
    valid_themes = list(THEMES.keys()) + list(CUSTOM_THEMES.keys())
    
    if theme not in valid_themes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid theme. Choose from: {', '.join(valid_themes[:10])}..."
        )
    
    return theme


def validate_hex_color(color: Optional[str]) -> Optional[str]:
    """
    Validate hex color format.
    
    Args:
        color: Hex color string (e.g., "#FF5733")
        
    Returns:
        Validated color or None if not provided
        
    Raises:
        HTTPException: If color format is invalid
    """
    if not color:
        return None
    
    # Remove # if present for validation
    color_value = color.lstrip('#')
    
    if not re.match(r'^[0-9A-Fa-f]{6}$', color_value):
        raise HTTPException(
            status_code=400,
            detail="Invalid color format. Use hex format: #RRGGBB"
        )
    
    # Return with # prefix
    return f"#{color_value}"


def sanitize_for_svg(text: str) -> str:
    """
    Sanitize text for safe embedding in SVG.
    
    Escapes HTML/XML special characters to prevent XSS attacks.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text safe for SVG
    """
    if not text:
        return ""
    
    # Escape HTML/XML special characters
    sanitized = html.escape(str(text), quote=True)
    
    # Additional SVG-specific escaping
    sanitized = sanitized.replace('<', '&lt;')
    sanitized = sanitized.replace('>', '&gt;')
    sanitized = sanitized.replace('"', '&quot;')
    sanitized = sanitized.replace("'", '&#x27;')
    
    return sanitized


def validate_sort_by(sort_by: str) -> str:
    """
    Validate sort_by parameter for repository sorting.
    
    Args:
        sort_by: Sort field name
        
    Returns:
        Validated sort field
        
    Raises:
        HTTPException: If sort field is invalid
    """
    valid_sorts = ["stars", "forks", "updated"]
    
    if sort_by not in valid_sorts:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by. Choose from: {', '.join(valid_sorts)}"
        )
    
    return sort_by


def validate_limit(limit: int, min_val: int = 1, max_val: int = 20) -> int:
    """
    Validate numeric limit parameter.
    
    Args:
        limit: Limit value
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Validated limit
        
    Raises:
        HTTPException: If limit is out of range
    """
    if limit < min_val or limit > max_val:
        raise HTTPException(
            status_code=400,
            detail=f"Limit must be between {min_val} and {max_val}"
        )
    
    return limit


def validate_date(date_str: Optional[str]) -> Optional[str]:
    """
    Validate date string format (YYYY-MM-DD).
    
    Args:
        date_str: Date string to validate
        
    Returns:
        Validated date string or None
        
    Raises:
        HTTPException: If date format is invalid
    """
    if not date_str:
        return None
    
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    return date_str
