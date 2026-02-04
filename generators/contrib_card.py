import svgwrite
import random
from themes.styles import THEMES

def draw_contrib_card(data, theme_name="Default", custom_colors=None):
    """
    Generates the Contribution Graph Card SVG.
    Supports 'Snake', 'Space', 'Marvel' visualization logic.
    """
    theme = THEMES.get(theme_name, THEMES["Default"]).copy()
    if custom_colors:
        theme.update(custom_colors)
    
    # Fake contribution data for visualization if not fully populated
    # In a real scenario, data['contributions'] would have the last ~15-30 days or weeks
    # For MVP we simulate a strip of activity
    
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
        # "Eating my contributions" -> The snake head is at the last commit
        
        grid_size = 15
        start_x = 20
        start_y = 50
        
        # Draw a simple grid path (Snake body) taking up space
        dwg.add(dwg.text(f"SCORE: {data.get('total_commits', '0')}", insert=(width-120, 30),
                         fill=theme["text_color"], font_family="Courier New", font_size=16, font_weight="bold"))
        
        # Draw Food (Contributions) randomly placed
        # Red pixel apples
        for i in range(8):
             fx = random.randint(2, 28) * (grid_size+2) + start_x
             fy = random.randint(1, 5) * (grid_size+2) + start_y
             if fy > height - 20: fy = height - 20
             dwg.add(dwg.rect(insert=(fx, fy), size=(grid_size, grid_size), fill="#FF3333", rx=2, ry=2)) # Apple

        # Draw Snake Body - Green path
        # Simulating a snake that has grown long
        segments = [(start_x + i*(grid_size+2), start_y + (grid_size+2)*2) for i in range(10)]
        # Turn
        segments.extend([(start_x + 9*(grid_size+2), start_y + (grid_size+2)*j) for j in range(3, 5)])
        
        for px, py in segments:
            dwg.add(dwg.rect(insert=(px, py), size=(grid_size, grid_size), fill=theme["icon_color"], rx=2, ry=2))
            
        # Head
        hx, hy = segments[-1]
        dwg.add(dwg.rect(insert=(hx, hy), size=(grid_size, grid_size), fill=theme["title_color"])) 
        # Eyes
        dwg.add(dwg.rect(insert=(hx+3, hy+3), size=(3, 3), fill="black"))
        dwg.add(dwg.rect(insert=(hx+9, hy+3), size=(3, 3), fill="black"))

    elif theme_name == "Space":
        # Spaceship logic
        # Commits are stars.
        
        # Draw random stars
        for _ in range(30):
            sx = random.randint(20, width-20)
            sy = random.randint(50, height-20)
            r = random.uniform(1, 3)
            dwg.add(dwg.circle(center=(sx, sy), r=r, fill="white", opacity=random.uniform(0.5, 1.0)))
            
        # Draw Spaceship (Simple triangle)
        ship_x = width - 60
        ship_y = height / 2 + 10
        
        # Flame
        dwg.add(dwg.path(d=f"M {ship_x-10} {ship_y} L {ship_x-20} {ship_y-5} L {ship_x-20} {ship_y+5} Z", fill="orange"))
        # Body
        dwg.add(dwg.path(d=f"M {ship_x} {ship_y} L {ship_x-15} {ship_y-8} L {ship_x-15} {ship_y+8} Z", fill="#00a8ff"))
        
        # Beam eating a star?
        dwg.add(dwg.line(start=(ship_x, ship_y), end=(width, ship_y), stroke="#00a8ff", stroke_width=2, stroke_dasharray="4,2"))

    elif theme_name == "Marvel":
        # Infinity Stones
        stones = ["#FFD700", "#FF0000", "#0000FF", "#800080", "#008000", "#FFA500"] # Mind, Reality, Space, Power, Time, Soul
        
        # Draw slots
        cx = width / 2
        cy = height / 2 + 10
        
        # Gauntlet hints? Or just the stones glowing
        for i, color in enumerate(stones):
            sx = 60 + i * 60
            sy = cy
            
            # Glow
            dwg.add(dwg.circle(center=(sx, sy), r=15, fill=color, opacity=0.3))
            # Stone
            dwg.add(dwg.circle(center=(sx, sy), r=8, fill=color, stroke="white", stroke_width=1))
            
            # Label below
            dwg.add(dwg.text(f"Stone {i+1}", insert=(sx, sy+30), fill="white", font_size=10, text_anchor="middle"))
            
        dwg.add(dwg.text("SNAP!", insert=(width-80, cy), fill=theme["title_color"], font_size=24, font_weight="bold", font_family="Impact"))

    elif theme_name == "Glass":
        # Glassmorphism contribution panel

        # --- Background gradient (subtle, dark, non-flat) ---
        bg_grad = dwg.linearGradient(start=(0, 0), end=(1, 1), id="glassBg")
        bg_grad.add_stop_color(0, "#020617")
        bg_grad.add_stop_color(0.5, "#0b1220")
        bg_grad.add_stop_color(1, "#020617")
        dwg.defs.add(bg_grad)

        dwg.add(
            dwg.rect(
                insert=(0, 0),
                size=("100%", "100%"),
                rx=18,
                ry=18,
                fill="url(#glassBg)",
            )
        )

        # --- Noise overlay (very subtle grain) ---
        # Approximate with a low-opacity white overlay to simulate texture
        dwg.add(
            dwg.rect(
                insert=(0, 0),
                size=("100%", "100%"),
                rx=18,
                ry=18,
                fill="#ffffff",
                fill_opacity=0.02,
            )
        )

        # --- Glass blur filter for inner panel ---
        glass_filter = dwg.filter(
            id="glassBlur",
            x="-20%",
            y="-20%",
            width="140%",
            height="140%",
        )
        glass_filter.feGaussianBlur(in_="SourceGraphic", stdDeviation=10)
        glass_filter.feColorMatrix(
            type="matrix",
            values=(
                "1 0 0 0 0 "
                "0 1 0 0 0 "
                "0 0 1 0 0 "
                "0 0 0 0.75 0"
            ),
        )
        dwg.defs.add(glass_filter)

        # --- Inner glass card ---
        inner_margin_x = 28
        inner_margin_y = 30

        panel = dwg.rect(
            insert=(inner_margin_x, inner_margin_y),
            size=(width - inner_margin_x * 2, height - inner_margin_y * 2),
            rx=22,
            ry=22,
            fill="#ffffff",
            fill_opacity=0.10,
            stroke=theme["border_color"],
            stroke_width=1.2,
        )
        panel["filter"] = "url(#glassBlur)"
        dwg.add(panel)

        # Soft outer glow around panel
        dwg.add(
            dwg.rect(
                insert=(inner_margin_x - 2, inner_margin_y - 2),
                size=(width - inner_margin_x * 2 + 4, height - inner_margin_y * 2 + 4),
                rx=24,
                ry=24,
                fill=theme["border_color"],
                fill_opacity=0.06,
            )
        )

        # --- Header content ---
        header_y = inner_margin_y + 20

        dwg.add(
            dwg.text(
                title,
                insert=(inner_margin_x + 16, header_y),
                fill=theme["title_color"],
                font_size=theme["title_font_size"],
                font_family=theme["font_family"],
                font_weight="bold",
            )
        )

        # Small subtitle (optional) under title
        dwg.add(
            dwg.text(
                "Last year of activity",
                insert=(inner_margin_x + 16, header_y + 18),
                fill=theme["text_color"],
                font_size=theme["text_font_size"] - 2,
                font_family=theme["font_family"],
                fill_opacity=0.7,
            )
        )

        # --- Contributions as glass bubbles in a tight grid ---
        contributions = data.get("contributions", [])[-180:]  # last ~180 days
        grid_start_x = inner_margin_x + 20
        grid_start_y = inner_margin_y + 42
        cell_x_gap = 16
        cell_y_gap = 14
        max_cols = 24  # more compact than default card

        x = grid_start_x
        y = grid_start_y

        for idx, day in enumerate(contributions):
            count = day.get("count", 0)

            # Map count -> radius + opacity
            if count == 0:
                r = 2
                opacity = 0.12
                bubble_color = "#e5e7eb"
            elif count < 3:
                r = 3.5
                opacity = 0.25
                bubble_color = "#bae6fd"
            elif count < 7:
                r = 4.5
                opacity = 0.45
                bubble_color = "#7dd3fc"
            else:
                r = 6
                opacity = 0.7
                bubble_color = "#38bdf8"

            # Base bubble
            dwg.add(
                dwg.circle(
                    center=(x, y),
                    r=r,
                    fill=bubble_color,
                    fill_opacity=opacity,
                )
            )

            # Inner highlight for non-zero
            if count > 0:
                dwg.add(
                    dwg.circle(
                        center=(x - r * 0.3, y - r * 0.4),
                        r=r * 0.45,
                        fill="#ffffff",
                        fill_opacity=0.35,
                    )
                )

            # Slight shadow below to add depth
            if count > 0:
                dwg.add(
                    dwg.ellipse(
                        center=(x, y + r * 0.4),
                        r=(r * 0.9, r * 0.3),
                        fill="#020617",
                        fill_opacity=0.35,
                    )
                )

            # Advance grid
            if (idx + 1) % max_cols == 0:
                x = grid_start_x
                y += cell_y_gap
            else:
                x += cell_x_gap
    else:
        # Default Grid (Github Style)
        # Just simple squares
        box_size = 12
        gap = 3
        start_x = 20
        start_y = 60
        
        count = 0
        for col in range(25): # 25 weeks horizontal
            for row in range(5): # 5 days vertical
                x = start_x + col * (box_size + gap)
                y = start_y + row * (box_size + gap)
                
                # Random "green" level
                level = random.choice([0, 1, 2, 3, 4])
                colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
                
                # Use theme override if set
                # For default we stick to standard GH colors unless customized logic is deeper
                # But let's respect the theme accent
                fill = colors[level]
                if level > 0:
                     # Mix with theme accent roughly?
                     # For now just keep standard GH style for "Default"
                     pass
                     
                dwg.add(dwg.rect(insert=(x, y), size=(box_size, box_size), fill=fill, rx=2, ry=2))
                
    return dwg.tostring()
