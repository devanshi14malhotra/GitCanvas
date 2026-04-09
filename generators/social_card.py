import svgwrite
from themes.styles import THEMES

# Social platform configurations with shields.io logo names
SOCIAL_PLATFORMS = {
    "twitter": {
        "name": "Twitter",
        "logo": "twitter",
        "color": "1DA1F2",
        "placeholder": "username"
    },
    "linkedin": {
        "name": "LinkedIn",
        "logo": "linkedin",
        "color": "0A66C2",
        "placeholder": "username"
    },
    "website": {
        "name": "Website",
        "logo": "googlechrome",  # Using Chrome icon as generic web icon
        "color": "4285F4",
        "placeholder": "example.com"
    },
    "email": {
        "name": "Email",
        "logo": "gmail",
        "color": "EA4335",
        "placeholder": "email@example.com"
    },
    "youtube": {
        "name": "YouTube",
        "logo": "youtube",
        "color": "FF0000",
        "placeholder": "channel"
    }
}

def generate_social_badge_url(platform, label, color, logo, style="for-the-badge", logo_color="white"):
    """
    Generates a Shields.io badge URL for social media icons.
    """
    safe_label = label.replace(" ", "%20")
    safe_color = color.replace("#", "")
    return f"https://img.shields.io/badge/{safe_label}-{safe_color}?style={style}&logo={logo}&logoColor={logo_color}"

