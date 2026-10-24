# SPDX-License-Identifier: GPL-3.0-or-later
"""Trap's entry (task 3.4a): the 808 on the kicks and its slides, the snare fixed on 3, the hats turning, harmony
that barely moves, the motif's triplets, and the slides written as pitch bends."""
import mido
import pytest

from maestro.explain import flow_choices
from maestro.rng import ComposerRng
from maestro.sketch import flow_sketch
from maestro.stylebook import StyleError, part
from maestro.theory.chords import VOCAB, Chord
from maestro.theory.drums import BACKBEAT, DRUMMER, KIT, _drummer, check_drums
from maestro.theory.flow import BASS, FLOW, SLIDE, Family, Span, check_808, check_family
from maestro.theory.form import DEVELOPS, VALUES, Motif, _develop, _triplet, check_motif
from maestro.theory.pitch import Key
from maestro.theory.rhythm import METERS

MET = METERS["4/4"]
A_MINOR = Key(9, "minor")


def _rng(seed):
    r = ComposerRng()
    r.seed(seed)
    return r


def _takes(n=12, bars=32):
    return [flow_choices("trap", seed, bars, A_MINOR, 140)[1] for seed in range(300, 300 + n)]


def test_the_808_plays_on_the_kicks_and_slides_about_one_note_in_six():
    assert BASS["trap"].kick and not BASS["salsa"].kick
    notes = slides = 0
    for take in _takes():
        kicks = {h[0] for h in take["drums"] if h[4] == "kick"}
        changes = {s.at for s in take["spans"]}
        assert all(st in kicks | changes for st, _, _ in take["bass"])
        assert sum(st in kicks for st, _, _ in take["bass"]) > 0.6 * len(take["bass"])
        for at, steps, semis in take["slides"]:
            assert steps == SLIDE and 0 < abs(semis) <= 12
        notes, slides = notes + len(take["bass"]), slides + len(take["slides"])
    assert 1 / 9 < slides / notes < 1 / 4, (slides, notes)


def test_the_808_check_says_what_is_wrong():
    spans = [Span(0, 96, Chord(0, "min"))]
    key_at = lambda step: A_MINOR
    notes = [(0, 48, 45), (48, 48, 52)]                      # A, then E: root and fifth of Am
    assert check_808(notes, [(36, 12, 7)], [0, 48], spans, key_at) is None
    assert "no kick" in check_808(notes, [], [0], spans, key_at)
    assert "lands on 50" in check_808(notes, [(36, 12, 5)], [0, 48], spans, key_at)
    assert "off its chord" in check_808([(0, 48, 45), (48, 48, 50)], [(36, 12, 5)], [0, 48], spans, key_at)


def test_the_snare_stays_on_3_and_the_hats_turn():
    dr = DRUMMER["trap"]
    assert dr.fixed and all(g.snare == BACKBEAT for g in dr.grooves)
    turned = 0
    for take in _takes(6):
        end = 32 * MET.bar
        assert check_drums(take["drums"], MET, end, True, True) is None
        for h in take["drums"]:
            if h[4] == "snare":
                assert h[0] % MET.bar == 48, h                  # beat 3 of its bar
        turned += sum(1 for h in take["drums"] if h[4] == "hat" and h[0] % 6 and h[0] % MET.bar < 72)
    assert turned > 0                                          # off the 16ths before the last beat: a turn, not a roll
    snare_on_2 = [(0, 6, KIT["kick"], 100, "kick"), (24, 6, KIT["snare"], 100, "snare"),
                  (48, 6, KIT["snare"], 100, "snare")]
    assert "off the backbeat" in check_drums(snare_on_2, MET, 2 * MET.bar, True, True)


def test_turn_rates_are_checked(monkeypatch):
    monkeypatch.setitem(part("trap", "members", "drums"), "turn rates", {"quarter": 1})
    with pytest.raises(StyleError, match="turn rates.quarter"):
        _drummer("trap")


def test_trap_harmony_barely_moves():
    flow = FLOW["trap"]
    assert flow.still and flow.cadence < 50
    assert check_family(Family("one", "i | i"), A_MINOR, VOCAB["trap"], flow.still) is None
    assert check_family(Family("one", "i | i"), A_MINOR, VOCAB["salsa"]) == "one chord: it doesn't move"
    changes = bars = 0
    for take in _takes(8):
        spans = take["spans"]
        changes += sum(a.chord != b.chord for a, b in zip(spans, spans[1:]))
        bars += 32
    assert changes / bars < 0.7, changes / bars                # fewer than one change a bar, on the whole


def test_the_motif_turns_a_beat_into_triplets():
    m = Motif((0, 2, 1, 0), (12, 12, 12, 12))
    t = _triplet(_rng(1), m)
    third = VALUES["8th_triplet"]
    assert len(t.steps) == 5 and sum(t.lengths) == sum(m.lengths) and t.lengths.count(third) == 3
    assert _triplet(_rng(1), Motif((0, 1), (24, 24))) == Motif((0, 1), (24, 24))   # no two notes fill a beat
    assert DEVELOPS["trap"]["triplet"] > 0 and "triplet" not in DEVELOPS["salsa"]
    passed = sum(check_motif(_triplet(_rng(s), m), m) is None for s in range(20))
    assert passed > 0


def test_develop_weights_are_checked(monkeypatch):
    monkeypatch.setitem(part("trap", "members", "melody"), "develop", {"twirl": 1})
    with pytest.raises(StyleError, match="unknown move"):
        _develop("trap")


def test_slides_are_written_as_pitch_bends(tmp_path):
    for seed in range(300, 310):
        song, _ = flow_sketch("trap", seed, 16)
        bass = next(m for m in song.members if m.role == "bass")
        if bass.slides:
            break
    else:
        pytest.fail("no slides in ten trap clips")
    song.write(str(tmp_path / "t"))
    track = next(t for t in mido.MidiFile(str(tmp_path / "t.mid")).tracks if t.name == "bass")
    cc = [(m.control, m.value) for m in track if m.type == "control_change"]
    assert cc[:3] == [(101, 0), (100, 0), (6, 12)]          # the bend range: an octave
    now, bends, ons = 0, [], []
    for m in track:
        now += m.time
        if m.type == "pitchwheel":
            bends.append((now, m.pitch))
        elif m.type == "note_on":
            ons.append(now)
    assert len([p for _, p in bends if p]) >= len(bass.slides)
    for at, steps, _ in bass.slides:                         # back at rest when the next note starts
        rest = [p for t, p in bends if t <= (at + steps) * 20]
        assert rest[-1] == 0
