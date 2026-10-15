import streamlit as st  # type: ignore
import streamlit.components.v1 as components
import base64
import json
import os
import re
import requests
from urllib.parse import quote

# HEX color regex validation pattern
HEX_COLOR_REGEX = re.compile(r'^#[0-9A-Fa-f]{6}$')
from dotenv import load_dotenv
from config.settings import get_settings
from ui.roast_widget import render_roast_widget
from ui.compliment_widget import render_compliment_widget
from ai.description_generator import generate_github_description
from generators import stats_card, lang_card, contrib_card, badge_generator, recent_activity_card, streak_card, repo_card, social_card, trophy_card, sparkline, actions_card, achievement_card
from utils import github_api
try:
    from utils.github_utils import get_rate_limit_status as fetch_rate_limit_status
except ImportError:
    def fetch_rate_limit_status(token: str | None = None) -> dict | None:
        return None
from utils.cache import clear_cache as clear_ttl_cache
from utils.theme_state import reset_theme_filter_state
from themes.styles import THEMES, get_all_themes, CUSTOM_THEMES
from utils.theme_storage import get_storage_backend
from utils.error_card import draw_error_card
from utils.github_tokens import configured_tokens
from generators.visual_elements import emoji_element, gif_element, sticker_element
try:
    from generators.svg_base import get_svg_font_style as _shared_get_svg_font_style
except (ImportError, AttributeError):
    def _shared_get_svg_font_style(font_family):
        if not font_family:
            return ""
        return f"text, tspan, .svg-font {{ font-family: {font_family} !important; }}"

try:
    from generators.visual_elements import create_composite_canvas
except ImportError:
    def create_composite_canvas(svg_elements: list, bg_color: str = "#0d1117", padding: int = 20) -> str:
        """Fallback canvas renderer when create_composite_canvas is unavailable."""
        if not svg_elements:
            return f"""
            <svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400">
                <rect width="600" height="400" fill="{bg_color}"/>
                <text x="300" y="200" text-anchor="middle" dominant-baseline="middle"
                      fill="#888" font-size="16px" font-family="Arial">
                    Your canvas is empty. Add elements to get started!
                </text>
            </svg>
            """

        import math

        cols = math.ceil(math.sqrt(len(svg_elements)))
        rows = math.ceil(len(svg_elements) / cols)
        element_width = 140
        element_height = 140
        canvas_width = cols * (element_width + padding) + padding
        canvas_height = rows * (element_height + padding) + padding

        svg_content_list = []
        for idx, svg_str in enumerate(svg_elements):
            start = svg_str.find('>') + 1
            end = svg_str.rfind('</svg>')
            if start > 0 and end > start:
                svg_content_list.append((idx, svg_str[start:end]))

        composite = f"""
        <svg xmlns="http://www.w3.org/2000/svg" width="{canvas_width}" height="{canvas_height}" viewBox="0 0 {canvas_width} {canvas_height}">
            <rect width="{canvas_width}" height="{canvas_height}" fill="{bg_color}"/>
            <style>
                .canvas-border {{ stroke: #30363d; stroke-width: 1; fill: none; }}
            </style>
        """

        for idx, content in svg_content_list:
            col = idx % cols
            row = idx // cols
            x = padding + col * (element_width + padding)
            y = padding + row * (element_height + padding)
            composite += f"""
            <g transform="translate({x}, {y})">
                <rect x="0" y="0" width="{element_width}" height="{element_height}"
                      class="canvas-border" rx="8"/>
                <g transform="translate({element_width/2}, {element_height/2}) scale(1)">
                    {content}
                </g>
            </g>
            """

        return composite + "</svg>"
from ui.theme_gallery import render_theme_gallery



# Load environment variables
load_dotenv()
# Streamlit reruns this script without restarting the process; drop LRU cache so
# .env edits and new tokens are picked up, and avoid stale pydantic settings.
get_settings.cache_clear()
_settings = get_settings()

st.set_page_config(page_title="GitCanvas Builder", page_icon="🛠️", layout="wide")

# Load persisted custom themes from storage backend on every rerun
CUSTOM_THEMES.clear()
_storage = get_storage_backend()
for _name in _storage.list_themes():
    _data = _storage.load_theme(_name)
    if _data:
        CUSTOM_THEMES[_name] = _data

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

    /* Keep the long tab row usable on smaller screens */
    div[data-baseweb="tab-list"] {
        overflow-x: auto;
        overflow-y: hidden;
        flex-wrap: nowrap;
        scrollbar-width: thin;
    }
    div[data-baseweb="tab-list"] button {
        white-space: nowrap;
        flex: 0 0 auto;
    }

</style>
""", unsafe_allow_html=True)

# --- LIVE MARKDOWN PREVIEW PAGE LOGIC ---
if st.session_state.get("show_md_preview", False):
    st.title("📝 Live Markdown Preview")
    st.markdown("Test out your generated GitCanvas components and build your profile README in real-time.")
    
    if st.button("🔙 Back to Profile Architect", key="back_to_main"):
        st.session_state.show_md_preview = False
        st.rerun()

    DEMO_MARKDOWN = """# Hi there, I'm a GitCanvas User 👋

This is a **Heading 1** (`# Heading 1`). 

## This is a Heading 2 (`## Heading 2`)
### This is a Heading 3 (`### Heading 3`)

Welcome to my GitHub profile! Here is some **bold text** (`**bold text**`) and some *italic text* (`*italic text*`).

You can also use `inline code` (with backticks) or create lists:
- First item (`- First item`)
- Second item
  1. Numbered sub-item (`1. Numbered sub-item`)
  2. Another sub-item

