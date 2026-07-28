THEMES = {
    "Default": {
        "bg_color": "#0d1117",
        "border_color": "#30363d",
        "title_color": "#58a6ff",
        "text_color": "#c9d1d9",
        "icon_color": "#8b949e",
        "font_family": "Segoe UI, Ubuntu, Sans-Serif",
        "title_font_size": 20,
        "text_font_size": 14,
        "tags": ["dark", "minimal", "clean", "popular"]
    },
    
   "Spider-Man": {
    "bg_color": "#050505",
    "border_color": "#ff0000",
    "title_color": "#005aff",
    "text_color": "#ede7e7",
    "icon_color": "#b50505",
    "font_family": "'Courier New', sans-serif",
    "title_font_size": 24,
    "text_font_size": 14,
    "tags": ["balanced", "classic", "vibrant", "readable"]
},
    "Music": {
        "bg_color": "#0d0d0d",
        "border_color": "#9d00ff",
        "title_color": "#ff00cc",
        "text_color": "#ffffff",
        "icon_color": "#00f5ff",
        "font_family": "'Courier New', Courier, monospace",
        "title_font_size": 20,
        "text_font_size": 14,
        "tags": ["dark", "music", "neon", "colorful", "fun"]
    },
    "Gaming": {
        "bg_color": "#0d0d0d",
        "border_color": "#00ff00",
        "title_color": "#00ff00",
        "text_color": "#00ff00",
        "icon_color": "#00aa00",
        "font_family": "'Courier New', Courier, monospace",
        "title_font_size": 18,
        "text_font_size": 14,
        "is_pixel": True,
        "tags": ["dark", "gaming", "neon", "fun", "pixel"]
    },
    "Marvel": {
        "bg_color": "#1a1a1a",
        "border_color": "#e23636",
        "title_color": "#f78f3f",
        "text_color": "#ffffff",
        "icon_color": "#e23636",
        "font_family": "Impact, sans-serif",
        "title_font_size": 22,
        "text_font_size": 14,
        "tags": ["dark", "colorful", "fun", "bold"]
    },
    "Space": {
        "bg_color": "#0b0c1f",
        "border_color": "#6e5cdb",
        "title_color": "#a371f7",
        "text_color": "#d0dfff",
        "icon_color": "#39d353",
        "font_family": "Verdana, Geneva, sans-serif",
        "title_font_size": 18,
        "text_font_size": 14,
        "tags": ["dark", "space", "minimal", "cool"]
    },
    "Dracula": {
        "bg_color": "#282a36",
        "border_color": "#bd93f9",
        "title_color": "#ff79c6",
        "text_color": "#f8f8f2",
        "icon_color": "#50fa7b",
        "font_family": "Segoe UI, Ubuntu, Sans-Serif",
        "title_font_size": 20,
        "text_font_size": 14,
        "tags": ["dark", "colorful", "popular", "cool"]
    },
    "Neural": {
        "bg_color": "#0a0f14",
        "border_color": "#1f6feb",
        "title_color": "#00e5ff",
        "text_color": "#9be7ff",
        "icon_color": "#00bcd4",
        "font_family": "'Consolas', 'Lucida Console', monospace",
        "title_font_size": 19,
        "text_font_size": 14,
        "tags": ["dark", "tech", "neon", "minimal"]
    },
    "Pacman": {
        "bg_color": "#000000",
        "border_color": "#1919a6",
        "title_color": "#ffff00",
        "text_color": "#ffffff",
        "icon_color": "#ff8c00",
        "font_family": "'Courier New', Courier, monospace",
        "title_font_size": 18,
        "text_font_size": 14,
        "tags": ["dark", "gaming", "fun", "retro", "pixel"]
    },
    "Cyberpunk": {
        "bg_color": "#0a0e27",
        "border_color": "#00ff41",
        "title_color": "#00ffff",
        "text_color": "#ffffff",
        "icon_color": "#ff00ff",
        "font_family": "'Courier New', monospace",
        "title_font_size": 18,
        "text_font_size": 14,
        "tags": ["dark", "neon", "colorful", "fun", "bold"]
    },
    "Black Panther": {
    "bg_color": "#0B0B0F",
    "border_color": "#C0C0C0",
    "title_color": "#9D4EDD",
    "text_color": "#F5F5F5",
    "icon_color": "#6A0DAD",
    "font_family": "Verdana, Geneva, sans-serif",
    "title_font_size": 20,
    "text_font_size": 14,
    "tags": ["dark", "marvel", "wakanda", "elegant", "purple"]
    }
}
import json
import os
from pathlib import Path
from themes.aurora_gradient import AURORA_GRADIENT


