import requests
import os

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"



def fetch_github_graphql(username):
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

    resp = requests.post(
        GITHUB_GRAPHQL_URL,
        json={"query": query, "variables": {"login": username}},
        headers=headers,
        timeout=10
    )

    if resp.status_code != 200:
        return None
    

    return resp.json()

def parse_graphql_contributions(graphql_json):
    weeks = (
        graphql_json["data"]["user"]
        ["contributionsCollection"]
        ["contributionCalendar"]
        ["weeks"]
    )

    contributions = []
    for week in weeks:
        for day in week["contributionDays"]:
            contributions.append({
                "date": day["date"],
                "count": day["contributionCount"]
            })

    total_commits = (
        graphql_json["data"]["user"]
        ["contributionsCollection"]
        ["totalCommitContributions"]
    )

    return contributions, total_commits


def get_github_headers():
    """
    Build headers for GitHub REST API requests.
    Uses Authorization header if GITHUB_TOKEN is set.
    """
    headers = {
        "Accept": "application/vnd.github+json"
    }

    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers

def get_live_github_data(username):
    """
    Fetches real data from GitHub API. 
    Notes: 
    - Unauthenticated requests are rate-limited (60/hr).
    - For a real production app, we need a token or use GraphQL.
    - For this MVP, we scrape or use public endpoints where possible to avoid token complexity for the user usage.
    """
    try:
        # User details
        user_url = f"https://api.github.com/users/{username}"
        headers = get_github_headers()
        user_resp = requests.get(user_url, headers=headers)

        if user_resp.status_code != 200:
            return None
        user_data = user_resp.json()
        
        # Repos for stars count (limited to first 100 public repos for basic sum without pagination for MVP speed)
        repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&type=owner"
        repos_resp = requests.get(repos_url, headers=headers)
        repos_data = repos_resp.json() if repos_resp.status_code == 200 else []
        
        total_stars = sum(repo.get("stargazers_count", 0) for repo in repos_data)
        
        # Languages (Approximation from top repos)
        languages = {}
        for repo in repos_data[:10]: # Check top 10 repos
            lang = repo.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
        
        top_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
        

        # Ensure total_commits is always an integer
        total_commits = 0 

        try:
            contrib_url = f"https://github-contributions-api.jogruber.de/v4/{username}"
            contrib_resp = requests.get(contrib_url)
            if contrib_resp.status_code == 200:
                c_data = contrib_resp.json()
                if 'total' in c_data and isinstance(c_data['total'], dict):
                    # Sum all year totals into a single integer
                    total_commits = sum(c_data['total'].values())
            # If the response isn't 200, it stays as 0
        except Exception as ex:
            print(f"Contrib API Error: {ex}")
            total_commits = 0 # Safety fallback

        data = {
            "username": username,
            "total_stars": total_stars,
            "total_commits": total_commits,
            "public_repos": user_data.get("public_repos", 0),
            "followers": user_data.get("followers", 0),
            "top_languages": top_langs,
        }

        # --- Optional GraphQL enrichment ---
        graphql_data = fetch_github_graphql(username)
        if graphql_data:
            try:
                contributions, gql_total_commits = parse_graphql_contributions(graphql_data)
                data["contributions"] = contributions
                data["total_commits"] = gql_total_commits
            except Exception:
                pass  # Never break REST fallback

        return data

            
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_mock_data(username):
    """Returns dummy data for layout testing/building without hitting API limits"""
    return {
        "username": username,
        "total_stars": 120,
        "total_commits": 450,
        "public_repos": 25,
        "followers": 85,
        "top_languages": [("Python", 10), ("JavaScript", 5), ("Rust", 2)],
        "contributions":[ 
            {"date": f"2025-01-{i+1:02d}", "count": (i * 3) % 10}
            for i in range(80)
        ]

    }
