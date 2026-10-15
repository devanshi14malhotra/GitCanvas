import requests
import os
import logging
import re
from collections import Counter
from .cache import cache_github_api
import streamlit as st
import traceback


try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from utils.logger import setup_logger, log_api_call
from .api_validators import (
    validate_github_user_response,
    validate_github_repos_response,
    validate_contribution_response,
    validate_graphql_response,
    safe_get_nested_value
)
from .github_tokens import configured_tokens, is_token_failure, token_candidates

logger = setup_logger(__name__)

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"


class GitHubDataError(Exception):
    """Base exception for GitHub data fetch failures."""

    def __init__(self, message: str, error_type: str = "api_error"):
        super().__init__(message)
        self.message = message
        self.error_type = error_type


class UserNotFoundError(GitHubDataError):
    """Raised when the provided GitHub username does not exist."""

    def __init__(self, username: str):
        super().__init__(
            f'GitHub user "{username}" was not found.',
            error_type="user_not_found",
        )


class RateLimitExceededError(GitHubDataError):
    """Raised when GitHub API rate limits are exceeded."""

    def __init__(self, message: str = "GitHub API rate limit was reached."):
        super().__init__(message, error_type="rate_limited")


class GitHubApiError(GitHubDataError):
    """Raised for non-rate-limit GitHub API failures."""

    def __init__(self, message: str = "GitHub API is currently unavailable."):
        super().__init__(message, error_type="api_error")

if load_dotenv:
    load_dotenv()


COMMIT_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "into",
    "is", "it", "of", "on", "or", "that", "the", "to", "with", "this", "these", "those",
    "your", "our", "their", "my", "me", "we", "you", "i", "its", "was", "were", "will",
    "can", "cannot", "should", "would", "could", "mr", "mrs", "feat", "fix", "chore", "docs",
    "test", "tests", "ci", "wip", "merge", "branch", "pull", "request", "update", "updated",
    "add", "added", "remove", "removed", "changes", "change"
}


def _extract_words_from_messages(messages):
    words = []
    for message in messages:
        if not message:
            continue
        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_+-]*", message.lower())
        words.extend(t for t in tokens if len(t) > 2 and t not in COMMIT_STOPWORDS)
    return words


def analyze_commit_messages(messages):
    """Summarize commit-message patterns for the commit analysis card."""
    clean_messages = [m.strip() for m in messages if isinstance(m, str) and m.strip()]
    count = len(clean_messages)
    if count == 0:
        return {
            "commit_messages": [],
            "total_messages": 0,
            "average_length": 0.0,
            "common_words": [],
            "mood": "No Signal",
            "mood_score": 0.0,
        }

    avg_length = round(sum(len(m) for m in clean_messages) / count, 1)
    word_counts = Counter(_extract_words_from_messages(clean_messages))
    common_words = [{"word": word, "count": freq} for word, freq in word_counts.most_common(15)]

    mood_keywords = {
        "Shipping": {"ship", "release", "deploy", "feat", "feature", "launch", "merge"},
        "Bug Hunting": {"fix", "bug", "hotfix", "patch", "revert", "rollback", "resolve"},
        "Refactoring": {"refactor", "cleanup", "clean", "optimize", "improve", "simplify"},
        "Maintenance": {"chore", "deps", "dependency", "docs", "test", "ci", "build"},
    }

    mood_scores = {mood: 0 for mood in mood_keywords}
    for message in clean_messages:
        lowered = message.lower()
        for mood, keywords in mood_keywords.items():
            mood_scores[mood] += sum(1 for keyword in keywords if keyword in lowered)

    dominant_mood = max(mood_scores, key=mood_scores.get)
    max_score = mood_scores[dominant_mood]
    mood = dominant_mood if max_score > 0 else "General Coding"
    mood_score = round((max_score / count) * 100, 1) if count > 0 else 0.0

    return {
        "commit_messages": clean_messages,
        "total_messages": count,
        "average_length": avg_length,
        "common_words": common_words,
        "mood": mood,
        "mood_score": mood_score,
    }


