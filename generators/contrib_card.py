import svgwrite
import random
from themes.styles import THEMES
import math


def draw_contrib_card(data, theme_name="Default", custom_colors=None):
    """
    Generates the Contribution Graph Card SVG.
    Supports Gaming, Space, Marvel, Cyberpunk, Retro, Neural, Default themes.
    """

    # ---------- THEME HANDLING (from main – KEEP THIS) ----------
    original_theme_name = theme_name

    if isinstance(theme_name, dict):
        theme = theme_name.copy()
        original_theme_name = theme.get('_theme_name', 'Default')
    else:
        theme = THEMES.get(theme_name, THEMES["Default"]).copy()
        original_theme_name = theme_name

        if custom_colors:
            theme.update(custom_colors)
    # -----------------------------------------------------------

    width = 500
    height = 150
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")

    # Background
    dwg.add(dwg.rect(
        insert=(0, 0),
        size=("100%", "100%"),
        rx=10, ry=10,
        fill=theme["bg_color"],
        stroke=theme["border_color"],
        stroke_width=2
    ))

    # Title
    title = f"{data['username']}'s Contributions"
    dwg.add(dwg.text(
        title,
        insert=(20, 30),
        fill=theme["title_color"],
        font_size=theme.get("title_font_size", 18),
        font_family=theme.get("font_family", "Arial"),
        font_weight="bold"
    ))

    # ============================================================
    # ===================== THEME LOGIC ==========================
    # ============================================================

    # ---------- Cyberpunk (YOUR FEATURE) ----------
    if original_theme_name == "Cyberpunk":
        NEON_COLORS = ["#00ffff", "#39ff14", "#fcee0c", "#ff00ff"]

        dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="#0a0a0a"))

        for commit in data.get("contributions", []):
            count = commit.get("count", 0)

            x = random.randint(20, width - 20)
            y = random.randint(50, height - 20)

            radius = min(2 + count * 0.6, 9)
            color = NEON_COLORS[count % len(NEON_COLORS)]

            dwg.add(dwg.circle(center=(x, y), r=radius * 2.5, fill=color, fill_opacity=0.12))
            dwg.add(dwg.circle(center=(x, y), r=radius, fill=color))

    # ---------- Retro (YOUR FEATURE) ----------
    elif original_theme_name == "Retro":
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

        for commit in data.get("contributions", []):
            count = commit.get("count", 0)

            x = random.randint(20, width - 20)
            y = random.randint(60, height - 20)

            radius = min(2 + count * 0.4, 7)
            color = INK_COLORS[count % len(INK_COLORS)]

            dwg.add(dwg.circle(center=(x, y), r=radius, fill=color, fill_opacity=0.85))

    # ---------- Neural (main) ----------
    elif original_theme_name == "Neural":
        cx = width / 2
        cy = height / 2 + 10

        contributions = data.get("contributions", [])[-80:]
        if not contributions:
            return dwg.tostring()

        nodes = []

        dwg.add(dwg.circle(center=(cx, cy), r=45, fill="#00f7ff", opacity=0.08))

        for day in contributions:
            count = day.get("count", 0)

            x = random.uniform(cx - 120, cx + 120)
            y = random.uniform(cy - 70, cy + 70)

            size = 2 + min(count, 10)
            brightness = min(255, 80 + count * 18)

            color = f"rgb(0,{brightness},255)"

            dwg.add(dwg.circle(center=(x, y), r=size, fill=color, opacity=0.9))
            nodes.append((x, y))

    # ---------- Default ----------
    else:
        box_size = 12
        gap = 3

        for col in range(25):
            for row in range(5):
                x = 20 + col * (box_size + gap)
                y = 60 + row * (box_size + gap)

                level = random.choice([0, 1, 2, 3, 4])
                colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

                dwg.add(dwg.rect(insert=(x, y), size=(box_size, box_size), fill=colors[level], rx=2, ry=2))

    return dwg.tostring()
