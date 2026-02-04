from fastapi import FastAPI, Response, Query
from generators import stats_card, lang_card, contrib_card
from utils import github_api
from typing import Optional

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "GitCanvas API is running"}

# this is for the error returned SVG
def error_svg(title: str, message: str):
    return f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="400" height="120">
        <rect width="100%" height="100%" fill="#0d1117"/>
        <text x="50%" y="45%" fill="#f85149" font-size="20"
              font-family="Arial, Helvetica, sans-serif"
              dominant-baseline="middle" text-anchor="middle">
            {title}
        </text>
        <text x="50%" y="70%" fill="#c9d1d9" font-size="14"
              font-family="Arial, Helvetica, sans-serif"
              dominant-baseline="middle" text-anchor="middle">
            {message}
        </text>
    </svg>
    """

def parse_colors(bg_color, title_color, text_color, border_color):
    """Helper to construct custom color dict only if values are provided."""
    colors = {}
    if bg_color: colors["bg_color"] = f"#{bg_color}" if not bg_color.startswith("#") else bg_color
    if title_color: colors["title_color"] = f"#{title_color}" if not title_color.startswith("#") else title_color
    if text_color: colors["text_color"] = f"#{text_color}" if not text_color.startswith("#") else text_color
    if border_color: colors["border_color"] = f"#{border_color}" if not border_color.startswith("#") else border_color
    return colors if colors else None

@app.get("/api/stats")
async def get_stats(
    username: str, 
    theme: str = "Default", 
    hide_stars: bool = False,
    hide_commits: bool = False,
    hide_repos: bool = False,
    hide_followers: bool = False,
    bg_color: Optional[str] = None,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    border_color: Optional[str] = None
):
    data = github_api.get_live_github_data(username) # get the userdata from the github api function

    if isinstance(data, dict) and data.get("error") == "User not found":
        svg = error_svg("User Not Found", f"GitHub user '{username}' does not exist")
        return Response(content=svg, media_type="image/svg+xml")

    if not data:
        svg = error_svg("Rate Limited", "GitHub API rate limit exceeded")
        return Response(content=svg, media_type="image/svg+xml")

    
    show_options = {
        "stars": not hide_stars,
        "commits": not hide_commits,
        "repos": not hide_repos,
        "followers": not hide_followers
    }
    
    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)
    svg_content = stats_card.draw_stats_card(data, theme, show_options=show_options, custom_colors=custom_colors)
    return Response(content=svg_content, media_type="image/svg+xml")

@app.get("/api/languages")
async def get_languages(
    username: str,
    theme: str = "Default",
    bg_color: Optional[str] = None,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    border_color: Optional[str] = None
):
    # get the userdata from the github api function
    data = github_api.get_live_github_data(username)

    if isinstance(data, dict) and data.get("error") == "User not found":
        return Response(
            content=error_svg("User Not Found", f"GitHub user '{username}' does not exist"),
            media_type="image/svg+xml"
        )

    if not data:
        return Response(
            content=error_svg("Rate Limited", "GitHub API rate limit exceeded"),
            media_type="image/svg+xml"
        )

    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)
    svg_content = lang_card.draw_lang_card(data, theme, custom_colors=custom_colors)
    return Response(content=svg_content, media_type="image/svg+xml")

@app.get("/api/contributions")
async def get_contributions(
    username: str,
    theme: str = "Default",
    bg_color: Optional[str] = None,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    border_color: Optional[str] = None
):
    # get the userdata from the github api function
    data = github_api.get_live_github_data(username)

    if isinstance(data, dict) and data.get("error") == "User not found":
        return Response(
            content=error_svg("User Not Found", f"GitHub user '{username}' does not exist"),
            media_type="image/svg+xml"
        )

    if not data:
        return Response(
            content=error_svg("Rate Limited", "GitHub API rate limit exceeded"),
            media_type="image/svg+xml"
        )


    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)
    svg_content = contrib_card.draw_contrib_card(data, theme, custom_colors=custom_colors)
    return Response(content=svg_content, media_type="image/svg+xml")
