import svgwrite
from themes.styles import THEMES
from .svg_base import create_svg_base

def draw_stats_card(data, theme_name="Default", show_options=None, custom_colors=None):
    """
    Generates the Main Stats Card SVG.
    data: dict with user stats
    theme_name: string key from THEMES
    show_options: dict with toggles (e.g. {'stars': True, 'prs': False})
    """
    if show_options is None:
        show_options = {"stars": True, "commits": True, "repos": True, "followers": True}

    # FIXED: Handle both string theme name and pre-resolved theme dict
    if isinstance(theme_name, dict):
        # Already a theme dictionary (e.g., current_theme_opts from app.py)
        theme = theme_name.copy()
    else:
        # Convert theme_name string to actual theme dictionary
        theme = THEMES.get(theme_name, THEMES["Default"]).copy()
        
        # Apply custom colors if provided
        if custom_colors:
            theme.update(custom_colors)

    width = 450
    # Calculate height dynamically based on visible items
    base_height = 50
    item_height = 25
    visible_items = sum(1 for k, v in show_options.items() if v)
    height = base_height + (visible_items * item_height) + 10
    
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
    
    # Add minimal CSS animations
    style = dwg.defs.add(dwg.style("""
        /* Minimal keyframes for text fade-in */
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        /* Minimal keyframes for number count-up effect */
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Apply animations to text elements */
        .title-text {
            animation: fadeIn 0.6s ease-out;
        }
        
        .stat-label {
            animation: fadeIn 0.6s ease-out;
            animation-delay: 0.2s;
            animation-fill-mode: both;
        }
        
        .stat-value {
            animation: slideUp 0.5s ease-out;
            animation-delay: 0.4s;
            animation-fill-mode: both;
        }
    """))
    
    # Background (no animation)
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=10, ry=10, 
                     fill=theme["bg_color"], stroke=theme["border_color"], stroke_width=2))
    
    # Title with animation
    font_family = theme["font_family"]
    dwg.add(dwg.text(f"{data['username']}'s Stats", insert=(20, 35), 
                     fill=theme["title_color"], font_size=theme["title_font_size"], 
                     font_family=font_family, font_weight="bold", class_="title-text"))
    
    # Stats
    start_y = 65
    current_y = start_y
    text_color = theme["text_color"]
    font_size = theme["text_font_size"]
    
    stats_map = [
        ("stars", "Total Stars", f"{data.get('total_stars', 0)}"),
        ("commits", "Total Commits (Year)", f"{data.get('total_commits', 'N/A')}"),
        ("repos", "Public Repos", f"{data.get('public_repos', 0)}"),
        ("followers", "Followers", f"{data.get('followers', 0)}")
    ]
    
    for key, label, value in stats_map:
        if show_options.get(key, True):
            # Icon (no animation)
            dwg.add(dwg.circle(center=(30, current_y - 5), r=4, fill=theme["icon_color"]))
            
            # Label with fade-in animation
            dwg.add(dwg.text(f"{label}:", insert=(45, current_y), 
                             fill=text_color, font_size=font_size, 
                             font_family=font_family, class_="stat-label"))
            
            # Value with slide-up animation
            dwg.add(dwg.text(f"{value}", insert=(width - 40, current_y), 
                             fill=text_color, font_size=font_size, 
                             font_family=font_family, text_anchor="end", 
                             font_weight="bold", class_="stat-value"))
                             
            current_y += item_height
            
    return dwg.tostring()