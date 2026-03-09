"""
API Response Validation Module

This module provides Pydantic models and validation functions for GitHub API responses
to prevent crashes from malformed or malicious data.
"""

from pydantic import BaseModel, Field, validator, ValidationError
from typing import List, Optional, Dict, Any, Union
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Constants for validation limits
MAX_COUNT = 1_000_000_000  # 1 billion max for any count field
MAX_STRING_LENGTH = 1000
MAX_ARRAY_LENGTH = 10000
MAX_REPO_COUNT = 1000


class GitHubRepo(BaseModel):
    """Validation model for GitHub repository data"""
    name: str = Field(..., max_length=MAX_STRING_LENGTH)
    description: Optional[str] = Field(None, max_length=MAX_STRING_LENGTH)
    stargazers_count: int = Field(default=0, ge=0, le=MAX_COUNT)
    forks_count: int = Field(default=0, ge=0, le=MAX_COUNT)
    language: Optional[str] = Field(None, max_length=100)
    fork: bool = Field(default=False)
    updated_at: Optional[str] = Field(None, max_length=50)
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Repository name cannot be empty')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            return v.strip()
        return v


class GitHubUser(BaseModel):
    """Validation model for GitHub user data"""
    login: str = Field(..., max_length=100)
    public_repos: int = Field(default=0, ge=0, le=MAX_COUNT)
    followers: int = Field(default=0, ge=0, le=MAX_COUNT)
    created_at: str = Field(..., max_length=50)
    
    @validator('login')
    def validate_login(cls, v):
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        return v.strip()
    
    @validator('created_at')
    def validate_created_at(cls, v):
        # Basic ISO date format validation
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError('Invalid date format')
        return v


class ContributionDay(BaseModel):
    """Validation model for contribution day data"""
    date: str = Field(..., max_length=20)
    count: int = Field(default=0, ge=0, le=MAX_COUNT)
    
    @validator('date')
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v


class GitHubEvent(BaseModel):
    """Validation model for GitHub events (for recent activity)"""
    type: str = Field(..., max_length=50)
    repo: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None
    
    @validator('type')
    def validate_type(cls, v):
        allowed_types = {
            'PullRequestEvent', 'IssuesEvent', 'PushEvent', 'CreateEvent',
            'DeleteEvent', 'ForkEvent', 'WatchEvent', 'ReleaseEvent'
        }
        if v not in allowed_types:
            # Log unknown type but don't fail validation
            logger.warning(f"Unknown event type: {v}")
        return v


class ContributionData(BaseModel):
    """Validation model for contribution API response"""
    total: Optional[Dict[str, int]] = None
    contributions: List[ContributionDay] = Field(default_factory=list, max_items=MAX_ARRAY_LENGTH)
    
    @validator('total')
    def validate_total(cls, v):
        if v is not None:
            # Validate that all values are reasonable integers
            for year, count in v.items():
                if not isinstance(count, int) or count < 0 or count > MAX_COUNT:
                    raise ValueError(f'Invalid contribution count for year {year}: {count}')
        return v


def validate_github_user_response(data: Any) -> Optional[GitHubUser]:
    """
    Validate GitHub user API response
    
    Args:
        data: Raw API response data
        
    Returns:
        Validated GitHubUser object or None if validation fails
    """
    try:
        if not isinstance(data, dict):
            logger.error(f"Expected dict, got {type(data)}")
            return None
        
        return GitHubUser(**data)
    except ValidationError as e:
        logger.error(f"GitHub user validation failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error validating GitHub user: {e}")
        return None


