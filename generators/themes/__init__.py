"""
Contribution card theme rendering engine.

This module provides a centralized dispatcher for rendering contribution cards
with different visual themes. Each theme is isolated in its own function.
"""

from .arcade_themes import render_gaming_theme, render_pacman_theme
from .space_themes import render_space_theme, render_marvel_theme
from .supernatural_themes import render_stranger_things_theme
from .sports_themes import render_cricket_theme
from .modern_themes import render_cyberpunk_theme, render_ocean_theme
from .advanced_themes import render_glass_theme, render_neural_theme, render_default_theme
from .sakura_theme import render_sakura_theme

# Theme dispatcher: maps theme names to rendering functions
THEME_DISPATCHER = {
    "Gaming": render_gaming_theme,
    "Space": render_space_theme,
    "Marvel": render_marvel_theme,
    "Stranger_things": render_stranger_things_theme,
    "Pacman": render_pacman_theme,
    "Cyberpunk": render_cyberpunk_theme,
    "Cricket": render_cricket_theme,
    "Ocean": render_ocean_theme,
    "Glass": render_glass_theme,
    "Neural": render_neural_theme,
    "Matrix": None,  # Matrix delegates to its own module
    "Sakura": render_sakura_theme,
}

__all__ = [
    "THEME_DISPATCHER",
    "render_gaming_theme",
    "render_pacman_theme",
    "render_space_theme",
    "render_marvel_theme",
    "render_stranger_things_theme",
    "render_cricket_theme",
    "render_cyberpunk_theme",
    "render_ocean_theme",
    "render_glass_theme",
    "render_neural_theme",
    "render_default_theme",
    "render_sakura_theme",
]
