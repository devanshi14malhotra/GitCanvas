import svgwrite
import requests
from themes.styles import THEMES


def draw_recent_activity_card(data, theme_name="Default", custom_colors=None, token=None):
    """
    Fetches the user's GitHub events and renders a simple text-based SVG
    showing the last 3 Pull Request or Issue events.

    Params:
      data: dict with at least 'username'
      theme_name: string key from THEMES OR a theme dictionary (if already resolved)
      custom_colors: dict to override theme values (only used if theme_name is a string)
      token: optional GitHub token string for higher rate limit

    Returns: SVG string
    """
    username = data.get('username')
    if not username:
        raise ValueError("data must include 'username'")

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

    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    url = f"https://api.github.com/users/{username}/events"
    try:
        resp = requests.get(url, headers=headers, timeout=8)
    except Exception as e:
        # Return an SVG with the error
        return _render_svg_lines([f"Error fetching events: {e}"], theme)

    if resp.status_code != 200:
        return _render_svg_lines([f"GitHub API error: {resp.status_code}"], theme)

    events = resp.json()

    lines = []
    for ev in events:
        if ev.get('type') == 'PullRequestEvent':
            payload = ev.get('payload', {})
            action = payload.get('action')
            pr = payload.get('pull_request', {})
            number = pr.get('number')
            title = pr.get('title') or ''
            repo = ev.get('repo', {}).get('name', '')
            merged = pr.get('merged')

            if merged:
                lines.append(f"Merged PR #{number} in {repo}: {title}")
            else:
                if action == 'opened':
                    lines.append(f"Opened PR #{number} in {repo}: {title}")
                elif action == 'closed':
                    lines.append(f"Closed PR #{number} in {repo}: {title}")
                else:
                    lines.append(f"PR #{number} {action} in {repo}: {title}")

        elif ev.get('type') == 'IssuesEvent':
            payload = ev.get('payload', {})
            action = payload.get('action')
            issue = payload.get('issue', {})
            number = issue.get('number')
            title = issue.get('title') or ''
            repo = ev.get('repo', {}).get('name', '')

            if action == 'opened':
                lines.append(f"Opened Issue #{number} in {repo}: {title}")
            elif action == 'closed':
                lines.append(f"Closed Issue #{number} in {repo}: {title}")
            else:
                lines.append(f"Issue #{number} {action} in {repo}: {title}")

        if len(lines) >= 3:
            break

    if not lines:
        lines = ["No recent PRs or Issues found."]

    return _render_svg_lines(lines[:3], theme)


def _render_svg_lines(lines, theme):
    width = 520
    height = 120
    dwg = svgwrite.Drawing(size=("100%", "100%"), viewBox=f"0 0 {width} {height}")

    dwg.add(dwg.rect(insert=(0, 0), size=(width, height), rx=8, ry=8,
                     fill=theme["bg_color"], stroke=theme["border_color"], stroke_width=2))

    title = "Recent Activity"
    dwg.add(dwg.text(title, insert=(20, 30),
                     fill=theme["title_color"], font_size=theme.get("title_font_size", 18),
                     font_family=theme.get("font_family", "sans-serif"), font_weight="bold"))

    y = 55
    for i, line in enumerate(lines):
        # simple truncation to avoid overflow
        text = line if len(line) <= 80 else line[:77] + '...'
        dwg.add(dwg.text(text, insert=(20, y + i * 20),
                         fill=theme["text_color"], font_size=theme.get("text_font_size", 14),
                         font_family=theme.get("font_family", "sans-serif")))

    return dwg.tostring()