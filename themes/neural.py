import svgwrite
import math
import random

def render(data):
    username = data['username']
    contributions = data['contributions'][-80:]  # recent activity

    width = 900
    height = 500
    dwg = svgwrite.Drawing(size=(f"{width}px", f"{height}px"))

    # Background
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="#0a0f1f"))

    # Title
    dwg.add(dwg.text(f"{username}'s Neural Activity",
                     insert=(width/2, 50),
                     text_anchor="middle",
                     fill="#00f7ff",
                     font_size="32px",
                     font_family="Segoe UI"))

    cx, cy = width/2, height/2 + 30
    nodes = []

    # Create neurons in circular brain-like layout
    for i, day in enumerate(contributions):
        angle = i * (360 / len(contributions))
        radius = 120 + random.randint(-40, 40)

        x = cx + math.cos(math.radians(angle)) * radius
        y = cy + math.sin(math.radians(angle)) * radius

        count = day['count']
        size = 4 + min(count, 10)

        brightness = min(255, 100 + count * 15)
        color = f"rgb(0,{brightness},255)"

        # neuron
        dwg.add(dwg.circle(center=(x, y), r=size, fill=color, opacity=0.9))
        nodes.append((x, y, count))

    # Draw synapse connections
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            x1, y1, c1 = nodes[i]
            x2, y2, c2 = nodes[j]

            dist = math.hypot(x2-x1, y2-y1)

            # only connect nearby neurons
            if dist < 120:
                strength = min(c1 + c2, 15)
                opacity = strength / 30

                dwg.add(dwg.line(start=(x1, y1), end=(x2, y2),
                                 stroke="#00f7ff",
                                 stroke_width=1,
                                 opacity=opacity))

    # Central Brain Core
    dwg.add(dwg.circle(center=(cx, cy), r=30, fill="#00f7ff", opacity=0.2))
    dwg.add(dwg.text("AI CORE", insert=(cx, cy+5),
                     text_anchor="middle",
                     fill="#00f7ff",
                     font_size="14px"))

    return dwg.tostring()
