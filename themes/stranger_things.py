import svgwrite
import math
import random

def render(data):
    """
    Stranger Things Theme - The Upside Down
    Dark atmosphere with red glowing contributions representing demogorgon activity
    """
    contributions = data['contributions'][-365:] if len(data['contributions']) > 365 else data['contributions']
    
    cols = 53
    rows = 7
    width = cols * 15 + 100
    height = rows * 15 + 150
    
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
    
    # Background gradient - Upside Down vibe
    gradient = dwg.defs.add(dwg.linearGradient(id="upside_down", x1="0%", y1="0%", x2="0%", y2="100%"))
    gradient.add_stop_color(offset="0%", color="#0a0a0a")
    gradient.add_stop_color(offset="100%", color="#1a0f0f")
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="url(#upside_down)"))
    
    # Floating particles effect
    random.seed(42)
    for i in range(20):
        x = random.randint(0, width)
        y = random.randint(0, height)
        r = random.randint(1, 3)
        dwg.add(dwg.circle(center=(x, y), r=r, fill="#ffffff", opacity=0.3))
    
    # Title
    dwg.add(dwg.text("THE UPSIDE DOWN", insert=(width//2, 30), 
                     text_anchor="middle", font_size="24px", font_family="monospace",
                     fill="#ff0000", style="letter-spacing: 3px; font-weight: bold;"))
    
    box_size = 12
    gap = 3
    start_x = 50
    start_y = 60
    
    max_count = max([day['count'] for day in contributions]) if contributions else 1
    
    for i, day in enumerate(contributions):
        msg_count = day['count']
        col = i // 7
        row = i % 7
        
        x = start_x + col * (box_size + gap)
        y = start_y + row * (box_size + gap)
        
        if msg_count == 0:
            fill_color = "#1a1a1a"
            opacity = 0.5
        elif msg_count <= max_count * 0.25:
            fill_color = "#8b0000"
            opacity = 0.6
        elif msg_count <= max_count * 0.5:
            fill_color = "#b22222"
            opacity = 0.7
        elif msg_count <= max_count * 0.75:
            fill_color = "#dc143c"
            opacity = 0.85
        else:
            fill_color = "#ff0000"
            opacity = 1.0
            # Glow effect for high activity
            dwg.add(dwg.rect(insert=(x-1, y-1), size=(box_size+2, box_size+2), 
                           fill="none", stroke="#ff0000", stroke_width=1, opacity=0.5))
        
        dwg.add(dwg.rect(insert=(x, y), size=(box_size, box_size), 
                        fill=fill_color, rx=2, ry=2, opacity=opacity))
    
    # Demogorgon silhouette
    demo_x = width - 80
    demo_y = height - 100
    
    dwg.add(dwg.circle(center=(demo_x, demo_y), r=25, fill="#330000", opacity=0.8))
    
    # Petal-like head opening
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x1 = demo_x + 20 * math.cos(rad)
        y1 = demo_y + 20 * math.sin(rad)
        x2 = demo_x + 35 * math.cos(rad)
        y2 = demo_y + 35 * math.sin(rad)
        dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), 
                        stroke="#ff0000", stroke_width=2, opacity=0.6))
    
    # Eyes
    dwg.add(dwg.circle(center=(demo_x-8, demo_y-5), r=3, fill="#ff0000"))
    dwg.add(dwg.circle(center=(demo_x+8, demo_y-5), r=3, fill="#ff0000"))
    
    dwg.add(dwg.text("HAWKINS LAB", insert=(10, height-10), 
                     font_size="10px", font_family="monospace",
                     fill="#666666", opacity=0.5))
    
    return dwg.tostring()