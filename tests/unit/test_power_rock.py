# SPDX-License-Identifier: GPL-3.0-or-later
"""Power rock's entry (task 3.4d), 80s arena rock (DadCraft, Oct 26): the doubled rhythm guitar on power chords,
harmony from our Rock Corpus counts, the rock bass, the pentatonic lead with bends and vibrato, the song's parts
(verse, pre-chorus, chorus) with the snare's build and the stops, the pad sitting out."""
import json
import os

import mido
import pytest

from maestro.explain import flow_choices
from maestro.sketch import TEMPO, flow_sketch
from maestro.song import Song
from maestro.stylebook import StyleError
from maestro.theory.arrange import ARRANGE
from maestro.theory.chords import parse_roman
from maestro.theory.guitar import GUITAR, VOICINGS, _guitar_flow, bends, pentatonic, scale_of
from maestro.theory.pitch import Key
from maestro.theory.rhythm import METERS

MET = METERS["4/4"]
A = Key(9, "minor")
DATA = os.path.join(os.path.dirname(__file__), "..", "..", "maestro", "data", "rock.json")


def _takes(n=12, bars=40):
    return [flow_choices("power_rock", seed, bars, A, TEMPO["power_rock"]) for seed in range(1, 1 + n)]


def test_the_band_passes_its_checks_and_the_pad_sits_out():
    for lines, take in _takes():
        assert not [ln for ln in lines if " check: " in ln], [ln for ln in lines if " check: " in ln]
        assert set(take["guitar"]) == {"guitar L", "guitar R"} and all(take["guitar"].values())
    song, _ = flow_sketch("power_rock", seed=3, bars=16)
    assert {m.role for m in song.members} == {"guitar", "bass", "melody", "drums"}
    pans = {m.name: m.pan for m in song.members if m.role == "guitar"}
    assert pans["guitar L"] < 0 < pans["guitar R"]


def test_the_guitars_play_power_chords_each_in_its_own_octave():
    gf = GUITAR["power_rock"]
    for _, take in _takes(4):
        for t in gf.tracks:
            by = {}
            for st, _, m in take["guitar"][t.name]:
                by.setdefault(st, []).append(m)
            for ms in by.values():
                root = min(ms)
                assert VOICINGS[t.voicing] <= root <= VOICINGS[t.voicing] + 12
                assert {m - root for m in ms} <= {0, 6, 7, 8, 12}       # root, its fifth, the octave
        low = min(m for _, _, m in take["guitar"]["guitar L"])
        high = min(m for _, _, m in take["guitar"]["guitar R"])
        assert high - low >= 6                                         # the two sit apart, so they sound wide


def test_the_parts_go_verse_to_chorus_with_builds_and_stops():
    seen, builds, stops = set(), 0, 0
    for _, take in _takes(20, 48):
        names = [x.name for _, _, x in take["parts"]]
        assert names[0] == "verse"                                     # the play opens on a verse
        seen |= set(names)
        builds += len(take["builds"])
        stops += len(take["breaks"])
        for b in take["builds"]:                                       # a pre-chorus's last bar: the snare builds
            snares = [h for h in take["drums"] if b * MET.bar <= h[0] < (b + 1) * MET.bar and h[4] == "snare"]
            assert len(snares) >= 8 and snares[-1][3] > snares[0][3]
        for b in take["breaks"]:                                       # a stop: one chord ringing through the bar
            hits = {st for st, _, _ in take["guitar"]["guitar L"] if b * MET.bar <= st < (b + 1) * MET.bar}
            assert hits == {b * MET.bar}
    assert {"verse", "chorus", "pre-chorus"} <= seen and builds and stops


def test_the_drums_keep_time_on_the_hat_in_a_verse_and_ride_in_a_chorus():
    for lines, take in _takes(8):
        for p in take["plan"]:
            first = p["parts"][0][1]
            said = p["drums"][0]
            if first == "verse":
                assert "drums: hat" in said, said
    ar = ARRANGE["power_rock"]
    assert ar.stop and ar.build == "pre-chorus"


def test_the_harmony_draws_on_the_corpus_counts():
    d = json.load(open(DATA))
    assert d["all"]["songs"] > 150 and d["era"]["songs"] > 30
    assert d["era"]["flat_sides"]["bVII"] > d["all"]["flat_sides"]["bVII"]   # the era leans on the flat seventh
    assert list(d["all"]["roots"])[:3] == ["I", "IV", "V"]
    majors = [p for _, take in _takes(20) for p in take["plan"] if not p["section"].key.minorish]
    assert majors                                                    # mostly a major home
    assert {"double plagal", "anthem"} & {p["family"].name for p in majors}


