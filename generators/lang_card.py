import svgwrite
import math
from themes.styles import THEMES
from .svg_base import create_svg_base

def draw_lang_card(data, theme_name="Default", custom_colors=None, excluded_languages=None, font_family=None):
    """
    Generates the Top Languages Card SVG.
    
    Args:
        data: dict with user stats including 'top_languages'
        theme_name: string key from THEMES
        custom_colors: dict with custom color overrides
        excluded_languages: list of language names to exclude (case-insensitive)
        font_family: optional custom font family override (e.g. 'Inter', 'Roboto')
    """
    # FIXED: Handle both string theme name and pre-resolved theme dict
    if isinstance(theme_name, dict):
        # Already a theme dictionary (e.g., current_theme_opts from app.py)
        theme = theme_name.copy()
    else:
        # Convert theme_name string to actual theme dictionary
        theme = THEMES.get(theme_name, THEMES["Default"]).copy()
    
    # Determine font family - use custom override if provided, otherwise fall back to theme
    effective_font_family = font_family if font_family else theme.get("font_family", "Segoe UI, sans-serif")
        
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
    if langs:
        langs = sorted(langs, key=lambda x: x[1], reverse=True)
    
    # Handle empty result after filtering
    if not langs:
        langs = [("No Data", 0)]

    item_height = 35
    header_height = 40
    
    is_glass = False
    if isinstance(theme_name, dict):
        is_glass = theme_name.get("name") == "Glass" or theme.get("name") == "Glass"
    else:
        is_glass = theme_name == "Glass"

    if is_glass:
        margin = 15
        item_spacing = 40
        p_height = 70 + (len(langs) * item_spacing) + 15
        height = margin * 2 + p_height
    else:
        height = header_height + (len(langs) * item_height) + 10

    
    if is_glass:
        # Neon Liquid Glassmorphism Theme (Enhanced)
        
        # Theme Variables
        bg_col = theme.get("bg_color", "#050511")
        title_col = theme.get("title_color", "#00e5ff")
        text_col = theme.get("text_color", "#e2e8f0")
        border_col = theme.get("border_color", "white")
        
        # 1. Definitions
        dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
        
        # Blur filter for background blobs
        blob_blur = dwg.filter(id="blobBlur", x="-50%", y="-50%", width="200%", height="200%")
        blob_blur.feGaussianBlur(in_="SourceGraphic", stdDeviation=40)
        dwg.defs.add(blob_blur)
        
        # Glow filter for text
        text_glow = dwg.filter(id="textGlow")
        text_glow.feGaussianBlur(in_="SourceAlpha", stdDeviation=2, result="blur")
        text_glow.feOffset(in_="blur", dx=0, dy=0, result="offsetBlur")
        text_glow.feFlood(flood_color=title_col, result="glowColor")
        text_glow.feComposite(in_="glowColor", in2="offsetBlur", operator="in", result="coloredBlur")
        text_glow.feMerge(["coloredBlur", "SourceGraphic"])
        dwg.defs.add(text_glow)
        
        # Glass Panel Gradient
        glass_grad = dwg.linearGradient(start=(0, 0), end=(1, 1), id="glassGrad")
        glass_grad.add_stop_color(0, "white", opacity=0.15)
        glass_grad.add_stop_color(1, "white", opacity=0.05)
        dwg.defs.add(glass_grad)
        
        # Border Gradient
        border_grad = dwg.linearGradient(start=(0, 0), end=(1, 1), id="borderGrad")
        border_grad.add_stop_color(0, border_col, opacity=0.4)
        border_grad.add_stop_color(1, border_col, opacity=0.1)
        dwg.defs.add(border_grad)

        # Background Base
        dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=16, ry=16, fill=bg_col))

        # Neon Blobs
        dwg.add(dwg.circle(center=(0, 0), r=120, fill="#ff00ff", filter="url(#blobBlur)", opacity=0.5))
        dwg.add(dwg.circle(center=(width, height), r=140, fill="#00ffff", filter="url(#blobBlur)", opacity=0.4))

        # 2. Glass Panel
        margin = 15
        p_width = width - margin * 2
        p_height = height - margin * 2
        dwg.add(dwg.rect(insert=(margin, margin), size=(p_width, p_height), rx=16, ry=16, fill="#000000", opacity=0.3))
        dwg.add(dwg.rect(insert=(margin, margin), size=(p_width, p_height), rx=16, ry=16, 
                         fill="url(#glassGrad)", stroke="url(#borderGrad)", stroke_width=1.2))
        
        # Top Reflection
        reflection_grad = dwg.linearGradient(start=(0, 0), end=(0, 1), id="reflGrad")
        reflection_grad.add_stop_color(0, "white", opacity=0.08)
        reflection_grad.add_stop_color(1, "white", opacity=0)
        dwg.defs.add(reflection_grad)
        dwg.add(dwg.rect(insert=(margin + 4, margin + 4), size=(p_width - 8, p_height / 4), rx=12, ry=12, fill="url(#reflGrad)"))

        # 3. Content
        dwg.add(dwg.text("Top Languages".upper(), insert=(width/2, margin + 35), fill="white", font_size=16, 
                         font_weight="800", font_family=f"{effective_font_family}, system-ui, sans-serif", text_anchor="middle", 
                         letter_spacing=2, filter="url(#textGlow)"))

        # Calculate percentages
        total = sum([c for l, c in langs])
        if total == 0: total = 1

        start_y = margin + 70
        item_spacing = 40
        for i, (lang, count) in enumerate(langs):
            y = start_y + (i * item_spacing)
            pct = (count / total) * 100
            
            # Label
            dwg.add(dwg.text(lang, insert=(35, y), fill=text_col, font_size=12, font_family=f"{effective_font_family}, sans-serif"))
            
            # Percentage
            dwg.add(dwg.text(f"{pct:.1f}%", insert=(width - 35, y), fill=text_col, font_size=12, 
                             font_family=f"{effective_font_family}, sans-serif", text_anchor="end", opacity=0.8))
            
            # Bar Background
            bar_y = y + 8
            bar_w = width - 70
            dwg.add(dwg.rect(insert=(35, bar_y), size=(bar_w, 6), rx=3, ry=3, fill="white", opacity=0.08))
            
            # Bar Fill
            fill_w = (pct / 100) * bar_w
            dwg.add(dwg.rect(insert=(35, bar_y), size=(fill_w, 6), rx=3, ry=3, fill=title_col, opacity=0.8))
            # Subtle Highlight on Bar
            dwg.add(dwg.rect(insert=(35, bar_y + 1), size=(fill_w, 2), rx=1, ry=1, fill="white", opacity=0.2))

    else:
        # DEFAULT / OTHER THEMES
        dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
        
        # Background
        dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=10, ry=10, 
                         fill=theme["bg_color"], stroke=theme["border_color"], stroke_width=2))
        
        # Title
        dwg.add(dwg.text("Top Languages", insert=(20, 30), 
                         fill=theme["title_color"], font_size=18, font_weight="bold", font_family=effective_font_family))
        
        # Calculate percentages
        total = sum([c for l, c in langs])
        if total == 0: total = 1
        
        start_y = header_height
        for i, (lang, count) in enumerate(langs):
            y = start_y + (i * item_height)
            pct = (count / total) * 100
            
            # Language Name
            dwg.add(dwg.text(lang, insert=(20, y + 20), fill=theme["text_color"], font_size=14, font_family=effective_font_family))
            
            # Bar Background
            bar_x = 120
            bar_width = width - bar_x - 50
            dwg.add(dwg.rect(insert=(bar_x, y + 10), size=(bar_width, 10), rx=5, ry=5, fill="#333"))
            
            # Bar Fill
            fill_width = (pct / 100) * bar_width
            dwg.add(dwg.rect(insert=(bar_x, y + 10), size=(fill_width, 10), rx=5, ry=5, fill=theme["title_color"]))
            
            # Percentage
            dwg.add(dwg.text(f"{pct:.1f}%", insert=(width - 40, y + 20), fill=theme["text_color"], font_size=12, font_family=effective_font_family, text_anchor="end"))

        
    return dwg.tostring()
