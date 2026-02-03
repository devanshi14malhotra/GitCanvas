import svgwrite

def render(data):
    """
    Renders the Music theme (Audio Waveform).
    Logic: Commit frequency determines the 'amplitude' of the bars.
    """
    # Take last 100 days for a nice waveform look
    contributions = data['contributions'][-100:] if len(data['contributions']) > 0 else []
    
    width = 800
    height = 400
    # Make responsive: use a viewBox and percentage sizing so SVG scales on small screens
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
    
    # Background: Dark Studio
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="#1a1a1a"))
    
    if not contributions:
        dwg.add(dwg.text("No Data", insert=(width/2, height/2), fill="white"))
        return dwg.tostring()
        
    num_bars = len(contributions)
    bar_width = (width - 40) / num_bars  - 2 # dynamic width with some padding
    if bar_width < 1: bar_width = 1
    
    center_y = height / 2
    max_amp = height / 2 - 20
    
    # Calculate max commit to normalize
    max_commits = max(d['count'] for d in contributions) if contributions else 1
    if max_commits == 0: max_commits = 1
    
    start_x = 20
    
    for i, day in enumerate(contributions):
        count = day['count']
        
        # Amplitude
        # Add a baseline so even 0 commits show a line
        normalized = count / max_commits
        amp = normalized * max_amp + 5 
        
        x = start_x + i * (bar_width + 2)
        
        # Draw mirrored bar
        # Color: Gradient like? Let's use Neon Pink/Purple
        color = "#d600ff"
        if count > 5:
            color = "#00ffea" # High notes are Cyan
            
        dwg.add(dwg.rect(insert=(x, center_y - amp), size=(bar_width, amp * 2), fill=color, rx=bar_width/2, ry=bar_width/2))
        
    return dwg.tostring()
