import svgwrite
import random

def render(data):
    """
    Renders the Ocean theme (Underwater Scene).
    Contributions represented as fish or bubbles, background with waves and coral.
    """
    # We will accept up to 365 days (last year)
    contributions = data['contributions'][-365:] if len(data['contributions']) > 365 else data['contributions']

    # Grid layout or scattered for ocean
    width = 500
    height = 150
    dwg = svgwrite.Drawing(size=(f"{width}px", f"{height}px"))

    # Background: Deep ocean blue
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="#001122"))

    # Waves at top
    wave_path = "M0,20 Q100,10 200,20 T400,20 T500,20 L500,0 L0,0 Z"
    dwg.add(dwg.path(d=wave_path, fill="#004466", opacity=0.7))

    # Coral reefs at bottom
    coral_y = height - 30
    dwg.add(dwg.path(d=f"M50,{coral_y} Q70,{coral_y-20} 90,{coral_y} Q110,{coral_y-15} 130,{coral_y} Z", fill="#8B4513"))
    dwg.add(dwg.path(d=f"M200,{coral_y} Q220,{coral_y-25} 240,{coral_y} Q260,{coral_y-20} 280,{coral_y} Z", fill="#A0522D"))

    # Bubbles (low activity) and Fish (high activity)
    for i, day in enumerate(contributions):
        msg_count = day['count']

        # Scatter positions
        x = random.randint(20, width-20)
        y = random.randint(50, height-50)

        if msg_count == 0:
            # Bubble
            dwg.add(dwg.circle(center=(x, y), r=3, fill="#66ddaa", opacity=0.5))
        elif msg_count < 5:
            # Small fish
            dwg.add(dwg.path(d=f"M{x},{y} L{x+10},{y-5} L{x+10},{y+5} Z", fill="#2288cc"))
        else:
            # Big fish for high activity
            dwg.add(dwg.path(d=f"M{x},{y} L{x+20},{y-10} L{x+20},{y+10} Z", fill="#00aaff"))
            # Add fin
            dwg.add(dwg.path(d=f"M{x+10},{y} L{x+15},{y-5} L{x+15},{y+5} Z", fill="#00aaff"))

    # Title
    dwg.add(dwg.text(f"{data['username']}'s Ocean Contributions", insert=(10, 30),
                     fill="#00aaff", font_family="Arial", font_size=16, font_weight="bold"))

    return dwg.tostring()
