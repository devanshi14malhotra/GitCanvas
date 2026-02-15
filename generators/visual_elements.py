# generators/visual_elements.py

def emoji_element(emoji: str, size: int = 48) -> str:
    """
    Generate SVG for an emoji
    """
    return f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">
        <text x="50%" y="50%" dominant-baseline="middle"
              text-anchor="middle" font-size="{size}px">
            {emoji}
        </text>
    </svg>
    """


def gif_element(gif_url: str, size: int = 120) -> str:
    """
    Generate SVG wrapper for a GIF
    """
    return f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">
        <image href="{gif_url}" width="{size}" height="{size}" />
    </svg>
    """


def sticker_element(image_url: str, size: int = 100) -> str:
    """
    Generate SVG for a sticker / icon
    """
    return f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">
        <image href="{image_url}" width="{size}" height="{size}" />
    </svg>
    """
