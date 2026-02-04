import hashlib
from fastapi import FastAPI, Response, Query , Request
from generators import stats_card, lang_card, contrib_card
from utils import github_api
from typing import Optional

app = FastAPI()

# Implements HTTP conditional requests for CDN-safe SVG caching

def svg_response(svg_content: str, request: Request):
    etag = hashlib.md5(svg_content.encode("utf-8")).hexdigest()

    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304)

    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=14400, s-maxage=14400",
            "ETag": etag,
            "Vary": "Accept-Encoding"
        }
    )



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
    request: Request,
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
    return svg_response(svg_content , request)


@app.get("/api/languages")
async def get_languages(
    request: Request,
    username: str,
    theme: str = "Default",
    bg_color: Optional[str] = None,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    border_color: Optional[str] = None
):
    data = github_api.get_live_github_data(username) or github_api.get_mock_data(username)
    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)
    svg_content = lang_card.draw_lang_card(data, theme, custom_colors=custom_colors)
    return svg_response(svg_content , request)


@app.get("/api/contributions")
async def get_contributions(
    request: Request,
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
    return svg_response(svg_content , request)

