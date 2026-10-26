# SPDX-License-Identifier: GPL-3.0-or-later
"""A quick seed fuzz on every push (task 3.8); `tools/fuzz.py` runs thousands before a listen."""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))

from fuzz import BARS, faults
from maestro.theory.form import FORM

# Faults the first fuzz found (Oct 26), open until DadCraft picks their fixes: the phrase melody over C7 when the pad
# sits high, salsa's melody crossing the clave, a phrase's first half ending home. Anything else fails.
KNOWN = ("out of its range 60-96", "the melody is crossed", "the first half ends home already")


def test_forty_seeds_a_style_find_no_new_fault():
    for style in FORM:
        for seed in range(1, 41):
            new = [f for f in faults(style, seed, BARS[seed % len(BARS)]) if not any(k in f for k in KNOWN)]
            assert not new, (style, seed, new)
