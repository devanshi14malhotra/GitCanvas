"""
AI Compliment Widget for Streamlit
Add this to your GitCanvas Streamlit app
"""

import streamlit as st
import requests
from typing import Any
from ai.compliment_service import generate_profile_compliment
from utils.github_utils import fetch_github_stats


def _normalize_profile_data(profile_data: dict[str, Any] | None, username: str) -> dict[str, Any]:
    """Normalize profile shape so AI compliment service always gets expected keys."""
    base: dict[str, Any] = {
        "username": username,
        "public_repos": 0,
        "total_commits": 0,
        "top_languages": [],
        "followers": 0,
        "stars": 0,
    }
    if not profile_data:
        return base

    normalized = dict(base)
    normalized["username"] = profile_data.get("username") or profile_data.get("login") or username
    normalized["public_repos"] = profile_data.get("public_repos", 0)
    normalized["total_commits"] = profile_data.get("total_commits", 0)
    normalized["followers"] = profile_data.get("followers", 0)
    normalized["stars"] = profile_data.get("stars", 0)

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


def render_compliment_widget(username: str, profile_data: dict[str, Any] | None = None):
    """
    Render the AI Compliment widget in Streamlit
    
    Args:
        username: GitHub username to compliment
        profile_data: Optional profile data to use
    """
    # Custom CSS for the widget
    st.markdown("""
    <style>
    .compliment-widget {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        border-radius: 16px;
        padding: 24px;
        color: white;
        margin: 20px 0;
    }
    .compliment-header {
        text-align: center;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .compliment-subtitle {
        text-align: center;
        font-size: 14px;
        opacity: 0.9;
        margin-bottom: 20px;
    }
    .compliment-text {
        background: rgba(255, 255, 255, 0.15);
        border-left: 4px solid #fbbf24;
        border-radius: 8px;
        padding: 20px;
        font-size: 20px;
        font-weight: 500;
        font-style: italic;
        margin: 20px 0;
        text-align: center;
    }
    .compliment-stats {
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
        st.markdown('<div class="compliment-widget">', unsafe_allow_html=True)
        
        # Header
        st.markdown('<div class="compliment-header">✨ AI Compliment</div>', unsafe_allow_html=True)
        st.markdown('<div class="compliment-subtitle">Celebrate this amazing GitHub profile</div>', unsafe_allow_html=True)

        compliment_state_key = f"compliment_data_{username}"
        
        # Initialize session state
        if compliment_state_key not in st.session_state:
            st.session_state[compliment_state_key] = None
        
        # Generate button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("⭐ Get Compliment", use_container_width=True, type="primary"):
                with st.spinner("✨ Generating compliment..."):
                    try:
                        # Reuse already loaded profile data first to avoid rate-limit failures.
                        source_profile = _normalize_profile_data(profile_data, username)
                        if source_profile.get("total_commits", 0) <= 0 and not source_profile.get("top_languages"):
                            fetched_profile = fetch_github_stats(username)
                            if fetched_profile:
                                source_profile = _normalize_profile_data(fetched_profile, username)

                        if source_profile:
                            # Generate compliment
                            compliment_result = generate_profile_compliment(source_profile)
                            st.session_state[compliment_state_key] = {
                                'compliment': compliment_result['compliment'],
                                'profile': source_profile,
                                'source': compliment_result['source']
                            }
                        else:
                            st.error("Failed to fetch GitHub profile data")
                    except requests.RequestException as e:
                        st.error(f"Network error: {type(e).__name__}. Check your connection and try again.")
                    except (KeyError, ValueError, TypeError) as e:
                        st.error(f"Invalid profile data received: {type(e).__name__}. The API may have returned unexpected data.")
                    except Exception as e:
                        st.error(f"Unexpected error generating compliment: {type(e).__name__}. Please try again.")
        
        # Display compliment if available
        if st.session_state[compliment_state_key]:
            compliment_text = st.session_state[compliment_state_key]['compliment']
            profile = st.session_state[compliment_state_key]['profile']
            
            # Compliment display
            st.markdown(f'<div class="compliment-text">"{compliment_text}"</div>', unsafe_allow_html=True)
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 New Compliment", use_container_width=True):
                    with st.spinner("✨ Generating new compliment..."):
                        try:
                            compliment_result = generate_profile_compliment(profile)
                            st.session_state[compliment_state_key]['compliment'] = compliment_result['compliment']
                            st.rerun()
                        except requests.RequestException as e:
                            st.error(f"Network error: {type(e).__name__}. Unable to generate new compliment.")
                        except (KeyError, ValueError, TypeError) as e:
                            st.error(f"Data error: {type(e).__name__}. Unable to generate compliment.")
                        except Exception as e:
                            st.error(f"Unexpected error: {type(e).__name__}. Please try again.")
            
            with col2:
                if st.button("📋 Copy", key=f"compliment_copy_{username}", use_container_width=True):
                    st.write("Compliment copied to clipboard!")
                    # Note: Direct clipboard access limited in Streamlit
                    st.code(compliment_text, language=None)
            
            with col3:
                st.download_button(
                    label="💾 Save",
                    data=compliment_text,
                    file_name=f"{username}_compliment.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            # Profile stats
            top_langs = [lang['name'] for lang in profile.get('top_languages', [])[:3]]
            langs_str = ', '.join(top_langs) if top_langs else 'N/A'
            
            st.markdown(f"""
            <div class="compliment-stats">
                <div class="stat">
                    <div class="stat-label">Top Languages</div>
                    <div class="stat-value">{langs_str}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Total Commits</div>
                    <div class="stat-value">{profile.get('total_commits', 'N/A')}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Public Repos</div>
                    <div class="stat-value">{profile.get('public_repos', 'N/A')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
