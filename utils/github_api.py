import requests
import os
import logging
from .cache import cache_github_api

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

from utils.logger import setup_logger, log_api_call
from .api_validators import (
    validate_github_user_response,
    validate_github_repos_response,
    validate_contribution_response,
    validate_graphql_response,
    safe_get_nested_value
)

logger = setup_logger(__name__)

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

if load_dotenv:
    load_dotenv()


def calculate_streak_data(contributions):
    """
    Calculate current streak, longest streak, and total contributions from contribution data.
    
    Args:
        contributions: List of dicts with 'date' and 'count' keys, sorted by date
    
    Returns:
        Dict with 'current_streak', 'longest_streak', and 'total_contributions'
    """
    from datetime import datetime, timedelta
    
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
    
    today = datetime.utcnow().date()
    
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
    if not token:
        token = os.getenv("GITHUB_TOKEN")
    if not token:
        return None

    query = """
    query ($login: String!) {
      user(login: $login) {
        contributionsCollection {
          totalCommitContributions
          contributionCalendar {
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

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        resp = requests.post(
            GITHUB_GRAPHQL_URL,
            json={"query": query, "variables": {"login": username}},
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
    
    except requests.RequestException as e:
        logger.error(f"GraphQL request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in GraphQL fetch: {e}")
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
            ["data", "user", "contributionsCollection", "totalCommitContributions"],
            0
        )
        
        # Validate total_commits
        if not isinstance(total_commits, int) or total_commits < 0:
            total_commits = 0
        elif total_commits > 1000000000:  # Sanity check
            total_commits = 1000000000

        return contributions, total_commits, contribution_weeks
    
    except Exception as e:
        logger.error(f"Error parsing GraphQL contributions: {e}")
        return [], 0, []


def get_github_headers(token=None):
    """
    Build headers for GitHub REST API requests.
    Uses Authorization header if GITHUB_TOKEN is set.
    """
    headers = {
        "Accept": "application/vnd.github+json"
    }

    if not token:
        token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers

@cache_github_api
def get_live_github_data(username, token=None):
    """
    Fetches real data from GitHub API with comprehensive validation.
    Notes: 
    - Unauthenticated requests are rate-limited (60/hr).
    - For a real production app, we need a token or use GraphQL.
    - For this MVP, we scrape or use public endpoints where possible to avoid token complexity for the user usage.
    """
    try:
        # User details
        user_url = f"https://api.github.com/users/{username}"
        headers = get_github_headers(token)
        
        try:
            user_resp = requests.get(user_url, headers=headers, timeout=10)
            log_api_call(logger, user_url, user_resp.status_code, has_token=bool(token))
        except requests.RequestException as e:
            logger.error(f"Failed to fetch user data: {e}")
            return None

        if user_resp.status_code != 200:
            logger.error(f"User API Error: Status {user_resp.status_code}")
            return None
        
        try:
            raw_user_data = user_resp.json()
        except ValueError as e:
            logger.error(f"Invalid JSON in user response: {e}")
            return None
        
        # Validate user data
        validated_user = validate_github_user_response(raw_user_data)
        if not validated_user:
            logger.error("User data validation failed")
            return None
        
        logger.info(f"User data fetched successfully for {username}")
        
        # Repos for stars count (limited to first 100 public repos for basic sum without pagination for MVP speed)
        repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
        
        try:
            repos_resp = requests.get(repos_url, headers=headers, timeout=10)
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
        
        # For stats calculation, filter out forks
        repos_data_no_forks = [repo for repo in validated_repos if not repo.fork]
        
        total_stars = sum(repo.stargazers_count for repo in repos_data_no_forks)
        
        # Languages (Approximation from top repos, excluding forks)
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

            
    except Exception as e:
        import traceback
        logger.error(f"Error in get_live_github_data: {e}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
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
    from datetime import datetime, timedelta
    
    today = datetime.utcnow().date()
    
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
