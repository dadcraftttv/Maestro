# SPDX-License-Identifier: GPL-3.0-or-later
from maestro.explain import passage
from maestro.sketch import TEMPO, sketch
from maestro.theory.form import FORM


def test_a_sketch_plays_what_the_explanation_says():
    for style in FORM:
        song, lines = sketch(style, seed=4, bars=8)
        assert lines == passage(style, seed=4, bars=8, bpm=TEMPO[style], flow=False), style   # no band check failed
        parts = {m.name: m.notes for m in song.members}
        assert all(parts[n] for n in ("pad", "bass", "melody", "drums")), style


def test_the_melody_sits_above_the_pad():
    for style in FORM:
        song, _ = sketch(style, seed=9, bars=8)
        parts = {m.name: m.notes for m in song.members}
        for m in parts["melody"]:
            under = [p for p in parts["pad"] if p.step <= m.step < p.step + p.steps]
            assert all(m.pitch > p.pitch for p in under), style
