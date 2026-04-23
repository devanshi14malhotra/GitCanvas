import svgwrite
from themes.styles import THEMES
from .svg_base import create_svg_base

def draw_streak_card(data, theme_name="Default", custom_colors=None):
    """
    Generates the GitHub Streak Card SVG showing current and longest streak.
    """
    width = 450
    height = 200
    
    streak_data = data.get('streak_data', {})
    current_streak = streak_data.get('current_streak', 0)
    longest_streak = streak_data.get('longest_streak', 0)
    
    username = data.get('username', 'Unknown')
    dwg, theme = create_svg_base(theme_name, custom_colors, width, height, f"{username}'s GitHub Streak")
    
    font_family = theme["font_family"]
    text_color = theme["text_color"]
    title_color = theme["title_color"]
    icon_color = theme["icon_color"]
    
    # Baseline for central alignment
    flame_x = 85
    # Moving flame_y up slightly to give text room below
    flame_y = 100 

    # --- LEFT SIDE: CURRENT STREAK ---
    
    # 1. Streak Value (Large number) - Raised to prevent overlap
    dwg.add(dwg.text(f"{current_streak}", insert=(flame_x, flame_y - 25), 
                     fill=title_color, font_size=36, font_family=font_family, 
                     text_anchor="middle", font_weight="bold"))
    
    # 2. Streak Unit ("days") - Positioned below the number
    dwg.add(dwg.text("days", insert=(flame_x, flame_y + 5), 
                     fill=text_color, font_size=14, font_family=font_family, 
                     text_anchor="middle"))
    
    # 3. Flame Icon - Moved lower so it doesn't mask the "days" text
    flame_body_y = flame_y + 35
    flame_path = f"M {flame_x} {flame_body_y + 15} " \
                 f"Q {flame_x - 12} {flame_body_y} {flame_x} {flame_body_y - 20} " \
                 f"Q {flame_x + 12} {flame_body_y} {flame_x} {flame_body_y + 15} Z"
    dwg.add(dwg.path(d=flame_path, fill=icon_color, opacity=0.8))
    
    # 4. Label ("Current Streak") - At the very bottom of the section
    dwg.add(dwg.text("Current Streak", insert=(flame_x, flame_y + 70), 
                     fill=text_color, font_size=12, font_family=font_family, 
                     text_anchor="middle"))

    # --- RIGHT SIDE: LONGEST STREAK ---
    
    trophy_x = width - 85
    trophy_y = flame_y

    # 1. Longest Streak Value
    dwg.add(dwg.text(f"{longest_streak}", insert=(trophy_x, trophy_y - 25), 
                     fill=title_color, font_size=36, font_family=font_family, 
                     text_anchor="middle", font_weight="bold"))
    
    # 2. Unit ("days")
    dwg.add(dwg.text("days", insert=(trophy_x, trophy_y + 5), 
                     fill=text_color, font_size=14, font_family=font_family, 
                     text_anchor="middle"))

    # 3. Trophy Icon - Centered below text
    trophy_icon_y = trophy_y + 30
    dwg.add(dwg.rect(insert=(trophy_x - 15, trophy_icon_y + 10), size=(30, 6), 
                     fill=icon_color, rx=2, ry=2, opacity=0.8))
    dwg.add(dwg.path(d=f"M {trophy_x - 15} {trophy_icon_y + 10} " \
                       f"L {trophy_x - 12} {trophy_icon_y - 10} " \
                       f"L {trophy_x + 12} {trophy_icon_y - 10} " \
                       f"L {trophy_x + 15} {trophy_icon_y + 10} Z", 
                     fill=icon_color, opacity=0.9))
    
    # 4. Label ("Longest Streak")
    dwg.add(dwg.text("Longest Streak", insert=(trophy_x, trophy_y + 70), 
                     fill=text_color, font_size=12, font_family=font_family, 
                     text_anchor="middle"))

    # --- DIVIDER & FOOTER ---
    
    dwg.add(dwg.line(start=(width/2, 60), end=(width/2, height - 40), 
                     stroke=theme.get("border_color", "#333"), 
                     stroke_width=1, opacity=0.2))
    
    total_contributions = streak_data.get('total_contributions', 0)
    dwg.add(dwg.text(f"Total Contributions: {total_contributions}", 
                     insert=(width/2, height - 15), 
                     fill=text_color, font_size=11, font_family=font_family, 
                     text_anchor="middle", opacity=0.7))
    
    return dwg.tostring()
