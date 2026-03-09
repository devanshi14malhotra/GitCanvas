"""
GitHub API utilities for fetching profile data
"""

import requests
from typing import Dict, List, Optional
from collections import Counter

from utils.logger import setup_logger

logger = setup_logger(__name__)

GITHUB_API_BASE = "https://api.github.com"


def fetch_github_stats(username: str) -> Optional[Dict]:
    """
    Fetch comprehensive GitHub profile statistics
    
    Args:
        username: GitHub username
        
    Returns:
        Dict with profile data or None if failed
    """
    try:
        # Fetch user profile
        user_response = requests.get(
            f"{GITHUB_API_BASE}/users/{username}",
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        
        if user_response.status_code != 200:
            logger.error(f"Failed to fetch user: {user_response.status_code}")
            return None
        
        user_data = user_response.json()
        
        # Fetch user's repositories
        repos_response = requests.get(
            f"{GITHUB_API_BASE}/users/{username}/repos",
            params={
                "per_page": 100,
                "sort": "updated"
            },
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        
        if repos_response.status_code != 200:
            logger.error(f"Failed to fetch repos: {repos_response.status_code}")
            repos = []
        else:
            repos = repos_response.json()
        
        # Calculate language statistics
        language_counts = Counter()
        total_commits_estimate = 0
        
        for repo in repos[:30]:  # Limit to 30 most recent repos
            if repo.get('language'):
                language_counts[repo['language']] += 1
            
            # Estimate commits (this is approximate)
            # For better accuracy, would need to query each repo's commit endpoint
            if not repo.get('fork'):  # Don't count forked repos
                total_commits_estimate += repo.get('size', 0) // 10  # Rough estimate
        
        # Get top languages
        top_languages = [
            {"name": lang, "count": count}
            for lang, count in language_counts.most_common(5)
        ]
        
        # Construct profile data
        profile_data = {
            "username": user_data.get('login'),
            "name": user_data.get('name') or user_data.get('login'),
            "bio": user_data.get('bio'),
            "public_repos": user_data.get('public_repos', 0),
            "followers": user_data.get('followers', 0),
            "following": user_data.get('following', 0),
            "avatar_url": user_data.get('avatar_url'),
            "created_at": user_data.get('created_at'),
            "top_languages": top_languages,
            "total_commits": max(total_commits_estimate, user_data.get('public_repos', 0) * 5),  # Rough estimate
        }
        
        return profile_data
        
    except Exception as e:
        logger.error(f"Error fetching GitHub stats: {e}")
        return None


def fetch_github_stats_detailed(username: str, github_token: Optional[str] = None) -> Optional[Dict]:
    """
    Fetch more detailed GitHub statistics using GraphQL API
    Requires GitHub Personal Access Token for better rate limits
    
    Args:
        username: GitHub username
        github_token: Optional GitHub Personal Access Token
        
    Returns:
        Dict with detailed profile data or None if failed
    """
    if not github_token:
        logger.info("No GitHub token provided, using basic REST API")
        return fetch_github_stats(username)
    
    query = """
    query($username: String!) {
      user(login: $username) {
        login
        name
        bio
        avatarUrl
        repositories(first: 100, orderBy: {field: UPDATED_AT, direction: DESC}) {
          totalCount
          nodes {
            name
            primaryLanguage {
              name
            }
            defaultBranchRef {
              target {
                ... on Commit {
                  history {
                    totalCount
                  }
                }
              }
            }
          }
        }
        contributionsCollection {
          totalCommitContributions
        }
      }
    }
    """
    
    try:
        response = requests.post(
            "https://api.github.com/graphql",
            json={
                "query": query,
                "variables": {"username": username}
            },
            headers={
                "Authorization": f"Bearer {github_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code != 200:
            logger.error(f"GraphQL query failed: {response.status_code}")
            return fetch_github_stats(username)  # Fallback to REST
        
        data = response.json()
        
        if 'errors' in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            return fetch_github_stats(username)
        
        user = data['data']['user']
        repos = user['repositories']['nodes']
        
        # Calculate language stats
        language_counts = Counter()
        for repo in repos:
            if repo.get('primaryLanguage'):
                lang = repo['primaryLanguage']['name']
                language_counts[lang] += 1
        
        top_languages = [
            {"name": lang, "count": count}
            for lang, count in language_counts.most_common(5)
        ]
        
        return {
            "username": user['login'],
            "name": user['name'] or user['login'],
            "bio": user['bio'],
            "avatar_url": user['avatarUrl'],
            "public_repos": user['repositories']['totalCount'],
            "total_commits": user['contributionsCollection']['totalCommitContributions'],
            "top_languages": top_languages
        }
        
    except Exception as e:
        logger.error(f"Error with GraphQL query: {e}")
        return fetch_github_stats(username)  # Fallback


# For testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        username = sys.argv[1]
        print(f"Fetching stats for: {username}")
        stats = fetch_github_stats(username)
        
        if stats:
            print(f"\nUsername: {stats['username']}")
            print(f"Public Repos: {stats['public_repos']}")
            print(f"Estimated Commits: {stats['total_commits']}")
            print(f"Top Languages: {', '.join([l['name'] for l in stats['top_languages']])}")
        else:
            print("Failed to fetch stats")
    else:
        print("Usage: python github_utils.py <username>")
