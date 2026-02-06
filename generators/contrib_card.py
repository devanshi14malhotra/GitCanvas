import svgwrite
import random
from themes.styles import THEMES
import math

def draw_contrib_card(data, theme_name="Default", custom_colors=None):
    """
    Generates the Contribution Graph Card SVG.
    Supports 'Snake', 'Space', 'Marvel', 'Cyberpunk', 'Retro' visualization logic.
    """
    theme = THEMES.get(theme_name, THEMES["Default"]).copy()
    if custom_colors:
        theme.update(custom_colors)
    
    width = 500
    height = 150
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
    
    # Background
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=10, ry=10, 
                     fill=theme["bg_color"], stroke=theme["border_color"], stroke_width=2))
    
    # Title
    title = f"{data['username']}'s Contributions"
    dwg.add(dwg.text(title, insert=(20, 30), 
                     fill=theme["title_color"], font_size=theme["title_font_size"], 
                     font_family=theme["font_family"], font_weight="bold"))
    
    # Theme Specific Logic
    
    if theme_name == "Gaming":
        # SNAKE Logic: A winding path of green blocks
        grid_size = 15
        start_x = 20
        start_y = 50
        
        dwg.add(dwg.text(f"SCORE: {data.get('total_commits', '0')}", insert=(width-120, 30),
                         fill=theme["text_color"], font_family="Courier New", font_size=16, font_weight="bold"))
        
        # Draw Food (Contributions)
        for i in range(8):
             fx = random.randint(2, 28) * (grid_size+2) + start_x
             fy = random.randint(1, 5) * (grid_size+2) + start_y
             if fy > height - 20: fy = height - 20
             dwg.add(dwg.rect(insert=(fx, fy), size=(grid_size, grid_size), fill="#FF3333", rx=2, ry=2))

        # Draw Snake Body
        segments = [(start_x + i*(grid_size+2), start_y + (grid_size+2)*2) for i in range(10)]
        segments.extend([(start_x + 9*(grid_size+2), start_y + (grid_size+2)*j) for j in range(3, 5)])
        
        for px, py in segments:
            dwg.add(dwg.rect(insert=(px, py), size=(grid_size, grid_size), fill=theme["icon_color"], rx=2, ry=2))
            
        # Head
        hx, hy = segments[-1]
        dwg.add(dwg.rect(insert=(hx, hy), size=(grid_size, grid_size), fill=theme["title_color"])) 
        dwg.add(dwg.rect(insert=(hx+3, hy+3), size=(3, 3), fill="black"))
        dwg.add(dwg.rect(insert=(hx+9, hy+3), size=(3, 3), fill="black"))

    elif theme_name == "Space":
        # Spaceship logic
        dwg.defs.add(dwg.style("""
            @keyframes twinkle {
            0%   { opacity: 0.3; }
            50%  { opacity: 1; }
            100% { opacity: 0.3; }
            }

            .star {
            animation: twinkle 2s ease-in-out infinite;
            }
            """))

        for i in range(30):
            sx = random.randint(20, width - 20)
            sy = random.randint(50, height - 20)
            r = random.uniform(1, 3)
            delay = random.uniform(0, 2)

            star = dwg.circle(
                center=(sx, sy),
                r=r,
                fill="white",
                class_="star",
                style=f"animation-delay: {delay}s"
            )

            dwg.add(star)

        # Draw Spaceship
        ship_x = width - 60
        ship_y = height / 2 + 10
        
        dwg.add(dwg.path(d=f"M {ship_x-10} {ship_y} L {ship_x-20} {ship_y-5} L {ship_x-20} {ship_y+5} Z", fill="orange"))
        dwg.add(dwg.path(d=f"M {ship_x} {ship_y} L {ship_x-15} {ship_y-8} L {ship_x-15} {ship_y+8} Z", fill="#00a8ff"))
        dwg.add(dwg.line(start=(ship_x, ship_y), end=(width, ship_y), stroke="#00a8ff", stroke_width=2, stroke_dasharray="4,2"))

    elif theme_name == "Marvel":
        # Infinity Stones
        stones = ["#FFD700", "#FF0000", "#0000FF", "#800080", "#008000", "#FFA500"]
        
        cx = width / 2
        cy = height / 2 + 10
        
        for i, color in enumerate(stones):
            sx = 60 + i * 60
            sy = cy
            
            dwg.add(dwg.circle(center=(sx, sy), r=15, fill=color, opacity=0.3))
            dwg.add(dwg.circle(center=(sx, sy), r=8, fill=color, stroke="white", stroke_width=1))
            dwg.add(dwg.text(f"Stone {i+1}", insert=(sx, sy+30), fill="white", font_size=10, text_anchor="middle"))
            
        dwg.add(dwg.text("SNAP!", insert=(width-80, cy), fill=theme["title_color"], font_size=24, font_weight="bold", font_family="Impact"))

    elif theme_name == "Cyberpunk":
        NEON_COLORS = ["#00ffff", "#39ff14", "#fcee0c", "#ff00ff"]

        dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="#0a0a0a"))

        contributions = data.get("contributions", [])

        for commit in contributions:
            count = commit.get("count", 0)

            x = random.randint(20, width - 20)
            y = random.randint(50, height - 20)

            radius = min(2 + count * 0.6, 9)
            color = NEON_COLORS[count % len(NEON_COLORS)]

            # Glow
            dwg.add(dwg.circle(center=(x, y), r=radius*2.5, fill=color, fill_opacity=0.12))

            # Main dot
            dwg.add(dwg.circle(center=(x, y), r=radius, fill=color))

    elif theme_name == "Retro":
        PAPER_BG = "#f5e6c8"
        INK_COLORS = ["#5c4632", "#7a5c3e", "#3b2b20"]

        dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill=PAPER_BG))

        dwg.add(dwg.text(
            "Contribution Log",
            insert=(20, 40),
            fill="#5c4632",
            font_size="20px",
            font_family="Courier New, monospace",
            font_weight="bold"
        ))

        contributions = data.get("contributions", [])

        for commit in contributions:
            count = commit.get("count", 0)

            x = random.randint(20, width - 20)
            y = random.randint(60, height - 20)

            radius = min(2 + count * 0.4, 7)
            color = INK_COLORS[count % len(INK_COLORS)]

            dwg.add(dwg.circle(center=(x, y), r=radius, fill=color, fill_opacity=0.85))

    elif theme_name == "Neural":
        cx = width / 2
        cy = height / 2 + 10

        contributions = data.get("contributions", [])[-80:]
        if not contributions:
            return dwg.tostring()

        nodes = []

        # Brain core glow
        dwg.add(dwg.circle(center=(cx, cy), r=45, fill="#00f7ff", opacity=0.08))
        dwg.add(dwg.text(
            "Contributions",
            insert=(cx, cy + 5),
            text_anchor="middle",
            fill="#00f7ff",
            font_size="12px",
            font_family="Courier New",
            opacity=0.8
        ))

        # Generate brain-shaped neuron positions
        for i, day in enumerate(contributions):
            count = day.get("count", 0)

            side = -1 if i % 2 == 0 else 1

            angle = random.uniform(0, math.pi)
            radius_x = random.uniform(90, 150)
            radius_y = random.uniform(60, 110)

            noise = random.uniform(0.85, 1.15)

            x = cx + side * math.cos(angle) * radius_x * noise
            y = cy + math.sin(angle) * radius_y * noise

            size = 2 + min(count, 10)
            brightness = min(255, 80 + count * 18)
            color = f"rgb(0,{brightness},255)"

            dwg.add(dwg.circle(
                center=(x, y),
                r=size,
                fill=color,
                opacity=0.9
            ))

            nodes.append((x, y, count))

        # Synapse connections
        for i in range(len(nodes)):
            x1, y1, c1 = nodes[i]

            for _ in range(random.randint(2, 6)):
                j = random.randint(0, len(nodes) - 1)
                x2, y2, c2 = nodes[j]

                dist = math.hypot(x2 - x1, y2 - y1)

                if dist < 140:
                    opacity = min((c1 + c2) / 20, 0.5)

                    dwg.add(dwg.line(
                        start=(x1, y1),
                        end=(x2, y2),
                        stroke="#00f7ff",
                        stroke_width=1,
                        opacity=opacity
                    ))

    else:
        # Default Grid (Github Style)
        box_size = 12
        gap = 3
        start_x = 20
        start_y = 60
        
        for col in range(25):
            for row in range(5):
                x = start_x + col * (box_size + gap)
                y = start_y + row * (box_size + gap)
                
                level = random.choice([0, 1, 2, 3, 4])
                colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
                fill = colors[level]
                     
                dwg.add(dwg.rect(insert=(x, y), size=(box_size, box_size), fill=fill, rx=2, ry=2))
                
    return dwg.tostring()