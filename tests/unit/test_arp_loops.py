# SPDX-License-Identifier: GPL-3.0-or-later
"""Loops of different lengths (task 3.12, from Tangerine): a calm section's arp figure runs 3 or 5 notes against the
bar's 8, its place kept across the chord changes, back in line at each phrase, the beat played harder."""
from dataclasses import replace

import pytest

from maestro.explain import flow_choices
from maestro.rng import ComposerRng
from maestro.stylebook import BOOK, StyleError
from maestro.theory.chords import Chord
from maestro.theory.flow import ARPS, Span, _arp_flow, arp_part, check_arp
from maestro.theory.pitch import Key
from maestro.theory.rhythm import METERS

MET = METERS["4/4"]
A_MINOR = Key(9, "minor")
UP = ("up", (0, 1, 2, 3), 1)


def _rng(seed):
    r = ComposerRng()
    r.seed(seed)
    return r


def _arp(n, energy=0.3, spans=None, bars=8):
    af = replace(ARPS["synthwave"], shapes=(UP,), loops=((n, 1),))
    spans = spans or [Span(b * MET.bar, MET.bar, Chord(0, "min")) for b in range(bars)]
    return arp_part(_rng(1), af, spans, lambda st: A_MINOR, 0, bars, MET, energy, phrase=4, loop_rng=_rng(2))


def test_a_loop_of_five_meets_the_bar_somewhere_new_and_is_back_in_line_each_phrase():
    notes, _, lines, n = _arp(5)
    assert n == 5 and "cut to a loop of 5 (0 1 2 3 0) against the bar's 8" in lines[0]
    first = [m for st, _, m in notes if st % MET.bar == 0]              # the note on each bar's start
    assert first[:4] == [60, 72, 64, 60]                              # tones 0, 3, 1, 0 of C E A C: it drifts
    assert first[4:] == first[:4]                                     # bar 4 starts a phrase: in line again
    phrase = [m for st, _, m in notes if st < 4 * MET.bar]
    assert all(phrase[i] == phrase[i + 5] for i in range(len(phrase) - 5))


def test_the_loop_keeps_its_place_across_a_chord_change():
    spans = [Span(0, 48, Chord(0, "min")), Span(48, 48, Chord(8)), Span(96, 288, Chord(0, "min"))]
    notes, *_ = _arp(3, spans=spans, bars=4)
    after = next(m for st, _, m in notes if st == 48)                 # the 5th note, the loop's 2nd, on bVI
    assert after == 65                                                 # C F A up from C4: its 2nd tone is F4
    assert check_arp(notes, spans, lambda st: A_MINOR) is None


def test_loud_sections_and_styles_without_loops_play_as_before():
    plain = replace(ARPS["synthwave"], shapes=(UP,), loops=())
    spans = [Span(b * MET.bar, MET.bar, Chord(0, "min")) for b in range(4)]
    for energy in (0.3, 0.8):
        a = arp_part(_rng(1), plain, spans, lambda st: A_MINOR, 0, 4, MET, energy)
        b = _arp(5, energy=energy, spans=spans, bars=4)
        assert (a[0] == b[0]) == (energy >= 0.5) and b[3] == (0 if energy >= 0.5 else 5)


def test_a_long_synthwave_play_loops_its_calm_sections_and_stays_on_its_chords():
    take = flow_choices("synthwave", 10, 120, A_MINOR, 112, layers=False)[1]
    assert take["looped"]
    calm = [p for p in take["plan"] if p["section"].energy < 0.5]
    assert all("a loop of" in p["arp"] for p in calm)
    assert not any("a loop of" in p["arp"] for p in take["plan"] if p not in calm)
    key_at = lambda st: next(r["key"] for r in take["bars"] if r["bar"] == st // MET.bar)
    assert check_arp(take["arp"], take["spans"], key_at) is None


@pytest.mark.parametrize("bad", [{"lengths": {"4": 1}}, {"lengths": {"2": 1}}, {"lengths": {"5": 1}, "accent": 90}])
def test_the_book_refuses_bad_loops(monkeypatch, bad):
    monkeypatch.setitem(BOOK["synthwave"]["members"]["arp"], "loops", bad)
    with pytest.raises(StyleError, match="loops"):
        _arp_flow("synthwave")