def test_the_lead_keeps_to_the_pentatonic_off_its_chord_tones():
    for _, take in _takes(6):
        spans = take["spans"]
        for st, _, m in take["melody"]:
            key = next(r["key"] for r in take["bars"] if r["bar"] == st // MET.bar)
            sp = max((s for s in spans if s.at <= st), key=lambda s: s.at)
            tones = {t % 12 for t in sp.chord.tones}
            assert (m - key.tonic) % 12 in scale_of(key) | tones


def test_pentatonic_moves_only_what_is_off_the_scale_and_the_chord():
    key = Key(9, "major")
    from maestro.theory.flow import Span
    spans = [Span(0, MET.bar, parse_roman("I", key))]
    notes = [(0, 12, 69), (12, 12, 74), (24, 12, 80), (36, 12, 76)]       # A (home), D (4th), G# (7th), E
    out, moved = pentatonic(notes, spans, key)
    assert moved == 2 and [m for _, _, m in out] == [69, 73, 81, 76]   # D down to C#, G# up to A


def test_bends_and_vibrato_reach_the_midi():
    _, take = _takes(1)[0]
    assert take["vibrato"]
    song, _ = flow_sketch("power_rock", seed=5, bars=32)
    mel = next(m for m in song.members if m.role == "melody")
    if mel.slides:
        st, steps, semis, hold = mel.slides[0]
        note = next(n for n in mel.notes if n.step == st)
        assert steps + hold == note.steps and semis in (1, 2)          # held up in tune to the note's end
    assert mel.vibrato


def test_a_held_bend_stays_up_and_the_pan_is_written(tmp_path):
    song = Song(tempo=120)
    m = song.member("lead", "melody", 29)
    m.pan = -48
    m.add(0, 48, 62)
    m.slide(0, 12, 2, 36)
    m.shake(12, 36)
    song.write(str(tmp_path / "x"))
    msgs = [x for x in mido.MidiFile(str(tmp_path / "x.mid")).tracks[1] if not x.is_meta]
    t, at = 0, []
    for x in msgs:
        t += x.time
        at.append((t, x))
    pan = [x for _, x in at if x.type == "control_change" and x.control == 10]
    assert pan and pan[0].value == 16
    bends_ = [(t, x.pitch) for t, x in at if x.type == "pitchwheel"]
    off = next(t for t, x in at if x.type == "note_off")
    assert max(p for _, p in bends_) > 0 and all(p > 0 for t, p in bends_ if 12 * 20 <= t < off)   # held up
    assert bends_[-1] == (off, 0)                                       # back at rest when the note ends
    assert [x.value for _, x in at if x.type == "control_change" and x.control == 1] == [48, 0]


def test_bends_go_up_from_a_step_under_on_the_scale():
    key = Key(9, "major")
    out = bends(type("R", (), {"rnd": staticmethod(lambda n: 0)})(), [(0, 48, 76), (48, 12, 74)], lambda st: key,
                100)
    assert out == [(0, 12, 2)]                                         # E from D, a whole step; the short note not


def test_the_book_refuses_a_guitar_pattern_with_an_unknown_shape(monkeypatch):
    bad = {"tracks": {"g": {}}, "patterns": {"odd": {"hits": [[0, 2, "triad", "now"]]}}}
    monkeypatch.setattr("maestro.theory.guitar.part", lambda *a: bad)
    with pytest.raises(StyleError, match="odd"):
        _guitar_flow("power_rock")


# ---- the second round (DadCraft, Oct 26): double bass, two leads, the duel, 150 BPM ----

def test_double_bass_runs_through_the_loud_parts():
    found = 0
    for _, take in _takes(10, 48):
        stops = set(take["breaks"]) | set(take["builds"])
        for at, _, x in take["parts"]:
            if x.name not in ("chorus", "drive", "duel"):
                continue
            for b in range(at, at + 8):
                if b in stops or b >= 48:
                    continue
                kicks = [h for h in take["drums"] if b * MET.bar <= h[0] < (b + 1) * MET.bar and h[4] == "kick"]
                assert len(kicks) >= 10, (at, b, len(kicks))           # both feet, 16ths or the gallop
                found += 1
    assert found and TEMPO["power_rock"] == 150


def test_the_chorus_twins_a_third_under_and_the_duel_trades():
    duels = 0
    for _, take in _takes(20, 48):
        one = {st: m for st, _, m in take["melody"]}
        for at, _, x in take["parts"]:
            lo, hi = at * MET.bar, (at + 8) * MET.bar
            two = [n for n in take["lead2"] if lo <= n[0] < hi]
            if x.lead == "twin":
                assert two and all((one[st] - m) % 12 in (3, 4, 8, 9) for st, _, m in two)
            elif x.lead == "duel" and hi <= 48 * MET.bar:
                duels += 1
                firsts = [n for n in take["melody"] if lo <= n[0] < hi]
                assert firsts and two
                last = hi - MET.bar
                for st, length, m in two:                              # the second plays while the first rests
                    if st < last:
                        assert not any(s <= st < s + n for s, n, _ in firsts), st
                ends = [n for n in take["melody"] if last <= n[0] < hi][-1]
                assert (ends[2] - next(r["key"] for r in take["bars"] if r["bar"] == at).tonic) % 12 == 0
    assert duels


def test_the_leads_check_refuses_clashing_leads():
    from maestro.theory.guitar import check_leads
    key = Key(9, "major")
    from maestro.theory.flow import Span
    spans = [Span(0, MET.bar, parse_roman("I", key))]
    assert check_leads([(0, 24, 81)], [(0, 24, 78)], lambda st: key, spans) is None   # A over F#, a third
    assert "not a third" in check_leads([(0, 24, 81)], [(0, 24, 79)], lambda st: key, spans)
    assert "held note" in check_leads([(0, 48, 81)], [(24, 12, 76)], lambda st: key, spans)
