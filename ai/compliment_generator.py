"""
AI Service for generating GitHub profile compliments
Supports both OpenAI and Google Gemini APIs
"""

import os
import random
from typing import Dict, Optional
try:
    import google.generativeai as genai  # type: ignore
    _HAS_GENAI = True
except Exception:
    genai = None
    _HAS_GENAI = False
from openai import OpenAI

from utils.logger import setup_logger

logger = setup_logger(__name__)

# Get API keys from environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Initialize APIs
if GEMINI_API_KEY:
    if _HAS_GENAI:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
        except Exception as e:
            logger.error(f"Failed to configure Google Generative AI client: {e}")
    else:
        logger.warning("Google Generative AI client not installed; Gemini support disabled.")

if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)


def create_compliment_prompt(profile_data: Dict) -> str:
    """Create the prompt for AI based on profile data"""
    username = profile_data.get('username', 'Unknown')
    top_languages = profile_data.get('top_languages', [])
    total_commits = profile_data.get('total_commits', 0)
    public_repos = profile_data.get('public_repos', 0)
    followers = profile_data.get('followers', 0)
    
    # Format languages
    languages_str = ', '.join([lang['name'] for lang in top_languages[:3]]) if top_languages else 'various languages'
    
    prompt = f"""Generate a single highly positive, enthusiastic one-liner compliment for this GitHub developer:

Username: {username}
Top Languages: {languages_str}
Total Commits: {total_commits}
Public Repos: {public_repos}
Followers: {followers}

Praise their coding journey, their dedication, their tech stack choices, or their impact on the community. 
Make it uplifting, motivating, and fun. Examples of the style:
- "Your Python code is so elegant, Guido van Rossum takes notes from YOUR style guide!"
- "500 commits of pure excellence - you're basically the main character of tech!"
- "Building with JavaScript like a digital architect designing the future!"
- "Your commit history reads like a success story that inspires other devs!"
- "{total_commits} contributions and counting - you're a coding powerhouse!"

Generate ONE creative, uplifting compliment now (no quotes, just the text):"""
    
    return prompt


def generate_compliment_with_openai(profile_data: Dict) -> str:
    """Generate compliment using OpenAI GPT"""
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not configured")
    
    prompt = create_compliment_prompt(profile_data)
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an enthusiastic, hype-building tech recruiter and mentor. You write extremely positive, motivating compliments that celebrate developers' achievements. Keep it uplifting, fun, and one line only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=100,
            temperature=0.9
        )
        
        compliment = response.choices[0].message.content.strip()
        # Remove quotes if present
        compliment = compliment.strip('"').strip("'")
        return compliment
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise


def generate_compliment_with_gemini(profile_data: Dict) -> str:
    """Generate compliment using Google Gemini"""
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API key not configured")
    if not _HAS_GENAI:
        raise ImportError("google.generativeai is not installed")
    
    prompt = create_compliment_prompt(profile_data)
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        system_prompt = "You are an enthusiastic tech mentor who generates ONE uplifting, highly positive one-liner compliment. Celebrate the developer's achievements with hype and encouragement. Return ONLY the compliment text, no quotes or explanation.\n\n"
        
        response = model.generate_content(
            system_prompt + prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.9,
                max_output_tokens=100,
            )
        )
        
        compliment = response.text.strip()
        # Remove quotes and take first line only
        compliment = compliment.strip('"').strip("'").split('\n')[0]
        return compliment
        
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise


def get_fallback_compliment(profile_data: Dict) -> str:
    """Get a fallback compliment when AI services are unavailable"""
    top_languages = profile_data.get('top_languages', [])
    total_commits = profile_data.get('total_commits', 0)
    public_repos = profile_data.get('public_repos', 0)
    
    top_lang = top_languages[0]['name'] if top_languages else 'Code'
    
    fallback_compliments = [
        f"Your {total_commits} commits prove you're a coding machine - absolutely inspiring!",
        f"Building {public_repos} public repos? You're basically a tech superhero!",
        f"Your {top_lang} skills are so sharp, you could debug a program just by looking at it!",
        "Your code is so clean, it sparkles brighter than a freshly polished IDE!",
        f"{total_commits} contributions? You're leaving a trail of awesome in the GitHub universe!",
        f"A {top_lang} virtuoso with {public_repos} repos - the dev community is lucky to have you!",
        "Your commit history is a masterpiece of dedication and consistency!",
        f"Creating magic with {top_lang} - your repos are like gifts to the open source world!",
        "Your coding journey is proof that passion + persistence = pure excellence!",
        f"From repo 1 to repo {public_repos}, you've built something truly remarkable!"
    ]
    
    return random.choice(fallback_compliments)


def generate_github_compliment(profile_data: Dict, provider: str = 'gemini') -> Dict:
    """
    Main function to generate compliment with fallback mechanism
    
    Args:
        profile_data: Dict containing user stats (username, top_languages, total_commits, public_repos, followers)
        provider: Preferred AI provider ('gemini', 'openai', or 'auto' to try both)
    
    Returns:
        Dict with compliment and metadata
    """
    compliment_text = None
    source = None
    
    # Validate profile data
    if not isinstance(profile_data, dict):
        logger.error("Invalid profile_data: must be a dictionary")
        return {
            "compliment": "You're amazing for even trying to get a compliment! 🌟",
            "source": "error_fallback",
            "username": None,
            "success": False,
            "error": "Invalid profile data"
        }
    
    # Auto mode: try preferred provider first, then fallback
    if provider == 'auto':
        # Try Gemini first (usually faster and free tier available)
        if GEMINI_API_KEY and _HAS_GENAI:
            try:
                compliment_text = generate_compliment_with_gemini(profile_data)
                source = "gemini"
            except Exception as e:
                logger.warning(f"Gemini failed: {e}")
        
        # Try OpenAI if Gemini failed or not available
        if not compliment_text and OPENAI_API_KEY:
            try:
                compliment_text = generate_compliment_with_openai(profile_data)
                source = "openai"
            except Exception as e:
                logger.warning(f"OpenAI failed: {e}")
    
    # Specific provider mode
    elif provider == 'gemini':
        if not GEMINI_API_KEY:
            logger.warning("Gemini API key not configured, using fallback")
        elif not _HAS_GENAI:
            logger.warning("google.generativeai not installed, using fallback")
        else:
            try:
                compliment_text = generate_compliment_with_gemini(profile_data)
                source = "gemini"
            except Exception as e:
                logger.warning(f"Gemini failed: {e}")
    
    elif provider == 'openai':
        if not OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured, using fallback")
        else:
            try:
                compliment_text = generate_compliment_with_openai(profile_data)
                source = "openai"
            except Exception as e:
                logger.warning(f"OpenAI failed: {e}")
    
    # Use fallback if all AI services failed or not configured
    if not compliment_text:
        compliment_text = get_fallback_compliment(profile_data)
        source = "fallback"
    
    return {
        "compliment": compliment_text,
        "source": source,
        "username": profile_data.get('username'),
        "success": True
    }


# For testing
if __name__ == "__main__":
    # Test data
    test_profile = {
        "username": "testuser",
        "top_languages": [
            {"name": "Python", "count": 10},
            {"name": "JavaScript", "count": 5}
        ],
        "total_commits": 500,
        "public_repos": 25,
        "followers": 100
    }
    
    result = generate_github_compliment(test_profile, provider='auto')
    print(f"Compliment: {result['compliment']}")
    print(f"Source: {result['source']}")
    print(f"Success: {result['success']}")
