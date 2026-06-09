"""
Contribution card SVG generator with support for multiple visual themes.

This module provides a central entry point for generating contribution cards
with different visual themes. Theme-specific rendering logic is delegated to
dedicated functions in the themes module.
"""
import logging
import svgwrite
from datetime import date, datetime, timedelta, timezone
from .svg_base import create_svg_base, CSS_ANIMATIONS, draw_card_background
from themes.styles import THEMES
from generators.themes import THEME_DISPATCHER, render_default_theme

logger = logging.getLogger(__name__)


def _latest_contribution_date(contributions):
    max_date = None
    for item in contributions:
        item_date = item.get("date") if item else None
        if not item_date:
            continue
        try:
            parsed = date.fromisoformat(item_date)
        except (TypeError, ValueError):
            continue
        if not max_date or parsed > max_date:
            max_date = parsed

    today = datetime.now(timezone.utc).date()
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
    """Resolve contribution weeks, preferring provided data over computed."""
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
                except (TypeError, ValueError):
                    parsed = None
            is_future = bool(max_date and parsed and parsed > max_date)
            cells.append({
                "date": item_date,
                "count": day.get("count", 0),
                "is_future": is_future
            })
    return cells


def _normalize_heatmap_contributions(contributions, date_range=None):
    normalized = contributions or []

    if date_range:
        try:
            from utils.github_api import filter_contributions_by_date
            normalized = filter_contributions_by_date(normalized, date_range)
        except Exception:
            pass

    parsed = []
    for item in normalized:
        if not isinstance(item, dict):
            continue

        item_date = item.get("date")
        if not isinstance(item_date, str) or not item_date.strip():
            continue

        try:
            parsed_date = date.fromisoformat(item_date)
        except Exception:
            continue

        count = item.get("count", 0)
        try:
            count = int(count)
        except Exception:
            count = 0

        parsed.append({"date": parsed_date, "count": max(0, count)})

    parsed.sort(key=lambda item: item["date"])
    return parsed


def _is_dark_theme_color(color_value):
    if not isinstance(color_value, str):
        return True

    color_value = color_value.lstrip("#")
    if len(color_value) != 6:
        return True

    try:
        red = int(color_value[0:2], 16)
        green = int(color_value[2:4], 16)
        blue = int(color_value[4:6], 16)
    except ValueError:
        return True

    luminance = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255
    return luminance < 0.5


def _hex_to_rgb(color_value):
    color_value = (color_value or "#000000").lstrip("#")
    if len(color_value) != 6:
        return 0, 0, 0
    try:
        return int(color_value[0:2], 16), int(color_value[2:4], 16), int(color_value[4:6], 16)
    except ValueError:
        return 0, 0, 0


def _rgb_to_hex(red, green, blue):
    return f"#{max(0, min(255, red)):02x}{max(0, min(255, green)):02x}{max(0, min(255, blue)):02x}"


def _mix_colors(base_color, target_color, ratio):
    base_red, base_green, base_blue = _hex_to_rgb(base_color)
    target_red, target_green, target_blue = _hex_to_rgb(target_color)
    return _rgb_to_hex(
        round(base_red + (target_red - base_red) * ratio),
        round(base_green + (target_green - base_green) * ratio),
        round(base_blue + (target_blue - base_blue) * ratio),
    )


