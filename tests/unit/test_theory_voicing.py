# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from maestro.rng import ComposerRng
from maestro.theory.chords import Chord, parse_roman
from maestro.theory.pitch import Key
from maestro.theory.voicing import (LEADING, RANGES, Leading, Range, check_band, check_voicing, choose_voicing,
                                    cost, explain, member_range, parallels, voicings)

C = Key(0, "major")
PAD, GUITAR, BASS = RANGES["pad"], RANGES["guitar"], RANGES["bass"]
PLAIN = LEADING["plain"]
TIGHT = Leading(slack=0)   # always the smoothest: for textbook moves


def rng(seed=1):
    r = ComposerRng()
    r.seed(seed)
    return r


# ---- ranges ----

def test_every_pitched_member_has_a_range():
    for role in ("bass", "pad", "melody", "arp", "guitar", "keys", "horns"):   # decision 11's new roles too
        assert RANGES[role].low < RANGES[role].high
    assert RANGES["bass"].low == min(r.low for r in RANGES.values())
    assert RANGES["melody"].high == max(r.high for r in RANGES.values())


def test_register_narrows_the_range():
    assert member_range("bass", [28, 48]) == Range(28, 48)
    assert member_range("bass", [10, 40]) == Range(24, 40)
    with pytest.raises(ValueError):
        member_range("bass", [60, 72])


# ---- the check: reasons ----

def test_check_gives_reasons():
    cmaj = Chord(0)
    assert check_voicing((60, 64, 67), cmaj, C, PAD) is None
    assert "above the range" in check_voicing((60, 64, 91), cmaj, C, PAD)
    assert "not in the chord" in check_voicing((60, 62, 67), cmaj, C, PAD)
    assert "third is missing" in check_voicing((60, 67, 72), cmaj, C, PAD)
    assert "not under the melody" in check_voicing((60, 64, 67), cmaj, C, PAD, ceiling=67)
    assert "bottom note should be E" in check_voicing((60, 64, 67), Chord(0, bass=4), C, PAD, on_bass=True)
    assert "seventh is missing" in check_voicing((55, 59, 62), parse_roman("V7", C), C, PAD)


def test_the_fifth_goes_first_when_there_is_no_room():
    g7 = parse_roman("V7", C)
    assert check_voicing((55, 59, 65), g7, C, PAD) is None                    # G B F: no D, still a G7
    assert "fifth is missing" in check_voicing((59, 62, 71), Chord(11, "dim"), C, PAD)   # B D B: a dim fifth stays


def test_low_thirds_are_mud_but_low_fifths_are_not():
    assert "muddy" in check_voicing((36, 40, 43), Chord(0), C, BASS)          # C2 E2: a third that low
    assert check_voicing((36, 43), Chord(0, "power"), C, BASS) is None        # C2 G2: clear
    assert "muddy" in check_voicing((36, 43, 48), Chord(0, "power"), C, BASS)  # G2 C3: a fourth needs A2
    assert check_voicing((36, 40, 43), Chord(0), C, BASS, Leading(low_limits=False)) is None


def test_rootless_only_when_the_style_says():
    c7 = Chord(0, "maj", "maj7")
    assert check_voicing((64, 67, 71), c7, C, PAD) is not None
    assert check_voicing((64, 67, 71), c7, C, PAD, LEADING["salsa"]) is None


# ---- smooth moves ----

def test_common_tone_held_steps_for_the_rest():
    v = choose_voicing(rng(), Chord(5), C, 3, PAD, prev=(60, 64, 67), leading=TIGHT)   # C to F
    assert v == (60, 65, 69)                                                            # C held, E-F, G-A


def test_leading_tone_resolves():
    v = choose_voicing(rng(), Chord(0), C, 4, PAD, prev=(55, 59, 62, 65), leading=TIGHT)  # G7 to C
    assert v == (55, 60, 64, 67)                                                          # B up to C, G held


def test_parallels_found():
    assert parallels((60, 64, 67), (62, 66, 69)) == [("fifths", 0, 2)]
    assert parallels((40, 47, 52), (43, 50, 55)) == [("fifths", 0, 1), ("octaves", 0, 2)]
    assert parallels((60, 67), (60, 67)) == []
    assert parallels((60, 67), (62, 67)) == []    # one voice held: not parallel


def test_parallels_are_a_tendency_the_style_sets():
    block = ((60, 64, 67), (62, 66, 69))          # C to D as one shape: parallel fifths
    plain = choose_voicing(rng(), Chord(2), C, 3, PAD, prev=block[0], leading=TIGHT)
    assert parallels(block[0], plain) == []       # a plain style finds another way
    glide = choose_voicing(rng(), Chord(2), C, 3, PAD, prev=block[0], leading=Leading(fifths=0, slack=0))
    assert glide == block[1]                      # synthwave's glide is the smoothest when fifths cost nothing
    power = ((40, 47, 52), (43, 50, 55))
    assert cost(*power, GUITAR, LEADING["power_rock"]) < cost(*power, GUITAR, PLAIN)


def test_bass_line_moves_to_the_nearest_root():
    prev = (36,)
    for numeral, want in (("IV", 41), ("V", 43), ("vi", 45)):
        v = choose_voicing(rng(), parse_roman(numeral, C), C, 1, BASS, prev=prev, leading=TIGHT, on_bass=True)
        assert v == (want,)
        prev = v


# ---- free to drift (decision 9) ----

def test_seeded_and_not_locked():
    seen = {choose_voicing(rng(s), Chord(5), C, 4, PAD, prev=(60, 64, 67, 72)) for s in range(40)}
    assert len(seen) >= 2
    assert all(check_voicing(v, Chord(5), C, PAD) is None for v in seen)
    a = choose_voicing(rng(7), Chord(5), C, 4, PAD, prev=(60, 64, 67, 72))
    assert a == choose_voicing(rng(7), Chord(5), C, 4, PAD, prev=(60, 64, 67, 72))


def test_a_long_play_stays_in_the_middle():
    r, prev, means = rng(3), None, []
    prog = [parse_roman(x, C) for x in ("I", "vi", "IV", "V", "iii", "ii", "V7", "I")]
    for i in range(400):
        prev = choose_voicing(r, prog[(i + r.rnd(3)) % len(prog)], C, 4, PAD, prev=prev)
        means.append(sum(prev) / 4)
    assert abs(sum(means) / len(means) - PAD.mid) < 6
    assert min(means) > PAD.low + 4 and max(means) < PAD.high - 4


def test_explain_in_plain_words():
    assert explain((60, 64, 67), (60, 65, 69), C) == "C4 held, E4 a step up to F4, G4 a step up to A4"
    assert "parallel fifths: C4-G4 to D4-A4" in explain((60, 64, 67), (62, 66, 69), C)


# ---- the band together ----

def test_melody_on_top():
    assert check_band({"melody": [76], "pad": [60, 64, 67], "bass": [36], "drums": [42, 81]}, C) == []
    why = check_band({"melody": [72], "pad": [64, 67, 76]}, C)
    assert why == ["the pad's E5 is not under the melody (C5)"]


def test_mud_across_members():
    why = check_band({"bass": [36], "guitar": [40]}, C)   # C2 under E2, from two members
    assert len(why) == 1 and "muddy" in why[0]
    assert check_band({"bass": [36], "guitar": [43, 52]}, C) == []


def test_every_style_can_voice_the_four_styles_chords():
    a = Key(9, "minor")
    for style, lead in LEADING.items():
        for ch in (parse_roman(x, a) for x in ("i", "bVI", "bVII", "iv", "V7")):
            assert voicings(ch, a, 4, PAD, lead), (style, ch)
