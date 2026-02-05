import svgwrite

def render(data):
    """
    Renders the Gaming theme (8-bit Retro Map).
    Logic: Green squares are 'Grass', empty squares are 'Water'.
    High commit days are 'Castles'.
    """
    # We will accept up to 365 days (last year)
    contributions = data["contributions"][-365:] if len(data["contributions"]) > 365 else data["contributions"]
    
    # Grid layout: 53 columns x 7 rows (GitHub‑style)
    cols = 53
    rows = 7
    
    width = cols * 15 + 20
    height = rows * 15 + 40  # a bit of extra room at bottom for legend

    # Make responsive: use a viewBox and percentage sizing so SVG scales on small screens
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")

    # Background: deep navy, so tiles have strong contrast
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="#020617"))
    box_size = 12
    gap = 3
    start_x = 10
    start_y = 10

    # Pre‑compute maximum commit count to map intensity
    max_count = max((d["count"] for d in contributions), default=0)

    for i, day in enumerate(contributions):
        msg_count = day["count"]

        col = i // rows
        row = i % rows

        x = start_x + col * (box_size + gap)
        y = start_y + row * (box_size + gap)

        # ------- Color logic (deterministic, intensity‑based) -------
        if msg_count == 0:
            # No commits: "water" tile
            fill_color = "#1e3a8a"  # deep blue
            stroke_color = "#0f172a"
        else:
            # Normalize intensity to [0, 1] for visual mapping
            intensity = msg_count / max_count if max_count > 0 else 0

            if intensity < 0.33:
                # Low activity: dark grass
                fill_color = "#14532d"
            elif intensity < 0.66:
                # Medium activity: bright grass
                fill_color = "#22c55e"
            else:
                # High activity: "castle" tile – golden
                fill_color = "#facc15"
            stroke_color = "#020617"

        # Base tile with subtle border for grid clarity
        dwg.add(
            dwg.rect(
                insert=(x, y),
                size=(box_size, box_size),
                fill=fill_color,
                stroke=stroke_color,
                stroke_width=0.7,
                rx=1,
                ry=1,
            )
        )

        # Extra detail for high‑activity "castle" tiles
        if msg_count > 0 and max_count > 0 and (msg_count / max_count) >= 0.66:
            # Small darker doorway to suggest a castle sprite
            dwg.add(
                dwg.rect(
                    insert=(x + 4, y + 5),
                    size=(4, 5),
                    fill="#4b5563",
                    rx=0.5,
                    ry=0.5,
                )
            )
             
    # ------- Optional tiny legend for readability -------
    legend_y = height - 14
    legend_x = 10
    legend_box = 9
    legend_gap = 6

    def legend_entry(x, label, color):
        # Small colored box + label text
        dwg.add(
            dwg.rect(
                insert=(x, legend_y - legend_box + 2),
                size=(legend_box, legend_box),
                fill=color,
                stroke="#020617",
                stroke_width=0.6,
                rx=1,
                ry=1,
            )
        )
        dwg.add(
            dwg.text(
                label,
                insert=(x + legend_box + 4, legend_y + 1),
                fill="#e5e7eb",
                font_size=9,
                font_family="Courier New",
            )
        )

    # Legend colors mirror the tile palette
    legend_entry(legend_x, "Water", "#1e3a8a")
    legend_entry(legend_x + 80, "Grass", "#22c55e")
    legend_entry(legend_x + 150, "Castle", "#facc15")

    return dwg.tostring()
