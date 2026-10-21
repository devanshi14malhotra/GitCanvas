
import re
import unittest

import svgwrite

from generators.contrib_card import _palette_from_theme, draw_calendar_heatmap_card
from generators.svg_base import draw_card_background
from themes.theme_schema import normalize_theme, validate_theme


class ThemeSchemaTests(unittest.TestCase):
    def test_gradient_without_colors_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_theme({
                "background": {"type": "gradient"}
            })

    def test_legacy_theme_is_supported(self):
        theme = {
            "bg_color": "0d1117",
            "border_color": "#30363d",
            "title_color": "#58a6ff",
            "text_color": "#c9d1d9",
            "icon_color": "#8b949e",
        }
        normalized = normalize_theme(theme)
        self.assertEqual(normalized["bg_color"], "#0d1117")
        self.assertEqual(normalized["border_color"], "#30363d")

    def test_custom_contribution_palette_is_used(self):
        palette = ["#111111", "#222222", "#333333", "#444444", "#555555"]
        result = _palette_from_theme(
            "My Custom Theme",
            {"contribution_palette": palette},
        )
        self.assertEqual(result, palette)

    def test_invalid_contribution_palette_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_theme({
                "contribution_palette": ["#111111", "#222222"]
            })

    def test_invalid_legacy_color_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_theme({"bg_color": "not-a-color"})

    def test_negative_border_radius_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_theme({"border": {"radius": -1}})

    def test_negative_animation_duration_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_theme({
                "animation": {"enabled": True, "duration_ms": -1}
            })

    def test_renderer_options_must_be_a_dictionary(self):
        with self.assertRaises(ValueError):
            validate_theme({"renderer_options": "invalid"})

    def test_normalization_does_not_mutate_input(self):
        original = {"bg_color": "0d1117"}
        normalize_theme(original)
        self.assertEqual(original["bg_color"], "0d1117")

    def test_theme_can_enable_heatmap_animations(self):
        svg_output = draw_calendar_heatmap_card(
            {"username": "testuser", "contributions": []},
            theme_name="Default",
            custom_colors={
                "animation": {"enabled": True, "duration_ms": 300}
            },
        )
        self.assertIn("@keyframes heatmapFadeIn", svg_output)
        self.assertIn("0.3s", svg_output)
        self.assertIn("contribution-cell", svg_output)

    def test_theme_can_disable_heatmap_animations(self):
        svg_output = draw_calendar_heatmap_card(
            {"username": "testuser", "contributions": []},
            theme_name="Default",
            custom_colors={
                "animation": {"enabled": False, "duration_ms": 300}
            },
        )
        self.assertNotIn("@keyframes heatmapFadeIn", svg_output)


def test_multiple_gradient_backgrounds_have_unique_ids():
    drawing = svgwrite.Drawing()
    theme = {
        "background": {
            "type": "gradient",
            "colors": ["#111111", "#333333"],
        }
    }

    draw_card_background(drawing, 200, 100, theme)
    draw_card_background(drawing, 200, 100, theme)

    svg_output = drawing.tostring()
    gradient_ids = re.findall(
        r'<linearGradient[^>]*id="([^"]+)"',
        svg_output,
    )

    assert len(gradient_ids) == 2
    assert len(set(gradient_ids)) == 2


if __name__ == "__main__":
    unittest.main()