themes_dir = Path(__file__).parent / "json"
themes_dir.mkdir(exist_ok=True)


def _theme_name_from_stem(stem: str) -> str:
    """Convert a theme filename stem into a human-friendly theme name."""
    aliases = {
        "spiderman": "Spider-Man",
        "aurora_gradient": "Aurora Gradient",
    }
    if stem in aliases:
        return aliases[stem]

    return stem.replace("_", " ").replace("-", " ").title()

def normalize_theme_colors(theme_data):
    """Ensure hex color values include a leading #."""
    for key, value in theme_data.items():
        if key.endswith("_color") and isinstance(value, str) and value and not value.startswith("#"):
            theme_data[key] = f"#{value}"
    return theme_data


def load_predefined_themes():
    """Load predefined themes from JSON files"""
    if os.path.exists(themes_dir):
        for filename in os.listdir(themes_dir):
            if filename.endswith('.json') and not filename.startswith('custom_'):
                theme_name = _theme_name_from_stem(filename[:-5])
                with open(os.path.join(themes_dir, filename), 'r') as f:
                    theme_data = json.load(f)
                THEMES[theme_name] = normalize_theme_colors(theme_data)

def load_custom_themes():
    """Load custom themes from custom_*.json files"""
    custom_themes = {}
    if os.path.exists(themes_dir):
        for filename in os.listdir(themes_dir):
            if filename.startswith('custom_') and filename.endswith('.json'):
                # Extract theme name from custom_{name}.json
                theme_name = _theme_name_from_stem(filename[7:-5])
                with open(os.path.join(themes_dir, filename), 'r') as f:
                    theme_data = json.load(f)
                custom_themes[theme_name] = normalize_theme_colors(theme_data)
    return custom_themes

def save_custom_theme(theme_name, theme_data):
    """Save a custom theme to a JSON file"""
    # Sanitize theme name for filename
    safe_name = theme_name.lower().replace(' ', '_').replace('-', '_')
    filename = f"custom_{safe_name}.json"
    filepath = themes_dir / filename
    
    with filepath.open('w') as f:
        json.dump(theme_data, f, indent=4)
    
    return filename

def get_all_themes():
    """Get all themes including custom ones"""
    all_themes = THEMES.copy()
    all_themes.update(CUSTOM_THEMES)
    return all_themes

# Load predefined themes on module import
load_predefined_themes()


# Manually add Ocean theme with ocean-themed colors
THEMES["Ocean"] = {
    "bg_color": "#001122",
    "border_color": "#004466",
    "title_color": "#00aaff",
    "text_color": "#66ddaa",
    "icon_color": "#2288cc",
    "font_family": "Segoe UI, Ubuntu, Sans-Serif",
    "title_font_size": 20,
    "text_font_size": 14
}

# Manually add Retro theme (Beige background, typewriter font, "old paper" look)
THEMES["Retro"] = {
    "bg_color": "#f5f0e1",
    "border_color": "#8b7355",
    "title_color": "#5c4a32",
    "text_color": "#6b5b45",
    "icon_color": "#a08060",
    "font_family": "'Courier New', Courier, monospace",
    "title_font_size": 18,
    "text_font_size": 14
}
THEMES.pop("Aurora_gradient", None)
THEMES["Aurora Gradient"] = AURORA_GRADIENT.copy()
THEMES["Sakura"] = {
    "bg_color": "#0D0D2B",
    "border_color":"#FF8FAB",
    "title_color":"#FFB7C5",
    "text_color":"#FFF8F0",
    "icon_color":"#FF6B9D",
    "font_family":"Georgia,'Times New Roman',serif",
    "title_font_size":20,
    "text_font_size":14,
    "tags":["dark","japanese","elegant","pink","aesthetic"]
}
# Load custom themes on module import
CUSTOM_THEMES = load_custom_themes()
