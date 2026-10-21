from datetime import date, timedelta

from generators.contrib_card import draw_calendar_heatmap_card


def test_calendar_heatmap_returns_svg():
    today = date(2026, 4, 16)
    contributions = [
        {"date": (today - timedelta(days=index)).isoformat(), "count": (index % 6) + 1}
        for index in range(30)
    ]

    result = draw_calendar_heatmap_card(
        {"username": "testuser", "contributions": contributions},
        theme_name="Default",
        date_range={
            "start": (today - timedelta(days=365)).isoformat(),
            "end": today.isoformat(),
        },
    )

    assert isinstance(result, str)
    assert result.startswith("<svg")
    assert "viewBox=\"0 0 735 182\"" in result
    assert "testuser's Contribution Calendar" in result


def test_custom_contribution_palette_is_used():
    from generators.contrib_card import _palette_from_theme

    custom_palette = [
        "#111111",
        "#222222",
        "#333333",
        "#444444",
        "#555555",
    ]

    result = _palette_from_theme(
        "My Custom Theme",
        {
            "bg_color": "#000000",
            "title_color": "#ffffff",
            "border_color": "#888888",
            "contribution_palette": custom_palette,
        },
    )

    assert result == custom_palette
