import svgwrite

def render(data):
    """
    Renders the Gaming theme (8-bit Retro Map).
    Logic: Green squares are 'Grass', empty squares are 'Water'.
    High commit days are 'Castles'.
    """
    # We will accept up to 365 days (last year)
    contributions = data['contributions'][-365:] if len(data['contributions']) > 365 else data['contributions']
    
    # Grid layout: 53 columns x 7 rows
    cols = 53
    rows = 7
    
    width = cols * 15 + 20
    height = rows * 15 + 20

    # Make responsive: use a viewBox and percentage sizing so SVG scales on small screens
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
    
    # Background (Water / Dark Blue for map vibe)
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="#202040")) 
    
    box_size = 12
    gap = 3
    start_x = 10
    start_y = 10
    
    for i, day in enumerate(contributions):
        msg_count = day['count']
        
        col = i // 7
        row = i % 7
        
        x = start_x + col * (box_size + gap)
        y = start_y + row * (box_size + gap)
        
        # Logic
        if msg_count == 0:
            # Water
            fill_color = "#4fc3f7"
            # Optional: 8-bit water wave pattern? Simple blue square for now.
        elif msg_count > 5:
            # Castle / High activity
            # Gold/Stone
            fill_color = "#ffd700" 
        else:
            # Grass
            fill_color = "#388e3c" 
            
        dwg.add(dwg.rect(insert=(x, y), size=(box_size, box_size), fill=fill_color, rx=1, ry=1))
        
        # Detail for "Castle" - add a small 'door' or top
        if msg_count > 5:
             dwg.add(dwg.rect(insert=(x+4, y+2), size=(4, 4), fill="#d32f2f"))
             
    return dwg.tostring()
