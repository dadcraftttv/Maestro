# SPDX-License-Identifier: GPL-3.0-or-later
from maestro.explain import _said, flow_choices, member_summary, passage, summary
from maestro.sketch import TEMPO
from maestro.stylebook import part
from maestro.theory.form import FORM


def test_every_style_explains_a_passage():
    for style in FORM:
        lines = passage(style, seed=3, bars=16, flow=False)
        assert sum(line.startswith("bar ") and "(" in line for line in lines) >= 16
        assert not any("ruled out" in line or "still crossed" in line for line in lines), style


def test_a_seed_replays_its_passage_and_another_differs():
    assert passage("salsa", seed=5) == passage("salsa", seed=5)
    assert passage("salsa", seed=5) != passage("salsa", seed=6)


def test_a_summary_stays_short_and_names_every_member():
    # task 3.7: about a dozen lines however long the clip, each member who plays said once
    for style in FORM:
        for bars in (16, 84):
            _, take = flow_choices(style, 12, bars, bpm=TEMPO[style])
            said = _said(style, 12, bars, TEMPO[style], take)
            assert len(summary(style, 12, bars, TEMPO[style], take)) <= 12, (style, bars)
            playing = {"bass", "melody", "listen"} | {k for k in ("guitar", "keys", "horns", "drums", "percussion",
                                                                   "arp") if take.get(k)}
            assert playing <= set(said), (style, bars, playing - set(said))
            assert ("pad" in said) == part(style, "members", "pad").get("plays", True), style
            for member in playing - {"listen"}:
                assert len(member_summary(style, 12, bars, TEMPO[style], take, member)) == 3, (style, member)
