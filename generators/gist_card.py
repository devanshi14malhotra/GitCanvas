import svgwrite
from themes.styles import THEMES
from typing import Optional


def draw_gist_card(
    gist_data: dict,
    theme_name: str = "Default",
    custom_colors: Optional[dict] = None,
    font_family: str = 'Segoe UI, Ubuntu, sans-serif',
    animations_enabled: bool = True
) -> str:
    """
    Generates a Gist Card SVG that looks like a code snippet card.
    
    Args:
        gist_data: Dictionary containing gist info with keys:
                   - gist_id: The gist ID
                   - description: Gist description
                   - filename: Primary filename
                   - language: Programming language
                   - updated_at: Last updated timestamp
        theme_name: String key from THEMES
        custom_colors: Optional dict to override theme colors
        font_family: Custom font family for text rendering
        animations_enabled: Bool to enable/disable animations
        
    Returns:
        SVG string representation of the gist card
    """
    # Resolve theme
    if isinstance(theme_name, dict):
        theme = theme_name.copy()
    else:
        theme = THEMES.get(theme_name, THEMES["Default"]).copy()
        if custom_colors:
            theme.update(custom_colors)
    
    # Use theme font_family if no custom override provided
    effective_font = font_family if font_family else theme.get("font_family", "Segoe UI, sans-serif")
    
    # Card dimensions (consistent with other cards)
    width = 495
    height = 130
    margin = 15
    
    # Create SVG drawing
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
    
    # Extract gist data with fallbacks
    filename = gist_data.get("filename", "gistfile.txt")
    description = gist_data.get("description", "")
    language = gist_data.get("language", "Unknown")
    gist_id = gist_data.get("gist_id", "")
    
    # Truncate description if too long
    if description and len(description) > 60:
        description = description[:57] + "..."
    
    # Truncate filename if too long
    display_filename = filename
    if len(filename) > 35:
        display_filename = filename[:32] + "..."
    
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
    
    # Code snippet decorative elements
    # Top bar with file icon and language badge
    bar_height = 35
    
    # File icon (document symbol)
    icon_x = margin + 5
    icon_y = 22
    
    # Draw file icon
    file_icon = dwg.g()
    # Document outline
    file_icon.add(dwg.rect(
        insert=(icon_x, icon_y - 8),
        size=(12, 16),
        rx=2,
        fill="none",
        stroke=theme["icon_color"],
        stroke_width=1.5
    ))
    # File fold corner
    file_icon.add(dwg.path(
        d=f"M {icon_x + 8} {icon_y - 8} L {icon_x + 12} {icon_y - 4} L {icon_x + 8} {icon_y - 4} Z",
        fill=theme["icon_color"]
    ))
    dwg.add(file_icon)
    
    # Filename text
    dwg.add(dwg.text(
        display_filename,
        insert=(icon_x + 20, icon_y + 3),
        fill=theme["title_color"],
        font_size=14,
        font_family=effective_font,
        font_weight="bold"
    ))
    
    # Language badge (right side)
    if language and language != "Unknown":
        badge_text = language
        badge_padding_x = 8
        badge_padding_y = 4
        
        # Calculate badge width based on text
        # Approximate width: ~7px per character + padding
        badge_width = len(badge_text) * 7 + badge_padding_x * 2
        badge_x = width - margin - badge_width
        badge_y = 10
        
        # Badge background
        dwg.add(dwg.rect(
            insert=(badge_x, badge_y),
            size=(badge_width, 20),
            rx=10,
            ry=10,
            fill=theme.get("icon_color", theme["title_color"]),
            opacity=0.15
        ))
        
        # Badge text
        dwg.add(dwg.text(
            badge_text,
            insert=(badge_x + badge_width / 2, badge_y + 14),
            fill=theme["title_color"],
            font_size=10,
            font_family=effective_font,
            font_weight="600",
            text_anchor="middle"
        ))
    
    # Description text (below filename)
    desc_y = bar_height + 10
    if description:
        dwg.add(dwg.text(
            description,
            insert=(margin, desc_y),
            fill=theme["text_color"],
            font_size=12,
            font_family=effective_font,
            opacity=0.9
        ))
    else:
        # Show "No description" placeholder
        dwg.add(dwg.text(
            "No description provided",
            insert=(margin, desc_y),
            fill=theme["text_color"],
            font_size=12,
            font_family=effective_font,
            opacity=0.5,
            font_style="italic"
        ))
    
    # Gist ID hint at bottom
    if gist_id:
        dwg.add(dwg.text(
            f"gist:{gist_id[:7]}...",
            insert=(width - margin, height - 10),
            fill=theme["text_color"],
            font_size=9,
            font_family=effective_font,
            opacity=0.4,
            text_anchor="end"
        ))
    
    # Decorative code-like accent line on left
    dwg.add(dwg.rect(
        insert=(0, 40),
        size=(4, 50),
        rx=2,
        fill=theme["icon_color"],
        opacity=0.6
    ))
    
    return dwg.tostring()
