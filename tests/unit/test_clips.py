# SPDX-License-Identifier: GPL-3.0-or-later
"""Song files, the baseline clips and the clip player."""
import array, json, os, wave

import pytest

from maestro import baseline, play
from maestro.port import Composer, SCALE_IV, SCALE_N
from maestro.song import Note, Song, read_notes


def test_a_note_must_sit_on_the_grid():
    with pytest.raises(ValueError):
        Note(1.5, 6, 60)
    with pytest.raises(ValueError):
        Note(0, 0, 60)


def test_song_file_round_trip(tmp_path):
    s = Song(tempo=120, listen="a test", source={"seed": 5})
    m = s.member("bass", "bass", 38)
    m.add(0, 24, 40)
    m.add(24, 24, 40)          # the same note again, back to back
    m.add(48, 6, 43, 70)
    mid = s.write(str(tmp_path / "t"))
    assert read_notes(mid)["bass"] == sorted(m.notes, key=lambda n: (n.step, n.pitch))
    info = json.load(open(tmp_path / "t.json"))
    assert info["listen"] == "a test" and info["members"]["bass"] == {"role": "bass", "sound": 38}


def test_baseline_same_seed_same_clip_and_the_pad_is_the_composers(tmp_path):
    a, b = baseline.clip(7, bars=16), baseline.clip(7, bars=16)
    assert [m.notes for m in a.members] == [m.notes for m in b.members]
    assert [m.notes for m in baseline.clip(8, bars=16).members] != [m.notes for m in a.members]
    c = Composer(seed=7)                       # the first chord, sent the same way
    for msg, v in (("tempo", 92), ("color", 1), ("bright", 0.5), ("energy", 0.5), ("seed", 7), ("scale", 1)):
        c.send(msg, v)
    c.send("start")
    first = next(v for o, v in c.out if o == "chord")
    pad = next(m for m in a.members if m.name == "pad")
    assert sorted(n.pitch for n in pad.notes if n.step == 0) == sorted(48 + 9 + x for x in first[2:])


def test_baseline_every_member_plays_in_key_and_on_the_grid(tmp_path):
    for i, (scale, key, bpm) in enumerate(baseline.PRESETS):
        mid = baseline.clip(30 + i, scale, key, bpm, bars=16).write(str(tmp_path / f"c{i}"))
        notes = read_notes(mid)                # (refuses anything off the grid)
        assert set(notes) == {"pad", "bass", "melody", "arp", "drums"}
        tones = {(key + SCALE_IV[scale][d]) % 12 for d in range(SCALE_N[scale])}
        for name in ("melody", "arp"):
            assert {n.pitch % 12 for n in notes[name]} <= tones, name
        assert all(36 <= n.pitch < 48 for n in notes["bass"])


needs_synth = pytest.mark.skipif(not any(p and os.path.isfile(p) for p in play.SOUNDFONTS), reason="no soundfont")


@needs_synth
def test_the_player_renders_sound(tmp_path):
    mid = baseline.clip(3, bars=2).write(str(tmp_path / "c"))
    wav = play.render(mid, str(tmp_path / "c.wav"))
    w = wave.open(wav)
    a = array.array("h", w.readframes(w.getnframes()))
    assert abs(w.getnframes() / w.getframerate() - (2 * 4 * 60 / 92 + play.TAIL_S)) < 0.1
    assert 3000 < max(map(abs, a)) < 32767     # sound, and not clipped
