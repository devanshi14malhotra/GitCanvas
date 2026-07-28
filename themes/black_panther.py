import svgwrite

def render(data):
    contributions = data["contributions"][-365:] if len(data["contributions"]) > 365 else data["contributions"]

    cols = 53
    rows = 7
    width = cols * 15 + 20
    height = rows * 15 + 50

    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")

    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="#0B0B0F"))

    box_size = 12
    gap = 3
    start_x = 10
    start_y = 10

    max_count = max((d["count"] for d in contributions), default=0)

    for i, day in enumerate(contributions):
        count = day["count"]

        col = i // rows
        row = i % rows

        x = start_x + col * (box_size + gap)
        y = start_y + row * (box_size + gap)

        if count == 0:
            fill_color = "#151515"
        else:
            intensity = count / max_count if max_count > 0 else 0

            if intensity < 0.25:
                fill_color = "#6A0DAD"
            elif intensity < 0.6:
                fill_color = "#9D4EDD"
            else:
                fill_color = "#C0C0C0"

        dwg.add(
            dwg.rect(
                insert=(x, y),
                size=(12, 12),
                fill=fill_color,
                stroke="#2A2A2A",
                stroke_width=0.5,
                rx=2,
                ry=2,
            )
        )

    dwg.add(
        dwg.text(
            "WAKANDA FOREVER",
            insert=(width / 2, height - 15),
            text_anchor="middle",
            fill="#C0C0C0",
            font_size="14px",
            font_weight="bold",
        )
    )

    return dwg.tostring()