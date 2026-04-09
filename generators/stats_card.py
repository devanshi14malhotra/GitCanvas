import math
import random
import svgwrite
from themes.styles import THEMES
from .svg_base import create_svg_base, CSS_ANIMATIONS

# JavaScript for number counting animation
COUNTING_SCRIPT = """
<script type="text/javascript">
<![CDATA[
    function animateCounters() {
        var counters = document.querySelectorAll('.stat-counter');
        counters.forEach(function(counter, index) {
            var target = parseInt(counter.getAttribute('data-target'));
            var duration = 1500;
            var start = performance.now();
            var startVal = 0;
            
            function updateCounter(currentTime) {
                var elapsed = currentTime - start;
                var progress = Math.min(elapsed / duration, 1);
                var easeOut = 1 - Math.pow(1 - progress, 3);
                var current = Math.floor(startVal + (target - startVal) * easeOut);
                
                counter.textContent = current.toLocaleString();
                
                if (progress < 1) {
                    requestAnimationFrame(updateCounter);
                } else {
                    counter.textContent = target.toLocaleString();
                }
            }
            
            setTimeout(function() {
                requestAnimationFrame(updateCounter);
            }, index * 200);
        });
    }
    
    document.addEventListener('DOMContentLoaded', animateCounters);
]]>
</script>
"""

