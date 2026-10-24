# SPDX-License-Identifier: GPL-3.0-or-later
"""The two drift measures (decision 9): a loop scores stale, random notes fresh, a replayed play the same."""
import random

from maestro import baseline, drift
from maestro.song import Song
from maestro.theory.rhythm import STEPS


def _song(bars, pick, tempo=120):
    """A two-member song; pick(rng, bar) gives the melody's (step, pitch) list for a bar."""
    s = Song(tempo=tempo)
    mel, drums = s.member("lead", "melody"), s.member("kit", "drums", kit=True)
    rng, bar = random.Random(3), s.bar_steps()
    for b in range(bars):
        for step, pitch in pick(rng, b):
            mel.add(b * bar + step, STEPS // 2, pitch)
        drums.add(b * bar, STEPS, 36)
    return s


LOOP = lambda rng, b: [(0, 60), (STEPS, 64), (2 * STEPS, 67)]
FRESH = lambda rng, b: [(i * STEPS // 2, rng.randrange(48, 84)) for i in range(8)]


def test_a_loop_is_stale():
    m = drift.staleness(drift.from_song(_song(64, LOOP)))
    assert m["phrases_copied"] > 0.9 and m["longest_copy"] == 63 and m["melody_bars_copied"] > 0.9
    assert m["fresh_worst_window"] < 0.05
    v = drift.verdict(m)
    assert not any(v[k][2] for k in ("phrases_copied", "longest_copy", "melody_bars_copied", "fresh_worst_window"))


def test_random_notes_are_fresh_and_two_seeds_differ():
    a, b = drift.from_song(_song(64, FRESH)), drift.from_song(_song(64, lambda r, i: FRESH(random.Random(i), i)))
    assert all(ok for _, _, ok in drift.verdict({**drift.staleness(a), **drift.sameness(a, b)}).values())


def test_a_replayed_play_is_the_same():
    a = drift.from_song(_song(32, FRESH))
    m = drift.sameness(a, drift.from_song(_song(32, FRESH)))
    assert m == {"same_bar_same_place": 1.0, "phrases_shared": 1.0, "longest_shared_run": 32}


def test_a_held_note_sounds_into_the_next_bars():
    s = Song()
    s.member("pad", "pad").add(0, 3 * s.bar_steps(), 60)
    p = drift.from_song(s)
    assert p.bars["pad"][1] == p.bars["pad"][2] == ((-1, s.bar_steps(), 60),) != p.bars["pad"][0]


def test_todays_composer_meets_the_targets_over_20_minutes():
    bars = 20 * 92 // 4
    one, two = (baseline.clip(s, bars=bars, walk_from=bars) for s in (11, 12))
    assert not [n for n in one.members if n.name == "arp"][0].notes   # never walks
    p = drift.from_song(one)
    v = drift.verdict({**drift.staleness(p), **drift.sameness(p, drift.from_song(two))})
    assert len(v) == len(drift.TARGETS) and all(ok for _, _, ok in v.values()), v
