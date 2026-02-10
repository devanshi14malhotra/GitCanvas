import streamlit as st  # type: ignore
import base64
import os
from dotenv import load_dotenv  # type: ignore
from roast_widget_streamlit import render_roast_widget  # type: ignore
from generators import stats_card, lang_card, contrib_card, badge_generator, recent_activity_card  # type: ignore
from utils import github_api  # type: ignore
from themes.styles import THEMES  # type: ignore

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
    selected_theme = st.selectbox("Select Theme", list(THEMES.keys()))
    
    # Customization Expander
    # Ensure custom_colors exists even if the expander isn't opened
    custom_colors = {}
    with st.expander("Customize Colors", expanded=False):
        st.caption("Override theme defaults")
        default_theme = THEMES.get(selected_theme, THEMES["Default"]).copy() # Copy to avoid mutating global
        
        # Helper to get color safely
        def get_col(key): return default_theme.get(key, "#000000")
        
        custom_bg = st.color_picker("Background", value=get_col("bg_color"))
        custom_title = st.color_picker("Title Text", value=get_col("title_color"))
        custom_text = st.color_picker("Body Text", value=get_col("text_color"))
        custom_border = st.color_picker("Border", value=get_col("border_color"))
        
        # Build custom colors dict if changed
        custom_colors = {}
        if custom_bg != get_col("bg_color"): custom_colors["bg_color"] = custom_bg
        if custom_title != get_col("title_color"): custom_colors["title_color"] = custom_title
        if custom_text != get_col("text_color"): custom_colors["text_color"] = custom_text
        if custom_border != get_col("border_color"): custom_colors["border_color"] = custom_border

    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
    github_token = st.text_input("GitHub Token (optional)", type="password")
        
    st.info("💡 Tip: Use the 'Badges' tab to add your tech stack icons!")

# Data Loading
@st.cache_data
def load_data(user):
    d = github_api.get_live_github_data(user)
    if not d:
        st.warning("Using mock data (API limits).")
        d = github_api.get_mock_data(user)
    return d

data = load_data(username if username else "torvalds")

# Apply custom colors to current theme for python logic
current_theme_opts = THEMES.get(selected_theme, THEMES["Default"]).copy()
if custom_colors:
    current_theme_opts.update(custom_colors)

# --- Layout: Tabs ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Main Stats", "Languages", "Contributions", "Icons & Badges", "🔥 AI Roast", "Recent Activity"])

def show_code_area(code_content, label="Markdown Code"):
    st.markdown(f"**{label}** (Copy below)")
    st.text_area(label, value=code_content, height=100, label_visibility="collapsed")

def render_tab(svg_bytes, endpoint, username, selected_theme, custom_colors, hide_params=None, code_template=None, excluded_languages=None):
    col1, col2 = st.columns([1.5, 1])
    with col1:
        # Render SVG
        b64 = base64.b64encode(svg_bytes.encode('utf-8')).decode("utf-8")
        st.markdown(f'<img src="data:image/svg+xml;base64,{b64}" style="max-width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-radius: 10px;"/>', unsafe_allow_html=True)

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
        if code_template:
            code = code_template.format(url=url, username=username)
        else:
            code = f"![{endpoint.title()}]({url})"

        show_code_area(code)

with tab1:
    st.subheader("Stats Card")
    # Options
    c1, c2, c3, c4 = st.columns(4)
    show_stars = c1.checkbox("Stars", True)
    show_commits = c2.checkbox("Commits", True)
    show_repos = c3.checkbox("Repos", True)
    show_followers = c4.checkbox("Followers", True)

    show_ops = {"stars": show_stars, "commits": show_commits, "repos": show_repos, "followers": show_followers}

    # Render - FIXED: Pass current_theme_opts (dictionary) instead of selected_theme (string)
    svg_bytes = stats_card.draw_stats_card(data, current_theme_opts, show_ops, custom_colors)
    render_tab(svg_bytes, "stats", username, selected_theme, custom_colors, hide_params=show_ops, code_template=f"[![{username}'s Stats]({{url}})](https://github.com/{{username}})")

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
    
    # Generate card with exclusions - FIXED: Pass current_theme_opts
    svg_bytes = lang_card.draw_lang_card(data, current_theme_opts, custom_colors, excluded_languages=excluded_languages)
    render_tab(svg_bytes, "languages", username, selected_theme, custom_colors, code_template="![Top Langs]({url})", excluded_languages=excluded_languages_str)

