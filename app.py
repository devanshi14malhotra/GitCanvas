import streamlit as st  # type: ignore
import base64
import os
import re
import json

# HEX color regex validation pattern
HEX_COLOR_REGEX = re.compile(r'^#[0-9A-Fa-f]{6}$')
import streamlit.components.v1 as components
from dotenv import load_dotenv
from roast_widget_streamlit import render_roast_widget
from generators import stats_card, lang_card, contrib_card, badge_generator, recent_activity_card, streak_card, repo_card, social_card, trophy_card
from utils import github_api
from themes.styles import THEMES, get_all_themes, CUSTOM_THEMES
from generators.visual_elements import (
    emoji_element,
    gif_element,
    sticker_element
)


# Load environment variables
load_dotenv()

st.set_page_config(page_title="GitCanvas Builder", page_icon="🛠️", layout="wide")

# Custom CSS for bigger code boxes and cleaner UI
st.markdown("""
<style>
    /* Make the code block width full and text bigger */
    code {
        font-size: 1.1rem !important;
        font-family: 'Courier New', monospace !important;
        white-space: pre-wrap !important; /* Allow wrapping so it doesn't hide */
    }
    .stTextArea textarea {
        background-color: #0d1117;
        color: #e6edf3;
        font-family: monospace;
    }
    /* Style for tool icons grid */
    .icon-btn {
        border: 1px solid #333;
        border-radius: 8px;
        padding: 5px;
        text-align: center;
        background: #111;
        cursor: pointer;
    }
    .icon-btn:hover {
        background: #222;
        border-color: #555;
    }
</style>
""", unsafe_allow_html=True)

st.title("GitCanvas: Profile Architect 🛠️")
st.markdown("### Design your GitHub Stats. Copy the Code. Done.")

# --- Sidebar Controls ---
with st.sidebar:
    st.header("1. Identify")
    username = st.text_input("GitHub Username", value="torvalds")
    
    st.header("2. Global Style")
    
    # Get all themes including custom ones
    all_themes = get_all_themes()
    
    # Separate predefined and custom themes for better organization
    predefined_themes = [k for k in all_themes.keys() if k not in CUSTOM_THEMES]
    custom_theme_names = list(CUSTOM_THEMES.keys())
    
    # Combine with custom themes at the end
    theme_options = predefined_themes + custom_theme_names
    
    selected_theme = st.selectbox("Select Theme", theme_options)
    
    # Customization Expander
    # Ensure custom_colors exists even if the expander isn't opened
    custom_colors = {}
    with st.expander("Customize Colors", expanded=False):
        st.caption("Override theme defaults")
        default_theme = all_themes.get(selected_theme, all_themes["Default"]).copy() # Copy to avoid mutating global
        
        # Helper to get color safely
        def get_col(key): return default_theme.get(key, "#000000")
        
        # Use theme-specific keys so each theme maintains its own customization
        custom_bg = st.color_picker("Background", value=get_col("bg_color"), key=f"customize_bg_{selected_theme}")
        
        # Validate HEX color format
        if not HEX_COLOR_REGEX.match(custom_bg):
            st.error("Invalid color format")
            custom_bg = get_col("bg_color")
        
        custom_title = st.color_picker("Title Text", value=get_col("title_color"), key=f"customize_title_{selected_theme}")
        
        # Validate title color format
        if not HEX_COLOR_REGEX.match(custom_title):
            st.error("Invalid title color format")
            custom_title = get_col("title_color")
        
        custom_text = st.color_picker("Body Text", value=get_col("text_color"), key=f"customize_text_{selected_theme}")
        
        # Validate text color format
        if not HEX_COLOR_REGEX.match(custom_text):
            st.error("Invalid text color format")
            custom_text = get_col("text_color")
        
        custom_border = st.color_picker("Border", value=get_col("border_color"), key=f"customize_border_{selected_theme}")
        
        # Validate border color format
        if not HEX_COLOR_REGEX.match(custom_border):
            st.error("Invalid border color format")
            custom_border = get_col("border_color")
        
        # Build custom colors dict if changed
        custom_colors = {}
        if custom_bg != get_col("bg_color"): custom_colors["bg_color"] = custom_bg
        if custom_title != get_col("title_color"): custom_colors["title_color"] = custom_title
        if custom_text != get_col("text_color"): custom_colors["text_color"] = custom_text
        if custom_border != get_col("border_color"): custom_colors["border_color"] = custom_border

    # Custom Theme Creator Section
    with st.expander("🎨 Custom Theme Creator", expanded=False):
        st.caption("Create and save your own custom theme")
        
        # Initialize session state for custom theme colors if not exists
        if "custom_theme_colors" not in st.session_state:
            st.session_state.custom_theme_colors = {
                "bg_color": "#0d1117",
                "border_color": "#30363d",
                "title_color": "#58a6ff",
                "text_color": "#c9d1d9",
                "icon_color": "#58a6ff",
            }
        
        theme_name = st.text_input("Theme Name", placeholder="My Awesome Theme", key="new_theme_name")
        
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.custom_theme_colors["bg_color"] = st.color_picker("Background", st.session_state.custom_theme_colors["bg_color"], key="creator_bg")
            st.session_state.custom_theme_colors["border_color"] = st.color_picker("Border", st.session_state.custom_theme_colors["border_color"], key="creator_border")
        with col2:
            st.session_state.custom_theme_colors["title_color"] = st.color_picker("Title", st.session_state.custom_theme_colors["title_color"], key="creator_title")
            st.session_state.custom_theme_colors["text_color"] = st.color_picker("Text", st.session_state.custom_theme_colors["text_color"], key="creator_text")
        
        if st.button("💾 Save Theme", use_container_width=True):
            if theme_name:
                from themes.styles import save_custom_theme
                filename = save_custom_theme(theme_name, st.session_state.custom_theme_colors)
                st.success(f"Theme '{theme_name}' saved! Refresh to see it in the theme list.")
            else:
                st.error("Please enter a theme name")

    github_token = st.text_input("GitHub Token (enter your token to view actual data)", type="password", help="Enter your GitHub token to fetch contribution data")
    
    # Animation toggle
    animations_enabled = st.checkbox("Enable Animations", value=False, help="Enable SVG animations for cards that support it")
    
    # Output format selector
    output_format = st.radio("Output Format", ["Markdown", "HTML"], index=0, help="Choose between Markdown or HTML code format")
    
    if st.button("Refresh Data", use_container_width=True):

        st.cache_data.clear()
        st.rerun()
        
    st.info("💡 Tip: Use the 'Icons & Badges' tab to add your tech stack icons!")

