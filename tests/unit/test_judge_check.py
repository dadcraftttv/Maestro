# SPDX-License-Identifier: GPL-3.0-or-later
"""Checking the style judge (task 3.5c): today's clips pass their own cards, wrong clips don't (a member from another
style, the velocities flattened, every note a 16th off the style's steps), a member swapped in with its own style is
scored by that style (decision 17), and SynTheory's chord progressions read back as they were written."""
import dataclasses as dc
from functools import cache

import pytest

from maestro import judge
from maestro.sketch import flow_sketch
from maestro.song import Song
from maestro.theory.rhythm import STEPS

STYLES = ("trap", "synthwave", "salsa", "power_rock")
S16 = STEPS // 4
BAR = 4 * STEPS


@cache
def _clip(style, seed=7):
    return judge.from_song(flow_sketch(style, seed, 16)[0])


def _swap(clip, other, role, label=False):
    """`clip` with its `role` member played by `other`'s (labelled with its style or not)."""
    mine = next(n for n, p in clip.players.items() if p.role == role)
    theirs = next(p for p in _clip(other).players.values() if p.role == role)
    return mine, dc.replace(clip, players={**clip.players, mine: theirs},
                            styles={**clip.styles, mine: other} if label else clip.styles)


def _each_note(clip, f):
    return dc.replace(clip, players={n: dc.replace(p, notes=[f(x) for x in p.notes]) for n, p in clip.players.items()})


@pytest.mark.parametrize("style", STYLES)
def test_today_s_clips_pass_their_own_cards(style):
    for seed in (1, 2, 3):
        c = _clip(style, seed)
        assert judge.passes(judge.score(c)), (style, seed, judge.weakest(judge.score(c)))
        assert next(iter(judge.cross(c))) == style


@pytest.mark.parametrize("style, other, role", [
    ("trap", "power_rock", "drums"), ("synthwave", "trap", "drums"), ("power_rock", "trap", "drums"),
    ("salsa", "trap", "bass"), ("power_rock", "trap", "bass"), ("synthwave", "salsa", "bass"),
    ("trap", "synthwave", "bass"), ("salsa", "power_rock", "bass")])
def test_a_member_from_another_style_fails(style, other, role):
    name, c = _swap(_clip(style), other, role)
    rows = judge.score(c)
    assert not judge.passes(rows) and judge.weakest(rows)[0] == name


@pytest.mark.parametrize("style, other", [("trap", "power_rock"), ("synthwave", "trap"), ("power_rock", "trap")])
def test_a_member_swapped_in_with_its_style_is_scored_by_it(style, other):
    # DadCraft, Oct 26: any member can be hot-swapped for another style's and still make sense; the judge scores
    # it by the style it's meant to be (a drummer: its card doesn't hang on the band's chords)
    name, c = _swap(_clip(style), other, "drums", label=True)
    assert judge.members(judge.score(c))[name] == pytest.approx(1.0, abs=0.05)


def test_a_swapped_member_s_style_reads_back_from_the_song_file(tmp_path):
    song, _ = flow_sketch("trap", 7, 16)
    drums = next(m for m in song.members if m.role == "drums")
    drums.notes, drums.style = list(next(m for m in flow_sketch("power_rock", 7, 16)[0].members
                                         if m.role == "drums").notes), "power_rock"
    song.write(str(tmp_path / "c"))
    c = judge.from_file(str(tmp_path / "c.mid"))
    assert c.style_of(drums.name) == "power_rock" and judge.passes(judge.score(c))


@pytest.mark.parametrize("style, member", [("trap", "drums"), ("power_rock", "drums")])
def test_flattened_velocities_are_named(style, member):
    flat = _each_note(_clip(style), lambda n: dc.replace(n, velocity=96))
    assert any(r.member == member and r.trait == "velocity" and not r.ok for r in judge.score(flat))


@pytest.mark.parametrize("style", STYLES)
def test_every_note_a_16th_late_leaves_the_style_s_steps(style):
    c = _each_note(_clip(style), lambda n: dc.replace(n, step=n.step + S16))
    rows = judge.score(c)
    assert any(r.trait.startswith("step") and not r.ok for r in rows)
    if style != "trap":   # trap's hats roll on every 16th; its clap's step 3 is named, the drums' mean holds
        assert not judge.passes(rows)


# SynTheory (brown-palm/syntheory, MIT): its chord progressions, rebuilt here from its recipe (two triads a bar at
# 120 BPM, every key, Ionian and Aeolian), our code, not theirs. Degrees of the scale, 1-based.
PROGRESSIONS = {
    "major": [(1, 4, 5, 1), (1, 4, 6, 5), (1, 5, 6, 4), (1, 6, 4, 5), (2, 5, 1, 6), (4, 1, 5, 6), (4, 5, 3, 6),
              (5, 4, 1, 5), (5, 6, 4, 1), (6, 4, 1, 5)],
    "minor": [(1, 2, 5, 1), (1, 3, 4, 1), (1, 4, 5, 1), (1, 6, 3, 7), (1, 6, 7, 1), (1, 6, 7, 3), (1, 7, 6, 4),
              (4, 7, 1, 1), (7, 6, 7, 1)],
}
SCALES = {"major": (0, 2, 4, 5, 7, 9, 11), "minor": (0, 2, 3, 5, 7, 8, 10)}
NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def _triad(key, scale, degree):
    sc = SCALES[scale]
    pcs = [(key + sc[(degree - 1 + k) % 7]) % 12 for k in (0, 2, 4)]
    third, fifth = (pcs[1] - pcs[0]) % 12, (pcs[2] - pcs[0]) % 12
    return pcs, NAMES[pcs[0]] + {(4, 7): "", (3, 7): "m", (3, 6): "dim"}[(third, fifth)]


def _progression(key, scale, degrees, timeline_shift=0):
    """Two bars, a triad every 2 beats on a pad; the timeline names each chord from its beat (after the first,
    shifted if asked)."""
    s = Song(tempo=120, source={"style": "trap"})
    pad = s.member("pad", "pad")
    for i, d in enumerate(degrees):
        pcs, name = _triad(key, scale, d)
        at = i * 2 * STEPS
        for pc in pcs:
            pad.add(at, 2 * STEPS, 48 + pc)
        mark = at + timeline_shift if i else at
        s.timeline.append({"bar": mark // BAR, "beat": mark % BAR // STEPS, "chord": name})
    return judge.from_song(s)


@pytest.mark.parametrize("scale", ["major", "minor"])
def test_syntheory_s_progressions_read_back_as_written(scale):
    for key in range(12):
        for degrees in PROGRESSIONS[scale]:
            c = _progression(key, scale, degrees)
            pad = c.players["pad"].notes
            assert judge.measure("chord tones", pad, c, "pad") == 100, (key, degrees)
            changes = sum(a != b for a, b in zip(degrees, (None,) + degrees))
            got = [r for r in judge.score(c, "salsa") if r.trait == "chords"][0].value
            assert got == changes / 2, (key, degrees)


def test_a_timeline_a_chord_late_is_caught():
    # each chord after the first named when the next sounds: the pad plays under the chord before
    for scale, progs in PROGRESSIONS.items():
        for degrees in progs:
            c = _progression(0, scale, degrees, timeline_shift=2 * STEPS)
            assert judge.measure("chord tones", c.players["pad"].notes, c, "pad") < 100, (scale, degrees)
