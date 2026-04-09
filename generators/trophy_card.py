import svgwrite
from themes.styles import THEMES
from .svg_base import create_svg_base


def draw_trophy_card(data, theme_name="Default", custom_colors=None, font_family=None):
    """
    Generates the GitHub Trophy Card SVG showing achievements.
    font_family: optional custom font family override (e.g. 'Inter', 'Roboto')
    """
    width = 450
    height = 240  # Increased for breathing room and to prevent bottom overlap
    
    # Calculate total forks from all repositories
    total_forks = sum(repo.get("forks", 0) for repo in data.get("top_repos", []))
    
    # Calculate years of contribution
    created_at = data.get("created_at", "")
    years_contributing = 0
    if created_at:
        try:
            from datetime import datetime
            created_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
            years_contributing = (datetime.now() - created_date).days // 365
            if years_contributing < 1:
                years_contributing = 1
        except Exception:
            years_contributing = 1
    
    # Determine repository quality tier
    total_stars = data.get("total_stars", 0)
    if total_stars >= 1000:
        repo_tier, tier_color = "Legend", "#FFD700"
    elif total_stars >= 100:
        repo_tier, tier_color = "Pro", "#C0C0C0"
    else:
        repo_tier, tier_color = "Newcomer", "#CD7F32"
    
    # Validate username to prevent KeyError
    username = data.get('username', 'Unknown')
    dwg, theme = create_svg_base(theme_name, custom_colors, width, height, f"{username}'s Trophy")
    
    # Use custom font override if provided, otherwise fall back to theme
    font_family = font_family if font_family else theme["font_family"]
    text_color = theme["text_color"]
    title_color = theme["title_color"]
    icon_color = theme["icon_color"]
    
    # Real GitHub Logo via Base64 SVG (Bypasses svgwrite path validation)
    import base64
    gh_svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="{text_color}" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.202 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.92.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.577.688.48C19.137 20.167 22 16.418 22 12c0-5.523-4.477-10-10-10z"/></svg>'
    gh_b64 = base64.b64encode(gh_svg.encode()).decode()
    dwg.add(dwg.image(href=f"data:image/svg+xml;base64,{gh_b64}", insert=(405, 15), size=(24, 24), opacity=0.7))

    # Detailed Trophy SVG
    trophy_group = dwg.g(id="trophy", transform="translate(60, 115)")
    # Shine effect (ellipse behind trophy doesn't overflow)
    trophy_group.add(dwg.ellipse(center=(0, 0), r=(35, 45), fill=tier_color, opacity=0.15))
    # Base
    trophy_group.add(dwg.path(d="M-25,30 h50 v5 a3,3 0 0 1 -3,3 h-44 a3,3 0 0 1 -3,-3 z", fill=icon_color))
    trophy_group.add(dwg.rect(insert=(-12, 18), size=(24, 12), fill=icon_color, rx=2))
    # Cup
    trophy_group.add(dwg.path(d="M-22,18 L-18,-15 Q-18,-25 0,-25 Q18,-25 18,-15 L22,18 Z", fill=icon_color))
    # Handles
    trophy_group.add(dwg.path(d="M-18,0 Q-32,-2 -28,15", fill="none", stroke=icon_color, stroke_width=3))
    trophy_group.add(dwg.path(d="M18,0 Q32,-2 28,15", fill="none", stroke=icon_color, stroke_width=3))
    # Star Shield on Trophy
    trophy_group.add(dwg.path(d="M0,-20 L8,-12 L5,-2 L-5,-2 L-8,-12 Z", fill=theme["bg_color"], opacity=0.5))
    star_path = "M0,-14 L2,-8 L8,-8 L3,-4 L5,2 L0,-1 L-5,2 L-3,-4 L-8,-8 L-2,-8 Z"
    trophy_group.add(dwg.path(d=star_path, fill=tier_color))
    dwg.add(trophy_group)

    # Repository Quality Tier Badge
    dwg.add(dwg.text(f"{repo_tier} Tier", insert=(60, 182), fill=tier_color, font_size=15, 
                     font_family=font_family, text_anchor="middle", font_weight="bold"))

    # Dashboard Stats Grid with simple valid SVG paths
    stats = [
        {"label": "Stars", "value": f"{total_stars:,}", 
         "icon": "M12,2 L15,8 L22,9 L17,14 L18,21 L12,18 L6,21 L7,14 L2,9 L9,8 Z"},
         
        {"label": "Forks", "value": f"{total_forks:,}", 
         "icon": "M8,2 V8 A4,4 0 0,0 16,8 V2 M12,8 V22 M9,14 L15,14 M12,2 V4"},
         
        {"label": "Followers", "value": f"{data.get('followers', 0):,}", 
         "icon": "M8,10 A4,4 0 1,1 16,10 A4,4 0 1,1 8,10 M4,20 Q12,14 20,20 V22 H4 Z"},
         
        {"label": "Experience", "value": f"{years_contributing} Yr{'s' if years_contributing != 1 else ''}", 
         "icon": "M4,6 H20 V20 H4 Z M4,10 H20 M8,4 V8 M16,4 V8 M8,14 H10 V16 H8 Z M14,14 H16 V16 H14 Z"}
    ]

    grid_x = [135, 290]
    grid_y = [75, 145]
    card_width = 145
    card_height = 55
    
    for i, stat in enumerate(stats):
        ix = grid_x[i % 2]
        iy = grid_y[i // 2]
        
        # Stat Card Background
        dwg.add(dwg.rect(insert=(ix, iy), size=(card_width, card_height), rx=6, ry=6, 
                         fill=text_color, opacity=0.08))
                         
        # Subtle border for stat card
        dwg.add(dwg.rect(insert=(ix, iy), size=(card_width, card_height), rx=6, ry=6, 
                         fill="none", stroke=text_color, stroke_width=1, opacity=0.25))
        
        # Icon (Valid SVG Path)
        dwg.add(dwg.path(d=stat["icon"], fill="none", stroke=icon_color, stroke_width=2, 
                         stroke_linejoin="round", stroke_linecap="round", 
                         transform=f"translate({ix + 10}, {iy + 15}) scale(0.9)"))
                         
        # Value (Large, bold)
        dwg.add(dwg.text(stat["value"], insert=(ix + 42, iy + 30), fill=title_color, 
                         font_size=18, font_family=font_family, font_weight="bold"))
                         
        # Label (Small, muted)
        dwg.add(dwg.text(stat["label"], insert=(ix + 42, iy + 45), fill=text_color, 
                         font_size=11, font_family=font_family, opacity=0.8))

    # Footer info (Positioned properly to avoid overlap)
    dwg.add(dwg.text(f"Public Repos: {data.get('public_repos', 0)}", 
                     insert=(width - 20, height - 15), 
                     fill=text_color, font_size=11, font_family=font_family, 
                     text_anchor="end", opacity=0.6))
    
    return dwg.tostring()

