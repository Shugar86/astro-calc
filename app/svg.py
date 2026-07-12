"""SVG chart rendering via kerykeion's ChartDrawer.

kerykeion emits SVG whose colors are CSS custom properties
(``var(--kerykeion-chart-color-*)``). Downstream consumers recolor a chart by
overriding those variables in their own stylesheet — no SVG surgery required.
The built-in themes are a fixed enum (light/dark/classic/strawberry/...), so we
pick a neutral default and leave palette customization to the caller.
"""

from __future__ import annotations

from typing import Literal

from kerykeion import ChartDrawer
from kerykeion.schemas.kr_models import ChartDataModel

Theme = Literal["light", "dark", "dark-high-contrast", "classic", "strawberry", "black-and-white"]


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
    drawer = ChartDrawer(chart_data, theme=theme)
    if variant == "full":
        return drawer.generate_svg_string()
    return drawer.generate_wheel_only_svg_string()
