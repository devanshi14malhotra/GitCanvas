import svgwrite
import random

def render(data, theme, **kwargs):

    width = 600
    height = 200

    dwg = svgwrite.Drawing(size=(width, height))

    for i in range(50):

        x = random.randint(0, width)

        rect = dwg.rect(
            insert=(x, 0),
            size=(4, 10),
            fill="#00ff00"
        )

        rect.add(
            dwg.animate(
                attributeName="y",
                from_="0",
                to=str(height),
                dur=f"{random.uniform(2,6)}s",
                repeatCount="indefinite"
            )
        )

        dwg.add(rect)

    return dwg.tostring()