# Data Loading
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data(user, token=None, _cache_version="v2"):  # Added version to force cache invalidation
    d = github_api.get_live_github_data(user, token)
    if not d:
        st.warning("Using mock data (API limits).")
        d = github_api.get_mock_data(user)
    return d

data = load_data(username if username else "torvalds", github_token if github_token else None)

# Ensure data is not None
if data is None:
    data = {}

# Ensure backward compatibility with old cached data
if "top_repos" not in data:
    data["top_repos"] = []

# Initialize other missing fields with defaults
data.setdefault("username", username if username else "torvalds")
data.setdefault("total_stars", 0)
data.setdefault("total_commits", 0)
data.setdefault("public_repos", 0)
data.setdefault("followers", 0)
data.setdefault("created_at", "")
data.setdefault("top_languages", [])
data.setdefault("contributions", [])

# Apply custom colors to current theme for python logic
current_theme_opts = all_themes.get(selected_theme, all_themes["Default"]).copy()
if custom_colors:
    current_theme_opts.update(custom_colors)


# --- Layout: Tabs ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs(["Main Stats", "Languages", "Top Repositories", "Contributions", "🔥 GitHub Streak", "🔗 Social Links", "Icons & Badges", "🔥 AI Roast", "Recent Activity", "✨ Visual Elements", "🏆 Trophy"])

def show_code_area(code_content, label="Markdown Code"):
    st.markdown(f"**{label}** (Copy below)")
    st.text_area(label, value=code_content, height=100, label_visibility="collapsed")

