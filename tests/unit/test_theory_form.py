# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from maestro.rng import ComposerRng
from maestro.theory.form import (CALM_MAX, DEVELOP, FORM, LIFTS, STALE, Motif, Play, Section, Theme, Wave,
                                 check_key_change, check_motif, check_section, explain_section, fifths_apart,
                                 kinship, make_motif, MOVES)
from maestro.theory.pitch import Key
from maestro.theory.rhythm import VALUES

A_MIN, C_MAJ = Key(9, "minor"), Key(0, "major")


def rng(seed=1):
    r = ComposerRng()
    r.seed(seed)
    return r


def plays(minutes=20, seeds=range(1, 9)):
    for style, form in FORM.items():
        for seed in seeds:
            p = Play(rng(seed), A_MIN, form, bpm=100)
            yield style, p, p.plan(minutes)


# ---- the energy arc ----

def test_a_wave_builds_then_releases():
    w = Wave(0, 100, 0.8, 0.6)
    assert w.at(0) == 0 and w.at(60) == pytest.approx(0.8)
    assert w.at(30) < w.at(50) < w.at(60) > w.at(80)


def test_a_full_opening_starts_at_the_top():
    p = Play(rng(), A_MIN, FORM["power_rock"])
    assert p.arc(0) >= 0.6
    assert Play(rng(), A_MIN, FORM["synthwave"]).arc(0) == 0


def test_a_long_play_rises_and_falls_more_than_once():
    for _, p, _ in plays():
        assert len(p.waves) >= 3


# ---- sections ----

def test_section_checks_give_their_reasons():
    prev = Section("home", 0, 16, A_MIN, 0.5, 0.05)
    assert check_section("lift", 0.4) == "a play opens at Home"
    assert "doesn't lift" in check_section("lift", 0.5, prev)
    assert "too loud" in check_section("calm", CALM_MAX + 0.05, prev)
    assert "too hard" in check_section("turn", 0.95, prev)
    assert check_section("lift", 0.95, prev) is None      # a drop may jump
    lift = Section("lift", 16, 16, A_MIN, 0.7, 0.1)
    assert "twice" in check_section("lift", 0.9, lift)


def test_every_section_of_every_play_passes_the_check():
    for style, p, ss in plays():
        assert ss[0].kind == "home" and ss[0].start == 0
        for prev, s in zip(ss, ss[1:]):
            assert s.start == prev.end
            assert s.bars % p.form.phrase == 0
            assert check_section(s.kind, s.energy, prev) is None, (style, explain_section(s, prev))


def test_sections_grow_heavier_as_they_go():
    s = Section("lift", 0, 16, A_MIN, 0.5, 0.1)
    assert s.energy_at(0) == 0.5 and s.energy_at(15) == pytest.approx(0.6)


def test_the_room_leans_the_plan():
    lo = Play(rng(4), A_MIN).plan(10, room=0.2)
    hi = Play(rng(4), A_MIN).plan(10, room=0.8)
    assert sum(s.energy for s in hi) / len(hi) > sum(s.energy for s in lo) / len(lo) + 0.3


# ---- key changes ----

def test_key_moves():
    assert MOVES["relative"](A_MIN) == C_MAJ and MOVES["relative"](C_MAJ) == A_MIN
    assert MOVES["parallel"](C_MAJ) == Key(0, "minor")
    assert MOVES["fifth_up"](A_MIN) == Key(4, "minor") and MOVES["step_up"](A_MIN) == Key(10, "minor")
    assert MOVES["relative"](Key(9, "minor_pent")) == C_MAJ


def test_fifths_apart_reads_the_relative_major():
    assert fifths_apart(A_MIN, C_MAJ) == 0
    assert fifths_apart(C_MAJ, Key(7, "major")) == 1 and fifths_apart(C_MAJ, Key(6, "major")) == 6


def test_key_change_checks_give_their_reasons():
    f, bpm = FORM["synthwave"], 25
    assert "too soon" in check_key_change(A_MIN, C_MAJ, "relative", "home", 20, 1, f, bpm)
    assert "belong on a Lift" in check_key_change(A_MIN, Key(10, "minor"), "step_up", "calm", 200, 1, f, bpm)
    assert check_key_change(A_MIN, Key(10, "minor"), "step_up", "lift", 200, 1, f, bpm) is None
    assert "too far" in check_key_change(A_MIN, C_MAJ, "relative", "home", 200, 3, f, bpm)
    assert "mode" in check_key_change(A_MIN, Key(9, "phrygian"), "relative", "home", 200, 1, f, bpm)


