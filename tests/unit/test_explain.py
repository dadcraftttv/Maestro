# SPDX-License-Identifier: GPL-3.0-or-later
from maestro.explain import passage
from maestro.theory.form import FORM


def test_every_style_explains_a_passage():
    for style in FORM:
        lines = passage(style, seed=3, bars=16)
        assert sum(line.startswith("bar ") and "(" in line for line in lines) >= 16
        assert not any("ruled out" in line or "still crossed" in line for line in lines), style


def test_a_seed_replays_its_passage_and_another_differs():
    assert passage("salsa", seed=5) == passage("salsa", seed=5)
    assert passage("salsa", seed=5) != passage("salsa", seed=6)