def _palette_from_theme(theme_name, theme):
    title_color = theme.get("title_color", "#58a6ff")
    border_color = theme.get("border_color", "#30363d")

    palette_map = {
        "Default": ["#0d1117", "#0c2b26", "#0f4f39", "#176f4c", "#25a067"],
        "Gaming": ["#0d0d0d", "#083808", "#0f5f0f", "#178d17", "#39c939"],
        "Marvel": ["#1a1a1a", "#3d1a25", "#742238", "#b2414b", "#d86a3f"],
        "Space": ["#0b0c1f", "#201d54", "#372f8d", "#5a4ddb", "#8a72ff"],
        "Dracula": ["#282a36", "#40245f", "#6538b8", "#9561f1", "#c47df7"],
        "Neural": ["#0a0f14", "#0b3366", "#114e9f", "#2a78da", "#63b7ff"],
        "Pacman": ["#000000", "#132f8a", "#6b5b00", "#c9a300", "#ffe766"],
        "Cyberpunk": ["#0a0e27", "#004a8c", "#0074c8", "#8e2ae6", "#d957b4"],
        "Ocean": ["#001122", "#003b55", "#00658a", "#0090c7", "#4dbfa8"],
        "Retro": ["#f5f0e1", "#d8c9ad", "#ba9f76", "#947658", "#6c563f"],
    }

    if theme_name in palette_map:
        return palette_map[theme_name]

    if theme_name == "Neural" or title_color.lower() == "#00e5ff":
        return ["#0a0f14", "#0b3366", "#114e9f", "#2a78da", "#63b7ff"]

    if theme_name == "Space" or title_color.lower() == "#a371f7":
        return ["#0b0c1f", "#201d54", "#372f8d", "#5a4ddb", "#8a72ff"]

    if theme_name == "Dracula" or border_color.lower() == "#bd93f9":
        return ["#282a36", "#40245f", "#6538b8", "#9561f1", "#c47df7"]

    if theme_name == "Cyberpunk":
        return ["#0a0e27", "#004a8c", "#0074c8", "#8e2ae6", "#d957b4"]

    if theme_name == "Gaming":
        return ["#0d0d0d", "#083808", "#0f5f0f", "#178d17", "#39c939"]

    # Generic fallback: build a ramp from the active title color.
    base = border_color if _is_dark_theme_color(border_color) else theme.get("bg_color", "#0d1117")
    return [
        base,
        _mix_colors(base, title_color, 0.28),
        _mix_colors(base, title_color, 0.52),
        _mix_colors(base, title_color, 0.74),
        _mix_colors(base, title_color, 1.0),
    ]


def _heatmap_level_for_count(count, max_count, intensity_mode):
    if count <= 0 or max_count <= 0:
        return 0

    if intensity_mode == "none":
        return 1
    if intensity_mode == "low":
        return 1 if count > 0 else 0
    if intensity_mode == "medium":
        return 1 if count <= max_count * 0.5 else 2
    if intensity_mode == "high":
        ratio = count / max_count
        if ratio <= 0.25:
            return 1
        if ratio <= 0.5:
            return 2
        if ratio <= 0.75:
            return 3
        return 4

    ratio = count / max_count
    if ratio <= 0.25:
        return 1
    if ratio <= 0.5:
        return 2
    if ratio <= 0.75:
        return 3
    return 4


