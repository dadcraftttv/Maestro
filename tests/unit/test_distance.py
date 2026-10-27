# SPDX-License-Identifier: GPL-3.0-or-later
"""Chord moves by shared notes (task 3.11, from Tangerine): a style's `distance` leans the harmony's choices (the
key move at a section, the family after a seam, a swapped chord) to the near or the far, gently, never past twice."""
from dataclasses import replace

import pytest

from maestro.rng import ComposerRng
from maestro.stylebook import BOOK, StyleError
from maestro.theory.chords import VOCAB, Chord
from maestro.theory.flow import FLOW, Family, _flow, closeness, progression, shared
from maestro.theory.form import MOVES, lean, notes_apart
from maestro.theory.pitch import Key
from maestro.theory.rhythm import METERS

MET = METERS["4/4"]
A_MINOR = Key(9, "minor")


def _rng(seed):
    r = ComposerRng()
    r.seed(seed)
    return r


def test_keys_are_counted_by_the_scale_notes_they_differ_by():
    assert [notes_apart(A_MINOR, MOVES[m](A_MINOR)) for m in ("relative", "fifth_down", "tone_up", "step_up")] \
        == [0, 1, 2, 5]


def test_chords_are_counted_by_the_notes_they_share_each_in_its_own_key():
    am, f = Chord(0, "min"), Chord(8)                        # i and bVI in A minor: A C E, F A C
    assert shared(am, A_MINOR, f, A_MINOR) == 2
    assert shared(am, A_MINOR, Chord(9, "min"), Key(0, "major")) == 3   # vi of C major is the same A minor
    assert closeness(am, A_MINOR, Chord(10), A_MINOR) == 0  # bVII: G B D


def test_the_lean_is_gentle_and_leaves_no_pull_alone():
    w, near = {"a": 3, "b": 3, "c": 3}, {"a": 1.0, "b": 0.5, "c": 0.2}
    assert lean(w, near, 0) == w
    assert lean(w, dict.fromkeys(w, 0.4), 2) == w           # every choice as close: nothing to lean on
    calm, lift = lean(w, near, 2), lean(w, near, -1)
    assert calm["a"] == 2 * calm["c"] and calm["c"] < calm["b"] < calm["a"]
    assert lift["c"] == 1.5 * lift["a"]


def test_only_synthwave_names_a_distance_so_the_others_draw_as_before():
    assert {s for s, f in FLOW.items() if f.distance} == {"synthwave"}
    d = FLOW["synthwave"].distance
    assert d["calm"] > d["home"] > d["turn"] == 0 > d["lift"]


@pytest.mark.parametrize("bad", [{"chorus": 1}, {"calm": 3}, {"calm": True}, {"lift": 0.5}])
def test_the_book_refuses_a_bad_distance(monkeypatch, bad):
    monkeypatch.setitem(BOOK["synthwave"]["harmony"]["progressions"], "distance", bad)
    with pytest.raises(StyleError, match="distance"):
        _flow("synthwave")


def test_after_a_seam_the_family_sharing_more_notes_is_likelier():
    near, far = Family("near", "i | bVII"), Family("far", "bVII | i")
    flow = replace(FLOW["synthwave"], families=(near, far), variants={"again": 1}, cadence=0)
    seam = (Chord(0, "min"), A_MINOR)                        # i heard last: "near" opens on it, "far" on bVII
    voc = VOCAB["synthwave"]

    def count(kind):
        return sum(progression(_rng(s), flow, A_MINOR, voc, 0, 8, MET, 8, None, kind, seam)[1] is near
                   for s in range(400))
    calm, turn, lift = count("calm"), count("turn"), count("lift")
    assert calm > 240 and 160 < turn < 240 and lift < 200   # 2:1, even, 2:3