@cache_github_api
def get_commit_history(username, token=None, max_repos=6, commits_per_repo=20, max_messages=120):
    """
    Fetch commit messages across a user's recently updated public repositories.

    Returns analyzed commit-message stats and extracted messages.
    """
    headers = get_github_headers(token)
    repos_url = f"https://api.github.com/users/{username}/repos?per_page={max_repos}&sort=updated"

    try:
        repos_resp = requests.get(repos_url, headers=headers, timeout=10)
        log_api_call(logger, repos_url, repos_resp.status_code, has_token=bool(token))
    except requests.RequestException as e:
        logger.error(f"Failed to fetch repositories for commit history: {e}")
        return analyze_commit_messages([])

    if repos_resp.status_code != 200:
        logger.warning(f"Commit history repos fetch failed with status {repos_resp.status_code}")
        return analyze_commit_messages([])

    try:
        repos = repos_resp.json()
    except ValueError as e:
        logger.error(f"Invalid JSON while fetching repos for commit history: {e}")
        return analyze_commit_messages([])

    if not isinstance(repos, list):
        return analyze_commit_messages([])

    messages = []
    seen_shas = set()

    for repo in repos:
        if not isinstance(repo, dict):
            continue
        repo_name = repo.get("name")
        if not repo_name:
            continue

        commits_url = (
            f"https://api.github.com/repos/{username}/{repo_name}/commits"
            f"?author={username}&per_page={commits_per_repo}"
        )

        try:
            commits_resp = requests.get(commits_url, headers=headers, timeout=10)
            log_api_call(logger, commits_url, commits_resp.status_code, has_token=bool(token))
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch commits for {repo_name}: {e}")
            continue

        if commits_resp.status_code != 200:
            continue

        try:
            commits = commits_resp.json()
        except ValueError:
            continue

        if not isinstance(commits, list):
            continue

        for commit in commits:
            if not isinstance(commit, dict):
                continue

            sha = commit.get("sha")
            if sha and sha in seen_shas:
                continue
            if sha:
                seen_shas.add(sha)

            full_message = (
                commit.get("commit", {})
                .get("message", "")
            )
            message = full_message.split("\n")[0].strip() if isinstance(full_message, str) else ""
            if not message:
                continue

            messages.append(message)
            if len(messages) >= max_messages:
                break

        if len(messages) >= max_messages:
            break

    return analyze_commit_messages(messages)


def calculate_streak_data(contributions):
    """
    Calculate current streak, longest streak, and total contributions from contribution data.
    
    Args:
        contributions: List of dicts with 'date' and 'count' keys, sorted by date
    
    Returns:
        Dict with 'current_streak', 'longest_streak', and 'total_contributions'
    """
    from datetime import datetime, timedelta, timezone
    
    if not contributions:
        return {
            'current_streak': 0,
            'longest_streak': 0,
            'total_contributions': 0
        }
    
    # Sort contributions by date (oldest first)
    sorted_contribs = sorted(contributions, key=lambda x: x.get('date', ''))
    
    # Calculate total contributions
    total_contributions = sum(c.get('count', 0) for c in sorted_contribs)
    
    # Calculate streaks
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    
    today = datetime.now(timezone.utc).date()
    
    # Build a dict for quick lookup
    contrib_dict = {c['date']: c['count'] for c in sorted_contribs}
    
    # Find the most recent contribution date
    if sorted_contribs:
        last_date_str = sorted_contribs[-1]['date']
        last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
    else:
        last_date = today
    
    # Calculate current streak (working backwards from today)
    check_date = today
    while True:
        date_str = check_date.strftime("%Y-%m-%d")
        if date_str in contrib_dict and contrib_dict[date_str] > 0:
            current_streak += 1
            check_date -= timedelta(days=1)
        else:
            # Allow one day gap (today might not have contributions yet)
            if check_date == today:
                check_date -= timedelta(days=1)
                continue
            break
    
    # Calculate longest streak by iterating through all dates
    if sorted_contribs:
        start_date = datetime.strptime(sorted_contribs[0]['date'], "%Y-%m-%d").date()
        check_date = start_date
        
        while check_date <= today:
            date_str = check_date.strftime("%Y-%m-%d")
            if date_str in contrib_dict and contrib_dict[date_str] > 0:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0
            check_date += timedelta(days=1)
    
    return {
        'current_streak': current_streak,
        'longest_streak': longest_streak,
        'total_contributions': total_contributions
    }


