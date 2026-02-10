import svgwrite
import math
from themes.styles import THEMES
from .svg_base import create_svg_base

def draw_lang_card(data, theme_name="Default", custom_colors=None, excluded_languages=None):
    """
    Generates the Top Languages Card SVG.
    
    Args:
        data: dict with user stats including 'top_languages'
        theme_name: string key from THEMES
        custom_colors: dict with custom color overrides
        excluded_languages: list of language names to exclude (case-insensitive)
    """
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

    width = 300
    # Dynamic height based on languages (max 5)
    langs = data.get("top_languages", [])
    
    # Apply exclusion filter if provided
    if excluded_languages and langs:
        # Convert excluded languages to lowercase for case-insensitive matching
        excluded_lower = [lang.lower() for lang in excluded_languages]
        langs = [
            (lang, count) 
            for lang, count in langs 
            if lang.lower() not in excluded_lower
        ]
    
    # Handle empty result after filtering
    if not langs:
        langs = [("No Data", 0)]

    item_height = 35
    header_height = 40
    height = header_height + (len(langs) * item_height) + 10
    
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
    
    # Background
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=10, ry=10, 
                     fill=theme["bg_color"], stroke=theme["border_color"], stroke_width=2))
    
    # Title
    dwg.add(dwg.text("Top Languages", insert=(20, 30), 
                     fill=theme["title_color"], font_size=theme["title_font_size"], 
                     font_family=theme["font_family"], font_weight="bold"))
    
    # Content
    start_y = 60
    
    # Calculate total for percentages
    total_usage = sum(count for _, count in langs)
    if total_usage == 0: total_usage = 1
    
    for i, (lang, count) in enumerate(langs):
        y = start_y + (i * item_height)
        pct = (count / total_usage) * 100
        
        # Label
        dwg.add(dwg.text(lang, insert=(20, y), fill=theme["text_color"], 
                         font_size=theme["text_font_size"], font_family=theme["font_family"]))
        
        # Percentage Text
        dwg.add(dwg.text(f"{pct:.1f}%", insert=(width - 20, y), fill=theme["text_color"], 
                         font_size=theme["text_font_size"], font_family=theme["font_family"], text_anchor="end"))
        
        # Progress Bar Background
        bar_y = y + 5
        bar_width = width - 40
        dwg.add(dwg.rect(insert=(20, bar_y), size=(bar_width, 6), rx=3, ry=3, fill=theme["border_color"], opacity=0.3))
        
        # Progress Bar Fill with sine wave animation
        fill_width = (pct / 100) * bar_width
        bar_color = theme["title_color"]
        
        # Create the progress bar fill
        progress_fill = dwg.rect(
            insert=(20, bar_y), 
            size=(0, 6),  # Start with 0 width
            rx=3, 
            ry=3, 
            fill=bar_color
        )
        
        # Add sine wave animation 
        progress_fill.add(dwg.animate(
            attributeName="width",
            values="0;{0}".format(fill_width),
            keyTimes="0;1",
            calcMode="spline",
            keySplines="0.445 0.05 0.55 0.95",  # Sine curve approximation
            dur="1s",
            begin="0s",
            fill="freeze"
        ))
        
        dwg.add(progress_fill)
        
    return dwg.tostring()