def draw_stats_card(data, theme_name="Default", show_options=None, custom_colors=None, animations_enabled=True, font_family=None):
    """
    Generates the Main Stats Card SVG.
    data: dict with user stats
    theme_name: string key from THEMES
    show_options: dict with toggles (e.g. {'stars': True, 'prs': False})
    animations_enabled: bool to enable/disable CSS animations
    font_family: optional custom font family override (e.g. 'Inter', 'Roboto')
    """
    if show_options is None:
        show_options = {"stars": True, "commits": True, "repos": True, "followers": True}

    # FIXED: Handle both string theme name and pre-resolved theme dict
    if isinstance(theme_name, dict):
        # Already a theme dictionary (e.g., current_theme_opts from app.py)
        theme = theme_name.copy()
    else:
        # Convert theme_name string to actual theme dictionary
        theme = THEMES.get(theme_name, THEMES["Default"]).copy()
        
        # Apply custom colors if provided
        if custom_colors:
            theme.update(custom_colors)
    
    # Determine font family - use custom override if provided, otherwise fall back to theme
    effective_font_family = font_family if font_family else theme["font_family"]

    width = 450
    # Calculate height dynamically based on visible items
    base_height = 50
    item_height = 25
    visible_items = sum(1 for k, v in show_options.items() if v)
    
    is_glass = False
    if isinstance(theme_name, dict):
        is_glass = theme_name.get("name") == "Glass" or theme.get("name") == "Glass"
    else:
        is_glass = theme_name == "Glass"
        
    if is_glass:
        margin = 15
        p_height = 65 + (visible_items * item_height) + 10
        height = margin * 2 + p_height
    else:
        height = base_height + (visible_items * item_height) + 10
    
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")
    
    # Validate username to prevent KeyError
    username = data.get('username', 'Unknown')
    
    # Add CSS animations if enabled (basic support only)
    # Note: Advanced animation features disabled due to svgwrite validation constraints
    
    # Background (with optional border pulse)
    bg_params = {
        "insert": (0, 0), 
        "size": ("100%", "100%"), 
        "rx": 10, 
        "ry": 10, 
        "fill": theme["bg_color"], 
        "stroke": theme["border_color"], 
        "stroke_width": 2
    }
    
    # Background (no animation)
    dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=10, ry=10, 
                     fill=theme["bg_color"], stroke=theme["border_color"], stroke_width=2))
    if theme_name == "Stranger_things":
        # Floating particles in background
        random.seed(42)
        for i in range(12):
            x = random.randint(20, width-20)
            y = random.randint(20, height-20)
            r = random.randint(1, 2)
            dwg.add(dwg.circle(center=(x, y), r=r, fill="#ffffff", opacity=0.2))
        
        # Mini demogorgon in corner
        demo_x = width - 40
        demo_y = 35
        dwg.add(dwg.circle(center=(demo_x, demo_y), r=12, fill="#330000", opacity=0.5))
        
        # Petals
        for angle in range(0, 360, 60):
            rad = math.radians(angle)
            x1 = demo_x + 9 * math.cos(rad)
            y1 = demo_y + 9 * math.sin(rad)
            x2 = demo_x + 15 * math.cos(rad)
            y2 = demo_y + 15 * math.sin(rad)
            dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), stroke="#ff0000", stroke_width=1, opacity=0.4))
        
        # Red glow around border
        dwg.add(dwg.rect(insert=(2, 2), size=(width-4, height-4), rx=9, ry=9, 
                        fill="none", stroke="#ff0000", stroke_width=1, opacity=0.3))
    elif theme_name == "Pacman":
        # Pac-Man character
        pac_x = width - 45
        pac_y = 30
        pacman_path = dwg.path(d=f"M {pac_x} {pac_y} " +
                              f"L {pac_x + 12} {pac_y - 10} " +
                              f"A 12 12 0 1 1 {pac_x + 12} {pac_y + 10} Z",
                              fill="#ffff00", stroke="#000000", stroke_width=0.5)
        dwg.add(pacman_path)
        dwg.add(dwg.circle(center=(pac_x + 8, pac_y - 3), r=2, fill="#000000"))
        
        # Pellets trail
        pellet_y = height - 15
        for i in range(5):
            pellet_x = 30 + i * 20
            dwg.add(dwg.circle(center=(pellet_x, pellet_y), r=3, fill="#ffff00"))
        
        # Ghost
        ghost_x = 25
        ghost_y = 25
        ghost_body = dwg.path(
            d=f"M {ghost_x} {ghost_y + 5} " +
              f"A 7 7 0 0 1 {ghost_x + 14} {ghost_y + 5} " +
              f"L {ghost_x + 14} {ghost_y + 14} " +
              f"L {ghost_x + 11} {ghost_y + 11} " +
              f"L {ghost_x + 7} {ghost_y + 14} " +
              f"L {ghost_x + 3} {ghost_y + 11} " +
              f"L {ghost_x} {ghost_y + 14} Z",
            fill="#ff0000", opacity=0.7
        )
        dwg.add(ghost_body)
        
        # Ghost eyes
        dwg.add(dwg.circle(center=(ghost_x + 5, ghost_y + 8), r=2, fill="#ffffff"))
        dwg.add(dwg.circle(center=(ghost_x + 10, ghost_y + 8), r=2, fill="#ffffff"))
    elif theme_name == "Cyberpunk":
        # Grid overlay
        for i in range(0, width, 30):
            dwg.add(dwg.line(start=(i, 0), end=(i, height), 
                           stroke="#1a1a2e", stroke_width=0.3, opacity=0.4))
        for i in range(0, height, 30):
            dwg.add(dwg.line(start=(0, i), end=(width, i), 
                           stroke="#1a1a2e", stroke_width=0.3, opacity=0.4))
        
        # Scan line effect
        scan_y = height / 2
        dwg.add(dwg.line(start=(0, scan_y), end=(width, scan_y), 
                        stroke="#00ff41", stroke_width=2, opacity=0.15))
        
        # Glitch rectangles
        random.seed(456)
        for _ in range(4):
            gx = random.randint(0, width - 40)
            gy = random.randint(0, height - 10)
            gw = random.randint(15, 40)
            dwg.add(dwg.rect(insert=(gx, gy), size=(gw, 2), 
                           fill="#ff00ff", opacity=0.25))
        
        # Corner brackets (HUD style)
        bracket_size = 15
        dwg.add(dwg.path(d=f"M 10 10 L 10 {10+bracket_size} M 10 10 L {10+bracket_size} 10", 
                        stroke="#00ffff", stroke_width=2, fill="none", opacity=0.5))
        dwg.add(dwg.path(d=f"M {width-10} 10 L {width-10} {10+bracket_size} M {width-10} 10 L {width-10-bracket_size} 10", 
                        stroke="#00ffff", stroke_width=2, fill="none", opacity=0.5))
    elif theme_name == "Glass":
        # Neon Liquid Glassmorphism Theme (Enhanced)
        
        # Theme Variables
        bg_col = theme.get("bg_color", "#050511")
        title_col = theme.get("title_color", "#00e5ff")
        text_col = theme.get("text_color", "#e2e8f0")
        border_col = theme.get("border_color", "white")
        
        # 1. Definitions
        # Blur filter for background blobs
        blob_blur = dwg.filter(id="blobBlur", x="-50%", y="-50%", width="200%", height="200%")
        blob_blur.feGaussianBlur(in_="SourceGraphic", stdDeviation=40)
        dwg.defs.add(blob_blur)
        
        # Glow filter for text
        text_glow = dwg.filter(id="textGlow")
        text_glow.feGaussianBlur(in_="SourceAlpha", stdDeviation=2, result="blur")
        text_glow.feOffset(in_="blur", dx=0, dy=0, result="offsetBlur")
        text_glow.feFlood(flood_color=title_col, result="glowColor")
        text_glow.feComposite(in_="glowColor", in2="offsetBlur", operator="in", result="coloredBlur")
        text_glow.feMerge(["coloredBlur", "SourceGraphic"])
        dwg.defs.add(text_glow)
        
        # Glass Panel Gradient
        glass_grad = dwg.linearGradient(start=(0, 0), end=(1, 1), id="glassGrad")
        glass_grad.add_stop_color(0, "white", opacity=0.15)
        glass_grad.add_stop_color(1, "white", opacity=0.05)
        dwg.defs.add(glass_grad)
        
        # Border Gradient
        border_grad = dwg.linearGradient(start=(0, 0), end=(1, 1), id="borderGrad")
        border_grad.add_stop_color(0, border_col, opacity=0.4)
        border_grad.add_stop_color(1, border_col, opacity=0.1)
        dwg.defs.add(border_grad)

        # Background Base
        dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), rx=16, ry=16, fill=bg_col))

        # Neon Blobs
        dwg.add(dwg.circle(center=(0, 0), r=120, fill="#ff00ff", filter="url(#blobBlur)", opacity=0.5))
        dwg.add(dwg.circle(center=(width, height), r=140, fill="#00ffff", filter="url(#blobBlur)", opacity=0.4))

        # 2. Glass Panel
        margin = 15
        p_width = width - margin * 2
        p_height = height - margin * 2
        dwg.add(dwg.rect(insert=(margin, margin), size=(p_width, p_height), rx=16, ry=16, fill="#000000", opacity=0.3))
        dwg.add(dwg.rect(insert=(margin, margin), size=(p_width, p_height), rx=16, ry=16, 
                         fill="url(#glassGrad)", stroke="url(#borderGrad)", stroke_width=1.2))
        
        # Top Reflection
        reflection_grad = dwg.linearGradient(start=(0, 0), end=(0, 1), id="reflGrad")
        reflection_grad.add_stop_color(0, "white", opacity=0.08)
        reflection_grad.add_stop_color(1, "white", opacity=0)
        dwg.defs.add(reflection_grad)
        dwg.add(dwg.rect(insert=(margin + 4, margin + 4), size=(p_width - 8, p_height / 4), rx=12, ry=12, fill="url(#reflGrad)"))

        # 3. Content Title
        title_text = f"{username}'s Stats".upper()
        # Dynamic font size for title
        base_f = 16
        n_len = len(title_text)
        d_font_size = max(11, base_f - (n_len - 15) // 1.5) if n_len > 15 else base_f
        
        dwg.add(dwg.text(title_text, insert=(width/2, margin + 35), fill="white", font_size=d_font_size, 
                         font_weight="800", font_family=f"{effective_font_family}, system-ui, sans-serif", text_anchor="middle", 
                         letter_spacing=2, filter="url(#textGlow)"))
        
        # Adjust start_y for stats
        start_y = margin + 65
        item_height = 25
        current_y = start_y
        
        stats_map = [
            ("stars", "Total Stars", f"{data.get('total_stars', 0)}", data.get('total_stars', 0)),
            ("commits", "Total Commits", f"{data.get('total_commits', 0)}", data.get('total_commits', 0)),
            ("repos", "Public Repos", f"{data.get('public_repos', 0)}", data.get('public_repos', 0)),
            ("followers", "Followers", f"{data.get('followers', 0)}", data.get('followers', 0))
        ]
        
        for idx, (key, label, display_value, numeric_value) in enumerate(stats_map):
            if show_options.get(key, True):
                # Row line (subtle)
                dwg.add(dwg.line(start=(margin + 20, current_y + 8), end=(width - margin - 20, current_y + 8), 
                                stroke="white", opacity=0.04))
                
                # Label
                dwg.add(dwg.text(f"{label}:", insert=(margin + 25, current_y), fill=text_col, 
                                 font_size=11, font_family=f"{effective_font_family}, sans-serif", opacity=0.8))
                
                # Value
                dwg.add(dwg.text(f"{display_value}", insert=(width - margin - 25, current_y), fill="white", 
                                 font_size=11, font_family=f"{effective_font_family}, sans-serif", text_anchor="end", font_weight="bold"))
                
                current_y += item_height
        
        return dwg.tostring()
    
    
    # Title - use effective_font_family determined earlier
    title_params = {
        "insert": (20, 35),
        "fill": theme["title_color"],
        "font_size": theme["title_font_size"],
        "font_family": effective_font_family,
        "font_weight": "bold"
    }
    
    if animations_enabled:
        dwg.add(dwg.text(f"{username}'s Stats", **title_params))
    else:
        dwg.add(dwg.text(f"{username}'s Stats", **title_params))
    
    # Stats with animations
    start_y = 65
    current_y = start_y
    text_color = theme["text_color"]
    font_size = theme["text_font_size"]
    
    # Logic to handle N/A display for commits
    commit_val = data.get('total_commits', 0)
    display_commits = str(commit_val) if commit_val > 0 else "N/A"

    stats_map = [
        ("stars", "Total Stars", f"{data.get('total_stars', 0)}", data.get('total_stars', 0)),
        ("commits", "Total Commits (Year)", display_commits, commit_val if commit_val > 0 else 0),
        ("repos", "Public Repos", f"{data.get('public_repos', 0)}", data.get('public_repos', 0)),
        ("followers", "Followers", f"{data.get('followers', 0)}", data.get('followers', 0))
    ]
    
    for idx, (key, label, display_value, numeric_value) in enumerate(stats_map):
        if show_options.get(key, True):
            # Icon (with optional pulse animation)
            icon_params = {
                "center": (30, current_y - 5),
                "r": 4,
                "fill": theme["icon_color"]
            }
            
            if animations_enabled:
                dwg.add(dwg.circle(**icon_params))
            else:
                dwg.add(dwg.circle(**icon_params))
            
            # Label with fade-in animation
            label_params = {
                "insert": (45, current_y),
                "fill": text_color,
                "font_size": font_size,
                "font_family": font_family
            }
            
            if animations_enabled:
                dwg.add(dwg.text(f"{label}:", **label_params))
            else:
                dwg.add(dwg.text(f"{label}:", **label_params))
            
            # Value with slide-up animation and counting effect
            value_params = {
                "insert": (width - 40, current_y),
                "fill": text_color,
                "font_size": font_size,
                "font_family": font_family,
                "text_anchor": "end",
                "font_weight": "bold"
            }
            
            if animations_enabled:
                dwg.add(dwg.text(f"{display_value}", **value_params))
            else:
                dwg.add(dwg.text(f"{display_value}", **value_params))
                             
            current_y += item_height
            
    return dwg.tostring()
