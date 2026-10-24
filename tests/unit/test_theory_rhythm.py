# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from maestro.rng import ComposerRng
from maestro.theory.rhythm import (CLAVES, FEEL, METERS, RHYTHM, STEPS, TICK, VALUES, Feel, Meter, check_clave,
                                   check_onsets, choose_onsets, explain_feel, explain_onsets, feel_for,
                                   from_tick16, meter, place, roll, to_step, velocity)

M44, M34, M68, M128, M78 = (METERS[m] for m in ("4/4", "3/4", "6/8", "12/8", "7/8"))


def rng(seed=1):
    r = ComposerRng()
    r.seed(seed)
    return r


# ---- the grid ----

def test_every_note_value_lands_on_the_grid():
    assert all(isinstance(v, int) for v in VALUES.values())
    assert VALUES["32nd"] * 8 == STEPS and VALUES["16th_triplet"] * 6 == STEPS and VALUES["32nd_triplet"] * 12 == STEPS
    assert TICK * STEPS == 480


def test_todays_tick16_is_every_sixth_step():
    assert [from_tick16(i) for i in (0, 1, 4, 15)] == [0, 6, 24, 90]


def test_ticks_round_to_the_nearest_step():
    assert to_step(0) == (0, 0)
    assert to_step(125) == (6, 5)       # a 16th, 5 ticks late
    assert to_step(109) == (5, 9)


# ---- meters ----

def test_meters_and_their_beats():
    assert M44.bar == 96 and M44.beats == (0, 24, 48, 72)
    assert M34.bar == 72 and M34.beats == (0, 24, 48)
    assert M68.bar == 72 and M68.beats == (0, 36) and M68.compound
    assert M128.bar == 144 and M128.beats == (0, 36, 72, 108)
    assert M78.beats == (0, 24, 48) and not M78.compound
    assert meter("7/8", (3, 2, 2)).beats == (0, 36, 60)
    assert meter("9/8").groups == (3, 3, 3)
    with pytest.raises(ValueError):
        Meter(7, 8, (2, 2))


def test_metric_weight_falls_from_the_downbeat():
    assert [M44.weight(s) for s in (0, 48, 24, 12, 6, 3, 8)] == [5, 4, 3, 2, 1, 0, 0]
    assert [M68.weight(s) for s in (0, 36, 12, 6)] == [5, 4, 2, 1]


def test_backbeat_and_half_time():
    assert M44.backbeat() == (24, 72)
    assert M44.backbeat("half") == (48,)               # trap: the snare on 3
    assert M44.backbeat("double") == (12, 36, 60, 84)
    assert M128.backbeat() == (36, 108)
    assert M34.backbeat() == (24, 48)                   # waltz: 2 and 3
    assert M44.weight(48, "half") == 4 and M44.weight(24, "half") == 2


def test_counting():
    assert [M44.count(s) for s in (0, 30, 36, 66, 8, 16)] == ["1", "2 e", "2 and", "3 a", "1 trip", "1 let"]
    assert [M68.count(s) for s in (0, 36, 42)] == ["1", "4", "4 and"]
    assert explain_onsets(CLAVES["son_3-2"].onsets, M44) == "bar 1: 1, 2 and, 4 | bar 2: 2, 3"


# ---- clave ----

def test_claves_and_their_directions():
    assert explain_onsets(CLAVES["son_2-3"].onsets, M44) == "bar 1: 2, 3 | bar 2: 1, 2 and, 4"
    assert explain_onsets(CLAVES["rumba_3-2"].onsets, M44) == "bar 1: 1, 2 and, 4 and | bar 2: 2, 3"
    assert CLAVES["son_3-2"].flipped() == CLAVES["son_2-3"]
    assert len(CLAVES["bell_6/8"].onsets) == 7 and not CLAVES["bell_6/8"].two_sided


def test_a_crossed_part_is_ruled_out():
    son = CLAVES["son_2-3"]
    assert check_clave(son.onsets, son) is None
    why = check_clave(CLAVES["son_3-2"].onsets, son)
    assert why and "crossed" in why and "son_3-2" in why


def test_a_part_the_same_each_bar_never_crosses():
    tumbao = [36, 72, 132, 168]          # 2 and, 4 in both bars: the bass's tumbao
    assert check_clave(tumbao, CLAVES["son_2-3"]) is None
    assert check_clave(tumbao, CLAVES["son_3-2"]) is None


