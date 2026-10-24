# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from maestro.rng import ComposerRng
from maestro.theory.rhythm import (CLAVES, FEEL, METERS, RHYTHM, STEPS, TICK, VALUES, Feel, Meter,
                                   check_band_rhythm, check_clave, check_onsets, choose_onsets, explain_feel,
                                   explain_onsets, feel_for, from_tick16, meter, place, roll, to_step, velocity)

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
    assert [place(s) for s in (0, 6, 12, 24)] == [0, 120, 240, 480]


def test_swing_moves_the_off_beat_to_a_later_step():
    assert place(12, Feel(swing=4)) == 320                    # triplet swing: the "and" on the third triplet
    assert place(12, Feel(swing=6)) == 360                    # hard swing, 75:25
    assert place(24, Feel(swing=6)) == 480                    # the beat never moves
    assert place(6, Feel(swing=2, unit=6)) == 160             # swung 16ths, triplet
    assert place(6, Feel(swing=6)) == 180                     # a 16th inside a swung 8th moves with it
    with pytest.raises(ValueError):
        Feel(swing=7)


def test_every_note_lands_on_a_grid_step():
    sixteenths = list(range(0, 96, 6))
    assert check_band_rhythm({"drums": (sixteenths, Feel(swing=4))}, M44) == []    # 6 -> 8: on the triplet
    why = check_band_rhythm({"drums": (sixteenths, Feel(swing=1))}, M44)           # 6 -> 6.5
    assert why and "off the grid" in why[0]


def test_swung_on_straight_is_out_of_sync():
    eighths = list(range(0, 96, 12))
    band = {"drums": (eighths, Feel(swing=4)), "bass": (eighths, Feel())}
    why = check_band_rhythm(band, M44)
    assert why and "out of sync" in why[0] and "1 and" in why[0]
    same = {"drums": (eighths, Feel(swing=4)), "bass": (eighths, Feel(swing=4))}
    assert check_band_rhythm(same, M44) == []
    apart = {"drums": ([12, 36], Feel(swing=4)), "bass": ([0, 24], Feel())}   # never on the same step: fine
    assert check_band_rhythm(apart, M44) == []


def test_every_member_lines_up_with_the_songs_clave():
    son = CLAVES["son_2-3"]
    band = {"percussion": (list(son.onsets), Feel()), "drums": (list(CLAVES["son_3-2"].onsets), Feel())}
    why = check_band_rhythm(band, M44, clave=son)
    assert len(why) == 1 and why[0].startswith("the drums is crossed")


def test_every_style_draft_is_on_the_grid_and_in_sync():
    on = list(range(0, 96, 3))
    for style in FEEL:
        band = {r: (on, feel_for(style, r)) for r in ("drums", "bass", "guitar", "keys", "percussion", "pad")}
        assert check_band_rhythm(band, M44) == [], style


def test_accents():
    f = Feel(accent=20)
    assert velocity(0, M44, f) == 96
    assert velocity(48, M44, f) > velocity(24, M44, f) > velocity(12, M44, f) > velocity(6, M44, f)
    assert velocity(48, M44, Feel(pulse="half")) > velocity(24, M44, Feel(pulse="half"))


def test_feel_drafts_per_member():
    for style, table in FEEL.items():
        assert "*" in table, style
    assert feel_for("trap", "bass").pulse == "half"
    assert feel_for("synthwave", "drums", swing=4).swing == 4                                 # a control overrides
    assert RHYTHM["salsa"].clave in CLAVES


def test_explain_feel():
    assert explain_feel(Feel()) == "straight, on the grid"
    assert explain_feel(Feel(swing=2, unit=6, pulse="half")) == "swung 16ths (67:33), on the grid, half-time"
