import requests

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
        user_resp = requests.get(user_url)
        if user_resp.status_code != 200:
            return None
        user_data = user_resp.json()
        
        # Repos for stars count (limited to first 100 public repos for basic sum without pagination for MVP speed)
        repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&type=owner"
        repos_resp = requests.get(repos_url)
        repos_data = repos_resp.json() if repos_resp.status_code == 200 else []
        
        total_stars = sum(repo.get("stargazers_count", 0) for repo in repos_data)
        
        # Languages (Approximation from top repos)
        languages = {}
        for repo in repos_data[:10]: # Check top 10 repos
            lang = repo.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
        
        top_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Try to get Total Commits/Contributions via 3rd party API
        total_commits = 0
        try:
            contrib_url = f"https://github-contributions-api.jogruber.de/v4/{username}"
            contrib_resp = requests.get(contrib_url)
            if contrib_resp.status_code == 200:
                c_data = contrib_resp.json()
                
                # The API returns a 'total' dictionary with counts per year
                # e.g., {"total": {"2022": 500, "2023": 600}}
                if 'total' in c_data and isinstance(c_data['total'], dict):
                    total_commits = sum(c_data['total'].values())
                else:
                    total_commits = "N/A"
            else:
                total_commits = "N/A"
        except Exception as ex:
            print(f"Contrib API Error: {ex}")
            total_commits = "N/A"

        return {
            "username": username,
            "total_stars": total_stars,
            "total_commits": total_commits,
            "public_repos": user_data.get("public_repos", 0),
            "followers": user_data.get("followers", 0),
            "top_languages": top_langs
        }
            
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
        "top_languages": [("Python", 10), ("JavaScript", 5), ("Rust", 2)]
    }
