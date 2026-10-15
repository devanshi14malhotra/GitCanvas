"""
AI Roast Widget for Streamlit
Add this to your GitCanvas Streamlit app
"""

import streamlit as st
import requests
from typing import Any
from ai.ai_roast_service import generate_profile_roast
from utils.github_utils import fetch_github_stats


def _normalize_profile_data(profile_data: dict[str, Any] | None, username: str) -> dict[str, Any]:
    """Normalize profile shape so AI roast service always gets expected keys."""
    base: dict[str, Any] = {
        "username": username,
        "public_repos": 0,
        "total_commits": 0,
        "top_languages": [],
    }
    if not profile_data:
        return base

    normalized = dict(base)
    normalized["username"] = profile_data.get("username") or profile_data.get("login") or username
    normalized["public_repos"] = profile_data.get("public_repos", 0)
    normalized["total_commits"] = profile_data.get("total_commits", 0)

    raw_langs = profile_data.get("top_languages", [])
    langs: list[dict[str, Any]] = []
    for entry in raw_langs:
        if isinstance(entry, dict):
            name = entry.get("name")
            if name:
                langs.append({"name": name, "count": entry.get("count", 0)})
        elif isinstance(entry, (list, tuple)) and entry:
            langs.append({"name": str(entry[0]), "count": entry[1] if len(entry) > 1 else 0})
    normalized["top_languages"] = langs
    return normalized


def render_roast_widget(username: str, profile_data: dict[str, Any] | None = None):
    """
    Render the AI Roast widget in Streamlit
    
    Args:
        username: GitHub username to roast
    """
    # Custom CSS for the widget
    st.markdown("""
    <style>
    .roast-widget {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 24px;
        color: white;
        margin: 20px 0;
    }
    .roast-header {
        text-align: center;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .roast-subtitle {
        text-align: center;
        font-size: 14px;
        opacity: 0.9;
        margin-bottom: 20px;
    }
    .roast-text {
        background: rgba(255, 255, 255, 0.15);
        border-left: 4px solid #ffd700;
        border-radius: 8px;
        padding: 20px;
        font-size: 20px;
        font-weight: 500;
        font-style: italic;
        margin: 20px 0;
        text-align: center;
    }
    .roast-stats {
        display: flex;
        justify-content: center;
        gap: 30px;
        margin-top: 20px;
        padding-top: 20px;
        border-top: 1px solid rgba(255, 255, 255, 0.2);
    }
    .stat {
        text-align: center;
    }
    .stat-label {
        font-size: 12px;
        opacity: 0.8;
        text-transform: uppercase;
    }
    .stat-value {
        font-size: 16px;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Widget container
    with st.container():
        st.markdown('<div class="roast-widget">', unsafe_allow_html=True)
        
        # Header
        st.markdown('<div class="roast-header">🔥 AI Profile Roast</div>', unsafe_allow_html=True)
        st.markdown('<div class="roast-subtitle">Let AI roast your GitHub profile</div>', unsafe_allow_html=True)
        
        # Initialize session state
        if 'roast_data' not in st.session_state:
            st.session_state.roast_data = None
        
        # Generate button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🎭 Generate Roast", use_container_width=True, type="primary"):
                with st.spinner("🔥 Cooking up a roast..."):
                    try:
                        # Reuse already loaded profile data first to avoid rate-limit failures.
                        source_profile = _normalize_profile_data(profile_data, username)
                        if source_profile.get("total_commits", 0) <= 0 and not source_profile.get("top_languages"):
                            fetched_profile = fetch_github_stats(username)
                            if fetched_profile:
                                source_profile = _normalize_profile_data(fetched_profile, username)

                        if source_profile:
                            # Generate roast
                            roast_result = generate_profile_roast(source_profile)
                            st.session_state.roast_data = {
                                'roast': roast_result['roast'],
                                'profile': source_profile,
                                'source': roast_result['source']
                            }
                        else:
                            st.error("Failed to fetch GitHub profile data")
                    except requests.RequestException as e:
                        st.error(f"Network error: {type(e).__name__}. Check your connection and try again.")
                    except (KeyError, ValueError, TypeError) as e:
                        st.error(f"Invalid profile data received: {type(e).__name__}. The API may have returned unexpected data.")
                    except Exception as e:
                        st.error(f"Unexpected error generating roast: {type(e).__name__}. Please try again.")
        
        # Display roast if available
        if st.session_state.roast_data:
            roast_text = st.session_state.roast_data['roast']
            profile = st.session_state.roast_data['profile']
            
            # Roast display
            st.markdown(f'<div class="roast-text">"{roast_text}"</div>', unsafe_allow_html=True)
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 New Roast", use_container_width=True):
                    with st.spinner("🔥 Generating new roast..."):
                        try:
                            roast_result = generate_profile_roast(profile)
                            st.session_state.roast_data['roast'] = roast_result['roast']
                            st.rerun()
                        except requests.RequestException as e:
                            st.error(f"Network error: {type(e).__name__}. Unable to generate new roast.")
                        except (KeyError, ValueError, TypeError) as e:
                            st.error(f"Data error: {type(e).__name__}. Unable to generate roast.")
                        except Exception as e:
                            st.error(f"Unexpected error: {type(e).__name__}. Please try again.")
            
            with col2:
                if st.button("📋 Copy", key=f"roast_copy_{username}", use_container_width=True):
                    st.write("Roast copied to clipboard!")
                    # Note: Direct clipboard access limited in Streamlit
                    st.code(roast_text, language=None)
            
            with col3:
                st.download_button(
                    label="💾 Save",
                    data=roast_text,
                    file_name=f"{username}_roast.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            # Profile stats
            top_langs = [lang['name'] for lang in profile.get('top_languages', [])[:3]]
            langs_str = ', '.join(top_langs) if top_langs else 'N/A'
            
            st.markdown(f"""
            <div class="roast-stats">
                <div class="stat">
                    <div class="stat-label">Top Languages</div>
                    <div class="stat-value">{langs_str}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Total Commits</div>
                    <div class="stat-value">{profile.get('total_commits', 'N/A')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show source
            st.caption(f"✨ Generated using {st.session_state.roast_data['source']}")
        
        st.markdown('</div>', unsafe_allow_html=True)


# Example usage
if __name__ == "__main__":
    st.set_page_config(page_title="AI Profile Roast", page_icon="🔥")
    
    st.title("🔥 AI GitHub Profile Roast")
    
    username = st.text_input("Enter GitHub username:", value="torvalds")
    
    if username:
        render_roast_widget(username)
