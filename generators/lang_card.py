import svgwrite
from themes.styles import THEMES

def draw_lang_card(data, theme_name="Default", custom_colors=None):
    """
    Generates the Top Languages Card SVG.
    """

    # handle API Error or invalid user 
    if data is None or "error" in data:
        return draw_error_lang_svg(
            data.get("error", "UNKNOWN") if isinstance(data, dict) else "UNKNOWN"
        )
    theme = THEMES.get(theme_name, THEMES["Default"]).copy()
    if custom_colors:
        theme.update(custom_colors)
        
    width = 300
    # Dynamic height based on languages (max 5)
    langs = data.get("top_languages", [])
    if not langs:
        langs = [("No Data", 0)]
        
    item_height = 35
    header_height = 40
    height = header_height + (len(langs) * item_height) + 10
    
    dwg = svgwrite.Drawing(size=(f"{width}px", f"{height}px"))
    
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
        
        # Progress Bar Fill
        fill_width = (pct / 100) * bar_width
        # Use icon_color or title_color for bar fill
        bar_color = theme["title_color"]
        dwg.add(dwg.rect(insert=(20, bar_y), size=(fill_width, 6), rx=3, ry=3, fill=bar_color))
        
    return dwg.tostring()

# error SVG 
def draw_error_lang_svg(error_type):
    messages = {
        "USER_NOT_FOUND": "GitHub User Not Found",
        "RATE_LIMITED": "GitHub API Rate Limited",
        "GITHUB_API_ERROR": "GitHub API Error",
        "UNKNOWN": "Something went wrong"
    }

    msg = messages.get(error_type, "Error")

    dwg = svgwrite.Drawing(size=("450px", "120px"))
    dwg.add(dwg.rect(
        insert=(0, 0),
        size=("100%", "100%"),
        rx=10,
        ry=10,
        fill="#0d1117",
        stroke="#30363d",
        stroke_width=2
    ))

    dwg.add(dwg.text(
        msg,
        insert=("50%", "55%"),
        text_anchor="middle",
        fill="#f85149",
        font_size="18",
        font_family="monospace",
        font_weight="bold"
    ))

    return dwg.tostring()