def draw_calendar_heatmap_card(
    data,
    theme_name="Default",
    custom_colors=None,
    date_range=None,
    intensity_mode="auto",
    intensity_colors=None,
    period_label="Last Year",
    animations_enabled=False,
):
    theme = THEMES.get(theme_name, THEMES["Default"]).copy()
    if custom_colors:
        theme.update(custom_colors)

    username = data.get("username", "Unknown")
    contributions = _normalize_heatmap_contributions(data.get("contributions", []), date_range=date_range)
    max_date = _latest_contribution_date(data.get("contributions", [])) or datetime.now(timezone.utc).date()

    if date_range:
        try:
            start_date = date.fromisoformat(date_range.get("start"))
            end_date = date.fromisoformat(date_range.get("end"))
        except Exception:
            end_date = max_date
            start_date = end_date - timedelta(days=370)
    elif period_label == "Current Year":
        end_date = max_date
        start_date = date(end_date.year, 1, 1)
    else:
        end_date = max_date
        start_date = end_date - timedelta(days=370)

    count_by_date = {item["date"]: item["count"] for item in contributions}
    selected_counts = [count for item_date, count in count_by_date.items() if start_date <= item_date <= end_date]
    max_count = max(selected_counts, default=0)

    default_palette = _palette_from_theme(theme_name, theme)
    palette = []
    for index in range(5):
        key = f"level_{index}"
        color_value = None
        if intensity_colors:
            color_value = intensity_colors.get(key)
            if not color_value:
                color_value = intensity_colors.get(f"heatmap_{key}")
        palette.append(color_value or default_palette[index])

    empty_cell_color = theme.get("bg_color", "#0d1117")
    empty_cell_color = "#161b22" if _is_dark_theme_color(empty_cell_color) else "#ebedf0"
    future_outline = theme.get("border_color", "#30363d")
    width = 735
    height = 182
    cell_size = 10
    gap = 2
    start_x = 70
    start_y = 46

    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
    draw_card_background(dwg, width, height, theme)

    title = f"{username}'s Contribution Calendar"
    dwg.add(dwg.text(
        title,
        insert=(20, 24),
        fill=theme["title_color"],
        font_size=theme.get("title_font_size", 16),
        font_family=theme.get("font_family", "Arial"),
        font_weight="bold",
    ))
    summary_text = f"{sum(selected_counts)} contributions in the last year"

    grid_start = start_date - timedelta(days=(start_date.weekday() + 1) % 7)

    month_seen = set()
    month_label_y = start_y - 6
    for col in range(53):
        week_start = grid_start + timedelta(days=col * 7)
        label_date = week_start
        month_key = (label_date.year, label_date.month)
        if label_date.day <= 7 and month_key not in month_seen:
            month_seen.add(month_key)
            dwg.add(dwg.text(
                label_date.strftime("%b"),
                insert=(start_x + col * (cell_size + gap) - 2, month_label_y),
                fill=theme["text_color"],
                font_size=9,
                font_family=theme.get("font_family", "Arial"),
                opacity=0.7,
            ))

    day_labels = [(1, "Mon"), (3, "Wed"), (5, "Fri")]
    for row, label in day_labels:
        dwg.add(dwg.text(
            label,
            insert=(18, start_y + row * (cell_size + gap) + 8),
            fill=theme["text_color"],
            font_size=9,
            font_family=theme.get("font_family", "Arial"),
            opacity=0.7,
        ))

    for col in range(53):
        week_start = grid_start + timedelta(days=col * 7)
        for row in range(7):
            current_day = week_start + timedelta(days=row)
            x = start_x + col * (cell_size + gap)
            y = start_y + row * (cell_size + gap)

            if current_day > end_date or current_day > max_date:
                dwg.add(dwg.rect(
                    insert=(x, y),
                    size=(cell_size, cell_size),
                    fill="none",
                    stroke=future_outline,
                    stroke_width=0.8,
                    opacity=0.25,
                    rx=2,
                    ry=2,
                ))
                continue

            count = count_by_date.get(current_day, 0)
            level = _heatmap_level_for_count(count, max_count, intensity_mode)
            fill = palette[level]

            if count <= 0:
                dwg.add(dwg.rect(
                    insert=(x, y),
                    size=(cell_size, cell_size),
                    fill=empty_cell_color,
                    opacity=0.95,
                    rx=2,
                    ry=2,
                ))
            else:
                dwg.add(dwg.rect(
                    insert=(x, y),
                    size=(cell_size, cell_size),
                    fill=fill,
                    rx=2,
                    ry=2,
                ))

    footer_y = start_y + (7 * (cell_size + gap) - gap) + 18
    dwg.add(dwg.text(
        summary_text,
        insert=(20, footer_y),
        fill=theme["text_color"],
        font_size=10,
        font_family=theme.get("font_family", "Arial"),
        opacity=0.78,
    ))

    legend_y = footer_y
    legend_x = 520
    dwg.add(dwg.text(
        "Less",
        insert=(legend_x, legend_y),
        fill=theme["text_color"],
        font_size=9,
        font_family=theme.get("font_family", "Arial"),
        opacity=0.75,
    ))

    for index, color_value in enumerate(palette):
        dwg.add(dwg.rect(
            insert=(legend_x + 26 + index * 14, legend_y - 9),
            size=(10, 10),
            fill=color_value,
            rx=2,
            ry=2,
        ))

    dwg.add(dwg.text(
        "More",
        insert=(legend_x + 26 + 5 * 14 + 4, legend_y),
        fill=theme["text_color"],
        font_size=9,
        font_family=theme.get("font_family", "Arial"),
        opacity=0.75,
    ))

    return dwg.tostring()