def draw_social_card(social_data, theme_name="Default", custom_colors=None, selected_platforms=None, icon_color=None, font_family=None):
    """
    Generates the Social Links Card SVG.
    
    Args:
        font_family: optional custom font family override (e.g. 'Inter', 'Roboto')
        social_data: dict with social media URLs (e.g., {'twitter': 'https://twitter.com/user', ...})
        theme_name: string key from THEMES
        custom_colors: dict with custom color overrides
        selected_platforms: list of platform keys to display (e.g., ['twitter', 'linkedin'])
        icon_color: optional custom color for all icons (hex string)
    """
    # Handle both string theme name and pre-resolved theme dict
    if isinstance(theme_name, dict):
        theme = theme_name.copy()
    else:
        theme = THEMES.get(theme_name, THEMES["Default"]).copy()
        
    # Apply custom colors if provided
    if custom_colors:
        theme.update(custom_colors)
    
    # Determine font family - use custom override if provided, otherwise fall back to theme
    effective_font_family = font_family if font_family else theme.get("font_family", "Segoe UI, sans-serif")
    
    # Filter to only selected platforms that have data
    if selected_platforms is None:
        selected_platforms = list(SOCIAL_PLATFORMS.keys())
    
    # Build list of active platforms with URLs
    active_platforms = []
    for platform_key in selected_platforms:
        if platform_key in SOCIAL_PLATFORMS and platform_key in social_data and social_data[platform_key]:
            platform_info = SOCIAL_PLATFORMS[platform_key].copy()
            platform_info["key"] = platform_key
            platform_info["url"] = social_data[platform_key]
            active_platforms.append(platform_info)
    
    # If no active platforms, show placeholder
    if not active_platforms:
        active_platforms = [{
            "key": "none",
            "name": "No Links",
            "logo": "github",
            "color": "181717",
            "url": "#",
            "placeholder": "Add social links"
        }]
    
    # Calculate dimensions
    width = 450
    badge_width = 100  # Approximate width per badge
    badge_height = 28   # Badge height
    badge_spacing = 10  # Space between badges
    
    # Layout: 2 columns of badges
    cols = 2
    rows = (len(active_platforms) + cols - 1) // cols  # Ceiling division
    
    header_height = 50
    footer_height = 20
    content_height = rows * (badge_height + badge_spacing)
    height = header_height + content_height + footer_height
    
    # Create SVG
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
    
    # Background
    dwg.add(dwg.rect(
        insert=(0, 0), 
        size=("100%", "100%"), 
        rx=10, 
        ry=10, 
        fill=theme["bg_color"], 
        stroke=theme["border_color"], 
        stroke_width=2
    ))
    
    # Title
    dwg.add(dwg.text(
        "Connect With Me", 
        insert=(20, 35), 
        fill=theme["title_color"], 
        font_size=theme["title_font_size"], 
        font_family=effective_font_family, 
        font_weight="bold"
    ))
    
    # Draw badges
    start_y = header_height
    col_width = (width - 40) // cols  # Available width per column (minus margins)
    
    for i, platform in enumerate(active_platforms):
        row = i // cols
        col = i % cols
        
        # Calculate position
        x = 20 + (col * col_width) + (col_width - badge_width) // 2
        y = start_y + (row * (badge_height + badge_spacing))
        
        # Determine badge color
        if icon_color:
            badge_color = icon_color.replace("#", "")
        else:
            badge_color = platform["color"]
        
        # Generate shields.io badge URL
        badge_url = generate_social_badge_url(
            platform["key"],
            platform["name"],
            badge_color,
            platform["logo"]
        )
        
        # Create a group for the badge (using foreignObject to embed the badge image)
        # Since we can't easily embed external images in SVG, we'll draw a styled rectangle
        # that looks like a badge with the platform icon and name
        
        # Badge background
        badge_rect = dwg.rect(
            insert=(x, y),
            size=(badge_width, badge_height),
            rx=4,
            ry=4,
            fill=f"#{badge_color}",
            class_="social-badge"
        )
        dwg.add(badge_rect)
        
        # Platform icon (simple circle with first letter)
        icon_size = 18
        icon_x = x + 5
        icon_y = y + (badge_height - icon_size) // 2
        
        dwg.add(dwg.circle(
            center=(icon_x + icon_size//2, y + badge_height//2),
            r=icon_size//2,
            fill="white",
            opacity=0.9
        ))
        
        # First letter of platform name
        dwg.add(dwg.text(
            platform["name"][0].upper(),
            insert=(icon_x + icon_size//2, y + badge_height//2 + 4),
            fill=f"#{badge_color}",
            font_size=10,
            font_family=effective_font_family,
            font_weight="bold",
            text_anchor="middle"
        ))
        
        # Platform name text
        text_x = x + icon_size + 10
        dwg.add(dwg.text(
            platform["name"],
            insert=(text_x, y + badge_height//2 + 4),
            fill="white",
            font_size=11,
            font_family=effective_font_family,
            font_weight="bold"
        ))
        
        # Add link wrapper if URL is available
        if platform["url"] and platform["url"] != "#":
            link = dwg.a(href=platform["url"], target="_blank")
            link.add(badge_rect)
            # Note: In SVG, we need to wrap all elements in the link
            # This is a simplified version - for full functionality, 
            # the entire badge group should be wrapped
    
    # Add CSS for hover effects
    style = dwg.defs.add(dwg.style("""
        .social-badge {
            cursor: pointer;
            transition: opacity 0.2s;
        }
        .social-badge:hover {
            opacity: 0.8;
        }
    """))
    
    return dwg.tostring()

def generate_markdown_badges(social_data, selected_platforms=None, icon_color=None, style="for-the-badge"):
    """
    Generates markdown code for social media badges.
    
    Args:
        social_data: dict with social media URLs
        selected_platforms: list of platform keys to include
        icon_color: optional custom color for all icons
        style: badge style (for-the-badge, flat, flat-square, plastic, social)
    
    Returns:
        str: Markdown code for badges
    """
    if selected_platforms is None:
        selected_platforms = list(SOCIAL_PLATFORMS.keys())
    
    markdown_lines = []
    
    for platform_key in selected_platforms:
        if platform_key in SOCIAL_PLATFORMS and platform_key in social_data and social_data[platform_key]:
            platform = SOCIAL_PLATFORMS[platform_key]
            url = social_data[platform_key]
            
            # Determine badge color
            if icon_color:
                badge_color = icon_color.replace("#", "")
            else:
                badge_color = platform["color"]
            
            # Generate badge URL
            badge_url = generate_social_badge_url(
                platform_key,
                platform["name"],
                badge_color,
                platform["logo"],
                style=style
            )
            
            # Generate markdown
            markdown_lines.append(f"[![{platform['name']}]({badge_url})]({url})")
    
    return " ".join(markdown_lines)
