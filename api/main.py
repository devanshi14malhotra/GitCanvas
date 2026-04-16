import hashlib
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Response, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from config.settings import get_settings
from generators import stats_card, lang_card, contrib_card, recent_activity_card, trophy_card, streak_card, repo_card, social_card, badge_generator
from utils import github_api
from utils.cache import cache_svg_response, get_cache_stats, clear_cache
from utils.validators import (
    validate_date,
    validate_hex_color,
    validate_limit,
    validate_sort_by,
    validate_theme,
    validate_username,
)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    settings.log_backend_warnings()
    yield

app = FastAPI(lifespan=lifespan)

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


def image_response(svg_content: str, request: Request, format: str = "svg"):
    format = format.lower()
    if format not in ["svg", "png", "jpeg", "jpg"]:
        raise HTTPException(status_code=400, detail="Invalid format. Supported formats: svg, png, jpeg")

    etag_content = f"{svg_content}_{format}"
    etag = hashlib.md5(etag_content.encode("utf-8")).hexdigest()

    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304)

    if format == "svg":
        content = svg_content
        media_type = "image/svg+xml"
    else:
        try:
            import cairosvg
        except (ImportError, OSError):
            raise HTTPException(
                status_code=500,
                detail="Server-side image generation is disabled (Cairo library not found). Please use format=svg."
            )
            
        try:
            png_bytes = cairosvg.svg2png(bytestring=svg_content.encode("utf-8"))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating PNG: {e}")

        if format == "png":
            content = png_bytes
            media_type = "image/png"
            
        elif format in ["jpeg", "jpg"]:
            try:
                from PIL import Image
                import io
            except ImportError:
                raise HTTPException(
                    status_code=500,
                    detail="Server-side JPEG generation is disabled (Pillow library not found). Please use format=svg or png."
                )
            try:
                img = Image.open(io.BytesIO(png_bytes))
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[3])
                    img = background
                else:
                    img = img.convert('RGB')
                    
                out = io.BytesIO()
                img.save(out, format="JPEG", quality=90)
                content = out.getvalue()
                media_type = "image/jpeg"
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error generating JPEG: {e}")

    headers = {
        "Cache-Control": "public, max-age=14400, s-maxage=14400",
        "ETag": etag,
        "Vary": "Accept-Encoding",
        "X-Content-Type-Options": "nosniff"
    }
    
    if format == "svg":
        headers["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'; img-src data:"
        headers["X-Frame-Options"] = "SAMEORIGIN"

    return Response(
        content=content,
        media_type=media_type,
        headers=headers
    )


def cached_text_response(content: str, request: Request, media_type: str = "text/plain; charset=utf-8"):
    """Return text response with ETag and CDN-friendly cache headers."""
    etag = hashlib.md5(content.encode("utf-8")).hexdigest()

    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304)

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=14400, s-maxage=14400",
            "ETag": etag,
            "Vary": "Accept-Encoding",
            "X-Content-Type-Options": "nosniff"
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
    border_color: Optional[str] = None,
    format: str = "svg"
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
    return image_response(svg_content, request, format)


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
    border_color: Optional[str] = None,
    format: str = "svg"
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
    return image_response(svg_content, request, format)


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
    end_date: Optional[str] = None,
    format: str = "svg"
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
    return image_response(svg_content, request, format)


@app.get("/api/recent")
async def get_recent(
    request: Request,
    username: str,
    theme: str = "Default",
    bg_color: Optional[str] = None,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    border_color: Optional[str] = None,
    format: str = "svg"
):
    # Validate inputs
    username = validate_username(username)
    theme = validate_theme(theme)
    
    # SECURITY FIX: Get token from Authorization header instead of URL parameter
    # This prevents token exposure in logs, browser history, and proxy logs
    token = get_token_from_header(request)
    
    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)
    svg_content = recent_activity_card.draw_recent_activity_card({'username': username}, theme, custom_colors=custom_colors, token=token)
    return image_response(svg_content, request, format)


@app.get("/api/trophy")
async def get_trophy(
    request: Request,
    username: str,
    theme: str = "Default",
    bg_color: Optional[str] = None,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    border_color: Optional[str] = None,
    format: str = "svg"
):
    # Validate inputs
    username = validate_username(username)
    theme = validate_theme(theme)
    
    data = github_api.get_live_github_data(username) or github_api.get_mock_data(username)
    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)
    svg_content = trophy_card.draw_trophy_card(data, theme, custom_colors=custom_colors)
    return image_response(svg_content, request, format)


