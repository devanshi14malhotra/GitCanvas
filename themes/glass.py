import svgwrite

def render(data):
    width = 800
    height = 400

    dwg = svgwrite.Drawing(
        size=("100%", "100%"),
        viewBox=f"0 0 {width} {height}"
    )

    # Background
    dwg.add(
        dwg.rect(
            insert=(0, 0),
            size=("100%", "100%"),
            fill="#0f172a"  # dark slate
        )
    )

    # Define blur filter
    blur = dwg.filter(id="glassBlur")
    blur.feGaussianBlur(in_="SourceGraphic", stdDeviation=8)
    dwg.defs.add(blur)

    # Glass panel
    panel = dwg.rect(
        insert=(40, 40),
        size=(720, 320),
        rx=20,
        ry=20,
        fill="white",
        fill_opacity=0.15
    )
    panel['filter'] = 'url(#glassBlur)'
    dwg.add(panel)

    # Contributions
    x = 60
    y = 80
    for day in data["contributions"]:
        count = day["count"]
        if count == 0:
            continue

        r = min(4 + count, 10)
        dwg.add(
            dwg.circle(
                center=(x, y),
                r=r,
                fill="white",
                fill_opacity=0.8
            )
        )
        x += 20
        if x > 740:
            x = 60
            y += 20

    return dwg.tostring()
