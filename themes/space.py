import svgwrite
import random

def render(data):
    """
    Renders the Space theme.
    Commits are stars. Higher commit count = brighter/larger star.
    Background: Dark void.
    """
    width = 800
    height = 400
    # Make responsive: use a viewBox and percentage sizing so SVG scales on small screens
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
    
    # Background: Dark Void
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="#000000"))
    
    # Random stars for "void" effect (background stars)
    for _ in range(100):
        x = random.randint(0, width)
        y = random.randint(0, height)
        dwg.add(dwg.circle(center=(x, y), r=random.uniform(0.5, 1.5), fill="white", fill_opacity=0.3))

    contributions = [d for d in data['contributions'] if d['count'] > 0]
    
    # To make it "Art", we scatter the actual commits as brighter stars
    # Or we can map them to a grid if we want structure, but PRD says "not as a graph".
    # So we scatter them but maybe loosely ordered or just purely random for the 'Space' feel.
    
    for commit in contributions:
        count = commit['count']
        
        # Position: Random
        x = random.randint(20, width - 20)
        y = random.randint(20, height - 20)
        
        # Logic: Higher commit count = brighter/larger star.
        # Radius
        radius = min(2 + count * 0.5, 8)
        
        # Opacity / Brightness
        # White with some blue tint for high commits
        color = "#FFFFFF"
        if count > 10:
            color = "#AADDFF" # Blueish white
        
        opacity = min(0.6 + (count * 0.05), 1.0)
        
        # Glow effect (simulated with a larger, lower opacity circle behind)
        if count > 5:
             dwg.add(dwg.circle(center=(x, y), r=radius*2, fill=color, fill_opacity=0.2))
        
        dwg.add(dwg.circle(center=(x, y), r=radius, fill=color, fill_opacity=opacity))
        
    return dwg.tostring()