@app.get("/api/streak")
async def get_streak(
    request: Request,
    username: str,
    theme: str = "Default",
    bg_color: Optional[str] = None,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    border_color: Optional[str] = None,
    format: str = "svg"
):
    # Validate inputs
    username = validate_username(username)
    theme = validate_theme(theme)
    
    data = github_api.get_live_github_data(username) or github_api.get_mock_data(username)
    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)
    svg_content = streak_card.draw_streak_card(data, theme, custom_colors=custom_colors)
    return image_response(svg_content, request, format)


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
    border_color: Optional[str] = None,
    format: str = "svg"
):
    # Validate inputs
    username = validate_username(username)
    theme = validate_theme(theme)
    sort_by = validate_sort_by(sort_by)
    limit = validate_limit(limit, min_val=1, max_val=10)
    
    data = github_api.get_live_github_data(username) or github_api.get_mock_data(username)
    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)
    svg_content = repo_card.draw_repo_card(data, theme, custom_colors=custom_colors, sort_by=sort_by, limit=limit)
    return image_response(svg_content, request, format)


@app.get("/api/social_card")
async def get_social_card(
    request: Request,
    theme: str = "Default",
    platforms: Optional[str] = None,
    icon_color: Optional[str] = None,
    twitter: Optional[str] = None,
    linkedin: Optional[str] = None,
    website: Optional[str] = None,
    email: Optional[str] = None,
    youtube: Optional[str] = None,
    bg_color: Optional[str] = None,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    border_color: Optional[str] = None,
    format: str = "svg"
):
    theme = validate_theme(theme)
    custom_colors = parse_colors(bg_color, title_color, text_color, border_color)

    if icon_color:
        icon_color = validate_hex_color(icon_color)

    social_data = {
        "twitter": twitter,
        "linkedin": linkedin,
        "website": website,
        "email": email,
        "youtube": youtube,
    }

    selected_platforms = None
    if platforms:
        selected_platforms = [p.strip().lower() for p in platforms.split(",") if p.strip()]
        invalid_platforms = [
            p for p in selected_platforms
            if p not in social_card.SOCIAL_PLATFORMS
        ]
        if invalid_platforms:
            valid = ", ".join(sorted(social_card.SOCIAL_PLATFORMS.keys()))
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platforms: {', '.join(invalid_platforms)}. Valid values: {valid}"
            )

    svg_content = generate_cached_svg(
        social_card.draw_social_card,
        social_data,
        theme,
        custom_colors=custom_colors,
        selected_platforms=selected_platforms,
        icon_color=icon_color,
    )
    return image_response(svg_content, request, format)


@app.get("/api/badges")
@app.get("/api/badge_generator")
async def get_badges(
    request: Request,
    tools: str,
    style: str = "for-the-badge",
    match_theme_color: bool = False,
    theme: str = "Default",
    format: str = "markdown",
    link: Optional[str] = None,
):
    """
    Generate tech badge markdown (or JSON payload) from comma-separated tool names.

    Example:
    /api/badges?tools=Python,FastAPI,Docker&style=flat-square
    """
    valid_styles = {"for-the-badge", "flat", "flat-square", "plastic", "social"}
    if style not in valid_styles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid style. Choose from: {', '.join(sorted(valid_styles))}"
        )

    output_format = format.lower().strip()
    if output_format not in {"markdown", "json"}:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'markdown' or 'json'.")

    if match_theme_color:
        theme = validate_theme(theme)

    requested_tools = [tool.strip() for tool in tools.split(",") if tool.strip()]
    if not requested_tools:
        raise HTTPException(status_code=400, detail="At least one tool is required.")

    # Build a case-insensitive lookup of all supported tools.
    tool_lookup = {}
    for category, category_tools in badge_generator.TECH_STACK.items():
        for tool_name, config in category_tools.items():
            tool_lookup[tool_name.lower()] = {
                "name": tool_name,
                "category": category,
                "config": config,
            }

    unknown_tools = [tool for tool in requested_tools if tool.lower() not in tool_lookup]
    if unknown_tools:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported tools: {', '.join(unknown_tools)}"
        )

    title_color = None
    if match_theme_color:
        from themes.styles import THEMES
        title_color = THEMES.get(theme, THEMES["Default"])["title_color"].replace("#", "")

    badge_items = []
    markdown_parts = []

    for tool in requested_tools:
        tool_meta = tool_lookup[tool.lower()]
        tool_name = tool_meta["name"]
        tool_config = tool_meta["config"]
        color = title_color or tool_config["color"]

        badge_url = badge_generator.generate_badge_url(
            tool_name,
            color,
            tool_config["logo"],
            style=style,
        )
        markdown = badge_generator.generate_markdown(tool_name, badge_url, link=link)

        badge_items.append(
            {
                "tool": tool_name,
                "category": tool_meta["category"],
                "badge_url": badge_url,
                "markdown": markdown,
            }
        )
        markdown_parts.append(markdown)

    markdown_output = " ".join(markdown_parts)

    if output_format == "json":
        import json

        json_content = json.dumps(
            {
                "style": style,
                "match_theme_color": match_theme_color,
                "theme": theme,
                "tools": badge_items,
                "markdown": markdown_output,
            },
            separators=(",", ":"),
        )
        return cached_text_response(json_content, request, media_type="application/json")

    return cached_text_response(markdown_output, request)

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