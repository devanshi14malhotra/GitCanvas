import svgwrite
from themes.styles import THEMES
import math
import random
from datetime import date, datetime, timedelta


def _levels_from_cells(cells, max_count):
    levels = []

    for cell in cells:
        if cell.get("is_future"):
            levels.append(None)
            continue

        count = cell.get("count", 0)
        if count <= 0 or max_count == 0:
            levels.append(0)
            continue

        ratio = count / max_count
        if ratio <= 0.25:
            levels.append(1)
        elif ratio <= 0.5:
            levels.append(2)
        elif ratio <= 0.75:
            levels.append(3)
        else:
            levels.append(4)

    return levels


def _grid_positions(cols, rows, start_x, start_y, box_size, gap):
    positions = []
    for col in range(cols):
        for row in range(rows):
            x = start_x + col * (box_size + gap)
            y = start_y + row * (box_size + gap)
            positions.append((x, y))
    return positions


def _latest_contribution_date(contributions):
    max_date = None
    for item in contributions:
        item_date = item.get("date") if item else None
        if not item_date:
            continue
        try:
            parsed = date.fromisoformat(item_date)
        except Exception:
            continue
        if not max_date or parsed > max_date:
            max_date = parsed

    today = datetime.utcnow().date()
    if max_date and max_date > today:
        return today
    return max_date


def _weeks_from_dates(contributions, cols, rows):
    if not contributions:
        return [[{"date": None, "count": 0} for _ in range(rows)] for _ in range(cols)], None

    date_counts = {}
    for item in contributions:
        item_date = item.get("date")
        if not item_date:
            continue
        try:
            parsed = date.fromisoformat(item_date)
        except Exception:
            continue
        date_counts[parsed] = item.get("count", 0)

    max_date = _latest_contribution_date(contributions)
    if not max_date:
        return [[{"date": None, "count": 0} for _ in range(rows)] for _ in range(cols)], None

    days_to_sunday = (max_date.weekday() + 1) % 7
    end_week_start = max_date - timedelta(days=days_to_sunday)
    start_week_start = end_week_start - timedelta(days=(cols - 1) * 7)

    weeks = []
    for col in range(cols):
        week_start = start_week_start + timedelta(days=col * 7)
        week = []
        for row in range(rows):
            day_date = week_start + timedelta(days=row)
            week.append({
                "date": day_date.isoformat(),
                "count": date_counts.get(day_date, 0)
            })
        weeks.append(week)

    return weeks, max_date


def _resolve_weeks(contributions, contribution_weeks, cols, rows):
    if contribution_weeks:
        weeks = contribution_weeks[-cols:]
        normalized = []
        for week in weeks:
            week_days = list(week) if week else []
            if len(week_days) < rows:
                week_days = week_days + ([{"date": None, "count": 0}] * (rows - len(week_days)))
            normalized.append(week_days[:rows])
        if len(normalized) < cols:
            pad = [[{"date": None, "count": 0} for _ in range(rows)] for _ in range(cols - len(normalized))]
            normalized = pad + normalized
        return normalized, _latest_contribution_date(contributions)

    return _weeks_from_dates(contributions, cols, rows)


def _weeks_to_cells(weeks, cols, rows, max_date):
    cells = []
    for col in range(cols):
        week = weeks[col] if col < len(weeks) else []
        for row in range(rows):
            day = week[row] if row < len(week) else {"date": None, "count": 0}
            item_date = day.get("date") if day else None
            parsed = None
            if item_date:
                try:
                    parsed = date.fromisoformat(item_date)
                except Exception:
                    parsed = None
            is_future = bool(max_date and parsed and parsed > max_date)
            cells.append({
                "date": item_date,
                "count": day.get("count", 0),
                "is_future": is_future
            })
    return cells


def _add_timeline_labels(dwg, weeks, cols, rows, start_x, start_y, box_size, gap, theme):
    last_month = None
    max_label_x = start_x + (cols - 1) * (box_size + gap)

    for col, week in enumerate(weeks):
        day = week[0] if week else None
        day_date = None
        if day and day.get("date"):
            try:
                day_date = date.fromisoformat(day["date"])
            except Exception:
                day_date = None

        if not day_date:
            continue

        month_label = day_date.strftime("%b")
        if month_label != last_month:
            x = start_x + col * (box_size + gap) - 2
            if x > max_label_x - 10:
                x = max_label_x - 10
            y = start_y - 10
            dwg.add(dwg.text(
                month_label,
                insert=(x, y),
                fill=theme["text_color"],
                font_size=9,
                font_family=theme["font_family"],
                opacity=0.8
            ))
            last_month = month_label

    label_x = start_x - 24
    label_rows = {1: "Mon", 3: "Wed", 5: "Fri"}
    for row, label in label_rows.items():
        y = start_y + row * (box_size + gap) + box_size - 1
        dwg.add(dwg.text(
            label,
            insert=(label_x, y),
            fill=theme["text_color"],
            font_size=9,
            font_family=theme["font_family"],
            opacity=0.8
        ))


