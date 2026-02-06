import svgwrite
import random
from themes.styles import THEMES
import math
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
    
    # Allow a slightly larger playground for Gaming / Snake
    if theme_name == "Gaming":
        width = 560
        height = 180
    else:
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
        """
        Data-driven SNAKE Logic for the Gaming theme.
        
        Visual Storytelling Approach:
        - This is a snapshot of motion, not an animation
        - Snake path represents chronological progression through contribution days
        - Movement illusion: left→right, top→bottom (like GitHub's graph)
        - Snake grows as it "eats" commits over time
        - Head appears at the most recent active contribution day
        
        Grid Mapping:
        - 28 columns × 7 rows = 196 days (last ~6 months)
        - Each cell = one day, mapped chronologically
        - Layout: left→right, top→bottom (week-by-week, day-by-day)
        """
        
        contributions = data.get("contributions", []) or []
        # Use last 196 days to fit 28×7 grid (GitHub-style)
        contributions = contributions[-196:]
        
        tile_size = 12
        gap = 2
        cols = 28  # weeks
        rows = 7   # days per week
        
        start_x = 20
        start_y = 55
        
        # Retro HUD / score
        dwg.add(
            dwg.text(
                f"SCORE: {data.get('total_commits', '0')}",
                insert=(width - 150, 30),
                fill=theme["text_color"],
                font_family="Courier New",
                font_size=14,
                font_weight="bold",
            )
        )
        
        # --- STEP 1: Map contributions to grid cells chronologically ---
        # Each contribution day gets a position: left→right, top→bottom
        grid_cells = []
        for idx, day in enumerate(contributions):
            if idx >= cols * rows:
                break  # Only fit 196 days
            
            col = idx // rows  # Week column (0-27)
            row = idx % rows   # Day row (0-6)
            
            x = start_x + col * (tile_size + gap)
            y = start_y + row * (tile_size + gap)
            count = day.get("count", 0)
            
            grid_cells.append({
                "x": x,
                "y": y,
                "count": count,
                "index": idx,  # Chronological order (0 = oldest, 195 = newest)
            })
        
        # Fill empty grid if no contributions
        if not grid_cells:
            for col in range(cols):
                for row in range(rows):
                    x = start_x + col * (tile_size + gap)
                    y = start_y + row * (tile_size + gap)
                    grid_cells.append({"x": x, "y": y, "count": 0, "index": col * rows + row})
        
        # --- STEP 2: Draw base grid (ground tiles) ---
        for cell in grid_cells:
            base_color = "#1e293b"  # Dark ground
            fill = base_color
            
            if cell["count"] > 0:
                # Grass intensity by commit count
                if cell["count"] < 3:
                    fill = "#2e7d32"  # Dark grass
                elif cell["count"] < 7:
                    fill = "#43a047"  # Medium grass
                else:
                    fill = "#81c784"  # Bright grass
            
            dwg.add(
                dwg.rect(
                    insert=(cell["x"], cell["y"]),
                    size=(tile_size, tile_size),
                    fill=fill,
                    rx=1,
                    ry=1,
                )
            )
        
        # --- STEP 3: Identify active days and high-commit "food" days ---
        active_days = [c for c in grid_cells if c["count"] > 0]
        
        if not active_days:
            # Fallback: simple horizontal snake if no contributions
            center_row = rows // 2
            snake_segments = []
            for col in range(min(18, cols)):
                x = start_x + col * (tile_size + gap)
                y = start_y + center_row * (tile_size + gap)
                snake_segments.append((x, y))
            
            # Draw fallback snake
            for sx, sy in snake_segments[:-1]:
                dwg.add(
                    dwg.rect(
                        insert=(sx, sy),
                        size=(tile_size, tile_size),
                        fill=theme["icon_color"],
                        rx=2,
                        ry=2,
                    )
                )
            if snake_segments:
                hx, hy = snake_segments[-1]
                dwg.add(
                    dwg.rect(
                        insert=(hx, hy),
                        size=(tile_size, tile_size),
                        fill=theme["title_color"],
                        rx=2,
                        ry=2,
                    )
                )
                # Eyes
                dwg.add(dwg.rect(insert=(hx + 2, hy + 2), size=(2, 2), fill="black"))
                dwg.add(dwg.rect(insert=(hx + tile_size - 4, hy + 2), size=(2, 2), fill="black"))
        else:
            # --- STEP 4: Identify "food" hotspots (top commit days) ---
            # Find top N days by commit count - these are food targets
            sorted_by_count = sorted(active_days, key=lambda c: c["count"], reverse=True)
            num_food = min(max(5, len(active_days) // 5), 15)  # 5-15 food targets
            food_days = {c["index"]: c for c in sorted_by_count[:num_food]}
            
            # --- STEP 5: Build zig-zag snake path (GitHub-style weeks) ---
            # Strategy: Zig-zag through grid left→right, then down, then right→left
            # This creates visual "movement" without animation
            
            # Create a lookup: (week_col, day_row) → cell data
            grid_lookup = {}
            for cell in grid_cells:
                week_col = (cell["x"] - start_x) // (tile_size + gap)
                day_row = (cell["y"] - start_y) // (tile_size + gap)
                grid_lookup[(week_col, day_row)] = cell
            
            # Also create reverse lookup: index → cell
            index_lookup = {cell["index"]: cell for cell in grid_cells}
            
            snake_segments = []
            visited_indices = set()
            
            # Calculate snake length based on activity
            total_active = len(active_days)
            snake_length = min(max(20, total_active // 2), 50)  # 20-50 segments
            
            # Build zig-zag path: traverse weeks, alternating row direction
            # Week 0: rows 0→6 (left→right), Week 1: rows 6→0 (right→left), etc.
            for week_col in range(min(cols, snake_length // rows + 3)):
                if len(snake_segments) >= snake_length:
                    break
                
                # Alternate direction: even weeks go top→bottom, odd weeks go bottom→top
                is_top_to_bottom = (week_col % 2 == 0)
                
                if is_top_to_bottom:
                    row_range = range(rows)  # 0 to 6
                else:
                    row_range = range(rows - 1, -1, -1)  # 6 to 0
                
                for day_row in row_range:
                    if len(snake_segments) >= snake_length:
                        break
                    
                    pos = (week_col, day_row)
                    if pos in grid_lookup:
                        cell = grid_lookup[pos]
                        # Prioritize active days, but include some empty cells to maintain path
                        if cell["count"] > 0 or (len(snake_segments) < 3 and cell["index"] not in visited_indices):
                            snake_segments.append((cell["x"], cell["y"], cell["index"]))
                            visited_indices.add(cell["index"])
            
            # Ensure we pass through food hotspots
            # Insert food days into path if not already included
            for food_idx, food_cell in food_days.items():
                if food_cell["index"] not in visited_indices:
                    # Find insertion point (chronologically closest)
                    insert_idx = len(snake_segments)
                    for i, (_, _, seg_idx) in enumerate(snake_segments):
                        if seg_idx > food_cell["index"]:
                            insert_idx = i
                            break
                    snake_segments.insert(insert_idx, (food_cell["x"], food_cell["y"], food_cell["index"]))
                    visited_indices.add(food_cell["index"])
            
            # Trim to desired length
            snake_segments = snake_segments[:snake_length]
            
            # Ensure head is at the most recent active day
            most_recent = max(active_days, key=lambda c: c["index"])
            
            # Remove most_recent if already in path, then add to end
            snake_segments = [(x, y, idx) for x, y, idx in snake_segments if idx != most_recent["index"]]
            snake_segments.append((most_recent["x"], most_recent["y"], most_recent["index"]))
            
            # --- STEP 6: Draw "food" tiles FIRST (so snake appears on top) ---
            for cell_idx, cell in food_days.items():
                cx = cell["x"] + tile_size / 2
                cy = cell["y"] + tile_size / 2
                # Glowing red apple
                dwg.add(
                    dwg.circle(
                        center=(cx, cy),
                        r=tile_size * 0.45,
                        fill="#ff1744",
                        fill_opacity=0.95,
                    )
                )
                # Outer glow
                dwg.add(
                    dwg.circle(
                        center=(cx, cy),
                        r=tile_size * 0.55,
                        fill="#ff5252",
                        fill_opacity=0.3,
                    )
                )
                # Small green leaf
                dwg.add(
                    dwg.rect(
                        insert=(cx - 2, cy - tile_size * 0.45 - 3),
                        size=(4, 5),
                        fill="#43a047",
                    )
                )
            
            # --- STEP 7: Draw snake with time-gradient colors ---
            # Color gradient: tail (old) = darker green, head (new) = bright neon
            num_segments = len(snake_segments)
            
            # Color stops
            tail_color = "#1f6f1f"  # Dark green (old commits)
            mid_color = "#00c853"   # Medium green
            head_color = "#7CFF00"  # Bright neon green (new commits)
            
            for i, (sx, sy, seg_idx) in enumerate(snake_segments[:-1]):
                # Calculate gradient position (0 = tail, 1 = head)
                t = i / max(1, num_segments - 1)
                
                # Interpolate color
                if t < 0.5:
                    # Tail to mid
                    local_t = t * 2
                    r = int(int(tail_color[1:3], 16) * (1 - local_t) + int(mid_color[1:3], 16) * local_t)
                    g = int(int(tail_color[3:5], 16) * (1 - local_t) + int(mid_color[3:5], 16) * local_t)
                    b = int(int(tail_color[5:7], 16) * (1 - local_t) + int(mid_color[5:7], 16) * local_t)
                else:
                    # Mid to head
                    local_t = (t - 0.5) * 2
                    r = int(int(mid_color[1:3], 16) * (1 - local_t) + int(head_color[1:3], 16) * local_t)
                    g = int(int(mid_color[3:5], 16) * (1 - local_t) + int(head_color[3:5], 16) * local_t)
                    b = int(int(mid_color[5:7], 16) * (1 - local_t) + int(head_color[5:7], 16) * local_t)
                
                segment_color = f"#{r:02x}{g:02x}{b:02x}"
                
                dwg.add(
                    dwg.rect(
                        insert=(sx, sy),
                        size=(tile_size, tile_size),
                        fill=segment_color,
                        rx=2,
                        ry=2,
                        stroke="#020617",
                        stroke_width=0.5,
                    )
                )
            
            # --- STEP 8: Draw snake head with glow effect ---
            if snake_segments:
                hx, hy, _ = snake_segments[-1]
                
                # Head glow (outer)
                dwg.add(
                    dwg.rect(
                        insert=(hx - 1, hy - 1),
                        size=(tile_size + 2, tile_size + 2),
                        fill="#7CFF00",
                        fill_opacity=0.4,
                        rx=3,
                        ry=3,
                    )
                )
                
                # Head (bright neon)
                dwg.add(
                    dwg.rect(
                        insert=(hx, hy),
                        size=(tile_size, tile_size),
                        fill=head_color,
                        rx=2,
                        ry=2,
                        stroke="#020617",
                        stroke_width=1.5,
                    )
                )
                
                # Pixel eyes on head
                eye = 3
                dwg.add(dwg.rect(insert=(hx + 3, hy + 3), size=(eye, eye), fill="black"))
                dwg.add(dwg.rect(insert=(hx + tile_size - eye - 3, hy + 3), size=(eye, eye), fill="black"))

    elif theme_name == "Space":
        # Spaceship logic
        # Commits are stars.
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
                
    elif theme_name == "Neural":
        cx = width / 2
        cy = height / 2 + 10

        contributions = data.get("contributions", [])[-80:]
        if not contributions:
            return dwg.tostring()

        nodes = []

        # --- Brain core glow ---
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

        # --- Generate brain-shaped neuron positions ---
        for i, day in enumerate(contributions):
            count = day.get("count", 0)

            # Hemisphere split
            side = -1 if i % 2 == 0 else 1

            # Organic brain ellipse
            angle = random.uniform(0, math.pi)
            radius_x = random.uniform(90, 150)
            radius_y = random.uniform(60, 110)

            # Distortion noise
            noise = random.uniform(0.85, 1.15)

            x = cx + side * math.cos(angle) * radius_x * noise
            y = cy + math.sin(angle) * radius_y * noise

            # Visual weight
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

        # --- Synapse connections ---
        for i in range(len(nodes)):
            x1, y1, c1 = nodes[i]

            # Each neuron connects to a few others
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
