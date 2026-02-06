import svgwrite
import random

SPACE_COLORS = [
    "#22d3ee",  # cyan star
    "#6366f1",  # nebula indigo
    "#a855f7",  # cosmic purple
    "#f472b6",  # galaxy pink
    "#facc15",  # warm star yellow
]

def render(data):
    """
    Renders the Space theme.
    Commits are stars. Higher commit count = brighter/larger star.
    Background: Deep navy void.
    """
    width = 800
    height = 400
    # Make responsive: use a viewBox and percentage sizing so SVG scales on small screens
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
    
    # Background: Deep Navy Void
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="#0b1020"))
    
    # Random stars for "void" effect (background stars)
    for _ in range(100):
        x = random.randint(0, width)
        y = random.randint(0, height)
        dwg.add(dwg.circle(center=(x, y), r=random.uniform(0.5, 1.5), fill="white", fill_opacity=0.3))

    contributions = [d for d in data['contributions'] if d['count'] > 0]
    
    # Scatter commits as colored stars in space
    for commit in contributions:
        count = commit['count']
        
        # Position: Random
        x = random.randint(20, width - 20)
        y = random.randint(20, height - 20)
        
        # Logic: Higher commit count = larger star
        radius = min(2 + count * 0.5, 8)
        
        # Color variety using Space palette
        color = SPACE_COLORS[count % len(SPACE_COLORS)]
        
        # Opacity / Brightness
        opacity = min(0.6 + (count * 0.05), 1.0)
        
        # Glow effect (simulated with a larger, lower opacity circle behind)
        if count > 5:
             dwg.add(dwg.circle(center=(x, y), r=radius*2.2, fill=color, fill_opacity=0.15))
        
        # Main star with crisp white stroke
        dwg.add(dwg.circle(
            center=(x, y),
            r=radius,
            fill=color,
            fill_opacity=opacity,
            stroke="white",
            stroke_width=0.5
        ))
        
    return dwg.tostring()