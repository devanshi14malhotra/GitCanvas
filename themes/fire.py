import svgwrite
import random

def render(data, config):
    """
    Improved Fire Heatmap Theme
    """
    contributions = data['contributions'][-365:] if len(data['contributions']) > 365 else data['contributions']

    cols = 53
    rows = 7
    width = cols * 15 + 100
    height = rows * 15 + 150

    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")

    # Background
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill=config["bg_color"]))

    # Better Ember Particles (varying sizes and opacities)
    random.seed(42)
    for _ in range(40):
        x = random.randint(0, width)
        y = random.randint(0, height)
        r = random.uniform(0.5, 1.8)
        dwg.add(dwg.circle(center=(x, y), r=r, fill=config["icon_color"], opacity=random.uniform(0.1, 0.3)))

    # Title with subtle "heat" letter-spacing
    dwg.add(dwg.text(
        "ACTIVITY HEATMAP",
        insert=(width // 2, 40),
        text_anchor="middle",
        font_size=config["title_font_size"],
        font_family=config["font_family"],
        fill=config["title_color"],
        style="letter-spacing: 3px; font-weight: 800; text-transform: uppercase;"
    ))

    box_size = 12
    gap = 3
    start_x = 50
    start_y = 70

    max_count = max([day['count'] for day in contributions]) if contributions else 1

    for i, day in enumerate(contributions):
        count = day['count']
        col = i // 7
        row = i % 7

        x = start_x + col * (box_size + gap)
        y = start_y + row * (box_size + gap)

        # Smoother Heat Mapping
        if count == 0:
            fill = "#1a1a1a"
            opacity = 0.3
        elif count <= max_count * 0.25:
            fill = "#802b00"  # Deep ember
            opacity = 0.7
        elif count <= max_count * 0.5:
            fill = "#e65c00"  # Bright orange
            opacity = 0.85
        elif count <= max_count * 0.75:
            fill = "#ff3300"  # Fire red
            opacity = 0.95
        else:
            fill = "#ffcc00"  # White-hot yellow
            opacity = 1.0
            # Highlight peak days with a small inner dot instead of a bulky border
            dwg.add(dwg.circle(center=(x + 6, y + 6), r=2, fill="#ffffff", opacity=0.8))

        dwg.add(dwg.rect(
            insert=(x, y),
            size=(box_size, box_size),
            fill=fill,
            rx=3, # Slightly rounder boxes look more modern
            ry=3,
            opacity=opacity
        ))

    # Footer
    dwg.add(dwg.text(
        "Intensity Level: High",
        insert=(start_x, height - 20),
        font_size=10,
        font_family=config["font_family"],
        fill=config["text_color"],
        opacity=0.5
    ))

    # Modern Thin Border
    dwg.add(dwg.rect(
        insert=(0.5, 0.5),
        size=(width - 1, height - 1),
        fill="none",
        stroke=config["border_color"],
        stroke_width=1,
        opacity=0.5
    ))

    return dwg.tostring()