def _add_timeline_labels(dwg, weeks, cols, rows, start_x, start_y, box_size, gap, theme):
    last_month = None
    max_label_x = start_x + (cols - 1) * (box_size + gap)

    for col, week in enumerate(weeks):
        day = week[0] if week else None
        day_date = None
        if day and day.get("date"):
            try:
                day_date = date.fromisoformat(day["date"])
            except (TypeError, ValueError):
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
def draw_calendar_heatmap_card_legacy(
    data,
    theme_name="Default",
    custom_colors=None,
    date_range=None,
    animations_enabled=True,
    level_control="auto",
    level_colors=None
):
    """
    Generates an enhanced yearly Calendar Heatmap Card (365 days).

    level_control: "none" | "low" | "medium" | "high" | "auto"
    level_colors:  dict {0..4: color} or list of 5 colors
    """
    theme = THEMES.get(theme_name, THEMES["Default"]).copy()
    if custom_colors:
        theme.update(custom_colors)

    # ── Layout constants ────────────────────────────────────────────────────
    CELL      = 11   # cell size (px)
    GAP       = 2    # gap between cells
    STEP      = CELL + GAP
    COLS      = 53   # weeks
    ROWS      = 7    # days per week
    PAD_LEFT  = 32   # room for Mon/Wed/Fri labels
    PAD_TOP   = 52   # room for title + month labels
    PAD_BOT   = 28   # room for legend
    PAD_RIGHT = 16

    grid_w = COLS * STEP - GAP
    grid_h = ROWS * STEP - GAP
    width  = PAD_LEFT + grid_w + PAD_RIGHT
    height = PAD_TOP  + grid_h + PAD_BOT

    GRID_X = PAD_LEFT
    GRID_Y = PAD_TOP

    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")

    # Background
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=10, ry=10,
                     fill=theme["bg_color"], stroke=theme["border_color"], stroke_width=1.5))

    # Title
    username = data.get("username", "Unknown")
    total_commits = data.get("total_commits", 0)
    dwg.add(dwg.text(
        f"{username}'s Contribution Calendar",
        insert=(PAD_LEFT, 22),
        fill=theme["title_color"],
        font_size=13,
        font_family=theme.get("font_family", "Arial"),
        font_weight="bold"
    ))
    dwg.add(dwg.text(
        f"{total_commits:,} contributions in the last year",
        insert=(PAD_LEFT, 36),
        fill=theme["text_color"],
        font_size=9,
        font_family=theme.get("font_family", "Arial"),
        opacity=0.7
    ))

    # ── Contribution data ────────────────────────────────────────────────────
    contributions = data.get("contributions", [])
    if date_range:
        from utils.github_api import filter_contributions_by_date
        contributions = filter_contributions_by_date(contributions, date_range)

    date_counts = {}
    for item in contributions:
        d = item.get("date")
        if not isinstance(d, str) or not d.strip():
            continue
        try:
            date_counts[date.fromisoformat(d)] = item.get("count", 0)
        except ValueError:
            continue

    today = datetime.now(timezone.utc).date()

    if date_range and date_range.get("start"):
        try:
            start_date = date.fromisoformat(date_range["start"])
        except Exception:
            start_date = today - timedelta(days=364)
    else:
        start_date = today - timedelta(days=364)

    # Align start_date to the Sunday of its week (GitHub style)
    start_date -= timedelta(days=(start_date.weekday() + 1) % 7)
    end_date = start_date + timedelta(days=COLS * 7 - 1)

    max_count = max(date_counts.values(), default=1) or 1

    # ── Color palette ────────────────────────────────────────────────────────
    bg = theme["bg_color"]
    is_light_bg = bg.startswith("#f") or bg.startswith("#e") or bg in ("#ffffff", "#fff")
    default_empty = "#ebedf0" if is_light_bg else "#161b22"
    default_palette = [
        default_empty,
        "#0e4429", "#006d32", "#26a641", "#39d353"
    ]

    colors = {}
    if level_colors:
        if isinstance(level_colors, dict):
            colors = {int(k): v for k, v in level_colors.items()}
        elif isinstance(level_colors, (list, tuple)) and len(level_colors) >= 5:
            colors = {i: level_colors[i] for i in range(5)}
    if not colors:
        colors = {i: default_palette[i] for i in range(5)}

    if level_control == "none":
        colors = {i: colors[0] for i in range(5)}
    elif level_control == "low":
        colors = {0: colors[0], 1: colors[4], 2: colors[4], 3: colors[4], 4: colors[4]}
    elif level_control == "medium":
        colors = {0: colors[0], 1: colors[0], 2: colors[2], 3: colors[4], 4: colors[4]}

    def _level(count):
        if count <= 0:
            return 0
        if level_control == "none":
            return 0
        if level_control == "low":
            return 4
        ratio = count / max_count
        if level_control == "medium":
            return 4 if ratio > 0.5 else 2
        # high / auto
        if ratio <= 0.25: return 1
        if ratio <= 0.5:  return 2
        if ratio <= 0.75: return 3
        return 4

    # ── Month labels (above grid) ────────────────────────────────────────────
    MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]
    last_month = -1
    for col in range(COLS):
        week_start = start_date + timedelta(days=col * 7)
        if week_start.month != last_month:
            mx = GRID_X + col * STEP
            dwg.add(dwg.text(
                MONTH_NAMES[week_start.month - 1],
                insert=(mx, GRID_Y - 6),
                fill=theme["text_color"],
                font_size=9,
                font_family=theme.get("font_family", "Arial"),
                opacity=0.75
            ))
            last_month = week_start.month

    # ── Day-of-week labels (left of grid) ────────────────────────────────────
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        dwg.add(dwg.text(
            label,
            insert=(GRID_X - 4, GRID_Y + row * STEP + CELL - 1),
            fill=theme["text_color"],
            font_size=8,
            font_family=theme.get("font_family", "Arial"),
            text_anchor="end",
            opacity=0.65
        ))

    # ── Grid cells ───────────────────────────────────────────────────────────
    for col in range(COLS):
        for row in range(ROWS):
            current = start_date + timedelta(days=col * 7 + row)
            if current > today:
                # future cell — draw faint outline only
                dwg.add(dwg.rect(
                    insert=(GRID_X + col * STEP, GRID_Y + row * STEP),
                    size=(CELL, CELL),
                    fill="none",
                    stroke=theme["border_color"],
                    stroke_width=0.5,
                    rx=2, ry=2,
                    opacity=0.3
                ))
                continue
            count = date_counts.get(current, 0)
            lvl   = _level(count)
            dwg.add(dwg.rect(
                insert=(GRID_X + col * STEP, GRID_Y + row * STEP),
                size=(CELL, CELL),
                fill=colors[lvl],
                rx=2, ry=2
            ))

    # ── Legend ───────────────────────────────────────────────────────────────
    legend_y  = height - 10
    legend_x0 = width - PAD_RIGHT - (5 * (CELL + 3)) - 50

    dwg.add(dwg.text("Less",
        insert=(legend_x0, legend_y),
        fill=theme["text_color"], font_size=9,
        font_family=theme.get("font_family", "Arial"), opacity=0.6))

    for i in range(5):
        dwg.add(dwg.rect(
            insert=(legend_x0 + 28 + i * (CELL + 3), legend_y - CELL + 1),
            size=(CELL, CELL),
            fill=colors[i], rx=2, ry=2
        ))

    dwg.add(dwg.text("More",
        insert=(legend_x0 + 28 + 5 * (CELL + 3) + 3, legend_y),
        fill=theme["text_color"], font_size=9,
        font_family=theme.get("font_family", "Arial"), opacity=0.6))

    return dwg.tostring()


