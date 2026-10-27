# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthwave's entry (task 3.4b): outrun when the energy is up, dreamy when it's low (DadCraft, Oct 24). The bass by
mood (8ths locked to the drive, a held sub), the programmed drums (the snare on 2 and 4, half time when calm, tom
fills), the arp (a shape round each chord's tones, 16ths or 8ths, under the lead), and Maestro's own sounds with the
light pump."""
import numpy as np
import pytest

from maestro import play, synth
from maestro.explain import flow_choices
from maestro.sketch import flow_sketch
from maestro.stylebook import StyleError
from maestro.theory.drums import DRUMMER, Programmed, _programmed, check_drums
from maestro.theory.flow import ARPS, BASS, Pattern, check_arp, check_bass
from maestro.theory.pitch import Key
from maestro.theory.rhythm import METERS, VALUES

MET = METERS["4/4"]
A_MINOR = Key(9, "minor")


def _takes(n=12, bars=32):
    # each member as drawn, every bar: layering (task 3.6, its own tests) would rest some of them
    return [flow_choices("synthwave", seed, bars, A_MINOR, 112, layers=False)[1] for seed in range(1, 1 + n)]


def _in(notes, s):
    return [n for n in notes if s.start * MET.bar <= n[0] < s.end * MET.bar]


def test_the_bass_drives_when_the_energy_is_up_and_holds_when_it_is_low():
    seen = set()
    for take in _takes():
        assert check_bass(take["bass"], MET) is None
        for p in take["plan"]:
            s, pat = p["section"], p["pattern"]
            assert pat.when in ("any", "low" if s.energy < 0.5 else "high")
            seen.add(pat.when)
            if s.energy >= 0.5:      # 8ths or 16ths: most notes short
                notes = _in(take["bass"], s)
                assert sum(n[1] <= VALUES["8th"] for n in notes) > 0.8 * len(notes)
    assert seen == {"low", "high"}


def test_the_drums_keep_the_snare_on_2_and_4_and_go_half_time_when_calm():
    dr = DRUMMER["synthwave"]
    assert isinstance(dr, Programmed) and dr.snare == (2, 4) and dr.voice == "snare"
    assert set(dr.fixed) == {(2, 4), (3,)}
    toms = 0
    for take in _takes():
        hits = take["drums"]
        assert check_drums(hits, MET, 32 * MET.bar, False, dr.fixed) is None
        toms += any(h[4] in ("high tom", "mid tom", "floor tom") for h in hits)
        for p in take["plan"]:
            s = p["section"]
            snares = {h[0] % MET.bar for h in _in(hits, s) if h[4] == "snare"}
            if s.energy < 0.5:
                assert snares <= {MET.beats[2]}, (s, snares)
            else:
                assert {MET.beats[1], MET.beats[3]} <= snares
    assert toms >= 3


def test_the_snare_check_says_what_is_wrong():
    ok = [(0, 6, 36, 100, "kick"), (24, 6, 38, 100, "snare"), (72, 6, 38, 100, "snare")]
    assert check_drums(ok, MET, MET.bar, False, ((2, 4), (3,))) is None
    assert check_drums([(0, 6, 36, 100, "kick"), (48, 6, 38, 100, "snare")], MET, MET.bar, False, ((2, 4), (3,))) is None
    assert "off the backbeat" in check_drums(ok + [(60, 6, 38, 90, "snare")], MET, MET.bar, False, ((2, 4),))
    assert "no snare on" in check_drums(ok[:2] + [(48, 6, 36, 100, "kick")], MET, MET.bar, False, ((2, 4),))


def test_the_arp_plays_its_chord_tones_faster_when_the_energy_is_up_under_the_lead():
    assert ARPS["synthwave"] and not ARPS["trap"]
    for take in _takes():
        arp, mel = take["arp"], take["melody"]
        assert arp
        for p in take["plan"]:
            s = p["section"]
            want = VALUES["8th"] if s.energy < 0.5 else None
            lengths = {n[1] for n in _in(arp, s)}
            assert len(lengths) == 1 and (want is None or lengths == {want})
        over = sum(1 for st, _, m in arp if any(x[0] <= st < x[0] + x[1] and m > x[2] for x in mel))
        assert over <= 0.05 * len(arp)


def test_the_arp_check_says_what_is_wrong():
    from maestro.theory.chords import Chord
    from maestro.theory.flow import Span
    spans = [Span(0, 96, Chord(0, "min"))]
    key_at = lambda step: A_MINOR
    assert check_arp([(0, 6, 69), (6, 6, 72), (12, 6, 76)], spans, key_at) is None
    assert "off its chord" in check_arp([(0, 6, 71)], spans, key_at)
    assert "at once" in check_arp([(0, 12, 69), (6, 6, 72)], spans, key_at)


def test_bad_entries_are_refused():
    with pytest.raises(ValueError):
        Pattern("x", ((0, 2, "root", "now"),), when="sometimes")
    base = {"patterns": {"kicks": {"k": {"bars": [[0], [0]]}}, "hats": {"h": {"bars": ["x x x x x x x x"] * 2}}}}
    assert _programmed("t", base, "t").snare == (3,)
    for bad in ({"snare": [5]}, {"voice": "cowbell"}, {"toms": -1}):
        d = {"patterns": {**base["patterns"], **bad}}
        with pytest.raises(StyleError):
            _programmed("t", d, "t")


def test_the_sounds_render_in_stereo_and_the_pad_breathes_with_the_kick():
    n = synth.RATE
    notes = [(0.0, 0.5, 57, 100), (0.5, 0.9, 64, 90)]
    for f in (synth.supersaw, synth.saw_bass, synth.pluck, synth.saw_lead):
        x = f(notes, n)
        assert x.shape == (n, 2) and np.all(np.isfinite(x)) and np.abs(x).max() > 0.01, f.__name__
    kit = synth.linn_kit([(0.0, 0.1, 36, 110), (0.25, 0.35, 38, 110), (0.5, 0.6, 50, 100)], n)
    assert kit.shape == (n, 2) and np.abs(kit).max() > 0.05
    g = synth.pump(n, [0.5], 0.35)
    assert g[int(0.51 * n)] < 0.75 and g[int(0.9 * n)] > 0.95 and g[: n // 2].min() == 1.0
    room = synth.reverb(np.pad(np.ones((10, 2)), ((0, n - 10), (0, 0))), 1.0, 0.5)
    assert np.abs(room[n // 4]).max() > 0                  # the tail rings on


def test_the_clip_names_its_own_sounds_and_the_pump(tmp_path):
    song, lines = flow_sketch("synthwave", 3, 16)
    stem = str(tmp_path / "sw")
    song.write(stem)
    own = play._own(stem + ".mid")
    assert own == {"pad": ("supersaw", 0.35), "bass": ("saw bass", 0.2), "melody": ("saw lead", 0),
                   "arp": ("pluck", 0), "drums": ("linn kit", 0)}
    assert "Maestro's own" in song.listen
    assert not any("check:" in ln for ln in lines)
    wav = play.render(stem + ".mid", stem + ".wav")
    import wave
    with wave.open(wav) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, w.getnchannels()) / 32768
    assert x.shape[1] == 2 and 0.5 < np.abs(x).max() < 1.0
    assert np.abs(x[:, 0] - x[:, 1]).mean() > 0.002          # stereo, not mono twice
