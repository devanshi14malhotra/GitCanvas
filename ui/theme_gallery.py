# theme_gallery.py — Resolves #198
import base64
import streamlit as st

try:
    from generators.svg_base import get_svg_font_style as _shared_get_svg_font_style
except (ImportError, AttributeError):
    def _shared_get_svg_font_style(font_family):
        if not font_family:
            return ""
        return f"text, tspan, .svg-font {{ font-family: {font_family} !important; }}"


def _generate_mini_svg(theme_name: str, theme: dict, font_override: str | None = None) -> str:
    """
    Generates a rich 200x140 SVG that accurately represents a theme's
    full visual identity — gradient headers, contribution grid simulation,
    language bars, color palette, and typography sample.
    """
    bg        = theme.get("bg_color",        "#0d1117")
    border    = theme.get("border_color",    "#30363d")
    title_col = theme.get("title_color",     "#58a6ff")
    text_col  = theme.get("text_color",      "#c9d1d9")
    icon_col  = theme.get("icon_color",      "#8b949e")
    font      = font_override or theme.get("font_family", "Segoe UI, Ubuntu, sans-serif")
    font_size = theme.get("title_font_size", 14)

    pretty_name = theme_name.replace("_", " ")
    display_name = pretty_name if len(pretty_name) <= 14 else pretty_name[:13] + "…"
    accent = title_col

    # Simulate a mini contribution grid (5x4 cells)
    grid_cols = 10
    grid_rows = 4
    cell = 8
    gap = 2
    grid_x, grid_y = 10, 88
    grid_cells = ""
    intensities = [0.1, 0.2, 0.5, 0.8, 1.0, 0.6, 0.3, 0.9, 0.4, 0.7,
                   0.2, 1.0, 0.6, 0.1, 0.8, 0.5, 0.3, 0.7, 0.9, 0.4,
                   0.7, 0.4, 0.9, 0.6, 0.2, 1.0, 0.3, 0.8, 0.1, 0.5,
                   0.3, 0.8, 0.2, 0.9, 0.5, 0.4, 1.0, 0.6, 0.7, 0.1]
    idx = 0
    for row in range(grid_rows):
        for col in range(grid_cols):
            x = grid_x + col * (cell + gap)
            y = grid_y + row * (cell + gap)
            op = intensities[idx % len(intensities)]
            grid_cells += (
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" '
                f'rx="2" fill="{accent}" opacity="{op}"/>\n'
            )
            idx += 1

    # Language bar simulation (3 bars, different widths)
    lang_bars = [
        (accent, 0.9, 55),
        (icon_col, 0.7, 35),
        (text_col, 0.4, 20),
    ]
    lang_bar_svg = ""
    bar_x = 130
    for i, (color, op, w) in enumerate(lang_bars):
        by = 93 + i * 14
        lang_bar_svg += f"""
        <rect x="{bar_x}" y="{by}" width="58" height="6" rx="3"
              fill="{text_col}" opacity="0.15"/>
        <rect x="{bar_x}" y="{by}" width="{w}" height="6" rx="3"
              fill="{color}" opacity="{op}"/>"""

        font_style = _shared_get_svg_font_style(font)

        return f"""<svg xmlns="http://www.w3.org/2000/svg"
    width="200" height="140" viewBox="0 0 200 140">
  <defs>
        <style type="text/css"><![CDATA[
        {font_style}
        ]]></style>
    <linearGradient id="hdr_{theme_name.replace(' ','_')}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="{accent}" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="{bg}"      stop-opacity="0"/>
    </linearGradient>
    <clipPath id="clip_{theme_name.replace(' ','_')}">
      <rect width="200" height="140" rx="10"/>
    </clipPath>
  </defs>

  <!-- Card base -->
  <rect width="200" height="140" rx="10"
        fill="{bg}" stroke="{border}" stroke-width="1.5"
        clip-path="url(#clip_{theme_name.replace(' ','_')})"/>

  <!-- Top accent gradient wash -->
  <rect width="200" height="44"
        fill="url(#hdr_{theme_name.replace(' ','_')})"
        clip-path="url(#clip_{theme_name.replace(' ','_')})"/>

  <!-- Top accent line -->
  <rect width="200" height="2.5" rx="0" fill="{accent}" opacity="0.95"/>

  <!-- Avatar circle -->
  <circle cx="22" cy="22" r="11" fill="{icon_col}" opacity="0.2"/>
  <circle cx="22" cy="22" r="7"  fill="{icon_col}" opacity="0.5"/>
  <circle cx="22" cy="17" r="3"  fill="{bg}"       opacity="0.6"/>

  <!-- Theme name -->
  <text x="40" y="18" font-family="{font}" font-size="10"
        fill="{title_col}" font-weight="bold">{display_name}</text>

  <!-- Subtitle (simulated repo count / tagline) -->
  <rect x="40" y="24" width="50" height="3.5" rx="2"
        fill="{text_col}" opacity="0.3"/>

  <!-- Stat chips row -->
  <!-- Chip 1 -->
  <rect x="10" y="44" width="36" height="14" rx="4"
        fill="{accent}" opacity="0.15"/>
  <rect x="10" y="44" width="36" height="14" rx="4"
        fill="none" stroke="{accent}" stroke-width="0.6" opacity="0.4"/>
  <text x="28" y="54" font-family="{font}" font-size="6.5"
        fill="{accent}" text-anchor="middle" opacity="0.9">Stars</text>

  <!-- Chip 2 -->
  <rect x="52" y="44" width="40" height="14" rx="4"
        fill="{icon_col}" opacity="0.12"/>
  <rect x="52" y="44" width="40" height="14" rx="4"
        fill="none" stroke="{icon_col}" stroke-width="0.6" opacity="0.4"/>
  <text x="72" y="54" font-family="{font}" font-size="6.5"
        fill="{icon_col}" text-anchor="middle" opacity="0.9">Commits</text>

  <!-- Chip 3 -->
  <rect x="98" y="44" width="28" height="14" rx="4"
        fill="{text_col}" opacity="0.1"/>
  <rect x="98" y="44" width="28" height="14" rx="4"
        fill="none" stroke="{text_col}" stroke-width="0.6" opacity="0.3"/>
  <text x="112" y="54" font-family="{font}" font-size="6.5"
        fill="{text_col}" text-anchor="middle" opacity="0.8">PRs</text>

  <!-- Divider -->
  <line x1="10" y1="66" x2="190" y2="66"
        stroke="{border}" stroke-width="0.8" opacity="0.7"/>

  <!-- Section label: Contributions -->
  <text x="10" y="78" font-family="{font}" font-size="6.5"
        fill="{text_col}" opacity="0.5" font-weight="600"
        letter-spacing="0.5">CONTRIBUTIONS</text>

  <!-- Mini contribution grid -->
  {grid_cells}

  <!-- Divider between grid and lang bars -->
  <line x1="120" y1="82" x2="120" y2="135"
        stroke="{border}" stroke-width="0.6" opacity="0.4"/>

  <!-- Section label: Languages -->
  <text x="130" y="78" font-family="{font}" font-size="6.5"
        fill="{text_col}" opacity="0.5" font-weight="600"
        letter-spacing="0.5">LANGUAGES</text>

  <!-- Language bars -->
  {lang_bar_svg}

  <!-- Color palette dots at bottom -->
  <circle cx="13"  cy="133" r="4" fill="{accent}"   />
  <circle cx="24"  cy="133" r="4" fill="{icon_col}" />
  <circle cx="35"  cy="133" r="4" fill="{text_col}" opacity="0.7"/>
  <circle cx="46"  cy="133" r="4" fill="{border}"   />

  <!-- Font sample -->
  <text x="60" y="136" font-family="{font}" font-size="6.5"
        fill="{text_col}" opacity="0.35">Aa · {font.split(',')[0].strip()[:12]}</text>

</svg>"""