@cache_github_api
def fetch_github_graphql(username, token=None):
    if not token and not configured_tokens():
        return None

    from datetime import datetime, timedelta, timezone as _tz
    _today = datetime.now(_tz.utc)
    _from  = (_today - timedelta(days=365)).strftime("%Y-%m-%dT00:00:00Z")
    _to    = _today.strftime("%Y-%m-%dT23:59:59Z")

    query = """
    query ($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """

    headers = {"Content-Type": "application/json"}

    try:
        resp = github_request(
            "POST",
            GITHUB_GRAPHQL_URL,
            token,
            json={"query": query, "variables": {"login": username, "from": _from, "to": _to}},
            headers=headers,
            timeout=10
        )

        if resp.status_code != 200:
            logger.error(f"GraphQL API error: {resp.status_code}")
            return None
        
        raw_data = resp.json()
        validated_data = validate_graphql_response(raw_data)
        
        if not validated_data:
            logger.error("GraphQL response validation failed")
            return None
            
        return validated_data
    
    except requests.exceptions.Timeout as e:
        logger.error(f"GraphQL request timeout: {e}")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"GraphQL connection error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"GraphQL request failed: {e}")
        return None
    except ValueError as e:
        logger.error(f"Invalid JSON in GraphQL response: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in GraphQL fetch: {e}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return None

def parse_graphql_contributions(graphql_json):
    """
    Parse GraphQL contributions data with validation
    """
    try:
        weeks = safe_get_nested_value(
            graphql_json, 
            ["data", "user", "contributionsCollection", "contributionCalendar", "weeks"],
            []
        )
        
        if not isinstance(weeks, list):
            logger.error("Invalid weeks data structure")
            return [], 0, []

        contributions = []
        contribution_weeks = []
        
        for week in weeks:
            if not isinstance(week, dict):
                continue
                
            contribution_days = week.get("contributionDays", [])
            if not isinstance(contribution_days, list):
                continue
                
            week_days = []
            for day in contribution_days:
                if not isinstance(day, dict):
                    continue
                    
                # Validate day data
                date = day.get("date", "")
                count = day.get("contributionCount", 0)
                
                # Basic validation
                if not isinstance(date, str) or not isinstance(count, int):
                    continue
                if count < 0 or count > 1000000:  # Sanity check
                    count = min(max(count, 0), 1000000)
                
                day_entry = {
                    "date": date,
                    "count": count
                }
                contributions.append(day_entry)
                week_days.append(day_entry)
            
            if week_days:  # Only add non-empty weeks
                contribution_weeks.append(week_days)

        total_commits = safe_get_nested_value(
            graphql_json,
            ["data", "user", "contributionsCollection", "contributionCalendar", "totalContributions"],
            0
        ) or safe_get_nested_value(
            graphql_json,
            ["data", "user", "contributionsCollection", "totalCommitContributions"],
            0
        )
        
        # Validate total_commits
        if not isinstance(total_commits, int) or total_commits < 0:
            total_commits = 0
        elif total_commits > 1000000000:  # Sanity check
            total_commits = 1000000000

        return contributions, total_commits, contribution_weeks
    
    except (KeyError, TypeError, ValueError) as e:
        logger.error(f"Invalid data structure in GraphQL contributions: {e}")
        return [], 0, []
    except Exception as e:
        logger.error(f"Unexpected error parsing GraphQL contributions: {e}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return [], 0, []


def get_github_headers(token=None):
    """
    Build headers for GitHub REST API requests.
    Uses Authorization header when a token is supplied.
    """
    headers = {
        "Accept": "application/vnd.github+json"
    }

    if not token:
        try:
            token = st.secrets.get("GITHUB_TOKEN")
        except (AttributeError, KeyError, RuntimeError, TypeError):
            token = None
        if not token:
            token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def github_request(method, url, token=None, **kwargs):
    """Make a GitHub request with server-token failover when needed."""
    request_headers = dict(kwargs.pop("headers", {}) or {})
    candidates = token_candidates(token)
    response = None

    for candidate in candidates:
        headers = dict(request_headers)
        headers.update(get_github_headers(candidate))
        request = requests.get if method.upper() == "GET" else requests.post
        response = request(url, headers=headers, **kwargs)
        if not is_token_failure(response) or candidate == candidates[-1]:
            return response

        logger.warning("GitHub token failed for %s; trying the next configured token.", url)

    return response


def _extract_github_error_message(response) -> str:
    """Safely extract GitHub API error message from JSON responses."""
    try:
        payload = response.json()
    except ValueError:
        return ""

    if isinstance(payload, dict):
        message = payload.get("message")
        if isinstance(message, str):
            return message
    return ""


def _build_user_fetch_error(username: str, response) -> GitHubDataError:
    """Map failed user API responses to typed exceptions."""
    status_code = response.status_code
    message = _extract_github_error_message(response)

    if status_code == 404:
        return UserNotFoundError(username)

    if status_code in (403, 429):
        remaining = response.headers.get("X-RateLimit-Remaining")
        if remaining == "0" or "rate limit" in message.lower():
            return RateLimitExceededError(message or "GitHub API rate limit was reached.")

    return GitHubApiError(message or f"GitHub API returned status code {status_code}.")

@cache_github_api
def get_live_github_data(username, token=None, raise_errors: bool = False):
    """
    Fetches real data from GitHub API with comprehensive validation.
    Notes: 
    - Unauthenticated requests are rate-limited (60/hr).
    - For a real production app, we need a token or use GraphQL.
    - For this MVP, we scrape or use public endpoints where possible to avoid token complexity for the user usage.

    Args:
        username: GitHub username.
        token: Optional GitHub token.
        raise_errors: When True, raise typed GitHubDataError exceptions instead
            of returning None on fatal failures.
    """
    try:
        # User details
        user_url = f"https://api.github.com/users/{username}"
        headers = get_github_headers(token)
        
        try:
            user_resp = github_request("GET", user_url, token, headers=headers, timeout=10)
            log_api_call(logger, user_url, user_resp.status_code, has_token=bool(token))
        except requests.RequestException as e:
            logger.error(f"Failed to fetch user data: {e}")
            if raise_errors:
                raise GitHubApiError("Failed to connect to GitHub API.") from e
            return None

        if user_resp.status_code != 200:
            logger.error(f"User API Error: Status {user_resp.status_code}")
            if raise_errors:
                raise _build_user_fetch_error(username, user_resp)
            return None
        
        try:
            raw_user_data = user_resp.json()
        except ValueError as e:
            logger.error(f"Invalid JSON in user response: {e}")
            if raise_errors:
                raise GitHubApiError("GitHub returned an invalid response payload.") from e
            return None
        
        # Validate user data
        validated_user = validate_github_user_response(raw_user_data)
        if not validated_user:
            logger.error("User data validation failed")
            if raise_errors:
                raise GitHubApiError("GitHub user response failed validation.")
            return None
        
        logger.info(f"User data fetched successfully for {username}")
        
        # Repos for stars count (limited to first 100 public repos for basic sum without pagination for MVP speed)
        repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
        
        try:
            repos_resp = github_request("GET", repos_url, token, headers=headers, timeout=10)
            if repos_resp:
                log_api_call(logger, repos_url, repos_resp.status_code, has_token=bool(token))
        except requests.RequestException as e:
            logger.error(f"Failed to fetch repos: {e}")
            repos_resp = None
        
        validated_repos = []
        if repos_resp and repos_resp.status_code == 200:
            try:
                raw_repos_data = repos_resp.json()
                validated_repos = validate_github_repos_response(raw_repos_data)
                logger.info(f"Repos API Status: {repos_resp.status_code}")
            except ValueError as e:
                logger.error(f"Invalid JSON in repos response: {e}")
        else:
            logger.warning(f"Repos API Error: Status {repos_resp.status_code if repos_resp else 'No response'}")
        
        # Store all repos including forks for frontend (let user decide)
        all_repos = validated_repos.copy()
        
        # Calculate global totals across all fetched repositories
        total_stars = sum(repo.stargazers_count for repo in validated_repos)
        total_forks = sum(repo.forks_count for repo in validated_repos)
        
        # Filter for non-forks specifically for language distribution and display
        repos_data_no_forks = [repo for repo in validated_repos if not repo.fork]
        
        languages = {}
        for repo in repos_data_no_forks[:10]: # Check top 10 non-fork repos
            lang = repo.language
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
        
        top_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Top repositories - include ALL repos (user can filter in UI if needed)
        top_repos = [{
            "name": repo.name,
            "description": repo.description or "",
            "language": repo.language or "",
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "updated_at": repo.updated_at or "",
            "is_fork": repo.fork
        } for repo in sorted(all_repos, key=lambda x: x.stargazers_count, reverse=True)[:10]]
        
        logger.info(f"Fetched {len(all_repos)} total repos ({len(repos_data_no_forks)} non-forks) for {username}")

        # Ensure total_commits is always an integer
        total_commits = 0 
        fallback_contributions = []

        try:
            contrib_url = f"https://github-contributions-api.jogruber.de/v4/{username}"
            
            try:
                contrib_resp = requests.get(contrib_url, timeout=10)
                if contrib_resp:
                    log_api_call(logger, contrib_url, contrib_resp.status_code, has_token=False)
            except requests.RequestException as e:
                logger.error(f"Failed to fetch contributions: {e}")
                contrib_resp = None
            
            if contrib_resp and contrib_resp.status_code == 200:
                try:
                    raw_contrib_data = contrib_resp.json()
                    validated_contrib = validate_contribution_response(raw_contrib_data)
                    
                    if validated_contrib:
                        if validated_contrib.total:
                            # Sum all year totals into a single integer
                            total_commits = sum(validated_contrib.total.values())
                        
                        # Extract contribution calendar data for streak calculation
                        fallback_contributions = [
                            {
                                'date': contrib.date,
                                'count': contrib.count
                            }
                            for contrib in validated_contrib.contributions
                        ]
                        logger.info(f"Fetched {len(fallback_contributions)} contribution days from fallback API")
                except ValueError as e:
                    logger.error(f"Invalid JSON in contributions response: {e}")
            # If the response isn't 200, it stays as 0
        except Exception as ex:
            logger.error(f"Contrib API Error: {ex}")
            total_commits = 0 # Safety fallback

        data = {
            "username": username,
            "total_stars": total_stars,
            "total_forks": total_forks,
            "total_commits": total_commits,
            "public_repos": validated_user.public_repos,
            "followers": validated_user.followers,
            "created_at": validated_user.created_at,
            "top_languages": top_langs,
            "top_repos": top_repos,
        }

        # --- Optional GraphQL enrichment ---
        graphql_data = fetch_github_graphql(username, token)
        if graphql_data:
            try:
                contributions, gql_total_commits, contribution_weeks = parse_graphql_contributions(graphql_data)
                data["contributions"] = contributions
                data["total_commits"] = gql_total_commits
                data["contribution_weeks"] = contribution_weeks
                
                # Calculate streak data from contributions
                data["streak_data"] = calculate_streak_data(contributions)
            except Exception as e:
                logger.warning(f"GraphQL failed for {username}: {e}, falling back to REST")
                data['data_source'] = 'rest_fallback'

        if "contributions" not in data:
            # Use fallback contributions if GraphQL didn't work
            if fallback_contributions:
                data["contributions"] = fallback_contributions
                logger.info(f"Using fallback contributions: {len(fallback_contributions)} days")
            else:
                # Fallback to empty list; UI should handle missing contribution data gracefully.
                data["contributions"] = []
        
        # If we don't have streak data yet, try to calculate from any contributions we have
        if "streak_data" not in data and data.get("contributions"):
            data["streak_data"] = calculate_streak_data(data["contributions"])
            logger.info(f"Calculated streak data: current={data['streak_data']['current_streak']}, longest={data['streak_data']['longest_streak']}")
        
        # Final fallback for streak data
        if "streak_data" not in data:
            data["streak_data"] = {
                'current_streak': 0,
                'longest_streak': 0,
                'total_contributions': 0
            }

        return data

            
    except GitHubDataError:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Unexpected error in get_live_github_data for {username}: {e}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        if raise_errors:
            raise GitHubApiError("Unexpected error while fetching GitHub data.") from e
        return None

def get_mock_data(username):
    """Returns dummy data for layout testing/building without hitting API limits"""
    mock_contributions = [
        {"date": f"2025-01-{i+1:02d}", "count": (i * 3) % 10}
        for i in range(30)  # Generate 30 days instead of 80
    ]
    
    return {
        "username": username,
        "total_stars": 120,
        "total_commits": 450,
        "public_repos": 25,
        "followers": 85,
        "created_at": "2015-06-15T00:00:00Z",
        "top_languages": [("Python", 10), ("JavaScript", 5), ("Rust", 2)],
        "contributions": mock_contributions,
        "streak_data": calculate_streak_data(mock_contributions),
        "top_repos": [
            {"name": "awesome-project", "description": "A cool project", "language": "Python", "stars": 150, "forks": 30, "updated_at": "2025-01-15"},
            {"name": "web-app", "description": "Modern web application", "language": "JavaScript", "stars": 89, "forks": 12, "updated_at": "2025-01-20"},
            {"name": "api-service", "description": "RESTful API service", "language": "Go", "stars": 65, "forks": 8, "updated_at": "2025-01-18"},
            {"name": "cli-tool", "description": "Command line utility", "language": "Rust", "stars": 42, "forks": 5, "updated_at": "2025-01-10"},
            {"name": "mobile-app", "description": "Cross-platform mobile app", "language": "TypeScript", "stars": 28, "forks": 3, "updated_at": "2025-01-12"}
        ]

    }


def filter_contributions_by_date(contributions, date_range):
    """
    Filter contributions by date range.
    
    Args:
        contributions: List of contribution dicts with 'date' and 'count' keys
        date_range: Dict with 'start' and 'end' date strings (YYYY-MM-DD format)
                    or None for all time
    
    Returns:
        Filtered list of contributions
    """
    if not contributions or not date_range:
        return contributions
    
    start_date = date_range.get('start')
    end_date = date_range.get('end')
    
    if not start_date or not end_date:
        return contributions
    
    try:
        from datetime import datetime
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return contributions
    
    filtered = []
    for item in contributions:
        item_date = item.get('date')
        if not item_date:
            continue
        try:
            parsed_date = datetime.strptime(item_date, "%Y-%m-%d").date()
            if start <= parsed_date <= end:
                filtered.append(item)
        except (ValueError, TypeError):
            continue
    
    return filtered


def get_date_range_from_option(date_option, custom_start=None, custom_end=None):
    """
    Get date range based on predefined options or custom range.
    
    Args:
        date_option: One of 'all_time', 'last_6_months', 'current_year', 'custom'
        custom_start: Start date for custom range (YYYY-MM-DD)
        custom_end: End date for custom range (YYYY-MM-DD)
    
    Returns:
        Dict with 'start' and 'end' date strings, or None for all time
    """
    from datetime import datetime, timedelta, timezone
    
    today = datetime.now(timezone.utc).date()
    
    if date_option == 'all_time' or date_option == 'all':
        return None
    
    elif date_option == 'last_6_months' or date_option == '6months':
        start = today - timedelta(days=180)
        return {
            'start': start.strftime("%Y-%m-%d"),
            'end': today.strftime("%Y-%m-%d")
        }
    
    elif date_option == 'current_year' or date_option == 'year':
        start = datetime(today.year, 1, 1).date()
        return {
            'start': start.strftime("%Y-%m-%d"),
            'end': today.strftime("%Y-%m-%d")
        }
    
    elif date_option == 'custom' and custom_start and custom_end:
        return {
            'start': custom_start,
            'end': custom_end
        }
    
    return None


def fetch_sparkline_data(username, token=None):
    """Fetches daily commit counts for the last 30 days."""
    import requests
    from datetime import datetime, timedelta
    
    # Initialize 30 days with 0
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
    daily_commits = {date: 0 for date in dates}
    
    headers = {"Authorization": f"token {token}"} if token else {}
    url = f"https://api.github.com/users/{username}/events/public"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            events = response.json()
            for event in events:
                try:
                    if event.get('type') == 'PushEvent':
                        date = event.get('created_at', '').split('T')[0]
                        if date in daily_commits:
                            daily_commits[date] += event.get('payload', {}).get('distinct_size', 0)
                except (AttributeError, KeyError, TypeError) as e:
                    logger.warning(f"Skipping malformed event for {username}: {e}")
                    continue
    except (requests.RequestException, ValueError, TypeError) as e:
        logger.warning(f"Failed to fetch sparkline data for {username}: {e}")
    
    # Return as a list of counts from oldest to newest
    return [daily_commits[date] for date in reversed(dates)]


@cache_github_api
def get_github_actions_data(username, token=None):
    """
    Fetches GitHub Actions statistics for a user.
    
    Requires authentication token - Actions data is not available publicly.
    
    Args:
        username: GitHub username
        token: GitHub API token (required for Actions data)
    
    Returns:
        Dict with actions statistics or None if no data available
    """
    if not token and not configured_tokens():
        logger.warning(f"GitHub token required to fetch Actions data for {username}")
        return None
    
    try:
        # Get user's repositories
        repos_url = f"https://api.github.com/users/{username}/repos?per_page=100"
        headers = get_github_headers(token)
        
        repos_resp = github_request("GET", repos_url, token, headers=headers, timeout=10)
        if repos_resp.status_code != 200:
            logger.error(f"Failed to fetch repos for Actions data: {repos_resp.status_code}")
            return None
        
        repos = repos_resp.json()
        if not isinstance(repos, list):
            logger.error("Invalid repos response format")
            return None
        
        # Collect actions data from repos
        total_workflows = 0
        total_runs = 0
        successful_runs = 0
        failed_runs = 0
        recent_runs = []
        workflows_by_repo = []
        
        for repo in repos:
            repo_name = repo.get('name', '')
            if not repo_name:
                continue
            
            try:
                # Fetch workflows for this repo
                workflows_url = f"https://api.github.com/repos/{username}/{repo_name}/actions/workflows"
                workflows_resp = github_request("GET", workflows_url, token, headers=headers, timeout=10)
                
                if workflows_resp.status_code == 200:
                    workflows = workflows_resp.json().get('workflows', [])
                    total_workflows += len(workflows)
                    
                    for workflow in workflows:
                        workflow_id = workflow.get('id')
                        workflow_name = workflow.get('name', 'Unknown')
                        
                        if workflow_id:
                            try:
                                # Fetch runs for this workflow
                                runs_url = f"https://api.github.com/repos/{username}/{repo_name}/actions/workflows/{workflow_id}/runs?per_page=10"
                                runs_resp = github_request("GET", runs_url, token, headers=headers, timeout=10)
                                
                                if runs_resp.status_code == 200:
                                    runs_data = runs_resp.json().get('workflow_runs', [])
                                    total_runs += len(runs_data)
                                    
                                    for run in runs_data:
                                        status = run.get('conclusion', '')
                                        if status == 'success':
                                            successful_runs += 1
                                        elif status == 'failure':
                                            failed_runs += 1
                                        
                                        # Collect recent runs
                                        recent_runs.append({
                                            'repo': repo_name,
                                            'workflow': workflow_name,
                                            'status': status,
                                            'created_at': run.get('created_at', ''),
                                            'updated_at': run.get('updated_at', ''),
                                            'conclusion': run.get('conclusion', 'unknown')
                                        })
                            except (requests.RequestException, (KeyError, ValueError)):
                                logger.warning(f"Failed to fetch runs for {repo_name}/{workflow_name}")
                else:
                    logger.debug(f"No workflows found for {repo_name}")
                    
            except (requests.RequestException, (KeyError, ValueError)):
                logger.warning(f"Failed to fetch workflows for {repo_name}")
        
        # Sort recent runs by updated_at (most recent first)
        try:
            from datetime import datetime
            recent_runs.sort(
                key=lambda x: datetime.fromisoformat(x.get('updated_at', '2000-01-01').replace('Z', '+00:00')),
                reverse=True
            )
        except (ValueError, TypeError):
            logger.warning(f"Failed to sort recent runs - invalid date format")
        
        # Keep only last 20 recent runs
        recent_runs = recent_runs[:20]
        
        # Calculate success rate
        success_rate = 0
        if total_runs > 0:
            success_rate = round((successful_runs / total_runs) * 100, 1)
        
        return {
            'total_workflows': total_workflows,
            'total_runs': total_runs,
            'successful_runs': successful_runs,
            'failed_runs': failed_runs,
            'success_rate': success_rate,
            'recent_runs': recent_runs,
            'data_source': 'github_actions_api'
        }
        
    except requests.exceptions.Timeout:
        logger.error(f"GitHub Actions API timeout for {username}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"GitHub Actions API connection error for {username}")
        return None
    except ValueError as e:
        logger.error(f"Invalid JSON response from GitHub Actions API: {e}")
        return None
    except Exception as e:
        import traceback
        logger.error(f"Unexpected error fetching GitHub Actions data for {username}: {e}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return None


def get_mock_actions_data(username):
    """Returns mock GitHub Actions data for testing."""
    return {
        'total_workflows': 5,
        'total_runs': 47,
        'successful_runs': 43,
        'failed_runs': 4,
        'success_rate': 91.5,
        'recent_runs': [
            {
                'repo': 'awesome-project',
                'workflow': 'Tests',
                'status': 'completed',
                'created_at': '2025-01-20T14:30:00Z',
                'updated_at': '2025-01-20T14:45:00Z',
                'conclusion': 'success'
            },
            {
                'repo': 'web-app',
                'workflow': 'Build & Deploy',
                'status': 'completed',
                'created_at': '2025-01-20T13:00:00Z',
                'updated_at': '2025-01-20T13:20:00Z',
                'conclusion': 'success'
            },
            {
                'repo': 'api-service',
                'workflow': 'Linting',
                'status': 'completed',
                'created_at': '2025-01-19T10:15:00Z',
                'updated_at': '2025-01-19T10:18:00Z',
                'conclusion': 'failure'
            },
            {
                'repo': 'awesome-project',
                'workflow': 'Tests',
                'status': 'completed',
                'created_at': '2025-01-19T08:00:00Z',
                'updated_at': '2025-01-19T08:15:00Z',
                'conclusion': 'success'
            },
            {
                'repo': 'mobile-app',
                'workflow': 'Build',
                'status': 'completed',
                'created_at': '2025-01-18T16:45:00Z',
                'updated_at': '2025-01-18T17:00:00Z',
                'conclusion': 'success'
            },
        ],
        'username': username,
        'data_source': 'mock'
    }


@cache_github_api
def get_user_gists(username, token=None, limit=20):
    """
    Fetch a user's public gists and normalize minimal metadata for cards/UI.
    """
    headers = get_github_headers(token)
    url = f"https://api.github.com/users/{username}/gists?per_page={limit}"

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        log_api_call(logger, url, resp.status_code, has_token=bool(token))
    except requests.RequestException as e:
        logger.error(f"Failed to fetch gists for {username}: {e}")
        return []

    if resp.status_code != 200:
        logger.warning(f"Gists API returned status {resp.status_code} for {username}")
        return []

    try:
        payload = resp.json()
    except ValueError as e:
        logger.error(f"Invalid JSON from gists API for {username}: {e}")
        return []

    if not isinstance(payload, list):
        return []

    gists = []
    for item in payload:
        if not isinstance(item, dict):
            continue

        gist_id = item.get("id", "")
        html_url = item.get("html_url", "")
        description = (item.get("description") or "Untitled Gist").strip()
        updated_at = item.get("updated_at", "")
        files = item.get("files", {}) or {}

        file_entries = []
        if isinstance(files, dict):
            for filename, meta in files.items():
                meta = meta or {}
                file_entries.append({
                    "filename": filename,
                    "language": meta.get("language") or "Text",
                    "raw_url": meta.get("raw_url", ""),
                    "size": meta.get("size", 0),
                    "type": meta.get("type", ""),
                    "truncated": bool(meta.get("truncated", False)),
                })

        gists.append({
            "id": gist_id,
            "description": description,
            "html_url": html_url,
            "updated_at": updated_at,
            "public": bool(item.get("public", True)),
            "files": file_entries,
            "file_count": len(file_entries),
        })

    return gists


@cache_github_api
def get_gist_file_preview(gist_id, file_name=None, token=None, max_lines=8, max_chars=500):
    """
    Fetch a gist and return metadata + short preview for one selected file.
    """
    headers = get_github_headers(token)
    url = f"https://api.github.com/gists/{gist_id}"

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        log_api_call(logger, url, resp.status_code, has_token=bool(token))
    except requests.RequestException as e:
        logger.error(f"Failed to fetch gist details for {gist_id}: {e}")
        return None

    if resp.status_code != 200:
        logger.warning(f"Gist details API returned status {resp.status_code} for {gist_id}")
        return None

    try:
        payload = resp.json()
    except ValueError:
        return None

    files = payload.get("files", {}) or {}
    if not isinstance(files, dict) or not files:
        return None

    chosen_name = file_name if file_name in files else next(iter(files.keys()))
    selected = files.get(chosen_name, {}) or {}

    content = selected.get("content")
    if not isinstance(content, str) or not content.strip():
        raw_url = selected.get("raw_url")
        if raw_url:
            try:
                raw_resp = requests.get(raw_url, timeout=10)
                if raw_resp.status_code == 200:
                    content = raw_resp.text
            except requests.RequestException:
                content = ""

    content = content or ""
    lines = content.splitlines()
    snippet = "\n".join(lines[:max_lines])
    if len(snippet) > max_chars:
        snippet = snippet[:max_chars].rstrip() + "..."

    return {
        "id": payload.get("id", gist_id),
        "description": (payload.get("description") or "Untitled Gist").strip(),
        "html_url": payload.get("html_url", ""),
        "updated_at": payload.get("updated_at", ""),
        "filename": chosen_name,
        "language": selected.get("language") or "Text",
        "size": selected.get("size", 0),
        "preview": snippet,
    }


def get_mock_gists(username):
    """Returns mock gist metadata for local previews when API is unavailable."""
    return [
        {
            "id": "mock-gist-1",
            "description": f"Utility snippets by {username}",
            "html_url": "https://gist.github.com/mock-gist-1",
            "updated_at": "2026-04-20T10:00:00Z",
            "public": True,
            "file_count": 2,
            "files": [
                {
                    "filename": "quick_sort.py",
                    "language": "Python",
                    "raw_url": "",
                    "size": 420,
                    "type": "text/plain",
                    "truncated": False,
                },
                {
                    "filename": "README.md",
                    "language": "Markdown",
                    "raw_url": "",
                    "size": 180,
                    "type": "text/markdown",
                    "truncated": False,
                },
            ],
        },
        {
            "id": "mock-gist-2",
            "description": "Shell aliases and helpers",
            "html_url": "https://gist.github.com/mock-gist-2",
            "updated_at": "2026-04-18T08:30:00Z",
            "public": True,
            "file_count": 1,
            "files": [
                {
                    "filename": "aliases.sh",
                    "language": "Shell",
                    "raw_url": "",
                    "size": 250,
                    "type": "text/plain",
                    "truncated": False,
                },
            ],
        },
    ]


def get_mock_gist_preview(gist_id, file_name=None):
    """Returns a mock gist preview block for fallback rendering."""
    selected_name = file_name or "quick_sort.py"
    return {
        "id": gist_id,
        "description": "Mock gist preview",
        "html_url": f"https://gist.github.com/{gist_id}",
        "updated_at": "2026-04-20T10:00:00Z",
        "filename": selected_name,
        "language": "Python",
        "size": 420,
        "preview": "def quick_sort(items):\n    if len(items) <= 1:\n        return items\n    pivot = items[len(items) // 2]\n    left = [x for x in items if x < pivot]\n    mid = [x for x in items if x == pivot]\n    right = [x for x in items if x > pivot]\n    return quick_sort(left) + mid + quick_sort(right)",
    }