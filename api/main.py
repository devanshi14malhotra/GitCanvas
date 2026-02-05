from fastapi import FastAPI, Response, Query
from generators import stats_card, lang_card, contrib_card, recent_activity_card
from utils import github_api
from typing import Optional

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "GitCanvas API is running"}

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
    data = github_api.get_live_github_data(username) or github_api.get_mock_data(username)
    
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
    exclude: Optional[str] = None,
    bg_color: Optional[str] = None,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    border_color: Optional[str] = None
):
    data = github_api.get_live_github_data(username) or github_api.get_mock_data(username)
    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)
    
    # Parse exclude parameter into list of languages
    excluded_languages = []
    if exclude:
        excluded_languages = [lang.strip() for lang in exclude.split(',') if lang.strip()]
    
    svg_content = lang_card.draw_lang_card(data, theme, custom_colors=custom_colors, excluded_languages=excluded_languages)
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
    data = github_api.get_live_github_data(username) or github_api.get_mock_data(username)
    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)
    svg_content = contrib_card.draw_contrib_card(data, theme, custom_colors=custom_colors)
    return Response(content=svg_content, media_type="image/svg+xml")


@app.get("/api/recent")
async def get_recent(
    username: str,
    theme: str = "Default",
    token: Optional[str] = None,
    bg_color: Optional[str] = None,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    border_color: Optional[str] = None
):
    data = github_api.get_live_github_data(username) or github_api.get_mock_data(username)
    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)
    svg_content = recent_activity_card.draw_recent_activity_card({'username': username}, theme, custom_colors=custom_colors, token=token)
    return Response(content=svg_content, media_type="image/svg+xml")