with tab3:
    st.subheader("Contribution Graph")
    st.caption(f"Theme: **{selected_theme}**")
    if selected_theme == "Gaming": st.caption("🐍 Snake Mode: The snake grows as it eats commits.")
    elif selected_theme == "Space": st.caption("🚀 Space Mode: Spaceship traversing the contribution galaxy.")
    elif selected_theme == "Marvel": st.caption("💎 Infinity Mode: Collecting Stones based on activity.")

    # FIXED: Pass current_theme_opts
    svg_bytes = contrib_card.draw_contrib_card(data, current_theme_opts, custom_colors)
    render_tab(svg_bytes, "contributions", username, selected_theme, custom_colors, code_template="![Contributions]({url})")

with tab4:
    st.subheader("Tech Stack Badges")
    st.markdown("Click detailed settings to customize. Copy the code block to your README.")
    
    col_tools, col_preview = st.columns([2, 1.5])
    
    with col_tools:
        # Badge Settings
        badge_style = st.selectbox("Badge Style", ["for-the-badge", "flat", "flat-square", "plastic", "social"], index=0)
        
        # Categories
        for category, tools in badge_generator.TECH_STACK.items():
            st.markdown(f"**{category}**")
            cols = st.columns(4)
            for i, (tool_name, specs) in enumerate(tools.items()):
                # Checkbox to include
                # If we want a click-to-add flow without rerun, we need session state lists
                # Let's use Multiselect for efficiency or columns of checkboxes
                # A Multiselect for each category is cleaner
                pass
            
            # Better UI: Multi-selects per category
            selected = st.multiselect(f"Select {category}", list(tools.keys()), key=f"sel_{category}")
            if selected:
                # Add to a session state list for the preview? 
                # Actually just rendering them below is fine.
                if "badges" not in st.session_state: st.session_state.badges = []
                # append is tricky with immediate reruns. 
                # Let's just gather all selected options from all multiselects at render time.
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
                # Allow user to override color?
                # For now use default brand color
                all_selected_badges.append((item, conf))
        
        if not all_selected_badges:
            st.info("Select tools from the left to generate badges.")
        else:
            # Render Preview
            md_output = ""
            # Making Global Variable, if user wants to match the theme:   
            should_match = st.checkbox("Match Theme Color", value=False, key="match_theme_global")
            for name, conf in all_selected_badges:
                # Logic to use custom color if user wants consistency?
                # User asked for customization.
                # Let's add a "Override All Colors" checkbox
                
                final_color = conf['color']
                # Using the variable we captured before:
                if should_match:
                    final_color = current_theme_opts['title_color'].replace("#", "")
                
                url = badge_generator.generate_badge_url(name, final_color, conf['logo'], style=badge_style)
                st.markdown(f"![{name}]({url})")
                md_output += f"![{name}]({url}) "
            
            st.markdown("---")
            show_code_area(md_output, label="Badge Code")

# NEW TAB 5: AI ROAST
with tab5:
    st.subheader("🔥 AI Profile Roast")
    st.markdown("Let AI roast your GitHub profile with humor!")
    
    if username:
        render_roast_widget(username)
    else:
        st.warning("Please enter a GitHub username in the sidebar.")

with tab6:
    st.subheader("Recent Activity")
    st.markdown("Shows your last 3 PR or Issue events from GitHub.")

    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.caption("Theme: **{}**".format(selected_theme))
        try:
            # FIXED: Pass current_theme_opts
            svg_bytes = recent_activity_card.draw_recent_activity_card({'username': username}, current_theme_opts, custom_colors, token=github_token)
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
        code = f"![Recent Activity]({url})"
        show_code_area(code)