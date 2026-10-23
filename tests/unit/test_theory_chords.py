# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from maestro.port import MODES, PARENT, SCALE_IV, SCALE_N
from maestro.rng import ComposerRng
from maestro.theory.chords import (Chord, Vocabulary, borrowed_from, check_chord, choose_chord, diatonic, function,
                                   kind, name, parse_roman, pool, roman, two_five)
from maestro.theory.pitch import COMPOSER_SCALES, SCALES, Key, check_note, choose_scale

C, A = Key(0, "major"), Key(9, "minor")


def names(key, chords):
    return [name(c, key) for c in chords]


def romans(key, chords):
    return [roman(c, key) for c in chords]


# ---- keys and scales ----

def test_composer_scales_match_its_tables():
    for i, s in enumerate(COMPOSER_SCALES):
        assert list(SCALES[s]) == SCALE_IV[i][:SCALE_N[i]]
        m = MODES[PARENT[i]]   # the chords come from the same scale as the composer's
        assert list(SCALES[Key(0, s).chord_scale]) == m["iv"][:m["n"]]


def test_spelling():
    assert str(Key(1, "major")) == "Db major" and str(Key(1, "minor")) == "C# minor"
    assert Key(5, "major").name(10) == "Eb" and Key(11, "major").name(11) == "A#"
    assert check_note(C, 4) is None and check_note(C, 10) == "Bb is outside C major"


def test_choose_scale_is_seeded():
    picks = lambda seed: [choose_scale(ComposerRng(seed), {"minor": 3, "phrygian": 1, "major": 0}) for _ in range(1)]
    assert picks(5) == picks(5)
    r = ComposerRng(1)
    assert {choose_scale(r, {"minor": 3, "phrygian": 1, "major": 0}) for _ in range(200)} == {"minor", "phrygian"}


# ---- chords of a key ----

def test_major_triads():
    assert names(C, diatonic(C)) == ["C", "Dm", "Em", "F", "G", "Am", "Bdim"]
    assert romans(C, diatonic(C)) == ["I", "ii", "iii", "IV", "V", "vi", "vii°"]
    assert [function(c, C)[0] for c in diatonic(C)] == ["home", "away", "home", "away", "tension", "home", "tension"]


def test_minor_sevenths():
    d = diatonic(A, sevenths=True)
    assert names(A, d) == ["Am7", "Bm7b5", "Cmaj7", "Dm7", "Em7", "Fmaj7", "G7"]
    assert romans(A, d) == ["i7", "iiø7", "bIIImaj7", "iv7", "v7", "bVImaj7", "bVII7"]


def test_every_composer_scale_has_chords():
    for s in COMPOSER_SCALES:
        for c in diatonic(Key(0, s)):
            assert kind(c, Key(0, s)) == "diatonic" and function(c, Key(0, s))[0] in ("home", "away", "tension")


def test_inversions():
    assert roman(Chord(0, bass=4), C) == "I6" and name(Chord(0, bass=4), C) == "C/E"
    assert roman(Chord(7, "maj", "7", bass=11), C) == "V65"
    assert roman(Chord(5, bass=0), C) == "IV64"


@pytest.mark.parametrize("text", ["I", "ii", "V7", "vii°", "iiø7", "vii°7", "bVII", "bVI", "iv", "V7/ii", "V/V",
                                  "vii°/V", "bVII5", "V7sus4", "Imaj7", "bII", "III+", "V7/IV"])
def test_roman_round_trip(text):
    assert roman(parse_roman(text), C) == text


# ---- kinds: borrowed and secondary ----

def test_secondary_dominants():
    a7 = parse_roman("V7/ii")
    assert name(a7, C) == "A7" and kind(a7, C) == "secondary" and function(a7, C)[0] == "tension"
    assert name(parse_roman("vii°/V"), C) == "F#dim"
    assert kind(Chord(2), C) == "secondary"   # D major in C: V/V before lydian's II


def test_borrowed():
    e = Chord(7)   # E major in A minor: the harmonic minor's dominant
    assert name(e, A) == "E" and kind(e, A) == "borrowed" and "harmonic_minor" in borrowed_from(e, A)
    assert function(e, A)[0] == "tension"


# ---- what the four first styles need ----

def test_trap_dark_minor():
    phr = Key(9, "phrygian")
    bii = Chord(1)
    assert name(bii, phr) == "Bb" and roman(bii, phr) == "bII" and function(bii, phr)[0] == "tension"
    hm = Key(9, "harmonic_minor")
    assert romans(hm, diatonic(hm)) == ["i", "ii°", "bIII+", "iv", "V", "bVI", "vii°"]


def test_synthwave_borrowed():
    for t in ("bVI", "bVII", "iv"):
        assert kind(parse_roman(t), C) == "borrowed" and "minor" in borrowed_from(parse_roman(t), C)
    iv_major = parse_roman("IV")   # D major in A minor: the dorian IV
    assert name(iv_major, A) == "D" and "dorian" in borrowed_from(iv_major, A)


def test_salsa_two_five():
    two, five = two_five(0)
    assert names(C, [two, five]) == ["Dm7", "G7"]
    cm = Key(0, "minor")
    two, five = two_five(0, minor=True)
    assert romans(cm, [two, five]) == ["iiø7", "V7"] and function(five, cm)[0] == "tension"
    two, five = two_five(2)   # a secondary ii-V to ii
    assert names(C, [two, five]) == ["Em7", "A7"] and roman(five, C) == "V7/ii"


def test_rock_power_chords():
    e = Key(4, "major")
    d5 = parse_roman("bVII5")
    assert name(d5, e) == "D5" and kind(d5, e) == "borrowed" and function(d5, e)[0] == "away"
    assert name(Chord(7, "power"), e) == "B5" and function(Chord(7, "power"), e)[0] == "tension"


# ---- the rule: check and choose ----

def test_check_gives_the_reason():
    v = Vocabulary()
    assert check_chord(Chord(0), C, v) is None
    assert check_chord(parse_roman("bVII"), C, v) == "Bb (bVII) is borrowed (from minor), which this style doesn't use"
    v = Vocabulary(kinds=frozenset(("diatonic", "borrowed")), borrow=("dorian",))
    assert "not a scale this style borrows from" in check_chord(parse_roman("bVI"), C, v)


def test_pool_and_choose():
    assert set(pool(C, Vocabulary())) == set(diatonic(C))
    v = Vocabulary(kinds=frozenset(("diatonic", "borrowed")), qualities=frozenset(("maj", "min", "power")))
    p = pool(C, v)
    assert parse_roman("bVII") in p and Chord(10, "power") in p and parse_roman("vii°") not in p
    seq = lambda seed: [choose_chord(r, p) for r in [ComposerRng(seed)] for _ in range(16)]
    assert seq(3) == seq(3) and seq(3) != seq(4)
    no_minor = choose_chord(ComposerRng(9), p, lambda c: 0 if c.quality == "min" else 1)
    assert no_minor.quality != "min"