def render_tab(svg_bytes, endpoint, username, selected_theme, custom_colors, hide_params=None, code_template=None, excluded_languages=None, output_format="Markdown"):
    col1, col2 = st.columns([1.5, 1])
    with col1:
        # Render SVG
        b64 = base64.b64encode(svg_bytes.encode('utf-8')).decode("utf-8")
        st.markdown(f'<img src="data:image/svg+xml;base64,{b64}" style="max-width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-radius: 10px;"/>', unsafe_allow_html=True)

        # --- SVG Download ---
        st.download_button(
            label="⬇️ Download SVG",
            data=svg_bytes.encode("utf-8"),
            file_name=f"{endpoint}_{username}.svg",
            mime="image/svg+xml",
            use_container_width=True
        )

        # --- PNG & JPEG Download via browser Canvas (no system dependencies) ---
        svg_b64 = base64.b64encode(svg_bytes.encode("utf-8")).decode("utf-8")
        filename_prefix_safe = json.dumps(f"{endpoint}_{username}")

        components.html(f"""
        <div style="display:flex; flex-direction:column; gap:8px; margin-top:4px;">
            <button onclick="downloadSVGAs('png')" style="
                width:100%; padding:8px; font-size:14px; cursor:pointer;
                background:#1a1a2e; color:white; border:1px solid #444;
                border-radius:6px;">
                ⬇️ Download PNG
            </button>
            <button onclick="downloadSVGAs('jpeg')" style="
                width:100%; padding:8px; font-size:14px; cursor:pointer;
                background:#1a1a2e; color:white; border:1px solid #444;
                border-radius:6px;">
                ⬇️ Download JPEG
            </button>
        </div>

        <script>
        function downloadSVGAs(format) {{
            const svgText = atob('{svg_b64}');
            const parser = new DOMParser();
            const svgDoc = parser.parseFromString(svgText, 'image/svg+xml');
            const svgEl = svgDoc.documentElement;

            const vb = svgEl.getAttribute('viewBox');
            let w = 800, h = 400;
            if (vb) {{
                const parts = vb.split(/[\s,]+/);
                w = parseFloat(parts[2]) || 800;
                h = parseFloat(parts[3]) || 400;
            }}

            const blob = new Blob([svgText], {{type: 'image/svg+xml'}});
            const url = URL.createObjectURL(blob);
            const img = new Image();
            img.onload = function() {{
                const SCALE = 4;

                const canvas = document.createElement('canvas');
                canvas.width = w * SCALE;
                canvas.height = h * SCALE;
                const ctx = canvas.getContext('2d');

                // Optional: fill white background for JPEG
                if (format === 'jpeg') {{
                    ctx.fillStyle = '#ffffff';
                    ctx.fillRect(0, 0, canvas.width, canvas.height);
                }}

                // Draw image preserving aspect ratio
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

                canvas.toBlob(function(blob) {{
                    const link = document.createElement('a');
                    link.download = {filename_prefix_safe} + (format === 'jpeg' ? '.jpeg' : '.png');
                    link.href = URL.createObjectURL(blob);
                    link.click();
                    URL.revokeObjectURL(url);
                }}, 'image/' + format, 1.0);
            }};
            img.src = url;
        }}
        </script>
        """, height=150)

    with col2:
        st.subheader("Integration")
        # Construct URL
        params = []
        if hide_params:
            for key, value in hide_params.items():
                if not value:
                    params.append(f"hide_{key}=true")

        if selected_theme != "Default":
            params.append(f"theme={selected_theme}")
        for k, v in custom_colors.items():
            params.append(f"{k}={v.replace('#', '')}")
        
        # Add exclude parameter for languages endpoint
        if excluded_languages and endpoint == "languages":
            # Remove spaces and add to params
            params.append(f"exclude={excluded_languages.replace(' ', '')}")

        query_str = "&".join(params)
        if query_str:
            query_str = "?" + query_str

        url = f"https://gitcanvas-api.vercel.app/api/{endpoint}{query_str}&username={username}"
        
        # Generate code based on output format
        if output_format == "HTML":
            # Generate HTML format
            if code_template and "[" in code_template:
                # Handle templates that have link wrapping (like stats card)
                # Extract alt text from markdown template
                import re
                alt_match = re.search(r'!\[([^\]]+)\]', code_template)
                alt_text = alt_match.group(1) if alt_match else endpoint.title()
                code = f'<a href="https://github.com/{username}"><img src="{url}" alt="{alt_text}"/></a>'
            else:
                # Simple image tag
                code = f'<img src="{url}" alt="{endpoint.title()}"/>'
        else:
            # Generate Markdown format (default)
            if code_template:
                code = code_template.format(url=url, username=username)
            else:
                code = f"![{endpoint.title()}]({url})"

        # Update label based on format
        code_label = "HTML Code" if output_format == "HTML" else "Markdown Code"
        show_code_area(code, label=code_label)

