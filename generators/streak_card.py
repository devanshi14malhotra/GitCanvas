import svgwrite
from themes.styles import THEMES
from .svg_base import create_svg_base

def draw_streak_card(data, theme_name="Default", custom_colors=None, font_family=None):
    """
    Generates the GitHub Streak Card SVG showing current and longest streak.
    data: dict with user stats including streak_data
    theme_name: string key from THEMES
    font_family: optional custom font family override (e.g. 'Inter', 'Roboto')
    """
    width = 450
    height = 200
    
    streak_data = data.get('streak_data', {})
    current_streak = streak_data.get('current_streak', 0)
    longest_streak = streak_data.get('longest_streak', 0)
    
    # Validate username to prevent KeyError
    username = data.get('username', 'Unknown')
    dwg, theme = create_svg_base(theme_name, custom_colors, width, height, f"{username}'s GitHub Streak")
    
    # Use custom font override if provided, otherwise fall back to theme
    font_family = font_family if font_family else theme["font_family"]
    text_color = theme["text_color"]
    title_color = theme["title_color"]
    icon_color = theme["icon_color"]
    
    # Draw flame icon for current streak (left side)
    flame_x = 80
    flame_y = 110
    
    # Flame body (main flame shape using path)
    flame_path = f"M {flame_x} {flame_y + 20} " \
                 f"Q {flame_x - 15} {flame_y} {flame_x} {flame_y - 25} " \
                 f"Q {flame_x + 15} {flame_y} {flame_x} {flame_y + 20} Z"
    dwg.add(dwg.path(d=flame_path, fill=icon_color, opacity=0.9))
    
    # Inner flame highlight
    inner_flame = f"M {flame_x} {flame_y + 15} " \
                  f"Q {flame_x - 8} {flame_y + 5} {flame_x} {flame_y - 10} " \
                  f"Q {flame_x + 8} {flame_y + 5} {flame_x} {flame_y + 15} Z"
    dwg.add(dwg.path(d=inner_flame, fill=title_color, opacity=0.6))
    
    # Current Streak Label
    dwg.add(dwg.text("Current Streak", insert=(flame_x, flame_y + 45), 
                     fill=text_color, font_size=12, font_family=font_family, 
                     text_anchor="middle"))
    
    # Current Streak Value
    dwg.add(dwg.text(f"{current_streak}", insert=(flame_x, flame_y - 35), 
                     fill=title_color, font_size=32, font_family=font_family, 
                     text_anchor="middle", font_weight="bold"))
    
    # Current Streak Unit
    dwg.add(dwg.text("days", insert=(flame_x, flame_y - 10), 
                     fill=text_color, font_size=14, font_family=font_family, 
                     text_anchor="middle"))
    
    # Draw trophy/crown icon for longest streak (right side)
    trophy_x = width - 80
    trophy_y = flame_y
    
    # Trophy base
    dwg.add(dwg.rect(insert=(trophy_x - 20, trophy_y + 10), size=(40, 8), 
                     fill=icon_color, rx=2, ry=2))
    # Trophy cup body
    dwg.add(dwg.path(d=f"M {trophy_x - 18} {trophy_y + 10} " \
                       f"L {trophy_x - 15} {trophy_y - 15} " \
                       f"L {trophy_x + 15} {trophy_y - 15} " \
                       f"L {trophy_x + 18} {trophy_y + 10} Z", 
                     fill=icon_color, opacity=0.9))
    # Trophy handles
    dwg.add(dwg.path(d=f"M {trophy_x - 15} {trophy_y - 5} " \
                       f"Q {trophy_x - 25} {trophy_y - 5} {trophy_x - 22} {trophy_y + 5}", 
                     fill="none", stroke=icon_color, stroke_width=3))
    dwg.add(dwg.path(d=f"M {trophy_x + 15} {trophy_y - 5} " \
                       f"Q {trophy_x + 25} {trophy_y - 5} {trophy_x + 22} {trophy_y + 5}", 
                     fill="none", stroke=icon_color, stroke_width=3))
    # Star on trophy (5-pointed star using path)
    star_path = f"M {trophy_x} {trophy_y - 14} " \
                f"L {trophy_x + 1.8} {trophy_y - 6.5} " \
                f"L {trophy_x + 5.7} {trophy_y - 5.5} " \
                f"L {trophy_x + 3.5} {trophy_y - 1.5} " \
                f"L {trophy_x + 4.4} {trophy_y + 2.5} " \
                f"L {trophy_x} {trophy_y - 0.5} " \
                f"L {trophy_x - 4.4} {trophy_y + 2.5} " \
                f"L {trophy_x - 3.5} {trophy_y - 1.5} " \
                f"L {trophy_x - 5.7} {trophy_y - 5.5} " \
                f"L {trophy_x - 1.8} {trophy_y - 6.5} Z"
    dwg.add(dwg.path(d=star_path, fill=title_color))
    
    # Longest Streak Label
    dwg.add(dwg.text("Longest Streak", insert=(trophy_x, trophy_y + 45), 
                     fill=text_color, font_size=12, font_family=font_family, 
                     text_anchor="middle"))
    
    # Longest Streak Value
    dwg.add(dwg.text(f"{longest_streak}", insert=(trophy_x, trophy_y - 35), 
                     fill=title_color, font_size=32, font_family=font_family, 
                     text_anchor="middle", font_weight="bold"))
    
    # Longest Streak Unit
    dwg.add(dwg.text("days", insert=(trophy_x, trophy_y - 10), 
                     fill=text_color, font_size=14, font_family=font_family, 
                     text_anchor="middle"))
    
    # Center divider line
    dwg.add(dwg.line(start=(width/2, 70), end=(width/2, height - 20), 
                     stroke=theme.get("border_color", "#333"), 
                     stroke_width=1, opacity=0.3))
    
    # Total contributions info at bottom
    total_contributions = streak_data.get('total_contributions', 0)
    dwg.add(dwg.text(f"Total Contributions: {total_contributions}", 
                     insert=(width/2, height - 10), 
                     fill=text_color, font_size=11, font_family=font_family, 
                     text_anchor="middle", opacity=0.8))
    
    return dwg.tostring()
