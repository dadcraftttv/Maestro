# SPDX-License-Identifier: GPL-3.0-or-later
"""Trap's entry (task 3.4a, two rounds): the 808 on the kicks and its slides, the programmed drums (the clap on 3,
written rolls, the hats-alone opening and the drop-outs, the 808 resting with them), harmony that barely moves, the
loop melody, the motif's triplets, the slides written as pitch bends, and Maestro's own sounds."""
import json

import mido
import numpy as np
import pytest

from maestro.explain import flow_choices
from maestro.rng import ComposerRng
from maestro.sketch import flow_sketch
from maestro.stylebook import StyleError, part
from maestro.theory.chords import VOCAB, Chord
from maestro import play, synth
from maestro.theory.drums import DRUMMER, Programmed, _programmed, check_drums, quiet_spans
from maestro.theory.flow import BASS, FLOW, LOOPS, SLIDE, Family, Span, check_808, check_family, check_loop
from maestro.theory.form import DEVELOPS, VALUES, Motif, _triplet, check_motif
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


def test_the_programmed_drums_keep_the_clap_on_3_and_roll():
    dr = DRUMMER["trap"]
    assert isinstance(dr, Programmed) and dr.fixed
    end = 32 * MET.bar
    rolls = 0
    for take in _takes(6):
        hits = take["drums"]
        assert check_drums(hits, MET, end, True, True) is None
        quiet = quiet_spans(hits, MET, end)
        assert quiet and quiet[0] == (0, dr.intro * MET.bar)            # the hats alone at the start
        assert any(h[4] == "hat" for h in hits if h[0] < dr.intro * MET.bar)
        for h in hits:
            if h[4] == "snare":
                assert h[0] % MET.bar == 48, h                          # beat 3 of its bar
        for q0, q1 in quiet:                                            # the 808 rests with the kick and clap
            assert not any(st < q1 and st + n > q0 for st, n, _ in take["bass"]), (q0, q1)
        hats = sorted((h[0], h[3]) for h in hits if h[4] == "hat")
        runs = [(a, b) for a, b in zip(hats, hats[1:]) if b[0] - a[0] < 6]
        rolls += len(runs)
        assert any(b[1] > a[1] for a, b in runs)                        # a roll gets louder as it runs
    assert rolls > 0


def test_kick_and_hat_patterns_are_checked():
    d = json.loads(json.dumps(part("trap", "members", "drums")))
    d["patterns"]["hats"]["eighths"]["bars"][0] = "x x x"
    with pytest.raises(StyleError, match="eight 8ths"):
        _programmed("trap", d, "trap: members.drums")
    d = json.loads(json.dumps(part("trap", "members", "drums")))
    d["patterns"]["kicks"]["home"]["bars"][0] = [10, 0]
    with pytest.raises(StyleError, match="in order"):
        _programmed("trap", d, "trap: members.drums")


def test_the_melody_is_a_loop_going_round():
    assert LOOPS["trap"] is not None and LOOPS["salsa"] is None
    for take in _takes(6):
        for p in take["plan"]:
            assert "loop" in p["loop"]
        assert check_loop(take["melody"], take["spans"], A_MINOR, 0) is None


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
    assert "triplet" not in DEVELOPS["salsa"]
    passed = sum(check_motif(_triplet(_rng(s), m), m) is None for s in range(20))
    assert passed > 0


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


def test_the_808_and_its_kit_are_rendered(tmp_path):
    song, _ = flow_sketch("trap", 300, 8)
    stem = str(tmp_path / "t")
    song.write(stem)
    assert play._own(stem + ".mid") == {"bass": "808", "drums": "808 kit"}
    midi = mido.MidiFile(stem + ".mid")
    n = int(midi.length * synth.RATE)
    bass = play._synth_tracks(midi, {"bass": "808"}, n)
    kit = play._synth_tracks(midi, {"drums": "808 kit"}, n)
    assert np.max(np.abs(bass)) > 0.05 and np.max(np.abs(kit)) > 0.05
    assert np.all(np.isfinite(bass)) and np.all(np.isfinite(kit))
    spec = np.abs(np.fft.rfft(bass))                     # the 808 lives low: most of its energy under 150 Hz
    hz = np.fft.rfftfreq(len(bass), 1 / synth.RATE)
    assert spec[hz < 150].sum() > spec[hz >= 150].sum()


def test_the_fills_roll_fall_and_swell():
    seen = set()
    for take in _takes(12):
        hits = take["drums"]
        assert check_drums(hits, MET, 32 * MET.bar, True, True) is None
        cascade = [h for h in hits if h[4] == "cascade"]
        for k in range(0, len(cascade), 8):                         # eight 16ths, each a step lower
            run = cascade[k:k + 8]
            assert [h[2] for h in run] == list(range(67, 59, -1))
            assert all(b[0] - a[0] == 6 for a, b in zip(run, run[1:]))
            assert not any(h[4] in ("hat", "kick") and run[0][0] <= h[0] < run[-1][0] + 6 for h in hits)
        roll = sorted((h[0], h[3]) for h in hits if h[4] == "roll")
        if roll:
            assert roll[-1][1] > roll[0][1]                         # louder as it goes
        for h in hits:
            if h[4] == "swell":
                assert h[1] == MET.bar and any(c[4] == "crash" and c[0] == h[0] + MET.bar for c in hits)
            if h[4] == "riser":
                assert h[1] == 2 * MET.bar
        seen |= {h[4] for h in hits}
    assert {"cascade", "roll", "swell", "crash", "riser"} <= seen
