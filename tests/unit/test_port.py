# SPDX-License-Identifier: GPL-3.0-or-later
"""The port on its own (the parity test checks it against the C; these run without Ouralia)."""
from maestro.port import Composer, MODES, PARENT, SCALE_IV, f32


def play(seed, scale=0, bars=200, color=0):
    c = Composer(seed=seed)
    c.send("color", color)
    c.send("scale", scale)
    c.send("start")
    for _ in range(bars):
        c.send("bar")
    return [v for o, v in c.out if o == "chord"], [v for o, v in c.out if o == "sect"]


def test_same_seed_same_piece_other_seed_other_piece():
    assert play(3)[0] == play(3)[0] != play(4)[0]


def test_chords_stay_in_their_scale():
    for s in range(8):
        parent = MODES[PARENT[s]]
        notes = set(parent["iv"][:parent["n"]])
        chords, sects = play(s + 1, scale=s, color=1)
        assert len(chords) > 50 and len(sects) >= 3
        for ch in chords:
            assert 0 <= ch[0] < len(SCALE_IV[s]) and ch[1] in notes
            assert {n % 12 for n in ch[2:]} <= notes


def test_starts_home():
    chords, sects = play(9)
    assert sects[0] == [0, 0] and sorted(n % 12 for n in chords[0][2:5]) == [0, 4, 7]


def test_f32():
    assert f32(0.1) != 0.1 and f32(f32(0.1)) == f32(0.1) and f32(2.5) == 2.5
