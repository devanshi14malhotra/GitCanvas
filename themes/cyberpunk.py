import svgwrite
import random

NEON_COLORS = [
    "#00ffff",  # cyan
    "#39ff14",  # neon green
    "#fcee0c",  # neon yellow
    "#ff00ff",  # magenta
]

def render(data):
    width = 800
    height = 400
    
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
    
    # Dark cyberpunk background
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="#0a0a0a"))
    
    contributions = [d for d in data['contributions'] if d['count'] > 0]
    
    for commit in contributions:
        count = commit["count"]
        
        x = random.randint(20, width - 20)
        y = random.randint(20, height - 20)
        
        radius = min(2 + count * 0.6, 9)
        color = NEON_COLORS[count % len(NEON_COLORS)]
        
        # Glow effect
        dwg.add(dwg.circle(
            center=(x, y),
            r=radius * 2.5,
            fill=color,
            fill_opacity=0.12
        ))
        
        # Main dot
        dwg.add(dwg.circle(
            center=(x, y),
            r=radius,
            fill=color
        ))
    
    return dwg.tostring()