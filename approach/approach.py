#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
# copyright (c) 2026 Isaac Adjei <https://isaacadjei.me>
#
# this generator script is licensed under the PolyForm Noncommercial License 1.0.0;
# see NOTICE.md. The repository's visual output (the SVGs, the README and the
# assets) is licensed under CC BY-NC-ND 4.0; see LICENSE.
"""
approach.py: derives approach-dark.svg and approach-light.svg
from approach.svg.

approach.svg (checked in, hand-edited) is the single theme-adaptive source: a
dark base palette plus a `@media (prefers-color-scheme: light)` override. This
script splits that into two fixed-palette siblings for the README's <picture>
element, the same reason profile.py emits profile-dark.svg / profile-light.svg
alongside profile.svg, since some forges and devices don't honour @media queries
inside an <img>-embedded SVG, so those need a fixed file per theme.

Run after editing approach.svg's markup or palette:
    python approach/approach.py
"""

import os
import re

HERE = os.path.dirname(__file__)
SOURCE = os.path.join(HERE, 'approach.svg')

# must match the .cls { fill: ...; } rules in approach.svg's base and light blocks exactly.
DARK = {
    'comment': '#616e7f', 'kw': '#ff7b72', 'type': '#ffa657', 'fn': '#d2a8ff',
    'str':     '#a5d6ff', 'plain': '#c9d1d9', 'bg': '#161b22',
}
LIGHT = {
    'comment': '#6e7781', 'kw': '#cf222e', 'type': '#953800', 'fn': '#8250df',
    'str':     '#0a3069', 'plain': '#24292f', 'bg': '#f6f8fa',
}

MEDIA_BLOCK_RE = re.compile(
    r'\n {6}@media \(prefers-color-scheme: light\) \{.*?\n {6}\}\n', re.DOTALL)


def render(svg: str, palette: dict, filename: str, description: str) -> str:
    out = svg
    for cls, colour in palette.items():
        # keep the existing column alignment (the whitespace before '{'); only swap the colour.
        out = re.sub(rf'(\.{cls}\s*{{ fill: )[^;]+(; }})', rf'\g<1>{colour}\g<2>', out)
    out = MEDIA_BLOCK_RE.sub('\n', out)
    out = out.replace(
        "approach.svg - my personal code philosophy, adapts to the viewer's theme.",
        f'{filename} - my personal code philosophy ({description}).')
    return out


def main() -> None:
    with open(SOURCE, 'r', encoding='utf-8') as f:
        svg = f.read()

    if not MEDIA_BLOCK_RE.search(svg):
        raise RuntimeError(f'Could not find the light-mode @media block in {SOURCE}')

    with open(os.path.join(HERE, 'approach-dark.svg'), 'w', encoding='utf-8') as f:
        f.write(render(svg, DARK, 'approach-dark.svg', 'fixed dark palette'))
    with open(os.path.join(HERE, 'approach-light.svg'), 'w', encoding='utf-8') as f:
        f.write(render(svg, LIGHT, 'approach-light.svg', 'fixed light palette'))
    print('Generated approach-dark.svg and approach-light.svg from approach.svg.')


if __name__ == '__main__':
    main()
