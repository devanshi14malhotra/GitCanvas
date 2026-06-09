from themes.sakura import render as sakura_render

def render_sakura_theme(dwg, data, theme, weeks, cols, rows, max_date, width, height):
    svg_string = sakura_render(data)
    return svg_string