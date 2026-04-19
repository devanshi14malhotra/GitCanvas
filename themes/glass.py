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
    contributions = data.get("contributions", [])
    
    if not contributions:
        # Display empty state message
        dwg.add(dwg.text(
            "No contributions data available",
            insert=(width/2, height/2),
            fill=theme.get("text_color", "#c9d1d9"),
            font_size=14,
            text_anchor="middle"
        ))
        return dwg.tostring()
    
    for day in contributions:
        count = day.get("count", 0)

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
