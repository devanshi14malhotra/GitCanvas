
from copy import deepcopy
import re


HEX_COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?$")

LEGACY_COLOR_KEYS = (
    "bg_color",
    "border_color",
    "title_color",
    "text_color",
    "icon_color",
)

THEME_SCHEMA = {
    "schema_version": int,
    "contribution_palette": list,
    "background": dict,
    "border": dict,
    "animation": dict,
    "renderer_options": dict,
}


def _validate_color(value, field):
    """Validate a three- or six-digit hexadecimal color."""
    if not isinstance(value, str) or not HEX_COLOR_PATTERN.fullmatch(value):
        raise ValueError(
            f"{field} must be a valid hex color such as '#abc' or '#aabbcc'."
        )


def validate_theme(theme_data):
    """Validate supported declarative theme properties.

    Unknown top-level keys are allowed for forward compatibility.
    Legacy themes may omit all new properties.
    """
    if not isinstance(theme_data, dict):
        raise ValueError("Theme must be a JSON object.")

    for key, expected_type in THEME_SCHEMA.items():
        if key in theme_data:
            value = theme_data[key]

            if key == "schema_version":
                if type(value) is not int or value < 1:
                    raise ValueError("schema_version must be a positive integer.")
            elif not isinstance(value, expected_type):
                raise ValueError(
                    f"{key} must be of type {expected_type.__name__}."
                )

    for key in LEGACY_COLOR_KEYS:
        if key in theme_data:
            _validate_color(theme_data[key], key)

    if "contribution_palette" in theme_data:
        palette = theme_data["contribution_palette"]

        if len(palette) != 5:
            raise ValueError(
                "contribution_palette must contain exactly five colors."
            )

        for index, color in enumerate(palette):
            _validate_color(color, f"contribution_palette[{index}]")

    background = theme_data.get("background", {})
    if background:
        allowed_background_keys = {"type", "colors", "direction"}
        unknown = set(background) - allowed_background_keys

        if unknown:
            raise ValueError(
                f"Unsupported background properties: {sorted(unknown)}"
            )

        background_type = background.get("type", "solid")
        if background_type not in {"solid", "gradient"}:
            raise ValueError(
                "background.type must be 'solid' or 'gradient'."
            )

        if background_type == "gradient" and "colors" not in background:
            raise ValueError(
                "A gradient background requires at least two colors."
            )

        if "colors" in background:
            colors = background["colors"]

            if not isinstance(colors, list) or not colors:
                raise ValueError(
                    "background.colors must be a non-empty list."
                )

            if background_type == "gradient" and len(colors) < 2:
                raise ValueError(
                    "A gradient background requires at least two colors."
                )

            for index, color in enumerate(colors):
                _validate_color(color, f"background.colors[{index}]")

        if "direction" in background and background["direction"] not in {
            "horizontal",
            "vertical",
            "diagonal",
        }:
            raise ValueError(
                "background.direction must be 'horizontal', 'vertical', "
                "or 'diagonal'."
            )

    border = theme_data.get("border", {})
    if border:
        allowed_border_keys = {"radius", "width", "color"}
        unknown = set(border) - allowed_border_keys

        if unknown:
            raise ValueError(
                f"Unsupported border properties: {sorted(unknown)}"
            )

        for key in ("radius", "width"):
            if key in border:
                value = border[key]

                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or value < 0
                ):
                    raise ValueError(
                        f"border.{key} must be a non-negative number."
                    )

        if "color" in border:
            _validate_color(border["color"], "border.color")

    animation = theme_data.get("animation", {})
    if animation:
        allowed_animation_keys = {"enabled", "duration_ms"}
        unknown = set(animation) - allowed_animation_keys

        if unknown:
            raise ValueError(
                f"Unsupported animation properties: {sorted(unknown)}"
            )

        if "enabled" in animation and not isinstance(
            animation["enabled"], bool
        ):
            raise ValueError("animation.enabled must be a boolean.")

        if "duration_ms" in animation:
            duration = animation["duration_ms"]

            if (
                isinstance(duration, bool)
                or not isinstance(duration, int)
                or duration < 0
            ):
                raise ValueError(
                    "animation.duration_ms must be a non-negative integer."
                )

    return True


def normalize_theme(theme_data):
    """Return a normalized, validated copy of a theme."""
    if not isinstance(theme_data, dict):
        raise ValueError("Theme must be a JSON object.")

    normalized = deepcopy(theme_data)

    # Preserve support for legacy colors without a leading '#'.
    for key in LEGACY_COLOR_KEYS:
        value = normalized.get(key)

        if isinstance(value, str) and value and not value.startswith("#"):
            normalized[key] = f"#{value}"

    # Normalize declarative border colors.
    border = normalized.get("border")
    if isinstance(border, dict):
        color = border.get("color")

        if isinstance(color, str) and color and not color.startswith("#"):
            border["color"] = f"#{color}"

    # Normalize declarative background colors.
    background = normalized.get("background")
    if isinstance(background, dict):
        colors = background.get("colors")

        if isinstance(colors, list):
            background["colors"] = [
                f"#{color}"
                if isinstance(color, str)
                and color
                and not color.startswith("#")
                else color
                for color in colors
            ]

    # Normalize contribution palette colors.
    palette = normalized.get("contribution_palette")
    if isinstance(palette, list):
        normalized["contribution_palette"] = [
            f"#{color}"
            if isinstance(color, str)
            and color
            and not color.startswith("#")
            else color
            for color in palette
        ]

    validate_theme(normalized)
    return normalized
