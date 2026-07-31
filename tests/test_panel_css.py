"""Guards the panel's readability without a browser.

The panel is plain CSS in a template string, so nothing would otherwise notice a font
shrinking again. Sizes are declared in ``em`` on purpose: ``rem`` would hang off the
browser root and ignore the panel's own base size, making "make everything bigger" a
find-and-replace across twenty rules instead of one number.
"""

from __future__ import annotations

import re
from pathlib import Path

_PANEL = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "statistics_toolset"
    / "panel"
    / "panel.js"
)
_SOURCE = _PANEL.read_text(encoding="utf-8")

# Text below these sizes was reported as too small to read on a laptop screen.
MIN_BASE_PX = 16
MIN_EM = 0.85
MIN_SVG_UNITS = 12


def test_base_font_size_is_large_enough() -> None:
    match = re.search(r"\.st-wrap\{[^}]*?font-size:(\d+)px", _SOURCE, re.S)
    assert match, ".st-wrap must set an explicit base font size"
    assert int(match.group(1)) >= MIN_BASE_PX


def test_no_font_size_below_minimum() -> None:
    too_small = [v for v in re.findall(r"font-size:([\d.]+)em", _SOURCE) if float(v) < MIN_EM]
    assert not too_small, f"font sizes below {MIN_EM}em: {too_small}"


def test_sizes_use_em_so_the_base_scales_everything() -> None:
    """A single rem would silently opt out of the panel's base size."""
    assert not re.findall(r"font-size:[\d.]+rem", _SOURCE), "use em, not rem"


def test_svg_labels_are_legible() -> None:
    sizes = [int(v) for v in re.findall(r'font-size="(\d+)"', _SOURCE)]
    assert sizes, "expected font sizes on the SVG chart labels"
    assert all(s >= MIN_SVG_UNITS for s in sizes), f"SVG label sizes too small: {sizes}"


def test_chart_labels_cannot_overlap() -> None:
    """Bar labels are only drawn while they still fit — check that budget holds."""
    max_bars = int(re.search(r"periods\.length <= (\d+)", _SOURCE).group(1))
    width = int(re.search(r"const w = (\d+)", _SOURCE).group(1))
    pad = int(re.search(r"pad = (\d+)", _SOURCE).group(1))
    label_px = max(int(v) for v in re.findall(r'font-size="(\d+)"', _SOURCE))
    bar_width = (width - 2 * pad) / max_bars
    # "24-12" is five glyphs; ~0.62 em per glyph in a proportional font.
    assert bar_width >= label_px * 0.62 * 5, (
        f"at {max_bars} bars each is {bar_width:.0f}px wide, too narrow for a "
        f"{label_px}px label"
    )
