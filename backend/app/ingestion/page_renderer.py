from __future__ import annotations


def render_page(page, output_path, dpi: int = 275):
    scale = dpi / 72
    pixmap = page.get_pixmap(matrix=__import__("fitz").Matrix(scale, scale), alpha=False)
    pixmap.save(output_path)
    return output_path

