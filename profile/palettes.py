#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
# copyright (c) 2026 Isaac Adjei <https://isaacadjei.me>
#
# this generator script is licensed under the PolyForm Noncommercial License 1.0.0;
# see NOTICE.md.
"""
palettes.py: every colour set the profile card and the approach panel can use.

ACTIVE picks the live one, which profile.py beside it reads. The live card stays on
Primer; every other set is kept here switched off, ready to try by changing ACTIVE.
The approach colours are kept as data only and approach/approach.py keeps its own.
A card set can add 'bold': True to draw the lines of code ++ and -- in bold.
"""

ACTIVE = 'primer'  # 'default', 'vivid', 'bold' and the zacess sets are switched off for now

PALETTES = {
    # GitHub's own Primer colours, the live card
    'primer': {
        'card': {'dark': {'bg': '#161b22', 'text': '#c9d1d9', 'key': '#ffa657', 'value': '#a5d6ff', 'add': '#3fb950', 'delete': '#f85149', 'dots': '#616e7f'},
                 'light': {'bg': '#f6f8fa', 'text': '#24292f', 'key': '#953800', 'value': '#0a3069', 'add': '#1a7f37', 'delete': '#cf222e', 'dots': '#c2cfde'}},
        'approach': {'dark': {'comment': '#616e7f', 'kw': '#ff7b72', 'type': '#ffa657', 'fn': '#d2a8ff', 'str': '#a5d6ff', 'plain': '#c9d1d9', 'bg': '#161b22'},
                     'light': {'comment': '#6e7781', 'kw': '#cf222e', 'type': '#953800', 'fn': '#8250df', 'str': '#0a3069', 'plain': '#24292f', 'bg': '#f6f8fa'}},
    },
    # the suggested set: Primer exactly, except the lines of code ++ and -- in a stronger green and red, in bold
    'default': {
        'card': {'dark': {'bg': '#161b22', 'text': '#c9d1d9', 'key': '#ffa657', 'value': '#a5d6ff', 'add': '#5cff85', 'delete': '#ff9e96', 'dots': '#616e7f', 'bold': True},
                 'light': {'bg': '#f6f8fa', 'text': '#24292f', 'key': '#953800', 'value': '#0a3069', 'add': '#004a14', 'delete': '#85000f', 'dots': '#c2cfde', 'bold': True}},
        'approach': {'dark': {'comment': '#616e7f', 'kw': '#ff7b72', 'type': '#ffa657', 'fn': '#d2a8ff', 'str': '#a5d6ff', 'plain': '#c9d1d9', 'bg': '#161b22'},
                     'light': {'comment': '#6e7781', 'kw': '#cf222e', 'type': '#953800', 'fn': '#8250df', 'str': '#0a3069', 'plain': '#24292f', 'bg': '#f6f8fa'}},
    },
    # Primer's hues on the same card backgrounds with every colour past 7:1 and the leader dots kept visible
    'vivid': {
        'card': {'dark': {'bg': '#161b22', 'text': '#f0f6fc', 'key': '#ffb05c', 'value': '#8fd0ff', 'add': '#5cff85', 'delete': '#ff9e96', 'dots': '#6e7781'},
                 'light': {'bg': '#f6f8fa', 'text': '#1f2328', 'key': '#7a2e00', 'value': '#002a63', 'add': '#004a14', 'delete': '#85000f', 'dots': '#8c959f'}},
        'approach': {'dark': {'comment': '#9198a1', 'kw': '#ff8a80', 'type': '#ffb05c', 'fn': '#dcb8ff', 'str': '#8fd0ff', 'plain': '#f0f6fc', 'bg': '#161b22'},
                     'light': {'comment': '#4d555e', 'kw': '#990012', 'type': '#7a2e00', 'fn': '#5b2bb5', 'str': '#002a63', 'plain': '#1f2328', 'bg': '#f6f8fa'}},
    },
    # the vivid hues pushed further on GitHub's page backgrounds, so the card blends into the page
    'bold': {
        'card': {'dark': {'bg': '#0d1117', 'text': '#ffffff', 'key': '#ffbb66', 'value': '#99d9ff', 'add': '#5cff85', 'delete': '#ff9e96', 'dots': '#7d8590'},
                 'light': {'bg': '#ffffff', 'text': '#0d1117', 'key': '#662600', 'value': '#00204d', 'add': '#004a14', 'delete': '#85000f', 'dots': '#8c959f'}},
        'approach': {'dark': {'comment': '#a2aab3', 'kw': '#ff9e96', 'type': '#ffbb66', 'fn': '#e2c4ff', 'str': '#99d9ff', 'plain': '#ffffff', 'bg': '#0d1117'},
                     'light': {'comment': '#3d444d', 'kw': '#85000f', 'type': '#662600', 'fn': '#4a1f99', 'str': '#00204d', 'plain': '#0d1117', 'bg': '#ffffff'}},
    },
    # the Zacess themes in their dark and light pairs (zacesshq/themes), Yellow on Black paired with Cream
    'zacess': {  # Zacess Dark and Zacess Light
        'card': {'dark': {'bg': '#121212', 'text': '#f5f5f5', 'key': '#d3bdff', 'value': '#84b7fa', 'add': '#01ea45', 'delete': '#f39992', 'dots': '#7a7a7a'},
                 'light': {'bg': '#ffffff', 'text': '#111111', 'key': '#59029f', 'value': '#0049a3', 'add': '#005b14', 'delete': '#5d0002', 'dots': '#707070'}},
        'approach': {'dark': {'comment': '#80c201', 'kw': '#d3bdff', 'type': '#03dedd', 'fn': '#84b7fa', 'str': '#1ee646', 'plain': '#f5f5f5', 'bg': '#121212'},
                     'light': {'comment': '#97016b', 'kw': '#59029f', 'type': '#003737', 'fn': '#0049a3', 'str': '#004a0e', 'plain': '#111111', 'bg': '#ffffff'}},
    },
    'zacess-high-contrast': {  # Zacess High Contrast Dark and Zacess High Contrast Light
        'card': {'dark': {'bg': '#000000', 'text': '#ffffff', 'key': '#f5c400', 'value': '#8fd0ff', 'add': '#3bff59', 'delete': '#ffaba3', 'dots': '#a6a6a6'},
                 'light': {'bg': '#ffffff', 'text': '#000000', 'key': '#4b0091', 'value': '#00347f', 'add': '#005518', 'delete': '#4a0000', 'dots': '#262626'}},
        'approach': {'dark': {'comment': '#c7b404', 'kw': '#f5c400', 'type': '#00f4e0', 'fn': '#8fd0ff', 'str': '#20fe34', 'plain': '#ffffff', 'bg': '#000000'},
                     'light': {'comment': '#1701fb', 'kw': '#4b0091', 'type': '#004f4e', 'fn': '#00347f', 'str': '#005518', 'plain': '#000000', 'bg': '#ffffff'}},
    },
    'zacess-deep-contrast': {  # Zacess Deep Contrast Dark and Zacess Deep Contrast Light
        'card': {'dark': {'bg': '#000000', 'text': '#ffffff', 'key': '#67aeff', 'value': '#ffdf5a', 'add': '#00f000', 'delete': '#ffaa7c', 'dots': '#00ffff'},
                 'light': {'bg': '#ffffff', 'text': '#000000', 'key': '#002ec2', 'value': '#824100', 'add': '#006108', 'delete': '#730000', 'dots': '#0f4a85'}},
        'approach': {'dark': {'comment': '#00c600', 'kw': '#67aeff', 'type': '#00ebb1', 'fn': '#ffdf5a', 'str': '#ffaa7c', 'plain': '#ffffff', 'bg': '#000000'},
                     'light': {'comment': '#006108', 'kw': '#002ec2', 'type': '#003a39', 'fn': '#824100', 'str': '#870000', 'plain': '#000000', 'bg': '#ffffff'}},
    },
    'zacess-yellow-cream': {  # Zacess Yellow on Black and Zacess Cream
        'card': {'dark': {'bg': '#000000', 'text': '#ffeb3b', 'key': '#ffffff', 'value': '#88c3ff', 'add': '#28f74f', 'delete': '#ffa59d', 'dots': '#7a7a7a'},
                 'light': {'bg': '#fdf6e3', 'text': '#000000', 'key': '#530093', 'value': '#004498', 'add': '#005512', 'delete': '#540002', 'dots': '#6e6555'}},
        'approach': {'dark': {'comment': '#88c200', 'kw': '#ffffff', 'type': '#e5c7ff', 'fn': '#88c3ff', 'str': '#43f480', 'plain': '#ffeb3b', 'bg': '#000000'},
                     'light': {'comment': '#8b0162', 'kw': '#530093', 'type': '#003232', 'fn': '#004498', 'str': '#00440c', 'plain': '#000000', 'bg': '#fdf6e3'}},
    },
}

CARD = PALETTES[ACTIVE]['card']
APPROACH = PALETTES[ACTIVE]['approach']
