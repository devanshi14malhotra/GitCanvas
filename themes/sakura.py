import svgwrite
import random
import math

SAKURA_COLORS = [
    "#FFE4EC", #pale blush: 1-2 commits
    "#FFB7C5", #soft pink: 3-5 commits
    "#FF8FAB", #medium pink: 6-10 commits
    "#FF6B9D", #deep pink: 11-15 commits
    "#C2185B", #magenta bloom: 16+ commits

]

def draw_petal(dwg,cx,cy,size,color,opacity,rotation=0):
    petal = dwg.ellipse(
        center = (cx,cy),
        r = (size*0.5 , size),
        fill = color,
        fill_opacity = opacity,
        stroke = "#FFF8F0",
        stroke_opacity = opacity,
    )
    
    petal.rotate(rotation,center = (cx,cy))
    return petal

def draw_sakura_flower(dwg,cx,cy,size,color,opacity):
    for i in range(5):
        angle = i*72
        offset_x = cx+math.cos(math.radians(angle))*size*0.4
        offset_y = cy+math.sin(math.radians(angle))*size*0.4
        petal = draw_petal(dwg, offset_x, offset_y, size*0.6, color, opacity, rotation = angle)
        dwg.add(petal)
        dwg.add(dwg.circle(
            center = (cx,cy),
            r = size*0.2,
            fill = "#FFF8F0",
            fill_opacity = opacity
        ))

def render(data):
    """
    Sakura/Japanese Theme
    contributions are Cherry blossom Flowers blooming on a Kyoto night sky.
    Low Activity = small plate petals
    Peak Activity = large deep magenta full bloom flowers

    """        
    width = 800
    height = 400
    dwg = svgwrite.Drawing(size=("100%","100%"),viewBox=f"0 0 {width} {height}")

    #Background: Deep midnight blue - Kyoto night sky
    dwg.add(dwg.rect(insert=(0,0),size =("100%","100%"), fill = "#0D0D2B"))

    #subtle purple/pink bottom glow
    dwg.add(dwg.rect(
        insert = (0, height*0.65),
        size = (width, height*0.35),
        fill = "#2D0A2E",
        fill_opacity = 0.5

    ))

    #Background stars - fixed seed for consistency
    random.seed(42)
    for _ in range(120):
        x = random.randint(0,width)
        y = random.randint(0,height//2)
        r = 0.3
        opacity = random.uniform(0.1, 0.4)
        dwg.add(dwg.circle(
            center = (x,y),
            r=r,
            fill = "#FFF8F0",
            fill_opacity = opacity
        ))

    #full moon
    dwg.add(dwg.circle(
        center = (680,70),
        r = 35,
        fill = "#FFF8F0",
        fill_opacity = 0.08
    ))
    dwg.add(dwg.circle(
        center = (680,70),
        r = 28,
        fill = "#FFF0F5",
        fill_opacity = 0.15
    ))
    dwg.add(dwg.circle(
        center = (680,70),
        r = 22,
        fill = "#FFFFFF",
        fill_opacity = 0.9
    ))
    #Decorative floating background petals
    random.seed(99)
    for _ in range(20):
        x = random.randint(0,width)
        y = random.randint(0,height)
        size = random.uniform(3,7)
        angle = random.randint(0,360)
        petal = draw_petal(dwg,x,y,size,"#FFB7C5",0.06,rotation=angle)
        dwg.add(petal)

    #Blossom tree silhoutte - left side
    #trunk
    dwg.add(dwg.line(
        start = (80,height),
        end = (80,height - 120),
        stroke = "#2A1A2A",
        stroke_width = 8,
        stroke_linecap = "round"
    ))

    #Branches
    for bx, by, bex, bey in[
        (80, height-100, 40, height-160),
        (80, height-100, 120, height-155),
        (80, height-130, 55, height-185),
        (80, height-130, 105, height-180),
    ]:
        dwg.add(dwg.line(
            start = (bx, by), end=(bex, bey),
            stroke = "#2A1A2A", stroke_width = 4,
            stroke_linecap = "round"
        ))
    
    #blossom clusters on tree
    random.seed(77)
    for bx, by in [(40,235),(120,240),(55,210),(105,215),(80,195)]:
        for _ in range(4):
            fx = bx + random.randint(-18,18)
            fy = by + random.randint(-18,18)
            draw_sakura_flower(dwg, fx,fy, random.uniform(5,9),"#FFB7C5",0.7)

    #Main Contribution flowders
    contributions = [d for d in data ['contributions'] if d['count']>0]
    random.seed(None)

    for commit in contributions:
        count = commit['count']
        x = random.randint(150,width - 30)
        y = random.randint(30,height - 30)
        size = min(4+count*0.7,14)

        if count <= 2:
            color = SAKURA_COLORS[0]
        elif count <= 5:
            color = SAKURA_COLORS[1]
        elif count <= 10:
            color = SAKURA_COLORS[2]
        elif count <= 15:
            color = SAKURA_COLORS[3]
        else:
            color = SAKURA_COLORS[4]

        opacity = min(0.5 + count*0.04, 1.0)

        # Soft glow for high activity 
        if count > 8:
            dwg.add(dwg.circle(
                center = (x,y),
                r = size*2.5,
                fill = color,
                fill_opacity = 0.08
            ))
        if count >= 5:
            draw_sakura_flower(dwg,x,y,size,color,opacity)
        else:
            petal = draw_petal(dwg,x,y, size, color, opacity, rotation = random.randint(0,360))
            dwg.add(petal)

    # Watermark
    dwg.add(dwg.text(
        "🌸 Sakura",
        insert=(width - 20,height - 12),
        text_anchor = "end",
        font_size="11px",
        font_family="georgia, serif",
        fill = "#FFB7C5",
        fill_opacity = 0.35

    ))

    return dwg.tostring()

