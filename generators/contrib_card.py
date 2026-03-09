import math
import svgwrite
import random
import logging
from themes.styles import THEMES
from datetime import date, datetime, timedelta
from .svg_base import CSS_ANIMATIONS

logger = logging.getLogger(__name__)


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
        # Explicit type checking and validation
        if not isinstance(item_date, str) or not item_date.strip():
            continue
        try:
            parsed = date.fromisoformat(item_date)
        except ValueError:
            logger.warning(f"Invalid date format: {item_date}")
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
def draw_contrib_card(data, theme_name="Default", custom_colors=None, date_range=None, animations_enabled=True):
    """
    Generates the Contribution Graph Card SVG.
    Supports 'Snake', 'Space', 'Marvel' visualization logic.
    
    Args:
        data: Dict containing contribution data with 'contributions' list
        theme_name: String name of the theme to use
        custom_colors: Optional dict of custom color overrides
        date_range: Optional dict with 'start' and 'end' date strings (YYYY-MM-DD)
                    to filter contributions. If None, shows all contributions.
        animations_enabled: Whether to enable CSS animations
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
    # Validate username to prevent KeyError
    username = data.get('username', 'Unknown')
    title = f"{username}'s Contributions"
    dwg.add(dwg.text(title, insert=(20, 24), 
                     fill=theme["title_color"], 
                     font_size=theme.get("title_font_size", 18), 
                     font_family=theme.get("font_family", "Arial"), 
                     font_weight="bold"))
    
    # Theme Specific Logic
    contributions = data.get("contributions", [])
    
    # Filter contributions by date range if provided
    if date_range:
        from utils.github_api import filter_contributions_by_date
        contributions = filter_contributions_by_date(contributions, date_range)
    
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
        # Marvel Infinity Stones Theme with ACTUAL contribution data
        # Each contribution cell is represented as an Infinity Stone with intensity-based glow
        
        box_size = 7
        gap = 2
        start_x = 26
        start_y = 72
        
        # Get actual contribution data
        cells = _weeks_to_cells(weeks, cols, rows, max_date)
        max_count = max((cell["count"] for cell in cells if not cell["is_future"]), default=0)
        levels = _levels_from_cells(cells, max_count)
        positions = _grid_positions(cols, rows, start_x, start_y, box_size, gap)
        
        _add_timeline_labels(dwg, weeks, cols, rows, start_x, start_y, box_size, gap, theme)
        
        # Infinity Stone colors (cycle through them for visual variety)
        stone_colors = [
            "#FFD700",  # Mind Stone (Yellow)
            "#FF0000",  # Reality Stone (Red)
            "#0099FF",  # Space Stone (Blue)
            "#9D00FF",  # Power Stone (Purple)
            "#00FF88",  # Time Stone (Green)
            "#FF6B35"   # Soul Stone (Orange)
        ]
        
        # Draw contribution grid as Infinity Stones
        for idx, (x, y) in enumerate(positions):
            level = levels[idx]
            if level is None:
                continue
            
            # Cycle through stone colors based on column for cleaner pattern
            col = idx // rows
            stone_color = stone_colors[col % len(stone_colors)]
            center_x = x + box_size // 2
            center_y = y + box_size // 2
            
            if level == 0:
                # No contributions - very subtle stone
                dwg.add(dwg.circle(center=(center_x, center_y), r=2, 
                                 fill=stone_color, opacity=0.1))
            else:
                # Contributions present - glowing stone based on intensity
                # More refined glow scaling
                glow_radius = 2.5 + (level * 1.2)
                stone_radius = 2 + (level * 0.6)
                glow_opacity = 0.15 + (level * 0.12)
                stone_opacity = 0.65 + (level * 0.08)
                
                # Outer glow
                dwg.add(dwg.circle(center=(center_x, center_y), r=glow_radius, 
                                 fill=stone_color, opacity=glow_opacity))
                
                # Inner stone with subtle border
                dwg.add(dwg.circle(center=(center_x, center_y), r=stone_radius, 
                                 fill=stone_color, opacity=stone_opacity, 
                                 stroke="white", stroke_width=0.2))
                
                # Extra glow for highest activity (level 4) - more subtle
                if level == 4:
                    dwg.add(dwg.circle(center=(center_x, center_y), r=glow_radius + 1.5, 
                                     fill=stone_color, opacity=0.1))
        
        # Subtle legend at bottom
        legend_y = height - 15
        legend_start_x = 30
        
        dwg.add(dwg.text("Less", insert=(legend_start_x, legend_y), 
                        fill=theme["text_color"], font_size=9, 
                        font_family=theme["font_family"], opacity=0.6))
        
        # Legend stones
        for i in range(5):
            lx = legend_start_x + 30 + (i * 12)
            level_opacity = 0.1 + (i * 0.2)
            level_size = 2 + (i * 0.5)
            dwg.add(dwg.circle(center=(lx, legend_y - 3), r=level_size, 
                             fill=stone_colors[0], opacity=level_opacity))
        
        dwg.add(dwg.text("More", insert=(legend_start_x + 90, legend_y), 
                        fill=theme["text_color"], font_size=9, 
                        font_family=theme["font_family"], opacity=0.6))

    elif original_theme_name == "Stranger_things":
        # Upside Down with demogorgon
        # Floating particles
        random.seed(42)
        for i in range(15):
            x = random.randint(20, width-20)
            y = random.randint(40, height-20)
            r = random.randint(1, 2)
            dwg.add(dwg.circle(center=(x, y), r=r, fill="#ffffff", opacity=0.3))
        
        # Contribution grid with red glow using ACTUAL GitHub data
        box_size = 7
        gap = 2
        start_x = 26
        start_y = 72
        
        cells = _weeks_to_cells(weeks, cols, rows, max_date)
        max_count = max((cell["count"] for cell in cells if not cell["is_future"]), default=0)
        levels = _levels_from_cells(cells, max_count)
        positions = _grid_positions(cols, rows, start_x, start_y, box_size, gap)

        _add_timeline_labels(dwg, weeks, cols, rows, start_x, start_y, box_size, gap, theme)
        
        # Red-tinted colors for Stranger Things theme
        colors = ["#1a1a1a", "#8b0000", "#b22222", "#dc143c", "#ff0000"]
        
        for idx, (x, y) in enumerate(positions):
            level = levels[idx]
            if level is None:
                continue
            fill = colors[level]
            
            dwg.add(dwg.rect(insert=(x, y), size=(box_size, box_size), fill=fill, rx=1, opacity=0.7))
            
            if level == 4:  # High activity - add glow
                dwg.add(dwg.rect(insert=(x-1, y-1), size=(box_size+2, box_size+2), 
                               fill="none", stroke="#ff0000", stroke_width=0.5, opacity=0.4))
        
        # Mini demogorgon silhouette
        demo_x = width - 50
        demo_y = height - 50
        dwg.add(dwg.circle(center=(demo_x, demo_y), r=15, fill="#330000", opacity=0.6))
        
        # Petals
        for angle in range(0, 360, 60):
            rad = math.radians(angle)
            x1 = demo_x + 12 * math.cos(rad)
            y1 = demo_y + 12 * math.sin(rad)
            x2 = demo_x + 20 * math.cos(rad)
            y2 = demo_y + 20 * math.sin(rad)
            dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), stroke="#ff0000", stroke_width=1.5, opacity=0.5))
    elif theme_name == "Pacman":
        # Pac-Man arcade theme with ACTUAL GitHub contribution data
        # Maze grid lines
        for i in range(0, width, 25):
            dwg.add(dwg.line(start=(i, 50), end=(i, height-10), stroke="#1919a6", stroke_width=0.5, opacity=0.3))
        
        # Get actual contribution data
        box_size = 7
        gap = 2
        start_x = 26
        start_y = 72
        
        cells = _weeks_to_cells(weeks, cols, rows, max_date)
        max_count = max((cell["count"] for cell in cells if not cell["is_future"]), default=0)
        levels = _levels_from_cells(cells, max_count)
        positions = _grid_positions(cols, rows, start_x, start_y, box_size, gap)
        
        _add_timeline_labels(dwg, weeks, cols, rows, start_x, start_y, box_size, gap, theme)
        
        # Draw pellets based on actual contribution levels
        for idx, (x, y) in enumerate(positions):
            level = levels[idx]
            if level is None:
                continue
            
            center_x = x + box_size // 2
            center_y = y + box_size // 2
            
            if level == 0:
                # Empty space - small dot
                dwg.add(dwg.circle(center=(center_x, center_y), r=1.5, fill="#333333"))
            elif level >= 4:
                # Power pellet (high activity)
                dwg.add(dwg.circle(center=(center_x, center_y), r=4, fill="#ffb8ae"))
                # Pulsing effect
                dwg.add(dwg.circle(center=(center_x, center_y), r=5, fill="none", 
                                 stroke="#ffb8ae", stroke_width=1, opacity=0.5))
            else:
                # Regular pellet - color based on level
                colors = ["#4169e1", "#ff8c00", "#ffff00"]  # Blue, Orange, Yellow
                dwg.add(dwg.circle(center=(center_x, center_y), r=3, fill=colors[level-1]))
        
        # Pac-Man character
        pacman_x = 15
        pacman_y = 75
        pacman_path = dwg.path(d=f"M {pacman_x} {pacman_y} " +
                              f"L {pacman_x + 10} {pacman_y - 8} " +
                              f"A 10 10 0 1 1 {pacman_x + 10} {pacman_y + 8} Z",
                              fill="#ffff00")
        dwg.add(pacman_path)
        
        # Score display using actual commits
        dwg.add(dwg.text(f"SCORE: {data.get('total_commits', '0')}", 
                        insert=(width-120, 35), 
                        fill="#ffff00", 
                        font_family="Courier New", 
                        font_size=12, 
                        font_weight="bold"))
        
    elif theme_name == "Cyberpunk":
        # Cyberpunk theme with neon grid and ACTUAL GitHub contribution data
        # Neon grid background
        for i in range(0, width, 20):
            dwg.add(dwg.line(start=(i, 0), end=(i, height), stroke="#1a1a2e", stroke_width=0.3, opacity=0.5))
        for i in range(0, height, 20):
            dwg.add(dwg.line(start=(0, i), end=(width, i), stroke="#1a1a2e", stroke_width=0.3, opacity=0.5))
        
        # Get actual contribution data
        box_size = 7
        gap = 2
        start_x = 26
        start_y = 72
        
        cells = _weeks_to_cells(weeks, cols, rows, max_date)
        max_count = max((cell["count"] for cell in cells if not cell["is_future"]), default=0)
        levels = _levels_from_cells(cells, max_count)
        positions = _grid_positions(cols, rows, start_x, start_y, box_size, gap)
        
        _add_timeline_labels(dwg, weeks, cols, rows, start_x, start_y, box_size, gap, theme)
        
        # Neon blocks based on actual contribution levels
        neon_colors = ["#1a1a2e", "#00ffff", "#00ff41", "#ff00ff", "#ff0080"]
        
        for idx, (x, y) in enumerate(positions):
            level = levels[idx]
            if level is None:
                continue
            
            fill_color = neon_colors[level]
            
            if level == 0:
                dwg.add(dwg.rect(insert=(x, y), size=(box_size, box_size), fill=fill_color, rx=1, opacity=0.5))
            else:
                dwg.add(dwg.rect(insert=(x, y), size=(box_size, box_size), fill=fill_color, rx=1, opacity=0.7))
                
                if level >= 3:  # Glow effect for high activity
                    dwg.add(dwg.rect(insert=(x-1, y-1), size=(box_size+2, box_size+2), 
                                   fill="none", stroke=fill_color, stroke_width=1, rx=2, opacity=0.3))
        
        # Scan line effect
        scan_y = 90
        dwg.add(dwg.line(start=(0, scan_y), end=(width, scan_y), stroke="#00ff41", stroke_width=1.5, opacity=0.2))
    elif theme_name == "Cricket":
        # Cricket stadium theme
        # Stadium lights
        for i in range(3):
            light_x = 80 + i * 150
            light_y = 45
            dwg.add(dwg.circle(center=(light_x, light_y), r=4, fill="#ffeb3b", opacity=0.8))
            dwg.add(dwg.circle(center=(light_x, light_y), r=7, fill="#ffeb3b", opacity=0.3))
        
        # Cricket field boundary
        field_center_x = width // 2
        field_center_y = height // 2 + 20
        dwg.add(dwg.ellipse(center=(field_center_x, field_center_y), r=(200, 50), 
                           fill="none", stroke="#ffffff", stroke_width=2, 
                           stroke_dasharray="5,5", opacity=0.4))
        
        # Contribution boxes as runs - using ACTUAL GitHub data
        box_size = 7
        gap = 2
        start_x = 26
        start_y = 72
        
        # Get actual contribution data
        cells = _weeks_to_cells(weeks, cols, rows, max_date)
        max_count = max((cell["count"] for cell in cells if not cell["is_future"]), default=0)
        levels = _levels_from_cells(cells, max_count)
        positions = _grid_positions(cols, rows, start_x, start_y, box_size, gap)
        
        # Add timeline labels
        _add_timeline_labels(dwg, weeks, cols, rows, start_x, start_y, box_size, gap, theme)
        
        # Draw contribution grid with cricket scoring
        for idx, (x, y) in enumerate(positions):
            level = levels[idx]
            if level is None:
                continue
                
            if level == 0:
                # Duck (out) - no contributions
                dwg.add(dwg.rect(insert=(x, y), size=(box_size, box_size), 
                               fill="#8b4513", rx=1, opacity=0.3))
            else:
                # Runs: 1, 2, 4, 6 based on contribution levels
                colors = ["#90ee90", "#7fbf7f", "#ffd700", "#ff6b35"]
                scores = ["1", "2", "4", "6"]
                fill_color = colors[min(level-1, 3)]
                score = scores[min(level-1, 3)]
                
                dwg.add(dwg.rect(insert=(x, y), size=(box_size, box_size), 
                               fill=fill_color, rx=1, opacity=0.8))
                
                # Score number
                dwg.add(dwg.text(score, insert=(x + box_size//2, y + box_size//2 + 2), 
                               font_size="6px", fill="#000000", text_anchor="middle", 
                               font_weight="bold", opacity=0.6))
                
                # Glow for sixes (highest contribution level)
                if level == 4:
                    dwg.add(dwg.rect(insert=(x-1, y-1), size=(box_size+2, box_size+2), 
                                   fill="none", stroke="#ff6b35", stroke_width=1, 
                                   rx=2, opacity=0.5))
        
        # Cricket bat
        bat_x = width - 60
        bat_y = height - 50
        dwg.add(dwg.rect(insert=(bat_x, bat_y - 25), size=(4, 25), fill="#8b4513", rx=1))
        dwg.add(dwg.rect(insert=(bat_x - 6, bat_y), size=(16, 35), fill="#d2691e", rx=2))
        
        # Cricket ball
        ball_x = bat_x + 30
        ball_y = bat_y + 15
        dwg.add(dwg.circle(center=(ball_x, ball_y), r=5, fill="#cc0000"))
        
        # Wickets
        wicket_x = 25
        wicket_y = height - 40
        for i in range(3):
            dwg.add(dwg.rect(insert=(wicket_x + i * 4, wicket_y), size=(2, 25), fill="#f5deb3"))
        dwg.add(dwg.rect(insert=(wicket_x - 1, wicket_y - 2), size=(11, 2), fill="#8b4513", rx=1))
        
        # Scoreboard will show actual total commits
        total_commits = data.get('total_commits', 0)
        dwg.add(dwg.text(f"RUNS: {total_commits}", insert=(width - 110, 30), 
                        font_size="12px", font_family="monospace", fill="#00ff00", 
                        font_weight="bold"))
    
    elif theme_name == "Ocean":
        # Ocean underwater theme with fish representing contributions
        # Background waves at top
        wave_path = "M0,45 Q60,35 120,45 T240,45 T360,45 T480,45 T500,45 L500,0 L0,0 Z"
        dwg.add(dwg.path(d=wave_path, fill=theme.get("border_color", "#004466"), opacity=0.5))
        
        # Coral reefs at bottom
        coral_y = height - 25
        dwg.add(dwg.path(d=f"M50,{coral_y} Q70,{coral_y-15} 90,{coral_y} Q110,{coral_y-12} 130,{coral_y} Z", 
                        fill="#8B4513", opacity=0.6))
        dwg.add(dwg.path(d=f"M200,{coral_y} Q220,{coral_y-18} 240,{coral_y} Q260,{coral_y-14} 280,{coral_y} Z", 
                        fill="#A0522D", opacity=0.6))
        dwg.add(dwg.path(d=f"M350,{coral_y} Q370,{coral_y-16} 390,{coral_y} Q410,{coral_y-13} 430,{coral_y} Z", 
                        fill="#8B4513", opacity=0.6))
        
        # Bubbles floating up
        for i in range(8):
            bubble_x = 40 + i * 60
            bubble_y = 55 + (i % 3) * 12
            dwg.add(dwg.circle(center=(bubble_x, bubble_y), r=2, fill="#66ddaa", opacity=0.4))
            dwg.add(dwg.circle(center=(bubble_x, bubble_y), r=3, fill="none", stroke="#66ddaa", 
                             stroke_width=0.5, opacity=0.3))
        
        # Contribution grid as fish
        box_size = 6
        gap = 3
        start_x = 26
        start_y = 70
        cells = _weeks_to_cells(weeks, cols, rows, max_date)
        max_count = max((cell["count"] for cell in cells if not cell["is_future"]), default=0)
        positions = _grid_positions(cols, rows, start_x, start_y, box_size, gap)
        
        # Add timeline labels
        _add_timeline_labels(dwg, weeks, cols, rows, start_x, start_y, box_size, gap, theme)
        
        # Draw fish based on contribution intensity
        for idx, (x, y) in enumerate(positions):
            cell = cells[idx] if idx < len(cells) else None
            if not cell or cell.get("is_future"):
                continue

            count = cell.get("count", 0)
            if count <= 0:
                # Empty cell - small bubble
                dwg.add(dwg.circle(center=(x + 3, y + 3), r=1.4, 
                                 fill=theme.get("text_color", "#66ddaa"), opacity=0.5))
                continue

            # Fish size based on contribution intensity
            intensity = 0 if max_count == 0 else count / max_count
            fish_w = 8 + int(6 * intensity)
            fish_h = 4 + int(4 * intensity)
            
            # Fish colors based on intensity
            if intensity < 0.25:
                fish_color = "#5599cc"
            elif intensity < 0.5:
                fish_color = "#4488bb"
            elif intensity < 0.75:
                fish_color = "#2277aa"
            else:
                fish_color = "#0066aa"

            # Fish body (triangle)
            body = f"M{x},{y} L{x + fish_w},{y - fish_h} L{x + fish_w},{y + fish_h} Z"
            dwg.add(dwg.path(d=body, fill=fish_color, opacity=0.9))
            
            # Add fin for high activity fish
            if intensity > 0.6:
                fin = f"M{x + fish_w // 2},{y} L{x + fish_w - 2},{y - 3} L{x + fish_w - 2},{y + 3} Z"
                dwg.add(dwg.path(d=fin, fill=fish_color, opacity=0.9))
                
                # Eye dot for biggest fish
                if intensity > 0.8:
                    dwg.add(dwg.circle(center=(x + fish_w - 3, y), r=0.7, fill="#ffffff", opacity=0.8))
    
    elif original_theme_name == "Glass":
        # Neon Liquid Glassmorphism Theme (from main branch)
        
        # Theme Variables
        bg_col = theme.get("bg_color", "#050511")
        title_col = theme.get("title_color", "#00e5ff")
        text_col = theme.get("text_color", "#e0e0e0")
        border_col = theme.get("border_color", "white")

        # Basic stats to make the card feel more like a dashboard
        total_commits = data.get("total_commits", sum(d.get("count", 0) for d in contributions))
        active_days = sum(1 for d in contributions if d.get("count", 0) > 0)
        
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

        # Attach shared CSS animations for a more interactive feel
        if animations_enabled:
            dwg.defs.add(dwg.style(CSS_ANIMATIONS))

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
        
        dwg.add(dwg.rect(insert=(margin, margin), size=(panel_width, panel_height), rx=16, ry=16, fill="#000000", opacity=0.3))
        panel_rect = dwg.rect(
            insert=(margin, margin),
            size=(panel_width, panel_height),
            rx=16,
            ry=16,
            fill="url(#glassGrad)",
            stroke="url(#borderGrad)",
            stroke_width=1.2,
        )
        if animations_enabled:
            panel_rect["class"] = "anim-border-pulse"
        dwg.add(panel_rect)
        
        # More subtle Top Reflection
        reflection_grad = dwg.linearGradient(start=(0, 0), end=(0, 1), id="reflGrad")
        reflection_grad.add_stop_color(0, "white", opacity=0.08)
        reflection_grad.add_stop_color(1, "white", opacity=0)
        dwg.defs.add(reflection_grad)
        dwg.add(dwg.rect(insert=(margin + 4, margin + 4), size=(panel_width - 8, panel_height / 4), rx=12, ry=12, fill="url(#reflGrad)"))

        # --- 5. Content ---
        # More elegant typography
        base_title_size = 18
        name_len = len(title)
        
        # Scale font size more gracefully
        if name_len > 20:
            dynamic_font_size = max(11, base_title_size - (name_len - 20) // 1.5)
        else:
            dynamic_font_size = base_title_size

        # Use a more modern looking font stack and thinner weight for elegance
        title_text = dwg.text(
            title.upper(),
            insert=(width / 2, margin + 38),
            fill="white",
            font_size=dynamic_font_size,
            font_family="'Inter', system-ui, sans-serif",
            font_weight="800",
            text_anchor="middle",
            letter_spacing=2,
            filter="url(#textGlow)",
        )
        if animations_enabled:
            title_text["class"] = "anim-fade-in"
        dwg.add(title_text)
        
        subtitle = dwg.text(
            "GEOM-LIQUID INTERFACE",
            insert=(width / 2, margin + 55),
            fill=text_col,
            font_size=8,
            font_family="'Inter', sans-serif",
            letter_spacing=4,
            text_anchor="middle",
            opacity=0.6,
        )
        if animations_enabled:
            subtitle["class"] = "anim-slide-up"
        dwg.add(subtitle)

        # --- 6. Contributions Grid (Bubbles) - kept inside surrounding box ---
        contributions_subset = contributions[-119:]  # Fit 17 cols x 7 rows
        grid_cols = 17
        grid_rows = 7
        
        # Panel content area: below subtitle, with comfortable padding from panel edges
        grid_area_top = margin + 60
        grid_area_bottom = height - margin - 20
        grid_area_height = grid_area_bottom - grid_area_top
        # Size grid so 7 rows fit inside panel; circles stay in surrounding box
        step_y = grid_area_height / grid_rows
        step_x = (panel_width - 30) / (grid_cols - 1)  # 15px margin each side
        step_x = min(step_x, 26)
        cell_size = min(step_x, step_y) * 0.8
        radius = max(2, min(cell_size / 2, 5))
        # Center grid in panel
        grid_total_width = (grid_cols - 1) * step_x
        grid_total_height = (grid_rows - 1) * step_y
        start_x = margin + (panel_width - grid_total_width) / 2
        start_y = grid_area_top + (grid_area_height - grid_total_height) / 2
        
        # Clip path so contribution circles stay inside the glass panel
        clip_id = "glassPanelClip"
        clip = dwg.defs.add(dwg.clipPath(id=clip_id))
        clip.add(dwg.rect(insert=(margin, margin), size=(panel_width, panel_height), rx=16, ry=16))
        grid_group = dwg.g(clip_path=f"url(#{clip_id})")
        
        for i, day in enumerate(contributions_subset):
            col = i // grid_rows
            row = i % grid_rows
            
            cx = start_x + col * step_x
            cy = start_y + row * step_y
            
            count = day.get("count", 0)
            
            r = radius
            if count > 0:
                intensity = min(count / 10, 1)
                bubble = dwg.circle(
                    center=(cx, cy),
                    r=r,
                    fill=title_col,
                    opacity=0.4 + intensity * 0.5,
                )
                highlight = dwg.circle(
                    center=(cx - r * 0.3, cy - r * 0.4),
                    r=r * 0.4,
                    fill="#ffffff",
                    opacity=0.5,
                )

                if animations_enabled:
                    classes = ["anim-bubble"]
                    if intensity >= 0.7:
                        classes.append("anim-pulse-glow")
                    delay = 0.02 * col + 0.01 * row
                    bubble["class"] = " ".join(classes)
                    bubble["style"] = f"animation-delay: {delay:.2f}s"
                    highlight["class"] = " ".join(classes)
                    highlight["style"] = f"animation-delay: {delay:.2f}s"

                grid_group.add(bubble)
                grid_group.add(highlight)
            else:
                bubble = dwg.circle(
                    center=(cx, cy),
                    r=r,
                    fill="#ffffff",
                    opacity=0.12,
                )
                if animations_enabled:
                    delay = 0.02 * col + 0.01 * row
                    bubble["class"] = "anim-bubble"
                    bubble["style"] = f"animation-delay: {delay:.2f}s"
                grid_group.add(bubble)
        
        dwg.add(grid_group)
    elif original_theme_name == "Neural":
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

            # Organic brain ellipse (deterministic)
            angle = (i / max(len(contributions), 1)) * math.pi
            radius_x = 90 + (i % 10) * 6
            radius_y = 60 + (i % 7) * 6

            # Distortion noise derived from count
            noise = 0.9 + ((count % 5) * 0.03)

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

            for step in (1, 3, 7):
                j = i + step
                if j >= len(nodes):
                    continue

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
    elif original_theme_name == "Matrix":
        import random
        from themes import matrix

        svg = matrix.render(data, theme)
        return svg
    
    else:
        # Default Grid (Github Style)
        # Just simple squares
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

