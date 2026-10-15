from __future__ import annotations

import math

from bokeh.models import ColumnDataSource, Range1d
from bokeh.plotting import figure


def hand_endpoint(cx: float, cy: float, radius: float, angle_rad: float) -> tuple[float, float]:
    return (
        cx + math.sin(angle_rad) * radius,
        cy + math.cos(angle_rad) * radius,
    )


def build_clock_figure(size: int = 300) -> tuple[figure, dict[str, ColumnDataSource]]:
    cx, cy, r = 0.0, 0.0, 1.0

    p = figure(
        width=size,
        height=size,
        x_range=Range1d(start=-1.25, end=1.25),
        y_range=Range1d(start=-1.25, end=1.25),
        toolbar_location=None,
        background_fill_color="#1a1a1a",
        border_fill_color="#1a1a1a",
        outline_line_color=None,
    )
    p.axis.visible = False
    p.grid.visible = False

    p.circle(
        x=0,
        y=0,
        radius=r,
        fill_color="#1a1a1a",
        line_color="rgba(255,255,255,0.18)",
        line_width=2,
    )

    for i in range(60):
        ang = (i / 60.0) * 2.0 * math.pi
        is_maj = i % 5 == 0
        outer = (math.sin(ang) * r, math.cos(ang) * r)
        inner_r = r - (0.08 if is_maj else 0.04)
        inner = (math.sin(ang) * inner_r, math.cos(ang) * inner_r)
        p.line(
            x=[inner[0], outer[0]],
            y=[inner[1], outer[1]],
            line_color="rgba(180,180,180,0.65)",
            line_width=2.5 if is_maj else 1.2,
        )

    font_size = max(8, int(r * 300 * 0.036))
    for h in range(12):
        ang = (h / 12.0) * 2.0 * math.pi
        label_r = r - 0.22
        tx = math.sin(ang) * label_r
        ty = math.cos(ang) * label_r
        p.text(
            x=[tx],
            y=[ty],
            text=[str(((h + 11) % 12) + 1)],
            text_align="center",
            text_baseline="middle",
            text_color="rgba(255,255,255,0.85)",
            text_font_size=f"{font_size}px",
        )

    src_hour = ColumnDataSource({"x": [cx, cx], "y": [cy, cy]})
    src_min = ColumnDataSource({"x": [cx, cx], "y": [cy, cy]})
    src_sec = ColumnDataSource({"x": [cx, cx], "y": [cy, cy]})

    p.line("x", "y", source=src_hour, line_width=8, line_color="rgba(255,255,255,0.9)", line_cap="round")
    p.line("x", "y", source=src_min, line_width=6, line_color="rgba(200,200,200,0.75)", line_cap="round")
    p.line("x", "y", source=src_sec, line_width=2, line_color="#ff4444", line_cap="round")

    p.circle(x=0, y=0, radius=0.035, fill_color="#ff4444", line_color=None)

    src_text = ColumnDataSource({"x": [0.0], "y": [-0.55], "text": ["00:00:00.000"]})
    p.text(
        "x",
        "y",
        text="text",
        source=src_text,
        text_align="center",
        text_baseline="middle",
        text_color="#7af0a0",
        text_font="Consolas, monospace",
        text_font_size=f"{max(8, int(font_size * 0.95))}px",
    )

    sources = {"hour": src_hour, "minute": src_min, "second": src_sec, "time_text": src_text}
    return p, sources
