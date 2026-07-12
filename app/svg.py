"""SVG chart rendering via kerykeion's ChartDrawer.

kerykeion emits SVG whose colors are CSS custom properties
(``var(--kerykeion-chart-color-*)``). Downstream consumers recolor a chart by
overriding those variables in their own stylesheet — no SVG surgery required.
The built-in themes are a fixed enum (light/dark/classic/strawberry/...), so we
pick a neutral default and leave palette customization to the caller.
"""

from __future__ import annotations

from html import escape
from typing import Literal

from kerykeion import ChartDrawer
from kerykeion.schemas.kr_models import ChartDataModel

Theme = Literal["light", "dark", "dark-high-contrast", "classic", "strawberry", "black-and-white"]


def _escape_xml_text(value: str) -> str:
    """Escape user text and replace code points forbidden by XML 1.0."""
    cleaned = "".join(
        char
        if ord(char) in (0x09, 0x0A, 0x0D)
        or 0x20 <= ord(char) <= 0xD7FF
        or 0xE000 <= ord(char) <= 0xFFFD
        or 0x10000 <= ord(char) <= 0x10FFFF
        else "\N{REPLACEMENT CHARACTER}"
        for char in value
    )
    return escape(cleaned, quote=True)


def render_svg(
    chart_data: ChartDataModel,
    variant: Literal["wheel", "full"] = "wheel",
    *,
    theme: Theme = "light",
) -> str:
    """Render a chart to a standalone SVG string.

    Args:
        chart_data: Chart data produced by ``ChartDataFactory``.
        variant: ``"wheel"`` for the wheel only, ``"full"`` for wheel + aspect grid.
        theme: One of kerykeion's built-in themes.

    Returns:
        Self-contained SVG markup.
    """
    # kerykeion interpolates subject.name into SVG without XML escaping. Give
    # its templates a fixed safe name and provide an escaped custom title.
    safe_chart_data = chart_data.model_copy(deep=True)
    subject_name = safe_chart_data.subject.name
    safe_chart_data.subject.name = "Subject"
    custom_title = _escape_xml_text(f"{subject_name} - Birth Chart")
    drawer = ChartDrawer(safe_chart_data, theme=theme, custom_title=custom_title)
    if variant == "full":
        return drawer.generate_svg_string()
    return drawer.generate_wheel_only_svg_string()
