# SPDX-License-Identifier: GPL-3.0-or-later
"""The style judge (task 3.5b): each measure on a hand-made clip, the words for a miss, the cross check."""
import pytest

from maestro import judge
from maestro.sketch import flow_sketch
from maestro.song import Note, Song, read_notes
from maestro.theory.rhythm import STEPS

S16 = STEPS // 4
BAR = 4 * STEPS


def _clip(chords=("Am", "G")):
    """Two bars: a melody, a pad holding the chord, a kit."""
    s = Song(tempo=120, timeline=[{"bar": b, "chord": c} for b, c in enumerate(chords)], source={"style": "trap"})
    mel, pad, kit = s.member("lead", "melody"), s.member("pad", "pad"), s.member("kit", "drums", kit=True)
    for b in range(2):
        pad.add(b * BAR, BAR, 57)
        mel.add(b * BAR, STEPS, 69, 80)               # A4 on 1: a tone of Am, not of G
        mel.add(b * BAR + STEPS + S16, S16, 72, 100)  # C5 on the e of 2, nothing on 3: syncopated
        mel.add(b * BAR + 3 * STEPS + 8, 8, 76, 120)  # E5, an 8th triplet's last: off the 16th grid
        for i in range(4):
            kit.add(b * BAR + i * STEPS, S16, 36)
        for i in range(3):
            kit.add(b * BAR + 2 * STEPS + 3 * i, 6, 42)   # a 32nd roll on beat 3, the hits overlapping
    mel.slide(BAR + 12, 12, 2)
    return s


def test_chord_tones_read_the_timeline_symbols():
    assert judge.chord_tones("Am") == {9, 0, 4}
    assert judge.chord_tones("F#m7b5") == {6, 9, 0, 4}
    assert judge.chord_tones("C/E") == {0, 4, 7}
    assert judge.chord_tones("G7sus4") == {7, 0, 2, 5}
    assert judge.chord_tones("Bb5") == {10, 5}
    assert judge.chord_tones({"degree": 0}) is None and judge.chord_tones("Hm") is None


def test_each_measure():
    c = judge.from_song(_clip())
    mel = c.players["lead"].notes
    m = lambda t, notes=mel, **kw: judge.measure(t, notes, c, "lead", **kw)
    assert m("notes") == 3
    assert m("syncopation") == 50       # the e of 2 twice and the last triplet (no beat after it); not the triplet
    #                                     before bar 2's beat 1
    assert m("triplets") == pytest.approx(100 / 3)
    assert m("register") == (69, 76)
    assert m("chord tones") == 50                            # A on 1 fits Am, not G
    assert m("velocity") == pytest.approx(16.33, abs=0.01)
    assert m("repeats") == 100
    assert m("length") == pytest.approx(1 / 3)
    assert m("voices") == 1
    assert m("slides", slides=1) == pytest.approx(100 / 6)
    assert m("top") == 100
    hats = [n for n in c.players["kit"].notes if n.pitch == 42]
    assert m("rolls", hats) == 100 and m("rolls") == 0
    assert m("steps", [n for n in c.players["kit"].notes if n.pitch == 36], steps=[0, 4, 2]) == {0: 100, 4: 100, 2: 0}


def test_a_note_held_into_or_anticipating_the_next_chord_counts_its_tones():
    c = judge.from_song(_clip(("Am", "C")))
    held, short = Note(BAR - STEPS, 2 * STEPS, 67), Note(BAR - STEPS, STEPS, 67)   # G on beat 4: not in Am, in C
    assert judge.measure("chord tones", [held], c, "lead") == 100
    # the anticipation (DadCraft, Oct 26): the last beat before the change, held over or not
    assert judge.measure("chord tones", [short], c, "lead") == 100
    early = Note(BAR - 2 * STEPS, STEPS, 67)                                       # G on beat 3: too early
    assert judge.measure("chord tones", [early], c, "lead") == 0


def test_a_chord_changing_inside_a_bar_is_read_from_its_beat():
    s = _clip(("A", "A"))
    s.timeline += [{"bar": 0, "beat": 2, "chord": "D"}, {"bar": 1, "beat": 2, "chord": "E"}]
    c = judge.from_song(s)
    assert c.chord_at(2 * STEPS) == judge.chord_tones("D") and c.chord_at(BAR) == judge.chord_tones("A")
    d = Note(2 * STEPS, STEPS, 62)                                                 # D on beat 3, under D
    assert judge.measure("chord tones", [d], c, "lead") == 100


def test_a_miss_is_named_and_scored_by_its_distance():
    r = judge.Row("drums", "hats", "rolls", 10, 25, 100, judge._score("rolls", 10, 25, 100), "")
    assert r.says() == "too few rolls" and r.score == pytest.approx(1 - 15 / 75)
    r = judge.Row("melody", "", "register", (81, 88), "C4", "C6", judge._score("register", (81, 88), "C4", "C6"), "")
    assert r.says() == "too high" and r.shown() == ("A5-E6", "C4-C6")
    assert judge._score("notes", 4, 1, 3) == 0.5 and judge._score("notes", 2, 1, 3) == 1


def test_a_member_the_card_lacks_scores_zero():
    s = _clip()
    s.member("keys", "keys").add(0, STEPS, 60)
    rows = judge.score(judge.from_song(s))
    keys = [r for r in rows if r.member == "keys"]
    assert len(keys) == 1 and keys[0].score == 0 and keys[0].says() == "trap's card has no keys"


def test_a_file_reads_back_as_the_song_did(tmp_path):
    s = _clip()
    s.write(str(tmp_path / "c"))
    assert len(read_notes(str(tmp_path / "c.mid"))["kit"]) == 14      # the roll's overlapping hats all kept
    a, b = judge.score(judge.from_song(s)), judge.score(judge.from_file(str(tmp_path / "c.mid")))
    assert a == b


@pytest.mark.parametrize("style", ["trap", "synthwave", "salsa", "power_rock"])
def test_today_s_clips_fit_their_own_style_best(style):
    song, _ = flow_sketch(style, 7, 16)
    assert next(iter(judge.cross(judge.from_song(song)))) == style
