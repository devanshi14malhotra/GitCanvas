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
        
    width = 450 # Resized from 300 to match Stats card
    
        
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

    
    if theme_name == "Glass":
        margin = 25
        # Recalculate height: Margin + Header + Items + Item Padding + Margin
        header_height = 80
        item_spacing = 45
        height = margin + header_height + (len(langs) * item_spacing) + margin
        
        dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
        
        # Theme Variables
        bg_col = theme.get("bg_color", "#050511")
        title_col = theme.get("title_color", "#00e5ff")
        text_col = theme.get("text_color", "#e2e8f0")
        border_col = theme.get("border_color", "white")
        
        # 1. Definitions
        blob_blur = dwg.filter(id="blobBlur", x="-50%", y="-50%", width="200%", height="200%")
        blob_blur.feGaussianBlur(in_="SourceGraphic", stdDeviation=40)
        dwg.defs.add(blob_blur)
        
        # Background Base
        dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=16, ry=16, fill=bg_col))

        # Title
        dwg.add(dwg.text("Top Languages", insert=(40, 55), fill=title_col, font_size=24, font_weight="bold", font_family="Segoe UI, sans-serif"))

        # Calculate percentages
        total = sum([c for l, c in langs])
        if total == 0: total = 1

        for i, (lang, count) in enumerate(langs):
            y = margin + header_height + (i * item_spacing)
            pct = (count / total) * 100
            
            # Label
            dwg.add(dwg.text(lang, insert=(40, y), fill=text_col, font_size=16, font_family="Segoe UI, sans-serif"))
            
            # Percentage Text
            dwg.add(dwg.text(f"{pct:.1f}%", insert=(width - 40, y), fill=text_col, font_size=16, font_family="Segoe UI, sans-serif", text_anchor="end"))
            
            # Bar Background
            bar_y = y + 10
            bar_width = width - 80
            dwg.add(dwg.rect(insert=(40, bar_y), size=(bar_width, 6), rx=3, ry=3, fill="white", opacity=0.1))
            
            # Bar Fill
            fill_width = (pct / 100) * bar_width
            dwg.add(dwg.rect(insert=(40, bar_y), size=(fill_width, 6), rx=3, ry=3, fill=title_col))

    else:
        # DEFAULT / OTHER THEMES
        dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
        
        # Background
        dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=10, ry=10, 
                         fill=theme["bg_color"], stroke=theme["border_color"], stroke_width=2))
        
        # Title
        dwg.add(dwg.text("Top Languages", insert=(20, 30), 
                         fill=theme["title_color"], font_size=18, font_weight="bold", font_family="Segoe UI, sans-serif"))
        
        # Calculate percentages
        total = sum([c for l, c in langs])
        if total == 0: total = 1
        
        start_y = header_height
        for i, (lang, count) in enumerate(langs):
            y = start_y + (i * item_height)
            pct = (count / total) * 100
            
            # Language Name
            dwg.add(dwg.text(lang, insert=(20, y + 20), fill=theme["text_color"], font_size=14, font_family="Segoe UI, sans-serif"))
            
            # Bar Background
            bar_x = 120
            bar_width = width - bar_x - 50
            dwg.add(dwg.rect(insert=(bar_x, y + 10), size=(bar_width, 10), rx=5, ry=5, fill="#333"))
            
            # Bar Fill
            fill_width = (pct / 100) * bar_width
            dwg.add(dwg.rect(insert=(bar_x, y + 10), size=(fill_width, 10), rx=5, ry=5, fill=theme["title_color"]))
            
            # Percentage
            dwg.add(dwg.text(f"{pct:.1f}%", insert=(width - 40, y + 20), fill=theme["text_color"], font_size=12, font_family="Segoe UI, sans-serif", text_anchor="end"))

        
    return dwg.tostring()
