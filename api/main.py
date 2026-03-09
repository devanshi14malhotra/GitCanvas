import hashlib
from fastapi import FastAPI, Response, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from generators import stats_card, lang_card, contrib_card, recent_activity_card, trophy_card, streak_card, repo_card
from utils import github_api
from utils.cache import cache_svg_response, get_cache_stats, clear_cache
from typing import Optional

app = FastAPI()

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_methods=["GET", "DELETE"],  # Allow GET for API endpoints and DELETE for cache management
    allow_headers=["*"],
    allow_credentials=False,  # Set to True if you need to support credentials
)

# Implements HTTP conditional requests for CDN-safe SVG caching

@cache_svg_response
def generate_cached_svg(generator_func, *args, **kwargs):
    """
    Wrapper function to cache SVG generation results
    """
    return generator_func(*args, **kwargs)


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
            "Vary": "Accept-Encoding",
            # Security headers to prevent XSS
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src data:",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN"
        }
    )


def get_token_from_header(request: Request) -> Optional[str]:
    """
    Securely extract GitHub token from Authorization header.
    
    SECURITY: Tokens should NEVER be in URL parameters as they get logged in:
    - Server access logs
    - Browser history
    - Proxy logs
    - Referrer headers
    
    Use: Authorization: Bearer <token>
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Token string or None if not provided
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]  # Remove "Bearer " prefix
    return None


@app.get("/")
def read_root():
    return {"message": "GitCanvas API is running"}

def parse_colors(bg_color, title_color, text_color, border_color):
    """Helper to construct custom color dict with validation."""
    colors = {}
    
    # Validate and add colors
    if bg_color:
        validated_bg = validate_hex_color(bg_color)
        if validated_bg:
            colors["bg_color"] = validated_bg
            
    if title_color:
        validated_title = validate_hex_color(title_color)
        if validated_title:
            colors["title_color"] = validated_title
            
    if text_color:
        validated_text = validate_hex_color(text_color)
        if validated_text:
            colors["text_color"] = validated_text
            
    if border_color:
        validated_border = validate_hex_color(border_color)
        if validated_border:
            colors["border_color"] = validated_border
    
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
    animations_enabled: bool = True,
    bg_color: Optional[str] = None,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    border_color: Optional[str] = None
):
    # Validate inputs
    username = validate_username(username)
    theme = validate_theme(theme)
    
    # Get optional token from Authorization header for higher rate limits
    token = get_token_from_header(request)
    
    data = github_api.get_live_github_data(username, token) or github_api.get_mock_data(username)
    
    show_options = {
        "stars": not hide_stars,
        "commits": not hide_commits,
        "repos": not hide_repos,
        "followers": not hide_followers
    }
    
    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)
    svg_content = generate_cached_svg(stats_card.draw_stats_card, data, theme, show_options=show_options, custom_colors=custom_colors, animations_enabled=animations_enabled)
    return svg_response(svg_content , request)


@app.get("/api/languages")
async def get_languages(
    request: Request,
    username: str,
    theme: str = "Default",
    exclude: Optional[str] = None,
    excluded_languages: Optional[str] = None,
    bg_color: Optional[str] = None,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    border_color: Optional[str] = None
):
    # Validate inputs
    username = validate_username(username)
    theme = validate_theme(theme)
    
    data = github_api.get_live_github_data(username) or github_api.get_mock_data(username)
    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)
    
    # Parse exclude parameter into list of languages
    excluded_languages_list = []
    # Support both 'exclude' and 'excluded_languages' parameters
    param_value = exclude or excluded_languages
    if param_value:
        excluded_languages_list = [lang.strip() for lang in param_value.split(',') if lang.strip()]
    
    svg_content = generate_cached_svg(lang_card.draw_lang_card, data, theme, custom_colors=custom_colors, excluded_languages=excluded_languages_list)
    return svg_response(svg_content , request)


@app.get("/api/contributions")
async def get_contributions(
    request: Request,
    username: str,
    theme: str = "Default",
    animations_enabled: bool = True,
    date_range: Optional[str] = None,
    bg_color: Optional[str] = None,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    border_color: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    # Validate inputs
    username = validate_username(username)
    theme = validate_theme(theme)
    start_date = validate_date(start_date)
    end_date = validate_date(end_date)
    
    data = github_api.get_live_github_data(username) or github_api.get_mock_data(username)
    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)
    
    # Build date_range dict if dates are provided
    date_range = None
    if start_date and end_date:
        date_range = {
            'start': start_date,
            'end': end_date
        }
    
    svg_content = generate_cached_svg(contrib_card.draw_contrib_card, data, theme, custom_colors=custom_colors, date_range=date_range, animations_enabled=animations_enabled)
    return svg_response(svg_content , request)


@app.get("/api/recent")
async def get_recent(
    request: Request,
    username: str,
    theme: str = "Default",
    bg_color: Optional[str] = None,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    border_color: Optional[str] = None
):
    # Validate inputs
    username = validate_username(username)
    theme = validate_theme(theme)
    
    # SECURITY FIX: Get token from Authorization header instead of URL parameter
    # This prevents token exposure in logs, browser history, and proxy logs
    token = get_token_from_header(request)
    
    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)
    svg_content = recent_activity_card.draw_recent_activity_card({'username': username}, theme, custom_colors=custom_colors, token=token)
    return svg_response(svg_content, request)


@app.get("/api/trophy")
async def get_trophy(
    request: Request,
    username: str,
    theme: str = "Default",
    bg_color: Optional[str] = None,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    border_color: Optional[str] = None
):
    # Validate inputs
    username = validate_username(username)
    theme = validate_theme(theme)
    
    data = github_api.get_live_github_data(username) or github_api.get_mock_data(username)
    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)
    svg_content = trophy_card.draw_trophy_card(data, theme, custom_colors=custom_colors)
    return svg_response(svg_content, request)


@app.get("/api/streak")
async def get_streak(
    request: Request,
    username: str,
    theme: str = "Default",
    bg_color: Optional[str] = None,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    border_color: Optional[str] = None
):
    # Validate inputs
    username = validate_username(username)
    theme = validate_theme(theme)
    
    data = github_api.get_live_github_data(username) or github_api.get_mock_data(username)
    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)
    svg_content = streak_card.draw_streak_card(data, theme, custom_colors=custom_colors)
    return svg_response(svg_content, request)


@app.get("/api/repos")
async def get_repos(
    request: Request,
    username: str,
    theme: str = "Default",
    sort_by: str = "stars",
    limit: int = 5,
    bg_color: Optional[str] = None,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    border_color: Optional[str] = None
):
    # Validate inputs
    username = validate_username(username)
    theme = validate_theme(theme)
    sort_by = validate_sort_by(sort_by)
    limit = validate_limit(limit, min_val=1, max_val=10)
    
    data = github_api.get_live_github_data(username) or github_api.get_mock_data(username)
    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)
    svg_content = repo_card.draw_repo_card(data, theme, custom_colors=custom_colors, sort_by=sort_by, limit=limit)
    return svg_response(svg_content, request)

# Cache management endpoints

@app.get("/api/cache/stats")
async def get_cache_statistics():
    """
    Get cache statistics including hit rates and cache sizes
    """
    return get_cache_stats()


@app.delete("/api/cache/clear")
async def clear_all_caches():
    """
    Clear all caches (GitHub API and SVG caches)
    """
    return clear_cache()


@app.delete("/api/cache/clear/{cache_type}")
async def clear_specific_cache(cache_type: str):
    """
    Clear specific cache type
    
    Args:
        cache_type: 'github_api' or 'svg'
    """
    if cache_type not in ['github_api', 'svg']:
        return {"error": "Invalid cache type. Use 'github_api' or 'svg'"}
    
    return clear_cache(cache_type)