Here is a [link to GitCanvas](https://github.com/devanshi14malhotra/GitCanvas) (`[title](url)`).
"""

    if "md_text" not in st.session_state:
        st.session_state.md_text = DEMO_MARKDOWN

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Markdown Source")
        st.caption("Type or paste your Markdown here. The preview will update automatically.")
        
        md_input = st.text_area(
            "Source Code",
            value=st.session_state.md_text,
            height=500,
            label_visibility="collapsed",
            key="md_input_area"
        )
        
        if md_input != st.session_state.md_text:
            st.session_state.md_text = md_input
            
        c1, c2, c3 = st.columns([1, 1, 2])
        if c1.button("🔄 Reset Demo", use_container_width=True):
            st.session_state.md_text = DEMO_MARKDOWN
            st.rerun()
            
        if c2.button("🗑️ Clear", use_container_width=True):
            st.session_state.md_text = ""
            st.rerun()
        with st.expander("📖 Markdown Syntax Cheat Sheet"):
            st.markdown("""
            - **Bold**: `**text**`
            - *Italic*: `*text*`
            - [Link](url): `[title](https://...)`
            - ![Image](url): `![alt text](https://...)`
            - `Code`: `\\`inline code\\``
            - Lists: `- item` or `1. item`
            - Headers: `# H1`, `## H2`, `### H3`
            """)
    with col2:
        st.subheader("Live Preview")
        st.caption("How it will appear on GitHub")
        
        with st.container(border=True):
            if st.session_state.md_text.strip():
                st.markdown(st.session_state.md_text, unsafe_allow_html=True)
            else:
                st.info("Nothing to preview. Start typing on the left!")

    st.stop()  # Stop rendering the rest of app.py
# ----------------------------------------

st.title("GitCanvas: Profile Architect 🛠️")
st.markdown("### Craft a stunning GitHub profile card — pick a theme, preview instantly, and export in seconds.")

TAB_NAMES = [
    "Theme Gallery", "Main Stats", "Languages", "Top Repositories",
    "Contributions", "GitHub Streak", "Trophy", "Achievement Room",
    "Calendar Heatmap", "GitHub Actions", "Recent Activity", "AI Roast",
    "AI Compliment", "Social Links", "Icons & Badges", "Visual Elements"
]

if st.button("📝 Open Live Markdown Preview", type="primary"):
    st.session_state.show_md_preview = True
    st.rerun()
st.markdown("---")

# Initialize session state for canvas
if "canvas" not in st.session_state:
    st.session_state["canvas"] = []
if "canvas_elements_metadata" not in st.session_state:
    st.session_state["canvas_elements_metadata"] = []


@st.cache_data(ttl=60, show_spinner=False)
def get_cached_rate_limit_status(token: str | None) -> dict | None:
    """Cache rate-limit calls to avoid a network hit on every Streamlit rerun."""
    return fetch_rate_limit_status(token)


# --- Sidebar Controls ---
with st.sidebar:
    st.header("1. Identify")
     # Wrapping in st.form prevents API re-fetch on every keystroke.
    # Data only loads when user clicks "Load Profile" or presses Enter.
    with st.form(key="username_form"):
        username = st.text_input(
            "GitHub Username",
            value=st.session_state.get("last_username", "devanshi14malhotra"),
            placeholder="e.g. devanshi14malhotra",
            help="Press Enter or click Load Profile to fetch data"
        )
        submitted = st.form_submit_button(
            "🔍 Load Profile",
            use_container_width=True,
            type="primary"
        )

    # Only update the active username when form is submitted
    if submitted:
        st.session_state["last_username"] = username.strip()

    # Use last confirmed username — avoids mid-typing API calls
    username = st.session_state.get("last_username", "devanshi14malhotra").strip()
    # ── End debounce fix ─────────────────────────────────────────────────

    
    st.header("2. Global Style")
    
    # Get all themes including custom ones
    all_themes = get_all_themes()

    predefined_themes = [k for k in all_themes.keys() if k not in CUSTOM_THEMES]
    custom_theme_names = list(CUSTOM_THEMES.keys())
    
    # Combine with custom themes at the end
    theme_options = sorted(
        predefined_themes + custom_theme_names,
        key=lambda name: name.replace("_", " ").lower(),
    )
    
    theme_selection_container = st.container()
    
    st.markdown("---")
    st.markdown("**Filter Themes**")

    # Search bar
    theme_search = st.text_input("🔍 Search themes", placeholder="e.g. dark, gaming...", key="theme_search")

    # Collect all unique tags across themes
    all_tags = sorted(set(
        tag
        for t in all_themes.values()
        for tag in t.get("tags", [])
    ))

    # Filter buttons (pills)
    selected_tags = st.pills("Filter by tag", options=all_tags, selection_mode="multi", key="theme_tags")

    if st.button("Reset Theme Filters", key="reset_theme_filters", use_container_width=True):
        st.session_state["theme_search"] = ""
        st.session_state["theme_tags"] = []
        st.rerun()

    # Apply filters to theme_options
    def matches_filter(name, props):
        theme_tags = props.get("tags", [])
        search_term = (theme_search or "").strip().lower()
        normalized_name = name.replace("_", " ").lower()
        search_match = (
            not search_term
            or search_term in normalized_name
            or search_term in name.lower()
            or any(search_term in t.lower() for t in theme_tags)
        )
        
        if not selected_tags:
            tag_match = True
        else:
            tag_match = any(tag in theme_tags for tag in selected_tags)
            
        return search_match and tag_match

    filtered_theme_options = [
        name for name in theme_options
        if name in all_themes and matches_filter(name, all_themes[name])
    ]
    if not filtered_theme_options:
        filtered_theme_options = ["Default"]

    # Maintain selection synchronization
    if "gallery_selected_theme" in st.session_state:
        target_theme = st.session_state.pop("gallery_selected_theme")
        if target_theme not in filtered_theme_options:
            filtered_theme_options.append(target_theme)
        st.session_state["current_theme_selection"] = target_theme

    try:
        default_idx = filtered_theme_options.index(st.session_state.get("current_theme_selection", "Default"))
    except ValueError:
        default_idx = 0

    with theme_selection_container:
        selected_theme = st.selectbox(
            "Select Theme",
            filtered_theme_options,
            index=default_idx,
            key="current_theme_selection",
            format_func=lambda name: name.replace("_", " "),
        )
        
        # ── Custom Font Override (Issue #174) ────────────────────────────────────
        st.markdown("**Font Override**")
        FONT_OPTIONS = [
            "Theme Default",
            "Rubik", "Oswald", "Orbitron", "Fira Code",
            "Dancing Script", "Great Vibes", "Pacifico"
        ]
        selected_font = st.selectbox(
            "Card Font",
            FONT_OPTIONS,
            help="Small, high-contrast font set with visibly different styles."
        )
        # None means use theme default — only pass if user picked something
        font_override = None if selected_font == "Theme Default" else selected_font
        # ── End font override ─────────────────────────────────────────────────────
    
    # Customization Expander
    # Ensure custom_colors exists even if the expander isn't opened
    custom_colors = {}
    theme_defaults = all_themes.get(selected_theme, all_themes["Default"]).copy()

    def _reset_theme_filters():
        reset_theme_filter_state(st.session_state, selected_theme, theme_defaults)

    with st.expander("Customize Colors", expanded=False):
        st.caption("Override theme defaults")
        default_theme = theme_defaults  # Copy already taken above to avoid mutating global
        
        # Helper to get color safely
        def get_col(key):
            val = default_theme.get(key, "000000")
            return f"#{val}" if not str(val).startswith("#") else val
        
        # Use theme-specific keys so each theme maintains its own customization
        def hex_fix(v): return f"#{v}" if not v.startswith("#") else v
        custom_bg = st.color_picker("Background", value=hex_fix(get_col("bg_color")), key=f"customize_bg_{selected_theme}")
        
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

        st.button(
            "Reset Theme Filters",
            use_container_width=True,
            on_click=_reset_theme_filters,
            help="Restore this theme's color controls to their default values",
        )

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
                from utils.theme_storage import get_storage_backend
                storage = get_storage_backend()
                storage.save_theme(theme_name, st.session_state.custom_theme_colors)
                st.success(f"Theme '{theme_name}' saved!")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Please enter a theme name")

    github_token = st.text_input(
        "GitHub Token (enter your token to view actual data)",
        type="password",
        help="Paste your own token here, or configure server-side GITHUB_TOKEN_1, GITHUB_TOKEN_2, and GITHUB_TOKEN_3 secrets.",
    )

    # Resolve token once so UI status + data loading stay consistent.
    _github_from_sidebar = (github_token or "").strip()
    # Server-side tokens are resolved inside the GitHub API layer so the app can
    # fail over without ever exposing them to the browser or generated URLs.
    effective_github_token = _github_from_sidebar or None
    _configured_github_tokens = configured_tokens()

    # ==================== RATE LIMIT STATUS INDICATOR ====================
    st.markdown("**Rate Limit Status**")

    rate_info = get_cached_rate_limit_status(
        effective_github_token or (_configured_github_tokens[0] if _configured_github_tokens else None)
    )

    if rate_info:
        col1, col2 = st.columns([0.8, 3.2])
        with col1:
            st.markdown(f"{rate_info['color']}", unsafe_allow_html=True)
        with col2:
            st.markdown(f"**{rate_info['remaining']} / {rate_info['limit']}** remaining")

        st.caption(f"🔄 Resets in **{rate_info['reset_in']}** minutes")

        if rate_info['remaining'] < 200:
            st.warning("⚠️ Rate limit is getting low. Consider using a token with higher limits.", icon="⚠️")
    else:
        if effective_github_token or _configured_github_tokens:
            st.caption("Rate limit status unavailable right now.")
        else:
            st.caption("Using anonymous access → **60 requests/hour**")
    # =====================================================================
    
    # Animation toggle
    animations_enabled = st.checkbox("Enable Animations", value=False, help="Enable SVG animations for cards that support it")
    
    # Output format selector
    output_format = st.radio("Output Format", ["Markdown", "HTML"], index=0, help="markdown: best for github readme files - paste directly into your profile repo. html: gives full styling control, ideal for personal websites or portfolios.")
    
    # Dev/Test mock data toggle
    use_mock_data = st.checkbox("Use Mock Data on API Failure", value=False, help="Dev/Test mode: fallback to mock data if GitHub API hits rate limits or errors.")
    
    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        clear_ttl_cache("github_api")
        get_settings.cache_clear()
        st.rerun()
        
    st.info("💡 Tip: Use the 'Icons & Badges' tab to add your tech stack icons!")

# Data Loading
@st.cache_data(ttl=300)  # Keep live GitHub data reasonably fresh while limiting API load.
def load_data(user, token=None, use_mock=False, _cache_version="v4"):  # bump when auth/cache semantics change
    d = github_api.get_live_github_data(user, token)
    if not d:
        if use_mock:
            st.warning("API limits/errors reached. Using mock data (Dev/Test mode).")
            d = github_api.get_mock_data(user)
        else:
            return None
    return d


@st.cache_data(ttl=300, show_spinner=False)
def load_actions_data(user, token=None, use_mock=False, _cache_version="v2"):
    d = github_api.get_github_actions_data(user, token)
    if not d:
        if use_mock:
            st.warning("Actions API limits/errors reached. Using mock data (Dev/Test mode).")
            d = github_api.get_mock_actions_data(user)
        else:
            return None
    return d

data = load_data(username if username else "devanshi14malhotra", effective_github_token or None, use_mock_data)

# Show token warning only if no token is available from ANY source (env, secrets, sidebar)
if not effective_github_token and not _configured_github_tokens:
    st.info(
        "No server-side GitHub token found. GitHub data uses lower anonymous rate limits. "
        "Add a token in Streamlit secrets or paste your own token in the sidebar."
    )

# Ensure data is not None
if data is None:
    if effective_github_token or _configured_github_tokens:
        _err_type = "api_error"
        _err_type_msg = "GitHub is temporarily unavailable. Check the configured token or try again."
    else:
        _err_type = "rate_limit"
        _err_type_msg = "GitHub API rate limit reached — add a token in the sidebar or configure the server-side token pool."

    _err_svg = draw_error_card(_err_type, username=username if username else "user")

    st.error(f"⚠️ **Could not load GitHub data.** {_err_type_msg}")
    st.markdown(
        f'<div style="max-width:450px; margin-top:12px;">{_err_svg}</div>',
        unsafe_allow_html=True
    )
    st.info("💡 Add a GitHub token in the sidebar or configure the server-side token pool.")
    st.stop()


# Ensure backward compatibility with old cached data
if "top_repos" not in data:
    data["top_repos"] = []

# Initialize other missing fields with defaults
data.setdefault("username", username if username else "devanshi14malhotra")
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

# Add font override everywhere it is consumed so all renderers see the same font.
if font_override:
    current_theme_opts["font_family"] = font_override
    if custom_colors:
        custom_colors = {**custom_colors, "font_family": font_override}
    else:
        custom_colors = {"font_family": font_override}


tab14, tab1, tab2, tab3, tab4, tab5, tab12, tab13, tab15, tab16, tab10, tab8, tab9, tab6, tab7, tab11 = st.tabs(TAB_NAMES)

def show_code_area(code_content, label="Markdown Code"):
    st.markdown(f"**{label}** (Copy below)")
    st.text_area(label, value=code_content, height=100, label_visibility="collapsed")


def render_embedded_html(html_content: str, *, height: int) -> None:
    """Render embedded HTML in an iframe using a data URL.

    Streamlit deprecates st.components.v1.html after 2026-06-01.
    """
    # Use Streamlit components to render arbitrary HTML safely.
    # `components.html` creates an isolated iframe and supports inline scripts/styles.
    components.html(html_content, height=height, scrolling=True)

def render_tab(svg_bytes, endpoint, username, selected_theme, custom_colors, hide_params=None, code_template=None, excluded_languages=None, output_format="Markdown", font_override=None, extra_params=None):
    if font_override:
        font_style = _shared_get_svg_font_style(font_override)
        if font_style and "<svg" in svg_bytes:
            svg_open = svg_bytes.find(">")
            if svg_open != -1:
                svg_bytes = (
                    svg_bytes[: svg_open + 1]
                    + f"<defs><style type=\"text/css\"><![CDATA[{font_style}]]></style></defs>"
                    + svg_bytes[svg_open + 1 :]
                )

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
        filename_prefix_safe = f"{endpoint}_{username}"

        render_embedded_html(f"""
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
                const parts = vb.split(/[\\s,]+/);
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

                if (format === 'jpeg') {{
                    ctx.fillStyle = '#ffffff';
                    ctx.fillRect(0, 0, canvas.width, canvas.height);
                }}

                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

                canvas.toBlob(function(blob) {{
                    const link = document.createElement('a');
                    link.download = '{filename_prefix_safe}' + (format === 'jpeg' ? '.jpeg' : '.png');
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

        # Handle theme: for custom themes, extract colors and send as params instead of theme name
        # This ensures the API receives actual color values for unknown custom themes
        if selected_theme != "Default":
            if selected_theme in CUSTOM_THEMES:
                # Custom theme: send individual color params instead of theme name
                custom_theme_data = CUSTOM_THEMES[selected_theme]
                for color_key in ["bg_color", "border_color", "title_color", "text_color", "icon_color"]:
                    if color_key in custom_theme_data:
                        color_val = custom_theme_data[color_key]
                        params.append(f"{color_key}={color_val.replace('#', '')}")
            else:
                # Predefined theme: send theme name
                params.append(f"theme={selected_theme}")
        
        # Add custom color overrides from the "Customize Colors" section
        for k, v in custom_colors.items():
            params.append(f"{k}={v.replace('#', '')}")

        if extra_params:
            for key, value in extra_params.items():
                if value is None or value == "":
                    continue
                if isinstance(value, bool):
                    if value:
                        params.append(f"{key}=true")
                    continue
                params.append(f"{key}={str(value).replace('#', '')}")
        
        # Add exclude parameter for languages endpoint
        if excluded_languages and endpoint == "languages":
            # Remove spaces and add to params
            params.append(f"exclude={excluded_languages.replace(' ', '')}")

        query_str = "&".join(params)
        if query_str:
            query_str = "?" + query_str
            url = f"https://gitcanvas-api.vercel.app/api/{endpoint}{query_str}&username={username}"
        else:
            url = f"https://gitcanvas-api.vercel.app/api/{endpoint}?username={username}"
        
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
        # Compact layout toggle (Issue #164)
    compact_layout = st.checkbox("📐 Compact Layout", value=False, help="Slim 300x120 card — fit multiple cards in one README row")

    # Backward-compatible call: support generators that may not yet accept `compact`
    try:
        svg_bytes = stats_card.draw_stats_card(
            data,
            selected_theme,
            show_ops,
            custom_colors,
            animations_enabled,
            compact=compact_layout,
        )
    except TypeError as e:
        if "unexpected keyword argument 'compact'" not in str(e):
            raise
        svg_bytes = stats_card.draw_stats_card(
            data,
            selected_theme,
            show_ops,
            custom_colors,
            animations_enabled,
        )
    render_tab(svg_bytes, "stats", username, selected_theme, custom_colors, hide_params=show_ops, code_template=f"[![{username}'s Stats]({{url}})](https://github.com/{{username}})", output_format=output_format, font_override=font_override)
    
    # Prepare the SVG string from your generator
    # Use real contribution data already loaded (last 30 days) - no extra API call needed
    _contribs = data.get("contributions", [])
    spark_data = [c.get("count", 0) for c in _contribs[-30:]] if _contribs else []
    theme_color = current_theme_opts.get("title_color", "#58a6ff")
    spark_svg = sparkline.draw_sparkline(spark_data, theme_color)

    st.markdown("---")
    st.subheader("30-Day Activity Sparkline")

    spark_col1, spark_col2 = st.columns([1.5, 1])

    with spark_col1:
        # We wrap it in a component so the animations and styles actually trigger
        render_embedded_html(f"""
            <div style="background: {current_theme_opts.get('bg_color', '#0d1117')}; border-radius: 12px; border: 1px solid {current_theme_opts.get('border_color', '#30363d')}; overflow: hidden; position: relative; margin-bottom: 5px;">
                <!-- Corner Accents -->
                <div style="position: absolute; top: 0; left: 0; width: 10px; height: 10px; border-top: 2px solid {theme_color}; border-left: 2px solid {theme_color};"></div>
                <div style="position: absolute; top: 0; right: 0; width: 10px; height: 10px; border-top: 2px solid {theme_color}; border-right: 2px solid {theme_color};"></div>
                
                <!-- Header Bar -->
                <div style="color: {theme_color}; font-family: 'Courier New', monospace; font-size: 10px; font-weight: bold; letter-spacing: 1px; padding: 12px 15px 5px 15px; opacity: 0.8; display: flex; justify-content: space-between; border-bottom: 1px dashed {current_theme_opts.get('border_color', '#30363d')}44;">
                    <span>SYSTEM_ACTIVITY_MONITOR // {data.get('username', username).upper()}</span>
                    <span>STATUS: LIVE_FEED</span>
                </div>
                
                <!-- Graph Area (Edge to Edge) -->
                <div style="padding-top: 8px;">
                    {spark_svg}
                </div>
            </div>
        """, height=180)

    with spark_col2:
        st.subheader("Integration")
        _spark_params = []
        if selected_theme != "Default":
            _spark_params.append(f"theme={selected_theme}")
        for k, v in custom_colors.items():
            _spark_params.append(f"{k}={v.replace('#', '')}")
        _spark_qs = ("?" + "&".join(_spark_params)) if _spark_params else ""
        _spark_sep = "&" if _spark_qs else "?"
        _spark_url = f"https://gitcanvas-api.vercel.app/api/sparkline{_spark_qs}{_spark_sep}username={data.get('username', username)}"

        if output_format == "HTML":
            _spark_code = f'<img src="{_spark_url}" alt="30-Day Activity Sparkline"/>'
        else:
            _spark_code = f"![30-Day Activity Sparkline]({_spark_url})"

        _code_label = "HTML Code" if output_format == "HTML" else "Markdown Code"
        show_code_area(_spark_code, label=_code_label)


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
    try:
        svg_bytes = lang_card.draw_lang_card(
            data,
            selected_theme,
            custom_colors,
            excluded_languages=excluded_languages,
            animations_enabled=animations_enabled,
        )
    except TypeError as e:
        # Backward compatibility for deployments where lang_card.py does not yet
        # accept the animations_enabled argument.
        if "unexpected keyword argument 'animations_enabled'" not in str(e):
            raise
        svg_bytes = lang_card.draw_lang_card(
            data,
            selected_theme,
            custom_colors,
            excluded_languages=excluded_languages,
        )
    render_tab(svg_bytes, "languages", username, selected_theme, custom_colors, code_template="![Top Langs]({url})", excluded_languages=excluded_languages_str, output_format=output_format, font_override=font_override)

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
    
    compact_repo = st.checkbox("📐 Compact Layout", value=False, help="Slim 300px card — fit multiple cards in one README row", key="compact_repo")
    svg_bytes = repo_card.draw_repo_card(filtered_data, selected_theme, custom_colors, sort_by=sort_by, limit=repo_limit, compact=compact_repo, animations_enabled=animations_enabled)
    render_tab(svg_bytes, "repos", username, selected_theme, custom_colors, code_template="![Top Repos]({url})", output_format=output_format, font_override=font_override)

with tab4:
    st.subheader("Contribution Graph")
    st.caption(f"Theme: **{selected_theme}**")
    if selected_theme == "Gaming": st.caption("🐍 Snake Mode: The snake grows as it eats commits.")
    elif selected_theme == "Space": st.caption("🚀 Space Mode: Spaceship traversing the contribution galaxy.")
    elif selected_theme == "Marvel": st.caption("💎 Infinity Mode: Collecting Stones based on activity.")
    elif selected_theme == "Ocean": st.caption("🌊 Ocean Mode: Fish and bubbles swim through underwater contributions.")
    elif selected_theme == "Glass": st.caption("💎 GlassMorphism: Translucent Glass based theme card.")

    # Date Range Selector
    from datetime import datetime, timedelta, timezone
    today = datetime.now(timezone.utc).date()
    
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
    render_tab(svg_bytes, "contributions", username, selected_theme, custom_colors, code_template="![Contributions]({url})", output_format=output_format, font_override=font_override)

with tab5:
    st.subheader("GitHub Streak")
    st.caption("🔥 Track your contribution streaks! Shows current consecutive days and your all-time longest streak.")
    
    svg_bytes = streak_card.draw_streak_card(data, selected_theme, custom_colors, animations_enabled=animations_enabled)
    render_tab(svg_bytes, "streak", username, selected_theme, custom_colors, code_template="![GitHub Streak]({url})", output_format=output_format, font_override=font_override)

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
                    selected_platforms,
                    animations_enabled=animations_enabled
                )
                b64 = base64.b64encode(svg_bytes.encode('utf-8')).decode("utf-8")
                st.markdown(f'<img src="data:image/svg+xml;base64,{b64}" style="max-width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-radius: 10px;"/>', unsafe_allow_html=True)
            except requests.RequestException as e:
                st.error(f"Network error rendering social card: {type(e).__name__}. Check your internet connection.")
            except (KeyError, ValueError, TypeError) as e:
                st.error(f"Invalid data while rendering social card: {type(e).__name__}. The API may have returned unexpected data.")
            except Exception as e:
                st.error(f"Unexpected error rendering social card: {type(e).__name__}. Please try again.")
        
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

# AI ROAST & SUMMARY TAB
with tab8:
    st.subheader("🔥 AI Profile Roast")

    if not _settings.has_any_llm_key:
        st.warning(
            "No **OPENAI_API_KEY** or **GEMINI_API_KEY** in the environment: the AI Roast tab uses "
            "built-in fallback lines only until you add a provider key."
        )

    st.markdown("Let AI roast your GitHub profile with humor!")
    
    if username:
        render_roast_widget(username, profile_data=data)
    else:
        st.warning("Please enter a GitHub username in the sidebar.")
    
    st.markdown("---")
    st.subheader("🧠 AI Description Summary")
    st.caption("Generate a short, theme-aware summary of this GitHub profile.")

    tone_col, button_col = st.columns([1.2, 1])
    with tone_col:
        description_tone = st.selectbox(
            "Tone",
            ["professional", "funny", "creative"],
            index=0,
            key="ai_description_tone",
        )

    with button_col:
        if st.button("Generate AI Description", type="primary", use_container_width=True, key="generate_ai_description"):
            with st.spinner("Generating AI description..."):
                result = generate_github_description(data, selected_theme, tone=description_tone)
                st.session_state["ai_description_result"] = {
                    **result,
                    "username": username,
                    "theme": selected_theme,
                    "tone": description_tone,
                }

    current_description = st.session_state.get("ai_description_result")
    if (
        current_description
        and current_description.get("username") == username
        and current_description.get("theme") == selected_theme
        and current_description.get("tone") == description_tone
    ):
        description_text = current_description.get("description", "")
        st.markdown("**Generated Description**")
        st.write(description_text)

        source = current_description.get("source", "fallback")
        st.caption(f"Source: {source} • Tone: {description_tone} • Theme: {selected_theme}")

        st.download_button(
            label="💾 Save Description",
            data=description_text,
            file_name=f"{username}_{selected_theme}_description.txt",
            mime="text/plain",
            use_container_width=False,
            key="save_ai_description",
        )
    else:
        st.info("Click **Generate AI Description** to create a summary for the current theme.")

# AI COMPLIMENT TAB
with tab9:
    st.subheader("✨ AI Profile Compliment")

    if not _settings.has_any_llm_key:
        st.warning(
            "No **OPENAI_API_KEY** or **GEMINI_API_KEY** in the environment: the AI Compliment tab uses "
            "built-in fallback lines only until you add a provider key."
        )

    st.markdown("Let AI celebrate and compliment your GitHub profile!")
    
    if username:
        render_compliment_widget(username, profile_data=data)
    else:
        st.warning("Please enter a GitHub username in the sidebar.")

with tab10:
    st.subheader("Recent Activity")
    st.markdown("Shows your last 3 PR or Issue events from GitHub.")

    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.caption("Theme: **{}**".format(selected_theme))
        try:
            # Pass selected_theme string
            svg_bytes = recent_activity_card.draw_recent_activity_card(
                {"username": username}, selected_theme, custom_colors, token=effective_github_token, animations_enabled=animations_enabled
            )
        except requests.RequestException as e:
            st.error(f"Network error fetching recent activity: {type(e).__name__}. Check your connection and try again.")
            svg_bytes = recent_activity_card._render_svg_lines(["Network Error", "Unable to fetch data"], THEMES.get(selected_theme, THEMES['Default']))
        except (KeyError, ValueError, TypeError) as e:
            st.error(f"Invalid data format from GitHub API: {type(e).__name__}. Please try again.")
            svg_bytes = recent_activity_card._render_svg_lines(["Data Format Error", "Unable to parse response"], THEMES.get(selected_theme, THEMES['Default']))
        except Exception as e:
            st.error(f"Unexpected error rendering recent activity: {type(e).__name__}. Please try again.")
            svg_bytes = recent_activity_card._render_svg_lines(["Rendering Error", "Please try again"], THEMES.get(selected_theme, THEMES['Default']))

        b64 = base64.b64encode(svg_bytes.encode('utf-8')).decode("utf-8")
        st.markdown(f'<img src="data:image/svg+xml;base64,{b64}" style="max-width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-radius: 10px;"/>', unsafe_allow_html=True)

    with col2:
        st.subheader("Integration")
        params = []
        if selected_theme != "Default": params.append(f"theme={selected_theme}")
        for k, v in custom_colors.items():
            params.append(f"{k}={v.replace('#', '')}")
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

with tab11:
    st.subheader("✨ Visual Elements")
    st.markdown("Add emojis, GIFs, or stickers to your canvas")

    # --- Canvas Input Section ---
    col_input1, col_input2, col_input3 = st.columns([2, 2, 1.5])
    
    with col_input1:
        element_type = st.selectbox(
            "Choose element type",
            ["Emoji", "GIF", "Sticker"]
        )
    
    with col_input2:
        value = st.text_input(
            "Enter value",
            placeholder="🔥 or https://gif-url"
        )
    
    with col_input3:
        add_button = st.button("Add to Canvas", use_container_width=True)
    
    # Add element to canvas
    if add_button:
        if value:
            if element_type == "Emoji":
                svg = emoji_element(value)
            elif element_type == "GIF":
                svg = gif_element(value)
            else:
                svg = sticker_element(value)
            
            st.session_state["canvas"].append(svg)
            st.session_state["canvas_elements_metadata"].append({
                "type": element_type,
                "value": value
            })
            st.success(f"✅ {element_type} added to canvas!")
        else:
            st.error("❌ Please enter a value")

    st.markdown("---")

    # --- Canvas Display & Export Section ---
    if st.session_state["canvas"]:
        st.subheader("Canvas Preview")
        
        # Generate composite canvas
        canvas_svg = create_composite_canvas(
            st.session_state["canvas"],
            bg_color=current_theme_opts.get("bg_color", "#0d1117"),
            padding=20
        )
        
        # Display canvas
        col_display, col_actions = st.columns([2, 1])
        
        with col_display:
            b64 = base64.b64encode(canvas_svg.encode('utf-8')).decode("utf-8")
            st.markdown(
                f'<img src="data:image/svg+xml;base64,{b64}" style="max-width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-radius: 10px;"/>',
                unsafe_allow_html=True
            )
        
        with col_actions:
            st.markdown("**Canvas Actions**")
            
            # SVG Download
            st.download_button(
                label="⬇️ Download SVG",
                data=canvas_svg.encode("utf-8"),
                file_name=f"canvas_{username}.svg",
                mime="image/svg+xml",
                use_container_width=True
            )
            
            # PNG & JPEG Download
            svg_b64 = base64.b64encode(canvas_svg.encode("utf-8")).decode("utf-8")
            filename_prefix_safe = json.dumps(f"canvas_{username}")
            
            render_embedded_html(f"""
            <div style="display:flex; flex-direction:column; gap:6px; margin-top:4px;">
                <button onclick="downloadCanvasAs('png')" style="
                    width:100%; padding:8px; font-size:12px; cursor:pointer;
                    background:#1a1a2e; color:white; border:1px solid #444;
                    border-radius:6px; font-weight: bold;">
                    ⬇️ PNG
                </button>
                <button onclick="downloadCanvasAs('jpeg')" style="
                    width:100%; padding:8px; font-size:12px; cursor:pointer;
                    background:#1a1a2e; color:white; border:1px solid #444;
                    border-radius:6px; font-weight: bold;">
                    ⬇️ JPEG
                </button>
            </div>

            <script>
            function downloadCanvasAs(format) {{
                const svgText = atob('{svg_b64}');
                const parser = new DOMParser();
                const svgDoc = parser.parseFromString(svgText, 'image/svg+xml');
                const svgEl = svgDoc.documentElement;

                const vb = svgEl.getAttribute('viewBox');
                let w = 600, h = 400;
                if (vb) {{
                    const parts = vb.split(/[\\s,]+/);
                    w = parseFloat(parts[2]) || 600;
                    h = parseFloat(parts[3]) || 400;
                }}

                const blob = new Blob([svgText], {{type: 'image/svg+xml'}});
                const url = URL.createObjectURL(blob);
                const img = new Image();
                img.onload = function() {{
                    const SCALE = 2;
                    const canvas = document.createElement('canvas');
                    canvas.width = w * SCALE;
                    canvas.height = h * SCALE;
                    const ctx = canvas.getContext('2d');

                    if (format === 'jpeg') {{
                        ctx.fillStyle = '#ffffff';
                        ctx.fillRect(0, 0, canvas.width, canvas.height);
                    }}

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
            """, height=120)
        
        st.markdown("---")
        st.subheader("Embed Code")
        
        # Generate embed URLs/code
        embed_col1, embed_col2 = st.columns(2)
        
        with embed_col1:
            st.markdown("**Markdown Code**")
            embed_code = f"![Canvas - {username}](https://your-image-hosting.com/canvas_{username}.svg)"
            st.text_area("Copy this code:", value=embed_code, height=60, label_visibility="collapsed", key="canvas_markdown_code")
        
        with embed_col2:
            st.markdown("**HTML Code**")
            html_code = f'<img src="https://your-image-hosting.com/canvas_{username}.svg" alt="Canvas - {username}"/>'
            st.text_area("Copy this code:", value=html_code, height=60, label_visibility="collapsed", key="canvas_html_code")
        
        st.info("💡 **Note:** Download your canvas SVG above and host it on GitHub, Imgur, or any image hosting service, then use the embed code above.")
        
        st.markdown("---")
        st.subheader("Canvas Contents")
        
        # Show list of elements
        for idx, metadata in enumerate(st.session_state["canvas_elements_metadata"]):
            col_item, col_remove = st.columns([4, 1])
            with col_item:
                st.caption(f"**{metadata['type']}** • {metadata['value']}")
            with col_remove:
                if st.button("🗑️", key=f"remove_{idx}", help="Remove this element"):
                    st.session_state["canvas"].pop(idx)
                    st.session_state["canvas_elements_metadata"].pop(idx)
                    st.rerun()
        
        # Clear canvas button
        if st.button("🧹 Clear All Canvas", use_container_width=True):
            st.session_state["canvas"] = []
            st.session_state["canvas_elements_metadata"] = []
            st.rerun()
    else:
        st.info("👆 Add elements to your canvas to get started. You can mix emojis, GIFs, and stickers!")

# TAB 12: Trophy Card
with tab12:
    st.subheader("🏆 GitHub Trophy")
    st.markdown("Display your achievements including stars, forks, followers, and repository quality tier!")
    
    # Get created_at from GitHub API data if available
    trophy_data = data.copy()
    # Try to get created_at from user data if available
    if "created_at" not in trophy_data:
        # Add a default for testing
        trophy_data["created_at"] = "2010-01-01T00:00:00Z"
    
    svg_bytes = trophy_card.draw_trophy_card(trophy_data, selected_theme, custom_colors, animations_enabled=animations_enabled)
    render_tab(svg_bytes, "trophy", username, selected_theme, custom_colors, code_template="![GitHub Trophy]({url})", output_format=output_format, font_override=font_override)

# TAB 13: Achievement Room Card
with tab13:
    st.subheader("🏆 Achievement Room")
    st.markdown("Showcase your GitHub milestones with dynamic achievement badges!")
    
    svg_bytes = achievement_card.draw_achievement_card(data, selected_theme, custom_colors, animations_enabled=animations_enabled)
    render_tab(svg_bytes, "achievements", username, selected_theme, custom_colors, code_template="![Achievement Room]({url})", output_format=output_format, font_override=font_override)

    # ── NEW: Theme Gallery Tab (Issue #162) ──────────────────────────────────
with tab14:
    chosen_theme = render_theme_gallery(all_themes, selected_theme, font_override=font_override)
    if chosen_theme:
        st.session_state["gallery_selected_theme"] = chosen_theme
        st.rerun()

with tab15:
    st.subheader("📅 Yearly Calendar Heatmap")
    st.caption("A 53-week contribution heatmap with selectable intensity mapping and custom colors.")

    def _heatmap_theme_palette(theme_name: str, theme: dict) -> list[str]:
        return contrib_card._palette_from_theme(theme_name, theme)

    from datetime import datetime, timedelta, timezone
    today = datetime.now(timezone.utc).date()

    control_col1, control_col2 = st.columns(2)
    with control_col1:
        intensity_mode = st.selectbox(
            "Intensity mode",
            ["auto", "none", "low", "medium", "high"],
            index=0,
            key="heatmap_intensity_mode",
        )
    with control_col2:
        period = st.selectbox(
            "Period",
            ["Last Year", "Current Year", "Custom Range"],
            index=0,
            key="heatmap_period",
        )

    heatmap_default_colors = _heatmap_theme_palette(selected_theme, current_theme_opts)
    heatmap_color_cols = st.columns(5)
    heatmap_colors = {}
    for index, column in enumerate(heatmap_color_cols):
        label = ["None", "Low", "Medium", "High", "Max"][index]
        session_key = f"heatmap_level_{selected_theme}_{index}"
        with column:
            heatmap_colors[f"level_{index}"] = st.color_picker(
                f"Level {index} ({label})",
                value=heatmap_default_colors[index],
                key=session_key,
            )

    heatmap_date_range = None
    if period == "Current Year":
        heatmap_date_range = {
            "start": datetime(today.year, 1, 1).date().strftime("%Y-%m-%d"),
            "end": today.strftime("%Y-%m-%d"),
        }
    elif period == "Custom Range":
        start_col, end_col = st.columns(2)
        with start_col:
            custom_start = st.date_input("Start Date", value=today - timedelta(days=180), key="heatmap_custom_start")
        with end_col:
            custom_end = st.date_input("End Date", value=today, key="heatmap_custom_end")
        heatmap_date_range = {
            "start": custom_start.strftime("%Y-%m-%d"),
            "end": custom_end.strftime("%Y-%m-%d"),
        }
    else:
        heatmap_date_range = {
            "start": (today - timedelta(days=365)).strftime("%Y-%m-%d"),
            "end": today.strftime("%Y-%m-%d"),
        }

    svg_bytes = contrib_card.draw_calendar_heatmap_card(
        data,
        selected_theme,
        custom_colors,
        date_range=heatmap_date_range,
        intensity_mode=intensity_mode,
        intensity_colors=heatmap_colors,
        period_label=period,
        animations_enabled=animations_enabled,
    )

    render_tab(
        svg_bytes,
        "calendar-heatmap",
        username,
        selected_theme,
        custom_colors,
        code_template="![Calendar Heatmap]({url})",
        output_format=output_format,
        extra_params={
            "period": period,
            "intensity_mode": intensity_mode,
            **heatmap_colors,
            "start_date": heatmap_date_range["start"],
            "end_date": heatmap_date_range["end"],
        },
    )

with tab16:
    st.subheader("⚙️ GitHub Actions")
    st.caption("Workflow run totals, success rate, and recent runs from GitHub Actions.")

    if not effective_github_token and not _configured_github_tokens:
        st.warning(
            "A GitHub token is required for live Actions data. Enable mock data for a local preview, or add a token in the sidebar."
        )

    actions_data = load_actions_data(username if username else "devanshi14malhotra", effective_github_token or None, use_mock_data)

    if actions_data:
        col1, col2 = st.columns([1.5, 1])

        with col1:
            svg_bytes = actions_card.draw_actions_card(actions_data, selected_theme, custom_colors, animations_enabled=animations_enabled)
            b64 = base64.b64encode(svg_bytes.encode("utf-8")).decode("utf-8")
            st.markdown(
                f'<img src="data:image/svg+xml;base64,{b64}" style="max-width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-radius: 10px;"/>',
                unsafe_allow_html=True,
            )

        with col2:
            st.subheader("API Usage")
            st.caption("This endpoint requires an Authorization header, so it cannot be embedded as a normal public README image URL.")
            example_url = f"https://gitcanvas-api.vercel.app/api/actions?username={username}&theme={selected_theme}"
            curl_example = (
                "curl -H \"Authorization: Bearer YOUR_GITHUB_TOKEN\" "
                f'"{example_url}"'
            )
            show_code_area(curl_example, label="Curl Example")

            st.divider()
            st.subheader("🤖 Automation")
            st.caption("Use GitHub Actions to automatically update this card in your README every day.")
            
            if st.button("Generate Workflow YAML"):
                workflow_yaml = f"""name: Update GitCanvas Actions Stats
on:
  schedule:
    - cron: '0 0 * * *' # Every day at midnight
  workflow_dispatch: # Allow manual trigger

jobs:
  update-metrics:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3

      - name: Fetch GitCanvas SVG
        run: |
          curl -H "Authorization: Bearer ${{{{ secrets.GITCANVAS_TOKEN }}}}" \\
          "https://gitcanvas-api.vercel.app/api/actions?username={username}&theme={selected_theme}" \\
          -o github-actions-stats.svg

      - name: Commit and Push Changes
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add github-actions-stats.svg
          git commit -m "Update GitHub Actions stats [skip ci]" || echo "No changes to commit"
          git push
"""
                st.code(workflow_yaml, language="yaml")
                st.info("💡 **Setup Instructions:**\n1. Create `.github/workflows/gitcanvas.yml` in your repo.\n2. Paste the code above.\n3. Add a secret named `GITCANVAS_TOKEN` in your repo settings with a Classic Personal Access Token (repo scope).")
    else:
        st.warning("No GitHub Actions data could be loaded for this account.")
