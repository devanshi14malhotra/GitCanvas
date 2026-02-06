import svgwrite
import random

RETRO_COLORS = [
    "#5c4632",  # dark brown ink
    "#7a5c3e",
    "#3b2b20",
]

def render(data):
    width = 800
    height = 400
    
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
    
    # Paper background
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="#f5e6c8"))
    
    # Header text
    dwg.add(dwg.text(
        "Contribution Log",
        insert=(20, 40),
        fill="#5c4632",
        font_size="22px",
        font_family="Courier New, monospace"
    ))
    
    contributions = [d for d in data["contributions"] if d["count"] > 0]
    
    for commit in contributions:
        count = commit["count"]
        
        x = random.randint(20, width - 20)
        y = random.randint(60, height - 20)
        
        radius = min(2 + count * 0.4, 7)
        color = RETRO_COLORS[count % len(RETRO_COLORS)]
        
        dwg.add(dwg.circle(
            center=(x, y),
            r=radius,
            fill=color,
            fill_opacity=0.8
        ))
    
    return dwg.tostring()