def draw_contrib_card(data, theme_name="Default", custom_colors=None):
    """
    Generates the Contribution Graph Card SVG.
    Supports 'Snake', 'Space', 'Marvel' visualization logic.
    """
    # Save original theme name for comparison (fix from main branch)
    original_theme_name = theme_name
    
    theme = THEMES.get(theme_name, THEMES["Default"]).copy()
    if custom_colors:
        theme.update(custom_colors)
    
    width = 500
    height = 170
    
    # Allow larger canvas for Gaming theme (from main branch)
    if original_theme_name == "Gaming":
        width = 560
        height = 180
    
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
    
    # Background
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=10, ry=10, 
                     fill=theme["bg_color"], stroke=theme["border_color"], stroke_width=2))
    
    # Title
    title = f"{data['username']}'s Contributions"
    dwg.add(dwg.text(title, insert=(20, 24), 
                     fill=theme["title_color"], 
                     font_size=theme.get("title_font_size", 18), 
                     font_family=theme.get("font_family", "Arial"), 
                     font_weight="bold"))
    
    # Theme Specific Logic
    contributions = data.get("contributions", [])
    
    total_days = len(contributions)
    cols = 53 if total_days >= 371 else 52
    rows = 7
    weeks, max_date = _resolve_weeks(contributions, data.get("contribution_weeks"), cols, rows)

    if original_theme_name == "Gaming":
        # SNAKE Logic: A winding path of green blocks
        # "Eating my contributions" -> The snake head is at the last commit
        
        grid_size = 7
        gap = 2
        start_x = 26
        start_y = 72
        cells = _weeks_to_cells(weeks, cols, rows, max_date)
        max_count = max((cell["count"] for cell in cells if not cell["is_future"]), default=0)
        levels = _levels_from_cells(cells, max_count)
        positions = _grid_positions(cols, rows, start_x, start_y, grid_size, gap)

        _add_timeline_labels(dwg, weeks, cols, rows, start_x, start_y, grid_size, gap, theme)
        
        # Draw a simple grid path (Snake body) taking up space
        dwg.add(dwg.text(f"SCORE: {data.get('total_commits', '0')}", insert=(width-120, 30),
                         fill=theme["text_color"], font_family="Courier New", font_size=16, font_weight="bold"))
        
        # Draw grid cells based on real contribution levels
        colors = [theme["bg_color"], "#0e4429", "#006d32", "#26a641", "#39d353"]
        last_active_index = None

        for idx, (x, y) in enumerate(positions):
            level = levels[idx]
            if level is None:
                continue
            fill = colors[level]
            dwg.add(dwg.rect(insert=(x, y), size=(grid_size, grid_size), fill=fill, rx=2, ry=2))
            if level > 0:
                last_active_index = idx

            # Apples represent peak contribution days
            if level == 4:
                dwg.add(dwg.rect(insert=(x, y), size=(grid_size, grid_size), fill="#FF3333", rx=2, ry=2))

        # Snake head at last active cell
        if last_active_index is not None:
            hx, hy = positions[last_active_index]
            dwg.add(dwg.rect(insert=(hx, hy), size=(grid_size, grid_size), fill=theme["title_color"], rx=2, ry=2))
            dwg.add(dwg.rect(insert=(hx + 1, hy + 2), size=(2, 2), fill="black"))
            dwg.add(dwg.rect(insert=(hx + 4, hy + 2), size=(2, 2), fill="black"))

    elif original_theme_name == "Space":
        # Spaceship logic
        # Commits are stars based on contribution levels
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

        cells = _weeks_to_cells(weeks, cols, rows, max_date)
        max_count = max((cell["count"] for cell in cells if not cell["is_future"]), default=0)
        levels = _levels_from_cells(cells, max_count)
        start_x = 26
        start_y = 72
        grid_size = 7
        gap = 2
        positions = _grid_positions(cols, rows, start_x, start_y, grid_size, gap)

        _add_timeline_labels(dwg, weeks, cols, rows, start_x, start_y, grid_size, gap, theme)

        for idx, (sx, sy) in enumerate(positions):
            level = levels[idx]
            if level is None:
                continue
            if level == 0:
                continue
            r = 1 + (level * 0.7)
            delay = (idx % 10) * 0.2

            star = dwg.circle(
                center=(sx + 5, sy + 5),
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

    elif original_theme_name == "Marvel":
        # Infinity Stones that glow based on contribution intensity per bucket
        stones = ["#FFD700", "#FF0000", "#0000FF", "#800080", "#008000", "#FFA500"] # Mind, Reality, Space, Power, Time, Soul
        
        # Draw slots
        cx = width / 2
        cy = height / 2 + 10
        
        counts = [cell["count"] for cell in _weeks_to_cells(weeks, cols, rows, max_date) if not cell["is_future"]]
        if counts:
            bucket_size = max(1, len(counts) // len(stones))
        else:
            bucket_size = 1

        bucket_values = []
        for i in range(len(stones)):
            start = i * bucket_size
            end = start + bucket_size
            values = counts[start:end] if counts else []
            avg = sum(values) / len(values) if values else 0
            bucket_values.append(avg)

        max_bucket = max(bucket_values) if bucket_values else 0

        # Gauntlet hints? Or just the stones glowing
        for i, color in enumerate(stones):
            sx = 60 + i * 60
            sy = cy
            intensity = 0 if max_bucket == 0 else bucket_values[i] / max_bucket
            glow = 8 + (intensity * 14)
            stone_r = 6 + (intensity * 6)
            
            # Glow
            dwg.add(dwg.circle(center=(sx, sy), r=glow, fill=color, opacity=0.25 + (intensity * 0.35)))
            # Stone
            dwg.add(dwg.circle(center=(sx, sy), r=stone_r, fill=color, stroke="white", stroke_width=1))
            
            # Label below
            dwg.add(dwg.text(f"Stone {i+1}", insert=(sx, sy+30), fill="white", font_size=10, text_anchor="middle"))
            
        dwg.add(dwg.text("SNAP!", insert=(width-80, cy), fill=theme["title_color"], font_size=24, font_weight="bold", font_family="Impact"))

    elif original_theme_name == "Glass":
        # Neon Liquid Glassmorphism Theme (from main branch)
        
        # Theme Variables
        bg_col = theme.get("bg_color", "#050511")
        title_col = theme.get("title_color", "#00e5ff")
        text_col = theme.get("text_color", "#e0e0e0")
        border_col = theme.get("border_color", "white")
        
        # --- 1. Defining Filters & Gradients ---
        
        # Blur filter for background blobs
        blob_blur = dwg.filter(id="blobBlur", x="-50%", y="-50%", width="200%", height="200%")
        blob_blur.feGaussianBlur(in_="SourceGraphic", stdDeviation=40)
        dwg.defs.add(blob_blur)
        
        # Glow filter for text
        text_glow = dwg.filter(id="textGlow")
        text_glow.feGaussianBlur(in_="SourceAlpha", stdDeviation=2, result="blur")
        text_glow.feOffset(in_="blur", dx=0, dy=0, result="offsetBlur")
        text_glow.feFlood(flood_color=title_col, result="glowColor")
        text_glow.feComposite(in_="glowColor", in2="offsetBlur", operator="in", result="coloredBlur")
        text_glow.feMerge(["coloredBlur", "SourceGraphic"])
        dwg.defs.add(text_glow)
        
        # Glass Panel Gradient
        glass_grad = dwg.linearGradient(start=(0, 0), end=(1, 1), id="glassGrad")
        glass_grad.add_stop_color(0, "white", opacity=0.15)
        glass_grad.add_stop_color(1, "white", opacity=0.05)
        dwg.defs.add(glass_grad)
        
        # Border Gradient
        border_grad = dwg.linearGradient(start=(0, 0), end=(1, 1), id="borderGrad")
        border_grad.add_stop_color(0, border_col, opacity=0.4)
        border_grad.add_stop_color(1, border_col, opacity=0.1)
        dwg.defs.add(border_grad)

        # --- 2. Background Base ---
        dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=16, ry=16, fill=bg_col))

        # --- 3. Neon Blobs (The "Liquid") ---
        dwg.add(dwg.circle(center=(0, 0), r=120, fill="#ff00ff", filter="url(#blobBlur)", opacity=0.6))
        dwg.add(dwg.circle(center=(width, height), r=140, fill="#00ffff", filter="url(#blobBlur)", opacity=0.5))
        dwg.add(dwg.circle(center=(width*0.8, height*0.3), r=80, fill=title_col, filter="url(#blobBlur)", opacity=0.6))
        dwg.add(dwg.circle(center=(width*0.2, height*1.1), r=100, fill="#2563eb", filter="url(#blobBlur)", opacity=0.6))

        # --- 4. The Glass Panel ---
        margin = 25
        panel_width = width - margin * 2
        panel_height = height - margin * 2
        
        dwg.add(dwg.rect(insert=(margin, margin), size=(panel_width, panel_height), rx=16, ry=16, fill="#000000", opacity=0.2))
        dwg.add(dwg.rect(insert=(margin, margin), size=(panel_width, panel_height), rx=16, ry=16, 
                         fill="url(#glassGrad)", stroke="url(#borderGrad)", stroke_width=1.5))

        # --- 5. Content ---
        dwg.add(dwg.text(title.upper(), insert=(width/2, margin + 40), fill="white", font_size=20,
                         font_family="Verdana, sans-serif", font_weight="bold", text_anchor="middle",
                         letter_spacing=4, filter="url(#textGlow)"))
        
        dwg.add(dwg.text("NEON LIQUID", insert=(width/2, margin + 60), fill=text_col, font_size=10,
                         font_family="Verdana, sans-serif", letter_spacing=2, text_anchor="middle", opacity=0.8))

        # --- 6. Contributions Grid (Bubbles) ---
        contributions_subset = contributions[-119:]  # Fit ~17 weeks
        grid_cols = 17 
        grid_rows = 7
        
        start_x = (width - grid_cols * 22) / 2 + 10
        start_y = margin + 80
        
        for i, day in enumerate(contributions_subset):
            col = i // grid_rows
            row = i % grid_rows
            
            cx = start_x + col * 22
            cy = start_y + row * 22
            
            count = day.get("count", 0)
            
            r = 6
            if count > 0:
                intensity = min(count / 10, 1)
                dwg.add(dwg.circle(center=(cx, cy), r=r, fill=title_col, opacity=0.3 + intensity * 0.5))
                dwg.add(dwg.circle(center=(cx - r * 0.3, cy - r * 0.4), r=r * 0.45, fill="#ffffff", fill_opacity=0.35))
            else:
                dwg.add(dwg.circle(center=(cx, cy), r=r, fill="#ffffff", opacity=0.1))

    elif original_theme_name == "Neural":
        # Neural/Brain visualization with contribution-based neurons
        cx = width / 2
        cy = height / 2 + 10

        contributions_subset = contributions[-80:]
        if not contributions_subset:
            return dwg.tostring()

        nodes = []

        # --- Brain core glow ---
        dwg.add(dwg.circle(center=(cx, cy), r=45, fill="#00f7ff", opacity=0.08))
        dwg.add(dwg.text("Contributions", insert=(cx, cy + 5), text_anchor="middle",
                         fill="#00f7ff", font_size="12px", font_family="Courier New", opacity=0.8))

        # --- Generate brain-shaped neuron positions ---
        for i, day in enumerate(contributions_subset):
            count = day.get("count", 0)
            side = -1 if i % 2 == 0 else 1

            # Deterministic brain ellipse
            angle = (i / max(len(contributions_subset), 1)) * math.pi
            radius_x = 90 + (i % 10) * 6
            radius_y = 60 + (i % 7) * 6
            noise = 0.9 + ((count % 5) * 0.03)

            x = cx + side * math.cos(angle) * radius_x * noise
            y = cy + math.sin(angle) * radius_y * noise

            size = 2 + min(count, 10)
            brightness = min(255, 80 + count * 18)
            color = f"rgb(0,{brightness},255)"

            dwg.add(dwg.circle(center=(x, y), r=size, fill=color, opacity=0.9))
            nodes.append((x, y, count))

        # --- Synapse connections ---
        for i in range(len(nodes)):
            x1, y1, c1 = nodes[i]
            for step in (1, 3, 7):
                j = i + step
                if j >= len(nodes):
                    continue
                x2, y2, c2 = nodes[j]
                dist = math.hypot(x2 - x1, y2 - y1)
                if dist < 140:
                    opacity = min((c1 + c2) / 20, 0.5)
                    dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), stroke="#00f7ff", stroke_width=1, opacity=opacity))

    else:
        # Default Grid (GitHub Style)
        box_size = 7
        gap = 2
        start_x = 26
        start_y = 72
        cells = _weeks_to_cells(weeks, cols, rows, max_date)
        max_count = max((cell["count"] for cell in cells if not cell["is_future"]), default=0)
        levels = _levels_from_cells(cells, max_count)
        positions = _grid_positions(cols, rows, start_x, start_y, box_size, gap)

        _add_timeline_labels(dwg, weeks, cols, rows, start_x, start_y, box_size, gap, theme)

        colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

        for idx, (x, y) in enumerate(positions):
            level = levels[idx]
            if level is None:
                continue
            fill = colors[level]
            dwg.add(dwg.rect(insert=(x, y), size=(box_size, box_size), fill=fill, rx=2, ry=2))
                
    return dwg.tostring()
