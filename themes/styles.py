
import json
import os

THEMES = {}

themes_dir = os.path.join(os.path.dirname(__file__), 'json')
if os.path.exists(themes_dir):
    for filename in os.listdir(themes_dir):
        if filename.endswith('.json'):
            theme_name = filename[:-5].capitalize()  # Remove .json and capitalize
            with open(os.path.join(themes_dir, filename), 'r') as f:
                THEMES[theme_name] = json.load(f)