with tab1:
    st.subheader("Stats Card")
    # Options
    c1, c2, c3, c4 = st.columns(4)
    show_stars = c1.checkbox("Stars", True)
    show_commits = c2.checkbox("Commits", True)
    show_repos = c3.checkbox("Repos", True)
    show_followers = c4.checkbox("Followers", True)

    show_ops = {"stars": show_stars, "commits": show_commits, "repos": show_repos, "followers": show_followers}

    # Pass selected_theme string to support theme-specific logic (e.g. Glass)
    svg_bytes = stats_card.draw_stats_card(data, selected_theme, show_ops, custom_colors, animations_enabled)
    render_tab(svg_bytes, "stats", username, selected_theme, custom_colors, hide_params=show_ops, code_template=f"[![{username}'s Stats]({{url}})](https://github.com/{{username}})", output_format=output_format)

with tab2:
    st.subheader("Top Languages")
    
    # Get available languages from data
    available_languages = [lang for lang, _ in data.get("top_languages", [])]
    
    # Use st.pills() for better UX - click to toggle, no dropdown to close
    excluded_languages = st.pills(
        "Languages to Exclude:",
        options=available_languages,
        default=[],
        selection_mode="multi",
        help="Click to toggle languages you want to hide from your stats"
    )
    
    # Convert list to comma-separated string for URL generation
    excluded_languages_str = ",".join(excluded_languages) if excluded_languages else None
    
    # Generate card with exclusions - Pass selected_theme string
    svg_bytes = lang_card.draw_lang_card(data, selected_theme, custom_colors, excluded_languages=excluded_languages)
    render_tab(svg_bytes, "languages", username, selected_theme, custom_colors, code_template="![Top Langs]({url})", excluded_languages=excluded_languages_str, output_format=output_format)

with tab3:
    st.subheader("Top Repositories")
    
    # Sorting options
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        sort_by = st.selectbox("Sort by:", ["stars", "forks", "updated"], index=0, 
                              format_func=lambda x: {"stars": "⭐ Most Starred", "forks": "🔱 Most Forked", "updated": "🕐 Recently Updated"}[x])
    with col2:
        repo_limit = st.slider("Number of repos:", min_value=3, max_value=10, value=5)
    with col3:
        exclude_forks = st.checkbox("Exclude forks", value=False, help="Hide forked repositories")
    
    # Filter data based on user preference
    filtered_data = data.copy()
    if exclude_forks and "top_repos" in filtered_data:
        filtered_data["top_repos"] = [r for r in filtered_data["top_repos"] if not r.get("is_fork", False)]
    
    # Generate card - Pass selected_theme string
    svg_bytes = repo_card.draw_repo_card(filtered_data, selected_theme, custom_colors, sort_by=sort_by, limit=repo_limit)
    render_tab(svg_bytes, "repos", username, selected_theme, custom_colors, code_template="![Top Repos]({url})", output_format=output_format)

with tab4:
    st.subheader("Contribution Graph")
    st.caption(f"Theme: **{selected_theme}**")
    if selected_theme == "Gaming": st.caption("🐍 Snake Mode: The snake grows as it eats commits.")
    elif selected_theme == "Space": st.caption("🚀 Space Mode: Spaceship traversing the contribution galaxy.")
    elif selected_theme == "Marvel": st.caption("💎 Infinity Mode: Collecting Stones based on activity.")
    elif selected_theme == "Ocean": st.caption("🌊 Ocean Mode: Fish and bubbles swim through underwater contributions.")
    elif selected_theme == "Glass": st.caption("💎 GlassMorphism: Translucent Glass based theme card.")

    # Date Range Selector
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    
    col_date1, col_date2 = st.columns([1, 1])
    with col_date1:
        date_option = st.selectbox(
            "Date Range",
            ["All Time", "Last 6 Months", "Current Year", "Custom Range"],
            index=0,
            help="Select the date range for contributions"
        )
    
    # Initialize date_range
    date_range = None
    
    if date_option == "Custom Range":
        with col_date2:
            custom_start = st.date_input("Start Date", value=today - timedelta(days=180))
            custom_end = st.date_input("End Date", value=today)
        date_range = {
            'start': custom_start.strftime("%Y-%m-%d"),
            'end': custom_end.strftime("%Y-%m-%d")
        }
    elif date_option == "Last 6 Months":
        date_range = {
            'start': (today - timedelta(days=180)).strftime("%Y-%m-%d"),
            'end': today.strftime("%Y-%m-%d")
        }
    elif date_option == "Current Year":
        date_range = {
            'start': datetime(today.year, 1, 1).date().strftime("%Y-%m-%d"),
            'end': today.strftime("%Y-%m-%d")
        }
    # All Time returns None, showing all contributions

    # Pass selected_theme string and date_range
    svg_bytes = contrib_card.draw_contrib_card(data, selected_theme, custom_colors, date_range=date_range, animations_enabled=animations_enabled)
    render_tab(svg_bytes, "contributions", username, selected_theme, custom_colors, code_template="![Contributions]({url})", output_format=output_format)

