# SPDX-License-Identifier: GPL-3.0-or-later
"""DNA nudges (task 3.9): a step leans the style's own choices, inside its bounds, and moves what it says."""
import statistics as st

import pytest

from maestro import judge
from maestro.sketch import flow_sketch
from maestro.stylebook import BOOK, STYLES, forget
from maestro.theory.flow import FLOW
from maestro.theory.nudge import axes, density, lean, nudged, parse, syncopation


@pytest.fixture(autouse=True)
def _clean_book():
    """The nudged styles a test makes leave the book after it, so other tests see only the book's own."""
    yield
    for name in [s for s in BOOK if "~" in s]:
        forget(name)


def test_lean_keeps_the_styles_choices():
    w = {"a": 4, "b": 1, "off": 0}
    got = lean(w, {"a": 1, "b": 8, "off": 8}.get, 5)
    assert got["off"] == 0 and got["a"] >= 1             # 0 stays out, a played option stays playable
    assert got["b"] / got["a"] > w["b"] / w["a"]         # leaned to the one measuring more
    assert lean(w, {"a": 1, "b": 8, "off": 8}.get, -5)["b"] / lean(w, {"a": 1, "b": 8, "off": 8}.get, -5)["a"] < 1 / 4
    assert lean(w, lambda k: 3, 5) == {k: 4 * v for k, v in w.items()}   # nothing to tell apart: same balance


def test_opposites_cancel_and_steps_hold():
    assert axes([("energetic", 3), ("minimal", 3)])["energy"] == 0
    assert axes([("minimal", 5), ("minimal", 5)])["energy"] == -5
    assert axes([("funky", 5), ("funky", 2)])["funk"] == 5
    assert parse("energetic=2,bass:funky=1") == [("band", "energetic", 2), ("bass", "funky", 1)]
    with pytest.raises(ValueError):
        nudged("synthwave", [("band", "louder", 1)])
    with pytest.raises(ValueError):
        nudged("synthwave", [("band", "funky", 6)])


def test_measures_of_an_option():
    assert density({"bars": [[0, 4, 8, 12], [0, 8]]}) == 3
    assert density({"bars": ["x x xx o - - x x"]}) == 7
    assert syncopation({"notes": [[0, 2, "root", "now"], [3, 1, "root", "now"]]}) == 0.5
    assert syncopation({"bars": ["xx xx xx xx xx xx xx xx"]}) == 0
    assert syncopation({"notes": [[6, None, "root", "ahead"]]}) == 1


def test_a_nudged_style_joins_the_book_but_not_styles():
    for style in ("synthwave", "trap", "salsa", "power_rock"):
        name = nudged(style, [("band", "energetic", 5), ("band", "funky", 5), ("band", "soulful", 5),
                              ("band", "sophisticated", 5), ("bass", "minimal", 5)])
        assert name in BOOK and name in FLOW and name not in STYLES
        flow_sketch(name, 1, 16)                          # its tables built, it plays
        base, new = BOOK[style]["members"], BOOK[name]["members"]
        assert set(base) == set(new)                      # no member added
        for role, m in base.items():
            for kind in ("patterns", "shapes"):
                if isinstance(m, dict) and isinstance(m.get(kind), dict):
                    added = set(new[role][kind]) - set(m[kind])     # only funky's pushes (DadCraft, Oct 27)
                    assert set(m[kind]) <= set(new[role][kind]) and all(k.endswith(", pushed") for k in added)


def _means(style, seeds=range(1, 13), bars=32):
    acc = {}
    for s in seeds:
        song = flow_sketch(style, s, bars)[0]
        clip = judge.from_song(song)
        for name, p in clip.players.items():
            for t in ("notes", "syncopation", "velocity"):
                acc.setdefault((p.role, t), []).append(judge.measure(t, p.notes, clip, name))
        acc.setdefault("fit", []).append(judge.fit(judge.score(clip)))
        acc.setdefault("bends", []).append(sum(p.slides for p in clip.players.values() if p.role == "melody") / clip.bars)
        acc.setdefault("band notes", []).append(sum(len(p.notes) for p in clip.players.values()) / clip.bars)
        ch = [e["chord"] for e in song.timeline if e.get("chord")]
        acc.setdefault("colour", []).append(sum(("7" in c or "9" in c) for c in ch) / len(ch))
    return {k: st.mean(v) for k, v in acc.items()}


# each direction at three steps on synthwave (DadCraft's style for the first listen): what it says it moves
MOVES = {"energetic": [("band notes", 1), (("bass", "notes"), 1)],
         "minimal": [("band notes", -1), (("arp", "notes"), -1)],   # fewer members too: notes a played bar may rise
         "funky": [(("bass", "syncopation"), 1), (("melody", "syncopation"), 1)],
         "soulful": [(("bass", "velocity"), 1), (("melody", "velocity"), 1), ("bends", 1)],
         "sophisticated": [("colour", 1)]}


def test_each_direction_moves_its_own_measures():
    base, got = _means("synthwave"), {}
    for d, moves in MOVES.items():
        g = got[d] = _means(nudged("synthwave", [("band", d, 3)]))
        for key, sign in moves:
            assert (g[key] - base[key]) * sign > 0, f"{d}+3 didn't move {key}: {base[key]:.2f} -> {g[key]:.2f}"
        assert g["fit"] >= base["fit"] - 0.02, f"{d}+3 lowered the judge's fit"
    # DadCraft (Oct 27): soulful and sophisticated sounded alike; soulful is the feel, sophisticated the harmony
    assert got["sophisticated"]["colour"] - base["colour"] > 2 * (got["soulful"]["colour"] - base["colour"])
    assert got["sophisticated"]["bends"] == base["bends"] < got["soulful"]["bends"]


@pytest.mark.parametrize("direction", sorted(MOVES))
def test_five_steps_stay_inside_the_styles_card(direction):
    """Decision 9 and 3.9's own rule: even at five steps the style's judge passes it (minimal at +4 once dropped
    synthwave's backbeat, Oct 27)."""
    name = nudged("synthwave", [("band", direction, 5)])
    for s in range(1, 7):
        clip = judge.from_song(flow_sketch(name, s, 48)[0])
        clip.style = "synthwave"
        assert judge.passes(judge.score(clip)), f"{direction}+5, seed {s}: {judge.weakest(judge.score(clip))}"
