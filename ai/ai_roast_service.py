"""
AI Service for generating GitHub profile roasts
Supports both OpenAI and Google Gemini APIs
"""

import os
import random
import requests
from typing import Dict, Optional
try:
    import google.generativeai as genai  # type: ignore
    _HAS_GENAI = True
except Exception:
    genai = None
    _HAS_GENAI = False
from openai import OpenAI

# Get API keys from environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Initialize APIs
if GEMINI_API_KEY:
    if _HAS_GENAI:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
        except Exception as e:
            print(f"Failed to configure Google Generative AI client: {e}")
    else:
        print("Google Generative AI client not installed; Gemini support disabled.")

if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)


def create_roast_prompt(profile_data: Dict) -> str:
    """Create the prompt for AI based on profile data"""
    username = profile_data.get('username', 'Unknown')
    top_languages = profile_data.get('top_languages', [])
    total_commits = profile_data.get('total_commits', 0)
    public_repos = profile_data.get('public_repos', 0)
    
    # Format languages
    languages_str = ', '.join([lang['name'] for lang in top_languages[:3]]) if top_languages else 'various languages'
    
    prompt = f"""Generate a single humorous one-liner roast for this GitHub developer:

Username: {username}
Top Languages: {languages_str}
Total Commits: {total_commits}
Public Repos: {public_repos}

Make it funny, creative, and tech-related. Examples of the style:
- "Python dev who thinks import happiness is a valid library"
- "500 commits, 499 were fixing typos"
- "JavaScript enthusiast still debugging async/await in their dreams"
- "Writes more TODO comments than actual code"

Generate ONE creative roast line now (no quotes, just the text):"""
    
    return prompt


def generate_roast_with_openai(profile_data: Dict) -> str:
    """Generate roast using OpenAI GPT"""
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not configured")
    
    prompt = create_roast_prompt(profile_data)
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a witty tech comedian who roasts developers based on their GitHub profiles. Keep it funny, lighthearted, and one line only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=100,
            temperature=0.9
        )
        
        roast = response.choices[0].message.content.strip()
        # Remove quotes if present
        roast = roast.strip('"').strip("'")
        return roast
        
    except Exception as e:
        print(f"OpenAI API error: {e}")
        raise


def generate_roast_with_gemini(profile_data: Dict) -> str:
    """Generate roast using Google Gemini"""
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API key not configured")
    if not _HAS_GENAI:
        raise ImportError("google.generativeai is not installed")
    
    prompt = create_roast_prompt(profile_data)
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        system_prompt = "You are a witty tech comedian. Generate ONE funny one-liner roast. Keep it lighthearted and use programming humor. Return ONLY the roast text, no quotes or explanation.\n\n"
        
        response = model.generate_content(
            system_prompt + prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.9,
                max_output_tokens=100,
            )
        )
        
        roast = response.text.strip()
        # Remove quotes and take first line only
        roast = roast.strip('"').strip("'").split('\n')[0]
        return roast
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        raise


def get_fallback_roast(profile_data: Dict) -> str:
    """Get a fallback roast when AI services are unavailable"""
    top_languages = profile_data.get('top_languages', [])
    total_commits = profile_data.get('total_commits', 0)
    
    top_lang = top_languages[0]['name'] if top_languages else 'Code'
    
    fallback_roasts = [
        f"{top_lang} warrior with {total_commits} commits of pure determination (and Stack Overflow copy-paste)",
        "Git commit history so active, your keyboard filed for workers' compensation",
        "Code so clean, Marie Kondo wants your GitHub in her portfolio",
        f"{total_commits} commits later, still Googling 'how to exit vim'",
        "Debugging skills so good, you find bugs that haven't been written yet",
        f"{top_lang} dev who debugs with print statements like it's 1999",
        "Commit messages so descriptive: 'fixed stuff', 'updated things', 'idk anymore'",
        f"You've made {total_commits} commits, but who's counting? (Git is. Git is counting.)",
        "Your code reviews are so thorough, you found bugs in the comments",
        f"{top_lang} expert who treats console.log() as a religion"
    ]
    
    return random.choice(fallback_roasts)


def generate_profile_roast(profile_data: Dict) -> Dict:
    """
    Main function to generate roast with fallback mechanism
    Returns dict with roast and metadata
    """
    roast_text = None
    source = None
    
    # Try OpenAI first if available
    if OPENAI_API_KEY:
        try:
            roast_text = generate_roast_with_openai(profile_data)
            source = "openai"
        except Exception as e:
            print(f"OpenAI failed: {e}")
    
    # Try Gemini if OpenAI failed or not available
    if not roast_text and GEMINI_API_KEY:
        try:
            roast_text = generate_roast_with_gemini(profile_data)
            source = "gemini"
        except Exception as e:
            print(f"Gemini failed: {e}")
    
    # Use fallback if all AI services failed
    if not roast_text:
        roast_text = get_fallback_roast(profile_data)
        source = "fallback"
    
    return {
        "roast": roast_text,
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
        "public_repos": 25
    }
    
    result = generate_profile_roast(test_profile)
    print(f"Roast: {result['roast']}")
    print(f"Source: {result['source']}")