with tab5:
    st.subheader("GitHub Streak")
    st.caption("🔥 Track your contribution streaks! Shows current consecutive days and your all-time longest streak.")
    
    svg_bytes = streak_card.draw_streak_card(data, selected_theme, custom_colors)
    render_tab(svg_bytes, "streak", username, selected_theme, custom_colors, code_template="![GitHub Streak]({url})", output_format=output_format)

with tab6:
    st.subheader("🔗 Social Links")
    st.markdown("Add badges for your social media profiles and connect with your audience!")
    
    # Social platform selection
    st.markdown("#### Select Platforms")
    available_platforms = list(social_card.SOCIAL_PLATFORMS.keys())
    selected_platforms = st.multiselect(
        "Choose platforms to display:",
        available_platforms,
        default=["twitter", "linkedin"],
        format_func=lambda x: social_card.SOCIAL_PLATFORMS[x]["name"]
    )
    
    # Input fields for each selected platform
    social_data = {}
    if selected_platforms:
        st.markdown("#### Enter Your Handles/URLs")
        cols = st.columns(2)
        for idx, platform in enumerate(selected_platforms):
            with cols[idx % 2]:
                placeholder = social_card.SOCIAL_PLATFORMS[platform]["placeholder"]
                social_data[platform] = st.text_input(
                    social_card.SOCIAL_PLATFORMS[platform]["name"],
                    placeholder=placeholder,
                    key=f"social_{platform}"
                )
    
    # Generate preview and code
    if selected_platforms and any(social_data.values()):
        col1, col2 = st.columns([1.5, 1])
        with col1:
            st.markdown("#### Preview")
            try:
                svg_bytes = social_card.draw_social_card(
                    social_data,
                    selected_theme,
                    custom_colors,
                    selected_platforms
                )
                b64 = base64.b64encode(svg_bytes.encode('utf-8')).decode("utf-8")
                st.markdown(f'<img src="data:image/svg+xml;base64,{b64}" style="max-width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-radius: 10px;"/>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error rendering social card: {e}")
        
        with col2:
            st.markdown("#### Markdown Code")
            # Generate individual badge code
            badge_code = ""
            for platform in selected_platforms:
                if social_data.get(platform):
                    platform_config = social_card.SOCIAL_PLATFORMS[platform]
                    badge_url = social_card.generate_social_badge_url(
                        platform,
                        social_data[platform],
                        platform_config["color"],
                        platform_config["logo"]
                    )
                    badge_code += f"[![{platform_config['name']}]({badge_url})](https://your-profile-url)\n"
            
            st.text_area("Copy the code below:", value=badge_code, height=200, label_visibility="collapsed")
    else:
        st.info("👆 Select platforms and enter your handles to generate social badges")

with tab7:
    st.subheader("Tech Stack Badges")
    st.markdown("Click detailed settings to customize. Copy the code block to your README.")
    
    col_tools, col_preview = st.columns([2, 1.5])
    
    with col_tools:
        # Badge Settings
        badge_style = st.selectbox("Badge Style", ["for-the-badge", "flat", "flat-square", "plastic", "social"], index=0)
        
        # Categories
        for category, tools in badge_generator.TECH_STACK.items():
            st.markdown(f"**{category}**")
            
            # Better UI: Multi-selects per category
            selected = st.multiselect(f"Select {category}", list(tools.keys()), key=f"sel_{category}")
            if selected:
                if "badges" not in st.session_state: st.session_state.badges = []
                pass

    with col_preview:
        st.subheader("Stack Preview")
        
        # Gather all selected
        all_selected_badges = []
        for category, tools in badge_generator.TECH_STACK.items():
            # We access the key we generated above
            val = st.session_state.get(f"sel_{category}", [])
            for item in val:
                conf = tools[item]
                all_selected_badges.append((item, conf))
        
        if not all_selected_badges:
            st.info("Select tools from the left to generate badges.")
        else:
            # Render Preview
            md_output = ""
            should_match = st.checkbox("Match Theme Color", value=False, key="match_theme_global")
            for name, conf in all_selected_badges:
                final_color = conf['color']
                if should_match:
                    final_color = current_theme_opts['title_color'].replace("#", "")
                
                url = badge_generator.generate_badge_url(name, final_color, conf['logo'], style=badge_style)
                st.markdown(f"![{name}]({url})")
                md_output += f"![{name}]({url}) "
            
            st.markdown("---")
            show_code_area(md_output, label="Badge Code")

# AI ROAST TAB
with tab8:
    st.subheader("🔥 AI Profile Roast")

    st.markdown("Let AI roast your GitHub profile with humor!")
    
    if username:
        render_roast_widget(username)
    else:
        st.warning("Please enter a GitHub username in the sidebar.")

with tab9:
    st.subheader("Recent Activity")
    st.markdown("Shows your last 3 PR or Issue events from GitHub.")

    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.caption("Theme: **{}**".format(selected_theme))
        try:
            # Pass selected_theme string
            svg_bytes = recent_activity_card.draw_recent_activity_card({'username': username}, selected_theme, custom_colors, token=github_token)
        except Exception as e:
            st.error(f"Error rendering recent activity: {e}")
            svg_bytes = recent_activity_card._render_svg_lines([f"Error: {e}"], THEMES.get(selected_theme, THEMES['Default']))

        b64 = base64.b64encode(svg_bytes.encode('utf-8')).decode("utf-8")
        st.markdown(f'<img src="data:image/svg+xml;base64,{b64}" style="max-width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-radius: 10px;"/>', unsafe_allow_html=True)

    with col2:
        st.subheader("Integration")
        params = []
        if selected_theme != "Default": params.append(f"theme={selected_theme}")
        for k, v in custom_colors.items():
            params.append(f"{k}={v.replace('#', '')}")
        if github_token:
            params.append(f"token={github_token}")

        query_str = "&".join(params)
        if query_str: query_str = "?" + query_str

        url = f"https://gitcanvas-api.vercel.app/api/recent{query_str}&username={username}"
        
        # Generate code based on output format
        if output_format == "HTML":
            code = f'<a href="https://github.com/{username}"><img src="{url}" alt="Recent Activity"/></a>'
        else:
            code = f"![Recent Activity]({url})"
        
        code_label = "HTML Code" if output_format == "HTML" else "Markdown Code"
        show_code_area(code, label=code_label)

with tab10:
    st.subheader("✨ Visual Elements")
    st.markdown("Add emojis, GIFs, or stickers to your canvas")

    element_type = st.selectbox(
        "Choose element type",
        ["Emoji", "GIF", "Sticker"]
    )

    value = st.text_input(
        "Enter value",
        placeholder="🔥 or https://gif-url"
    )

    if st.button("Add to Canvas"):
        if element_type == "Emoji":
            svg = emoji_element(value)
        elif element_type == "GIF":
            svg = gif_element(value)
        else:
            svg = sticker_element(value)

        st.session_state["canvas"].append(svg)

# TAB 11: Trophy Card
with tab11:
    st.subheader("🏆 GitHub Trophy")
    st.markdown("Display your achievements including stars, forks, followers, and repository quality tier!")
    
    # Get created_at from GitHub API data if available
    trophy_data = data.copy()
    # Try to get created_at from user data if available
    if "created_at" not in trophy_data:
        # Add a default for testing
        trophy_data["created_at"] = "2010-01-01T00:00:00Z"
    
    svg_bytes = trophy_card.draw_trophy_card(trophy_data, selected_theme, custom_colors)
    render_tab(svg_bytes, "trophy", username, selected_theme, custom_colors, code_template="![GitHub Trophy]({url})", output_format=output_format)