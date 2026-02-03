import svgwrite

def render(data):
    """
    Renders the Marvel theme (Comic Book Panel).
    Concept: User is the "Hero". Total commits = "Power Level".
    """
    username = data['username']
    total = data['total_commits']
    
    width = 800
    height = 500
    # Make responsive: use a viewBox and percentage sizing so SVG scales on small screens
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
    
    # Background: Iron Man Red
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="#7A0000"))
    
    # Panel Border
    dwg.add(dwg.rect(insert=(10, 10), size=(width-20, height-20), fill="none", stroke="#FFD700", stroke_width=5))
    
    # Text Panel - Comic Style font fallback
    # Title
    dwg.add(dwg.text("AVENGER PROFILE", insert=(width/2, 60), text_anchor="middle",
                     fill="#FFD700", font_size="30px", font_family="Impact, sans-serif", font_weight="bold"))
    
    # Hero Name
    dwg.add(dwg.text(f"CODENAME: {username.upper()}", insert=(width/2, 120), text_anchor="middle",
                     fill="white", font_size="50px", font_family="Impact, sans-serif"))
                     
    # Power Level
    dwg.add(dwg.text(f"POWER LEVEL: {total}", insert=(width/2, 180), text_anchor="middle",
                     fill="#00FFFF", font_size="40px", font_family="Impact, sans-serif"))
    
    # Arc Reactor Graphic
    cx, cy = width/2, 330
    
    # Outer ring
    dwg.add(dwg.circle(center=(cx, cy), r=80, fill="#222", stroke="#555", stroke_width=2))
    # Glowing ring
    dwg.add(dwg.circle(center=(cx, cy), r=70, fill="none", stroke="#00FFFF", stroke_width=8, stroke_opacity=0.8))
    # Inner light
    dwg.add(dwg.circle(center=(cx, cy), r=60, fill="#E0FFFF", fill_opacity=0.9))
    # Triangle (optional) or just circles
    
    # Commits as "Energy Cells" around the reactor ?? 
    # Let's add some orbiting particles based on recent contributions
    # Just a few
    commits = [d for d in data['contributions'][-20:] if d['count'] > 0]
    import math
    for i, com in enumerate(commits):
        angle = i * (360 / 20)
        rad = math.radians(angle)
        
        dist = 100 + com['count'] * 2
        
        px = cx + math.cos(rad) * dist
        py = cy + math.sin(rad) * dist
        
        dwg.add(dwg.circle(center=(px, py), r=4, fill="#FF4500"))
        
    return dwg.tostring()