def test_key_changes_in_a_play_follow_the_rules():
    moved = 0
    for style, p, ss in plays():
        last, away = 0, 0
        for prev, s in zip(ss, ss[1:]):
            if s.move:
                moved += 1
                assert s.key != prev.key
                assert s.start - last >= p.form.gap * p.bars_a_minute, style
                assert s.move not in LIFTS or s.kind == "lift"
                last, away = s.start, (0 if s.key == A_MIN else away + 1)
                assert away <= p.form.hops
            else:
                assert s.key == prev.key
    assert moved > 0


def test_trap_keeps_to_its_dark_modes():
    for _, p, ss in plays():
        if p.form is FORM["trap"]:
            assert all(s.key.scale in FORM["trap"].scales for s in ss)


def test_no_two_plays_alike():
    a = [(s.kind, s.bars, s.key, round(s.energy, 3)) for s in Play(rng(1), A_MIN).plan(20)]
    b = [(s.kind, s.bars, s.key, round(s.energy, 3)) for s in Play(rng(2), A_MIN).plan(20)]
    assert a != b
    assert a == [(s.kind, s.bars, s.key, round(s.energy, 3)) for s in Play(rng(1), A_MIN).plan(20)]   # a seed replays


# ---- motifs ----

def test_motif_checks_give_their_reasons():
    e = VALUES["8th"]
    assert "one note" in check_motif(Motif((0,), (e,)))
    assert "off the grid" in check_motif(Motif((0, 1), (e, 2)))
    assert "two bars" in check_motif(Motif((0, 1, 2), (96, 96, 96)))
    assert "too wide" in check_motif(Motif((0, 4, 8), (e, e, e)))
    assert "too wild" in check_motif(Motif((0, 5), (e, e)))
    m = Motif((0, 1, 2), (e, e, e))
    assert "stale" in check_motif(m, recent=[m] * (STALE - 1))
    assert "no longer heard" in check_motif(Motif((0, 3, 0, 3), (24, 6, 6, 24)), origin=m)
    assert check_motif(m, origin=m) is None


def test_kinship_hears_inversions_retrogrades_and_augmentation():
    m = Motif((0, 2, 1, 3), (12, 12, 24, 12))
    assert kinship(m, DEVELOP["invert"](rng(), m)) == 1
    assert kinship(m, DEVELOP["back"](rng(), m)) == 1
    assert kinship(m, DEVELOP["augment"](rng(), m)) == 1
    assert kinship(m, Motif((0, 4, 0, 4), (6, 6, 6, 6))) < 0.5


def test_new_motifs_fit():
    r = rng(9)
    for _ in range(200):
        assert check_motif(make_motif(r)) is None


def test_a_theme_develops_and_is_reborn():
    t = Theme(rng(5), life=6)
    seen = [t.next() for _ in range(40)]
    hows = [h for _, h in seen]
    assert [i for i, h in enumerate(hows) if h == "reborn"] == list(range(6, 40, 6))
    assert len(set(hows)) >= 5
    recent = []
    for m, _ in seen:
        assert all(isinstance(n, int) for n in m.lengths)          # on the grid (decision 13)
        assert check_motif(m, recent=recent) is None
        recent = (recent + [m])[-STALE:]


def test_young_motifs_stay_closer_than_old_ones():
    near = far = 0
    for seed in range(1, 30):
        t = Theme(rng(seed), life=99)
        hows = [t.next()[1] for _ in range(10)]
        near += hows[:3].count("again")
        far += hows[7:].count("again")
    assert near > far


def test_explain_section():
    prev = Section("home", 0, 16, A_MIN, 0.4, 0.05)
    s = Section("lift", 16, 16, Key(10, "minor"), 0.6, 0.1, "step_up")
    assert explain_section(s, prev) == ("bar 17: a Lift in Bb minor for 16 bars, energy 0.60 growing to 0.70, up "
                                        "from 0.45; the key moves up a semitone (from A minor)")
