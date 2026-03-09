import random
import svgwrite


def render(data, theme, width=600, height=200):

    dwg = svgwrite.Drawing(size=(width, height))

    # Background
    dwg.add(
        dwg.rect(
            insert=(0, 0),
            size=(width, height),
            fill=theme.get("bg_color", "#000000")
        )
    )

    contributions = data.get("contributions", [])

    if not contributions:
        # fallback rain if data missing
        contributions = [{"count": random.randint(0, 5)} for _ in range(60)]

    cols = min(len(contributions), 60)
    col_width = width / cols

    for i in range(cols):

        count = contributions[i].get("count", 0)

        # contribution affects rain density
        rain_length = max(4, min(12, count + 4))

        x = (i * col_width) + col_width / 2

        dur = f"{random.uniform(3,7)}s"

        for j in range(rain_length):

            char = random.choice(["0", "1"])

            y_offset = -j * 12

            opacity = max(0.2, 1 - j * 0.12)

            text = dwg.text(
                char,
                insert=(x, y_offset),
                fill=theme.get("icon_color", "#00ff41"),
                font_size=14,
                font_family="monospace",
                text_anchor="middle",
                opacity=opacity
            )

            text.add(
                dwg.animate(
                    attributeName="y",
                    from_=str(y_offset),
                    to=str(height + 20),
                    dur=dur,
                    repeatCount="indefinite"
                )
            )

            dwg.add(text)

    return dwg.tostring()