def validate_github_repos_response(data: Any) -> List[GitHubRepo]:
    """
    Validate GitHub repositories API response
    
    Args:
        data: Raw API response data (should be a list)
        
    Returns:
        List of validated GitHubRepo objects (empty list if validation fails)
    """
    try:
        if not isinstance(data, list):
            logger.error(f"Expected list, got {type(data)}")
            return []
        
        if len(data) > MAX_REPO_COUNT:
            logger.warning(f"Too many repos ({len(data)}), truncating to {MAX_REPO_COUNT}")
            data = data[:MAX_REPO_COUNT]
        
        validated_repos = []
        for i, repo_data in enumerate(data):
            try:
                if not isinstance(repo_data, dict):
                    logger.warning(f"Skipping non-dict repo at index {i}")
                    continue
                
                validated_repo = GitHubRepo(**repo_data)
                validated_repos.append(validated_repo)
            except ValidationError as e:
                logger.warning(f"Skipping invalid repo at index {i}: {e}")
                continue
        
        return validated_repos
    except Exception as e:
        logger.error(f"Unexpected error validating repos: {e}")
        return []


def validate_github_events_response(data: Any) -> List[GitHubEvent]:
    """
    Validate GitHub events API response
    
    Args:
        data: Raw API response data (should be a list)
        
    Returns:
        List of validated GitHubEvent objects (empty list if validation fails)
    """
    try:
        if not isinstance(data, list):
            logger.error(f"Expected list, got {type(data)}")
            return []
        
        if len(data) > MAX_ARRAY_LENGTH:
            logger.warning(f"Too many events ({len(data)}), truncating to {MAX_ARRAY_LENGTH}")
            data = data[:MAX_ARRAY_LENGTH]
        
        validated_events = []
        for i, event_data in enumerate(data):
            try:
                if not isinstance(event_data, dict):
                    logger.warning(f"Skipping non-dict event at index {i}")
                    continue
                
                validated_event = GitHubEvent(**event_data)
                validated_events.append(validated_event)
            except ValidationError as e:
                logger.warning(f"Skipping invalid event at index {i}: {e}")
                continue
        
        return validated_events
    except Exception as e:
        logger.error(f"Unexpected error validating events: {e}")
        return []


def validate_contribution_response(data: Any) -> Optional[ContributionData]:
    """
    Validate contribution API response
    
    Args:
        data: Raw API response data
        
    Returns:
        Validated ContributionData object or None if validation fails
    """
    try:
        if not isinstance(data, dict):
            logger.error(f"Expected dict, got {type(data)}")
            return None
        
        return ContributionData(**data)
    except ValidationError as e:
        logger.error(f"Contribution data validation failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error validating contributions: {e}")
        return None


def safe_get_nested_value(data: Dict[str, Any], path: List[str], default: Any = None) -> Any:
    """
    Safely extract nested values from dictionaries with validation
    
    Args:
        data: Dictionary to extract from
        path: List of keys representing the path (e.g., ['user', 'login'])
        default: Default value if path doesn't exist
        
    Returns:
        Value at path or default
    """
    try:
        current = data
        for key in path:
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        return current
    except Exception:
        return default


def validate_graphql_response(data: Any) -> Optional[Dict[str, Any]]:
    """
    Validate GitHub GraphQL API response structure
    
    Args:
        data: Raw GraphQL response
        
    Returns:
        Validated data dict or None if invalid
    """
    try:
        if not isinstance(data, dict):
            logger.error("GraphQL response is not a dict")
            return None
        
        # Check for GraphQL errors
        if 'errors' in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            return None
        
        # Validate basic structure
        user_data = safe_get_nested_value(data, ['data', 'user'])
        if not user_data:
            logger.error("Missing user data in GraphQL response")
            return None
        
        # Validate contributions structure
        contrib_collection = safe_get_nested_value(user_data, ['contributionsCollection'])
        if not contrib_collection:
            logger.error("Missing contributionsCollection in GraphQL response")
            return None
        
        # Validate calendar structure
        calendar = safe_get_nested_value(contrib_collection, ['contributionCalendar'])
        if not calendar:
            logger.error("Missing contributionCalendar in GraphQL response")
            return None
        
        weeks = safe_get_nested_value(calendar, ['weeks'])
        if not isinstance(weeks, list):
            logger.error("Invalid weeks data in GraphQL response")
            return None
        
        return data
    except Exception as e:
        logger.error(f"Unexpected error validating GraphQL response: {e}")
        return None