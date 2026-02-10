import svgwrite
from themes.styles import THEMES

def create_svg_base(theme_name, custom_colors, width, height, title_text):
    """
    Creates the base SVG drawing with theme setup, background, and title.
    Returns the drawing object and the theme dictionary.
    """
    theme = THEMES.get(theme_name, THEMES["Default"]).copy()
    if custom_colors:
        theme.update(custom_colors)
    
    dwg = svgwrite.Drawing(size=(f"{width}px", f"{height}px"))
    
    # Background
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=10, ry=10, 
                     fill=theme["bg_color"], stroke=theme["border_color"], stroke_width=2))
    
    # Title
    dwg.add(dwg.text(title_text, insert=(20, 30), 
                     fill=theme["title_color"], font_size=theme["title_font_size"], 
                     font_family=theme["font_family"], font_weight="bold"))
    
    return dwg, theme
