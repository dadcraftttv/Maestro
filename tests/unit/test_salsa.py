# SPDX-License-Identifier: GPL-3.0-or-later
"""Salsa's entry (task 3.4c), classic Fania era (DadCraft, Oct 26): the piano montuno, two trombones (punches, the
coro, the mambo's riff), the song's parts (cuerpo, montuno, mambo), the breaks on the clave's strokes, the bass's
walk-ups, the pad sitting out."""
import pytest

from maestro.explain import flow_choices
from maestro.sketch import TEMPO, flow_sketch
from maestro.stylebook import StyleError
from maestro.theory.arrange import ARRANGE, check_parts, cut
from maestro.theory.horns import HORNS, check_horns, harmonize, strokes
from maestro.theory.keys import KEYS, _keys_flow
from maestro.theory.pitch import Key
from maestro.theory.rhythm import CLAVES, METERS, check_clave

MET = METERS["4/4"]
A_MINOR = Key(9, "minor")
CLAVE = CLAVES["son_2-3"]


def _takes(n=12, bars=40):
    return [flow_choices("salsa", seed, bars, A_MINOR, TEMPO["salsa"]) for seed in range(1, 1 + n)]


def _in(notes, lo, hi):
    return [n for n in notes if lo <= n[0] < hi]


def test_every_montuno_sits_with_the_clave_and_the_book_refuses_one_that_crosses(monkeypatch):
    for p in KEYS["salsa"].patterns:
        assert check_clave(p.steps(), CLAVE) is None, p.name
    crossed = {"patterns": {"crossed": {"hits": [[0, 1, "now"], [3, 1, "now"], [6, 1, "now"], [10, 1, "now"],
                                                 [12, 1, "now"]]}}}
    monkeypatch.setattr("maestro.theory.keys.part", lambda *a: crossed)
    with pytest.raises(StyleError, match="crossed"):
        _keys_flow("salsa")


def test_the_band_passes_its_checks_and_the_pad_sits_out():
    for lines, take in _takes():
        assert not [ln for ln in lines if " check: " in ln], [ln for ln in lines if " check: " in ln]
        assert take["keys"] and take["horns"]
        assert check_clave(sorted({n[0] % CLAVE.length for n in take["keys"]}), CLAVE) is None   # the rest of
        #                                                     check_keys runs in flow_choices, on the uncut chords
        assert check_horns(take["horns"], HORNS["salsa"].voices, CLAVE) is None
    song, _ = flow_sketch("salsa", seed=3, bars=16)
    assert {m.role for m in song.members} >= {"keys", "horns", "bass", "melody", "percussion"}
    assert "pad" not in {m.role for m in song.members}


def test_the_montuno_plays_in_octaves_and_pushes_the_chord_in_early():
    _, take = _takes(1)[0]
    by = {}
    for st, _, m in take["keys"]:
        by.setdefault(st, []).append(m)
    assert all(max(v) - min(v) == 12 for v in by.values())                     # the top line over its octave
    assert any(len(v) == 3 for v in by.values())                               # a tone filling in on the strokes
    assert any(st % (MET.bar // 2) == MET.bar // 2 - 12 for st in by)           # an anticipation, an 8th early


def test_the_song_opens_on_its_body_and_a_mambo_only_follows_a_montuno():
    seen = set()
    for _, take in _takes(20, 48):
        parts = take["parts"]
        assert check_parts(parts, ARRANGE["salsa"]) is None
        assert all(x.name == "cuerpo" for _, s, x in parts if s is parts[0][1])
        for k, (_, _, x) in enumerate(parts):
            seen.add(x.name)
            if x.name == "mambo":
                assert parts[k - 1][2].name == "montuno"
    assert seen == {"cuerpo", "montuno", "mambo"}


def test_the_coro_answers_the_lead_and_the_lead_sits_out_the_mambo():
    for lines, take in _takes(20, 48):
        for at, s, x in take["parts"]:
            lo = at * MET.bar
            if x.name == "mambo" and "sings on" not in " ".join(lines):
                assert not _in(take["melody"], lo, lo + 8 * MET.bar)
            if x.name == "montuno" and any(f"bar {at + 1}, horns: the coro" in ln for ln in lines) and \
                    "sings on" not in " ".join(lines):
                for b in (2, 3, 6, 7):                        # the coro's bars: the lead leaves them
                    assert not _in(take["melody"], lo + b * MET.bar, lo + (b + 1) * MET.bar)
                assert _in(take["horns"], lo + 2 * MET.bar, lo + 4 * MET.bar)


def test_a_break_hits_the_clave_strokes_together():
    found = 0
    for lines, take in _takes(20, 48):
        for b in take["breaks"]:
            lo = b * MET.bar
            want = {lo + s for s in strokes(CLAVE, b, MET)}
            for role in ("bass", "keys", "horns"):
                assert {n[0] for n in _in(take[role], lo, lo + MET.bar)} == want, role
            found += 1
    assert found


def test_the_bass_walks_up_into_a_section():
    walks = 0
    for lines, take in _takes(20, 48):
        for ln in lines:
            if "walks up" in ln:
                b = int(ln.split("bar ")[1].split(":")[0]) - 1
                notes = _in(take["bass"], b * MET.bar, b * MET.bar + 72)
                assert [n[2] for n in notes] == sorted(n[2] for n in notes) and len(notes) == 3
                walks += 1
    assert walks


def test_the_horns_move_together_in_thirds_to_sixths():
    top = [(0, 12, 72), (12, 12, 71)]                 # over Am: C, then B (not the chord's): a third down the scale
    from maestro.theory.flow import Span
    from maestro.theory.chords import Chord
    spans = [Span(0, 96, Chord(0, "min"))]
    out = harmonize(top, spans, lambda st: A_MINOR, 2)
    assert out == [(0, 12, 72), (0, 12, 69), (12, 12, 71), (12, 12, 67)]


def test_cut_leaves_out_what_starts_inside_and_shortens_what_runs_in():
    assert cut([(0, 50, 60), (48, 12, 62), (100, 12, 64)], 48, 96) == [(0, 48, 60), (100, 12, 64)]
