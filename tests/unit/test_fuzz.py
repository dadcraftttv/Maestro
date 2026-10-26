# SPDX-License-Identifier: GPL-3.0-or-later
"""A quick seed fuzz on every push (task 3.8); `tools/fuzz.py` runs thousands before a listen."""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))

from fuzz import BARS, faults
from maestro.rng import ComposerRng
from maestro.theory.chords import VOCAB
from maestro.theory.flow import FLOW, check_phrase, plain_phrase, progression
from maestro.theory.form import FORM
from maestro.theory.pitch import Key
from maestro.theory.rhythm import CLAVES, METERS


def test_forty_seeds_a_style_find_no_fault():
    for style in FORM:
        for seed in range(1, 41):
            assert not faults(style, seed, BARS[seed % len(BARS)]), (style, seed)


def test_the_plain_phrase_passes_the_check_and_sits_with_the_clave():
    key, met, clave = Key(9, "minor"), METERS["4/4"], CLAVES["son_2-3"]
    for seed in range(1, 21):
        rng = ComposerRng()
        rng.seed(seed)
        spans = progression(rng, FLOW["salsa"], key, VOCAB["salsa"], 0, 8, met, 8, None)[0]
        notes, _ = plain_phrase(spans, key, 0, 8, met, 76, clave)
        assert check_phrase(notes, spans, key, met, 8, 0, clave) is None, seed