def render_theme_gallery(all_themes: dict, current_theme: str, font_override: str | None = None) -> str | None:
    """
    Renders a responsive 4-column theme gallery.
    Cards show actual theme colours, contribution grid, language bars,
    chip UI, and typography. Active theme is highlighted with a glowing ring.

    Returns the selected theme name or None.
    """
    st.subheader("🎨 Theme Gallery")
    st.caption("Every card shows the theme's **real colors, fonts & layout** — click Select to apply.")

    # Inject hover CSS for the gallery cards
    st.markdown("""
    <style>
    .theme-card-wrap {
        border-radius: 12px;
        padding: 3px;
        transition: border-color 0.25s ease, box-shadow 0.25s ease;
        cursor: pointer;
    }
    .theme-card-wrap:hover {
        box-shadow: 0 0 10px rgba(88,166,255,0.25);
    }
    .theme-card-active {
        border: 2px solid #58a6ff !important;
        box-shadow: 0 0 12px rgba(88,166,255,0.4) !important;
    }
    .theme-card-inactive {
        border: 2px solid #30363d;
    }
    .active-badge {
        text-align: center;
        color: #58a6ff;
        font-size: 11px;
        font-weight: 700;
        margin: 3px 0 6px;
        letter-spacing: 0.8px;
    }
    </style>
    """, unsafe_allow_html=True)

    @st.cache_data(show_spinner=False)
    def _build_svg_map(themes_snapshot: tuple, font_override: str | None) -> dict:
        return {
            name: _generate_mini_svg(name, dict(props), font_override=font_override)
            for name, props in themes_snapshot
        }

    themes_snapshot = tuple(
        (name, tuple(sorted(props.items())))
        for name, props in all_themes.items()
    )
    svg_map   = _build_svg_map(themes_snapshot, font_override)
    selected  = None
    themes_list = list(all_themes.items())

    for row_start in range(0, len(themes_list), 4):
        row_slice = themes_list[row_start: row_start + 4]
        cols      = st.columns(4)

        for col_offset, (col, (theme_name, _)) in enumerate(zip(cols, row_slice)):
            is_active  = theme_name == current_theme
            svg_html   = svg_map.get(theme_name, "")
            card_class = "theme-card-wrap theme-card-active" if is_active else "theme-card-wrap theme-card-inactive"

            with col:
                svg_b64 = base64.b64encode(svg_html.encode("utf-8")).decode("utf-8")
                st.markdown(
                    f'<div class="{card_class}"><img src="data:image/svg+xml;base64,{svg_b64}" style="width:100%; height:auto; display:block; border-radius:10px;"/></div>',
                    unsafe_allow_html=True,
                )
                if is_active:
                    st.markdown(
                        "<p class='active-badge'>✦ ACTIVE</p>",
                        unsafe_allow_html=True,
                    )
                else:
                    if st.button(
                        "Select",
                        key=f"gallery_btn_{row_start}_{col_offset}_{theme_name}",
                        use_container_width=True,
                    ):
                        selected = theme_name

    return selected