def draw_contrib_card(data, theme_name="Default", custom_colors=None, date_range=None, animations_enabled=True):
    """
    Generates a Contribution Graph Card SVG with theme-specific visualization.
    
    Supports multiple themes including Gaming, Space, Marvel, Stranger_things,
    Pacman, Cyberpunk, Cricket, Ocean, Glass, Neural, Matrix, and Default.
    
    Args:
        data: Dict containing contribution data with 'contributions' list
        theme_name: String name of the theme to use (case-sensitive)
        custom_colors: Optional dict of custom color overrides
        date_range: Optional dict with 'start' and 'end' date strings (YYYY-MM-DD)
                    to filter contributions. If None, shows all contributions.
        animations_enabled: Whether to enable CSS animations (default: True)
    
    Returns:
        SVG string for the contribution card
    """
    # Save original theme name for comparison
    original_theme_name = theme_name
    
    # Get theme configuration
    theme = THEMES.get(theme_name, THEMES["Default"]).copy()
    if custom_colors:
        theme.update(custom_colors)
    
    # Determine canvas size based on theme
    width = 500
    height = 170
    
    # Allow larger canvas for Gaming theme
    if original_theme_name == "Gaming":
        width = 560
        height = 180
    
    # Create SVG drawing
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
    
    # Background
    draw_card_background(dwg, width, height, theme)
    
    # Add title
    username = data.get('username', 'Unknown')
    title = f"{username}'s Contributions"
    dwg.add(dwg.text(title, insert=(20, 24), 
                     fill=theme["title_color"], 
                     font_size=theme.get("title_font_size", 18), 
                     font_family=theme.get("font_family", "Arial"), 
                     font_weight="bold"))
    
    # Prepare contribution data
    contributions = data.get("contributions", [])
    
    # Filter contributions by date range if provided
    if date_range:
        from utils.github_api import filter_contributions_by_date
        contributions = filter_contributions_by_date(contributions, date_range)
    
    # Calculate grid dimensions
    total_days = len(contributions)
    cols = 53 if total_days >= 371 else 52
    rows = 7
    
    # Convert contributions to weekly grid
    weeks, max_date = _resolve_weeks(contributions, data.get("contribution_weeks"), cols, rows)
    
    # Handle special case: Matrix theme delegates to its own module
    if original_theme_name == "Matrix":
        from themes import matrix
        svg = matrix.render(data, theme)
        return svg
    
    if original_theme_name == "Sakura":
        from themes import sakura
        return sakura.render(data)
    
    # Get the appropriate theme renderer from dispatcher
    theme_renderer = THEME_DISPATCHER.get(original_theme_name)
    
    # If theme not in dispatcher, use default
    if theme_renderer is None:
        theme_renderer = render_default_theme
    
    # Call the theme-specific renderer
    theme_renderer(
        dwg, data, theme, weeks, cols, rows, max_date, 
        width, height
    )
    
    # For Glass theme, pass additional parameters
    if original_theme_name == "Glass":
        # Re-render Glass theme with animation support
        from .themes.advanced_themes import render_glass_theme
        # Clear the SVG except for background and title (already added above)
        dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
        dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=10, ry=10, 
                         fill=theme["bg_color"], stroke=theme["border_color"], stroke_width=2))
        dwg.add(dwg.text(title, insert=(20, 24), 
                         fill=theme["title_color"], 
                         font_size=theme.get("title_font_size", 18), 
                         font_family=theme.get("font_family", "Arial"), 
                         font_weight="bold"))
        
        render_glass_theme(dwg, data, theme, weeks, cols, rows, max_date, width, height, animations_enabled, CSS_ANIMATIONS)
    
    return dwg.tostring()

