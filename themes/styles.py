
THEMES = {
    "Default": {
        "bg_color": "#0d1117",
        "border_color": "#30363d",
        "title_color": "#58a6ff",
        "text_color": "#c9d1d9",
        "icon_color": "#8b949e",
        "font_family": "Segoe UI, Ubuntu, Sans-Serif",
        "title_font_size": 20,
        "text_font_size": 14
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
        "is_pixel": True
    },
    "Marvel": {
        "bg_color": "#1a1a1a",
        "border_color": "#e23636",
        "title_color": "#f78f3f",
        "text_color": "#ffffff",
        "icon_color": "#e23636",
        "font_family": "Impact, sans-serif",
        "title_font_size": 22,
        "text_font_size": 14
    },
    "Space": {
        "bg_color": "#0b0c1f",
        "border_color": "#6e5cdb",
        "title_color": "#a371f7",
        "text_color": "#d0dfff",
        "icon_color": "#39d353",
        "font_family": "Verdana, Geneva, sans-serif",
        "title_font_size": 18,
        "text_font_size": 14
    },
    "Dracula": {
        "bg_color": "#282a36",
        "border_color": "#bd93f9",
        "title_color": "#ff79c6",
        "text_color": "#f8f8f2",
        "icon_color": "#50fa7b",
        "font_family": "Segoe UI, Ubuntu, Sans-Serif",
        "title_font_size": 20,
        "text_font_size": 14
    },
    "Neural": {
    "bg_color": "#0a0f14",        
    "border_color": "#1f6feb",    
    "title_color": "#00e5ff",    
    "text_color": "#9be7ff",      
    "icon_color": "#00bcd4",      
    "font_family": "'Consolas', 'Lucida Console', monospace",
    "title_font_size": 19,
    "text_font_size": 14
    }
}
import json
import os



themes_dir = os.path.join(os.path.dirname(__file__), 'json')
if os.path.exists(themes_dir):
    for filename in os.listdir(themes_dir):
        if filename.endswith('.json'):
            theme_name = filename[:-5].capitalize()  # Remove .json and capitalize
            with open(os.path.join(themes_dir, filename), 'r') as f:
                THEMES[theme_name] = json.load(f)
