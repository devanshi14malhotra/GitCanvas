import svgwrite
from themes.styles import THEMES

def draw_stats_card(data, theme_name="Default", show_options=None, custom_colors=None):
    # Handling API Error first 
    if data is None or "error" in data:
        return draw_error_stats_svg(
            data.get("error", "UNKNOWN") if isinstance(data, dict) else "UNKNOWN"
        )
    
    """
    Generates the Main Stats Card SVG.
    data: dict with user stats
    theme_name: string key from THEMES
    show_options: dict with toggles (e.g. {'stars': True, 'prs': False})
    """
    if show_options is None:
        show_options = {"stars": True, "commits": True, "repos": True, "followers": True}
        
    theme = THEMES.get(theme_name, THEMES["Default"]).copy()
    if custom_colors:
        theme.update(custom_colors)

    
    width = 450
    # Calculate height dynamically based on visible items
    base_height = 50
    item_height = 25
    visible_items = sum(1 for k, v in show_options.items() if v)
    height = base_height + (visible_items * item_height) + 10
    
    dwg = svgwrite.Drawing(size=(f"{width}px", f"{height}px"))
    
    # Background
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=10, ry=10, 
                     fill=theme["bg_color"], stroke=theme["border_color"], stroke_width=2))
    
    # Title
    font_family = theme["font_family"]
    dwg.add(dwg.text(f"{data['username']}'s Stats", insert=(20, 35), 
                     fill=theme["title_color"], font_size=theme["title_font_size"], font_family=font_family, font_weight="bold"))
    
    # Stats
    start_y = 65
    current_y = start_y
    text_color = theme["text_color"]
    font_size = theme["text_font_size"]
    
    # Logic to handle N/A display for commits if the value is 0 (API error)
    commit_val = data.get('total_commits', 0)
    # If commit_val is 0, we show "N/A", otherwise we show the number
    display_commits = str(commit_val) if commit_val > 0 else "N/A"

    stats_map = [
        ("stars", "Total Stars", f"{data.get('total_stars', 0)}"),
        ("commits", "Total Commits", display_commits),
        ("repos", "Public Repos", f"{data.get('public_repos', 0)}"),
        ("followers", "Followers", f"{data.get('followers', 0)}")
    ]
    
    for key, label, value in stats_map:
        if show_options.get(key, True):
            # Icon approximation (Circle)
            dwg.add(dwg.circle(center=(30, current_y - 5), r=4, fill=theme["icon_color"]))
            
            # Label
            dwg.add(dwg.text(f"{label}:", insert=(45, current_y), 
                             fill=text_color, font_size=font_size, font_family=font_family))
            
            # Value (Right aligned roughly)
            dwg.add(dwg.text(f"{value}", insert=(width - 40, current_y), 
                             fill=text_color, font_size=font_size, font_family=font_family, text_anchor="end", font_weight="bold"))
                             
            current_y += item_height
            
    return dwg.tostring()

# defining draw_error_stats_svg
def draw_error_stats_svg(error_type):
    messages = {
        "USER_NOT_FOUND": "GitHub User Not Found",
        "RATE_LIMITED": "GitHub API Rate Limited",
        "GITHUB_API_ERROR": "GitHub API Error",
        "INTERNAL_ERROR": "Internal Server Error",
        "UNKNOWN": "Something went wrong"
    }

    msg = messages.get(error_type, "Error")

    dwg = svgwrite.Drawing(size=("450px", "120px"))
    dwg.add(dwg.rect(
        insert=(0, 0),
        size=("100%", "100%"),
        rx=10,
        ry=10,
        fill="#0d1117",
        stroke="#30363d",
        stroke_width=2
    ))

    dwg.add(dwg.text(
        msg,
        insert=("50%", "55%"),
        text_anchor="middle",
        fill="#f85149",
        font_size="18",
        font_family="monospace",
        font_weight="bold"
    ))

    return dwg.tostring()