def test_check_onsets():
    assert check_onsets([0, 24, 48], M44) is None
    assert "outside" in check_onsets([96], M44)
    assert "between" in check_onsets([1.5], M44)
    assert "same step" in check_onsets([0, 0], M44)
    assert "crossed" in check_onsets(CLAVES["son_3-2"].onsets, M44, bars=2, clave=CLAVES["son_2-3"])


# ---- the choose ----

def test_choose_is_seeded_and_fits():
    a = choose_onsets(rng(7), M44, 6, RHYTHM["synthwave"], bars=2)
    assert a == choose_onsets(rng(7), M44, 6, RHYTHM["synthwave"], bars=2)
    assert a != choose_onsets(rng(8), M44, 6, RHYTHM["synthwave"], bars=2)
    assert len(a) == 6 and check_onsets(a, M44, bars=2) is None


def test_choose_keeps_given_onsets():
    out = choose_onsets(rng(3), M44, 4, keep=(0, 48))
    assert {0, 48} <= set(out) and len(out) == 4


def test_styles_lean_their_way():
    def share(style, test, n=6, runs=200):
        hits = total = 0
        for seed in range(runs):
            for s in choose_onsets(rng(seed), M44, n, RHYTHM[style]):
                hits += test(s)
                total += 1
        return hits / total
    on_beat = lambda s: s % 24 == 0
    assert share("synthwave", on_beat) > share("salsa", on_beat)        # salsa anticipates, synthwave sits on it
    triplet = lambda s: s % 6 != 0
    assert share("synthwave", triplet) == 0 and share("trap", triplet) > 0
    assert share("plain", triplet) == 0


def test_choose_says_when_it_cant():
    with pytest.raises(ValueError):
        choose_onsets(rng(), M44, 17, RHYTHM["synthwave"])   # 16 straight 16ths in a bar, no more


def test_rolls():
    assert roll(72, 24, "32nd") == list(range(72, 96, 3))
    assert roll(72, 24, "16th_triplet") == [72, 76, 80, 84, 88, 92]
    with pytest.raises(ValueError):
        roll(0, 24, "64th")


# ---- feel ----

def test_straight_places_on_the_grid():
    assert [place(rng(), s) for s in (0, 6, 12, 24)] == [0, 120, 240, 480]


def test_swing_moves_the_off_beat_late():
    assert place(rng(), 12, Feel(swing=2 / 3)) == 320          # triplet swing: the "and" on the third triplet
    assert place(rng(), 12, Feel(swing=1)) == 360              # hard swing, 75:25
    assert place(rng(), 24, Feel(swing=1)) == 480              # the beat never moves
    assert place(rng(), 6, Feel(swing=0.5, unit=6)) == 150     # swung 16ths
    assert place(rng(), 6, Feel(swing=1)) == 180               # a 16th inside a swung 8th moves with it


def test_push_and_jitter():
    assert place(rng(), 24, Feel(push=4)) == 484
    ticks = [place(rng(s), 24, Feel(jitter=6)) for s in range(100)]
    assert min(ticks) >= 474 and max(ticks) <= 486 and len(set(ticks)) > 5
    assert place(rng(5), 24, Feel(jitter=6)) == place(rng(5), 24, Feel(jitter=6))


def test_accents():
    f = Feel(accent=20)
    assert velocity(0, M44, f) == 96
    assert velocity(48, M44, f) > velocity(24, M44, f) > velocity(12, M44, f) > velocity(6, M44, f)
    assert velocity(48, M44, Feel(pulse="half")) > velocity(24, M44, Feel(pulse="half"))


def test_feel_drafts_per_member():
    for style, table in FEEL.items():
        assert "*" in table, style
    assert feel_for("trap", "bass").pulse == "half" and feel_for("trap", "bass").jitter == 0     # programmed
    assert feel_for("power_rock", "drums").jitter > 0                                          # human
    assert feel_for("power_rock", "bass").push > 0                                             # laid back
    assert feel_for("synthwave", "drums", swing=0.3).swing == 0.3                              # a control overrides
    assert RHYTHM["salsa"].clave in CLAVES


def test_explain_feel():
    assert explain_feel(Feel()) == "straight, tight to the grid"
    assert explain_feel(feel_for("power_rock", "bass")) == "straight, 4 ticks behind the beat, loose by up to 4 ticks"
    assert explain_feel(Feel(swing=2 / 3, unit=6, pulse="half")) == "swung 16ths (67:33), tight to the grid, half-time"
