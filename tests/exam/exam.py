# SPDX-License-Identifier: GPL-3.0-or-later
"""Maestro's theory exam: our own questions, after MusicTheoryBench's idea (knowledge and reasoning, scored), none
of its questions copied. Each answer was worked out by hand from theory, not from the library, and each comes with
why, in plain words. The library sits the exam; the score says how much of the theory it has right.

    python tests/exam/exam.py          the score card and any wrong answers
    python tests/exam/exam.py --all    every question, with its answer and why

A question the library can't answer yet is marked with its `gap`: it counts against the score, the test lets it
through, and the test fails once it's answered right (so the mark comes off)."""
import sys
from dataclasses import dataclass
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from maestro.theory.chords import (Chord, Vocabulary, borrowed_from, diatonic, function, kind, name, outside,
                                   parse_roman, roman, stack, two_five)
from maestro.theory.form import (DEVELOP, FORM, MOVES, Motif, Section, check_key_change, check_motif, check_section,
                                 fifths_apart)
from maestro.theory.pitch import LETTER_PC, LETTERS, Key, check_note
from maestro.theory.rhythm import CLAVES, Feel, check_band_rhythm, check_clave, explain_feel, explain_onsets, meter, \
    roll, swung, to_step
from maestro.theory.voicing import (LEADING, RANGES, Leading, Range, check_band, check_voicing, choose_voicing, explain,
                                    note_name, parallels)
from maestro.rng import ComposerRng

TOPICS = ("pitch", "chords", "voicing", "rhythm", "form")
LEVELS = ("knowledge", "reasoning")


@dataclass(frozen=True)
class Has:
    """A reason that must mention these words."""
    words: str

    def __eq__(self, got):
        return isinstance(got, str) and self.words in got

    def __repr__(self):
        return f"a reason with {self.words!r}"


@dataclass(frozen=True)
class Q:
    topic: str
    level: str
    question: str
    answer: object
    why: str
    ask: object          # () -> the library's answer
    gap: str | None = None


# ---- helpers: keys and chords from their names ----

def pc(note):
    """Pitch class of a note name: Bb is 10, E# is 5."""
    return (LETTER_PC[LETTERS.index(note[0])] + note.count("#") - note.count("b")) % 12


def key(text):
    """"Eb minor", "A harmonic minor" ... as a Key."""
    tonic, scale = text.split(" ", 1)
    return Key(pc(tonic), scale.replace(" ", "_"))


def chord(k, root, quality="maj", colour=None, bass=None):
    """A chord written with note names, in key k."""
    return Chord((pc(root) - k.tonic) % 12, quality, colour, None if bass is None else (pc(bass) - k.tonic) % 12)


def scale_of(text):
    k = key(text)
    return " ".join(k.name(s) for s in k.steps)


def numeral(ktext, *c):
    k = key(ktext)
    return roman(chord(k, *c), k)


def func(ktext, *c):
    k = key(ktext)
    return function(chord(k, *c), k)[0]


def names(k, chords):
    return " ".join(name(c, k) for c in chords)


def tones(ktext, *c):
    k = key(ktext)
    return " ".join(k.name(t) for t in chord(k, *c).tones)


def n(text):
    """A MIDI note from its name: C4 is 60, Bb1 is 34."""
    i = len(text) - (2 if text[-2] == "-" else 1)
    return 12 * (int(text[i:]) + 1) + pc(text[:i])


def notes(text):
    return [n(x) for x in text.split()]


def rng(seed=1):
    r = ComposerRng()
    r.seed(seed)
    return r


C = key("C major")
WIDE = Range(24, 96)   # a span wide enough that only the question's rule can rule a voicing out
M44, M68 = meter("4/4"), meter("6/8")
EIGHTHS = (12,) * 3


def motif(*steps, length=12):
    return Motif(steps, (length,) * len(steps))


def section(kind, energy, grow=0.0):
    return Section(kind, 0, 16, C, energy, grow)


# ---- the questions ----

EXAM = [
    # pitch: scales and their spelling
    Q("pitch", "knowledge", "Spell the D major scale.", "D E F# G A B C#",
      "Two sharps: F# and C#. Each letter once, so the seventh is C#, not Db.", lambda: scale_of("D major")),
    Q("pitch", "knowledge", "Spell the Eb minor scale.", "Eb F Gb Ab Bb Cb Db",
      "Six flats. The sixth is Cb, not B: the letter after B-flat is C.", lambda: scale_of("Eb minor")),
    Q("pitch", "knowledge", "Spell the F# major scale.", "F# G# A# B C# D# E#",
      "Six sharps. The seventh is E#, not F: F is already the tonic's letter.", lambda: scale_of("F# major")),
    Q("pitch", "knowledge", "Spell the C# minor scale.", "C# D# E F# G# A B",
      "The relative minor of E major: the same four sharps.", lambda: scale_of("C# minor")),
    Q("pitch", "knowledge", "Spell A harmonic minor.", "A B C D E F G#",
      "Natural minor with the seventh raised a semitone, so the V chord gets a leading tone.",
      lambda: scale_of("A harmonic minor")),
    Q("pitch", "knowledge", "Spell D melodic minor (as played going up).", "D E F G A B C#",
      "Minor with the sixth and seventh raised: a major scale with a minor third.", lambda: scale_of("D melodic minor")),
    Q("pitch", "knowledge", "Spell E phrygian.", "E F G A B C D",
      "The white notes from E: the dark half step from E up to F is phrygian's sound.", lambda: scale_of("E phrygian")),
    Q("pitch", "knowledge", "Spell F lydian.", "F G A B C D E",
      "The white notes from F: major with a raised fourth (B, not Bb).", lambda: scale_of("F lydian")),
    Q("pitch", "knowledge", "Spell Bb mixolydian.", "Bb C D Eb F G Ab",
      "Bb major with the seventh lowered: Ab, the flat seven rock leans on.", lambda: scale_of("Bb mixolydian")),
    Q("pitch", "knowledge", "Spell the E major pentatonic.", "E F# G# B C#",
      "E major without its fourth and seventh: no half steps at all.", lambda: scale_of("E major pent")),
    Q("pitch", "knowledge", "Spell the A blues scale.", "A C D Eb E G",
      "Minor pentatonic plus the blue note, the flat five: written Eb (b5), the way blues players and most books "
      "write it.", lambda: scale_of("A blues")),
    Q("pitch", "knowledge", "Is Bb in F major?", True, "F major's one flat is Bb.",
      lambda: check_note(key("F major"), (pc("Bb") - pc("F")) % 12) is None),
    Q("pitch", "knowledge", "Is F# in C major?", False, "C major has no sharps or flats.",
      lambda: check_note(C, pc("F#")) is None),
    # pitch: key relations
    Q("pitch", "reasoning", "What is the relative minor of Eb major?", "C minor",
      "Same three flats; the relative minor starts on the sixth degree (a minor third below).",
      lambda: str(MOVES["relative"](key("Eb major")))),
    Q("pitch", "reasoning", "What is the parallel minor of A major?", "A minor",
      "Parallel keys share the tonic and change the mode.", lambda: str(MOVES["parallel"](key("A major")))),
    Q("pitch", "reasoning", "Which key is a fifth up from E minor?", "B minor",
      "The dominant key, same mode: one sharp more.", lambda: str(MOVES["fifth_up"](key("E minor")))),
    Q("pitch", "reasoning", "How many steps round the circle of fifths from C major to A major?", 3,
      "C, G, D, A: A major has three sharps.", lambda: fifths_apart(C, key("A major"))),
    Q("pitch", "reasoning", "How far round the circle are A minor and C major?", 0,
      "Relative keys: the same notes, the same place on the circle.", lambda: fifths_apart(key("A minor"), C)),
    Q("pitch", "reasoning", "How far round the circle are C major and F# major?", 6,
      "The far side of the circle: six sharps, the tritone away.", lambda: fifths_apart(C, key("F# major"))),
    Q("pitch", "reasoning", "How far round the circle are D major and F major?", 3,
      "Two sharps to one flat: D, G, C, F.", lambda: fifths_apart(key("D major"), key("F major"))),

    # chords: names, numerals, spelling
    Q("chords", "knowledge", "Name the triads of C major, degree by degree.", "C Dm Em F G Am Bdim",
      "Major on I, IV and V; minor on ii, iii and vi; diminished on vii.", lambda: names(C, diatonic(C))),
    Q("chords", "knowledge", "Name the seventh chords of C major.", "Cmaj7 Dm7 Em7 Fmaj7 G7 Am7 Bm7b5",
      "Only V gets a dominant seventh; vii is half-diminished.", lambda: names(C, diatonic(C, sevenths=True))),
    Q("chords", "knowledge", "The roman numerals of A minor's triads?", "i ii° bIII iv v bVI bVII",
      "Counted from A major's scale, so the flat third, sixth and seventh show (DadCraft's choice, 2.2).",
      lambda: " ".join(roman(c, key("A minor")) for c in diatonic(key("A minor")))),
    Q("chords", "knowledge", "The roman numerals of A harmonic minor's triads?", "i ii° bIII+ iv V bVI vii°",
      "The raised seventh (G#) makes V major, vii diminished and III augmented.",
      lambda: " ".join(roman(c, key("A harmonic minor")) for c in diatonic(key("A harmonic minor")))),
    Q("chords", "knowledge", "Bb major in C major: which numeral?", "bVII",
      "Bb is a whole step below C: the flat seven, borrowed from C minor.", lambda: numeral("C major", "Bb")),
    Q("chords", "knowledge", "Ab major in C major: which numeral?", "bVI", "Ab is the flat sixth degree.",
      lambda: numeral("C major", "Ab")),
    Q("chords", "knowledge", "D major in C major: which numeral?", "V/V",
      "D major is G's dominant (its F# leads to G): the five of five.", lambda: numeral("C major", "D")),
    Q("chords", "knowledge", "D7 in C major: which numeral?", "V7/V", "The dominant seventh of G.",
      lambda: numeral("C major", "D", "maj", "7")),
    Q("chords", "knowledge", "E7 in C major: which numeral?", "V7/vi",
      "E7's G# leads to A: the dominant of A minor, the vi chord.", lambda: numeral("C major", "E", "maj", "7")),
    Q("chords", "knowledge", "F#dim in C major: which numeral?", "vii°/V",
      "F# is G's leading tone: the leading-tone chord of the five.", lambda: numeral("C major", "F#", "dim")),
    Q("chords", "knowledge", "Bm7b5 in C major: which numeral?", "viiø7",
      "The seventh chord on the seventh degree: half-diminished.", lambda: numeral("C major", "B", "dim", "7")),
    Q("chords", "knowledge", "Fm in C major: which numeral?", "iv", "The four chord with a minor third: Ab.",
      lambda: numeral("C major", "F", "min")),
    Q("chords", "knowledge", "G/B in C major: which numeral?", "V6",
      "The five chord with its third in the bass: first inversion, figure 6.",
      lambda: numeral("C major", "G", "maj", None, "B")),
    Q("chords", "knowledge", "C/G in C major: which numeral?", "I64",
      "The tonic with its fifth in the bass: second inversion, 6-4.", lambda: numeral("C major", "C", "maj", None, "G")),
    Q("chords", "knowledge", "G7 over B, over D and over F: the numerals?", "V65 V43 V42",
      "A seventh chord's inversions: third in the bass 6-5, fifth 4-3, seventh 4-2.",
      lambda: " ".join(numeral("C major", "G", "maj", "7", b) for b in ("B", "D", "F"))),
    Q("chords", "knowledge", "The bII in E phrygian?", "bII",
      "F major, a half step above E: phrygian's own chord.", lambda: numeral("E phrygian", "F")),
    Q("chords", "knowledge", "Name the chord a minor third above C in C major.", "Eb",
      "Written as a third (Eb, the bIII), not a second (D#).", lambda: name(Chord(3), C)),
    Q("chords", "knowledge", "Spell Cmaj7.", "C E G B", "Root, major third, fifth, major seventh.",
      lambda: tones("C major", "C", "maj", "maj7")),
    Q("chords", "knowledge", "Spell A7 in D major.", "A C# E G", "D's dominant seventh: its C# leads to D.",
      lambda: tones("D major", "A", "maj", "7")),
    Q("chords", "knowledge", "Spell Csus4.", "C F G", "The third replaced by the fourth.",
      lambda: tones("C major", "C", "sus4")),
    Q("chords", "knowledge", "Spell F#m7b5 in E minor.", "F# A C E",
      "E minor's ii chord with a seventh: half-diminished.", lambda: tones("E minor", "F#", "dim", "7")),
    Q("chords", "knowledge", "Name the power chord on the tonic of E major, and its numeral.", "E5 I5",
      "Root and fifth only: no third, so neither major nor minor.",
      lambda: f"{name(Chord(0, 'power'), key('E major'))} {roman(Chord(0, 'power'), key('E major'))}"),
    Q("chords", "knowledge", "bVI in A minor is which chord?", "F", "A's sixth degree is F.",
      lambda: name(parse_roman("bVI", key("A minor")), key("A minor"))),
    Q("chords", "knowledge", "V7/V in C is which chord?", "D7", "G's dominant seventh.",
      lambda: name(parse_roman("V7/V", C), C)),
    Q("chords", "knowledge", "iiø7 in C is which chord?", "Dm7b5", "D F Ab C: the minor key's ii chord in C.",
      lambda: name(parse_roman("iiø7", C), C)),
    # chords: what kind, what function
    Q("chords", "reasoning", "Fm in C major is diatonic, secondary, borrowed or chromatic? From where?",
      "borrowed minor", "Its Ab isn't in C major; C minor has all of F Ab C.",
      lambda: f"{kind(chord(C, 'F', 'min'), C)} {borrowed_from(chord(C, 'F', 'min'), C)[0]}"),
    Q("chords", "reasoning", "Db major in C major (the Neapolitan): what kind, from where, what numeral?",
      "borrowed phrygian bII", "Db F Ab sits in C phrygian, the one mode on C with a flat second.",
      lambda: f"{kind(chord(C, 'Db'), C)} {borrowed_from(chord(C, 'Db'), C)[0]} {numeral('C major', 'Db')}"),
    Q("chords", "reasoning", "G7 in C: home, away or tension?", "tension",
      "The dominant: its B pulls up to C and its F down to E.", lambda: func("C major", "G", "maj", "7")),
    Q("chords", "reasoning", "Am in C: home, away or tension?", "home",
      "It shares C and E with the tonic: a softer home (the deceptive cadence lands there).",
      lambda: func("C major", "A", "min")),
    Q("chords", "reasoning", "Em in C: home, away or tension?", "home",
      "It shares E and G with the tonic: another soft home.", lambda: func("C major", "E", "min")),
    Q("chords", "reasoning", "F in C: home, away or tension?", "away",
      "The subdominant leads away from home, on towards the dominant.", lambda: func("C major", "F")),
    Q("chords", "reasoning", "Bb in C: home, away or tension?", "away",
      "The flat seven, a step below home: it leads on, often straight back to C.", lambda: func("C major", "Bb")),
    Q("chords", "reasoning", "E7 in C: home, away or tension?", "tension",
      "A secondary dominant: it pulls to A minor.", lambda: func("C major", "E", "maj", "7")),
    Q("chords", "reasoning", "Bdim in C: home, away or tension?", "tension",
      "It holds the leading tone B and the tritone B-F: it wants to resolve.", lambda: func("C major", "B", "dim")),
    Q("chords", "reasoning", "C major in A minor: home, away or tension?", "home",
      "The relative major: home in a brighter light.", lambda: func("A minor", "C")),
    Q("chords", "reasoning", "Bdim in A minor: home, away or tension?", "away",
      "Here it's the ii chord with no leading tone (that would be G#): it leads on to the dominant.",
      lambda: func("A minor", "B", "dim")),
    Q("chords", "reasoning", "Em (the minor v) in A minor: home, away or tension?", "away",
      "Without G# there's no leading tone: only a soft pull home.", lambda: func("A minor", "E", "min")),
    Q("chords", "reasoning", "The ii-V into C major (salsa's ii7-V7-I)?", "Dm7 G7",
      "ii and V of C, with their sevenths.", lambda: names(C, two_five(0))),
    Q("chords", "reasoning", "In C, the secondary ii-V that leads to Dm?", "Em7 A7",
      "Treat D as a passing home: its ii is E, its V is A.", lambda: names(C, two_five(2))),
    Q("chords", "reasoning", "In C, the minor ii-V that leads to Am?", "Bm7b5 E7",
      "A minor's ii is half-diminished; its V takes the leading tone G#.", lambda: names(C, two_five(9, minor=True))),
    Q("chords", "reasoning", "A style that plays only diatonic chords meets Bb in C: why is it rare there?",
      Has("borrowed"), "Bb comes from C minor: borrowed, which this style seldom reaches for (a lean, never a ban).",
      lambda: outside(chord(C, "Bb"), C, Vocabulary())),

    # voicing
    Q("voicing", "knowledge", "The bass's lowest note and the melody's highest?", "C1 C7",
      "C1 is an 808's floor; C7 the top of a lead line.",
      lambda: f"{note_name(C, RANGES['bass'].low)} {note_name(C, RANGES['melody'].high)}"),
    Q("voicing", "reasoning", "C major played as C2 E2 G2: does it fit?", Has("muddy"),
      "A third that low turns to mud: thirds want C3 or so and up.",
      lambda: check_voicing(notes("C2 E2 G2"), Chord(0), C, WIDE)),
    Q("voicing", "reasoning", "A power chord C2 G2: does it fit?", None,
      "A fifth stays clear far lower (down to Bb1): why power chords work low.",
      lambda: check_voicing(notes("C2 G2"), Chord(0, "power"), C, WIDE)),
    Q("voicing", "reasoning", "A power chord C1 G1: does it fit?", Has("muddy"),
      "Even a fifth blurs below Bb1.", lambda: check_voicing(notes("C1 G1"), Chord(0, "power"), C, WIDE)),
    Q("voicing", "reasoning", "C major as C4 G4 C5: does it fit?", Has("third is missing"),
      "No E: without its third the chord is neither major nor minor.",
      lambda: check_voicing(notes("C4 G4 C5"), Chord(0), C, WIDE)),
    Q("voicing", "reasoning", "C major as C4 E4 F#4: does it fit?", Has("not in the chord"),
      "F# is not a note of C major.", lambda: check_voicing(notes("C4 E4 F#4"), Chord(0), C, WIDE)),
    Q("voicing", "reasoning", "A pad plays C4 E4 G4 under a melody on F4: does it fit?", Has("not under the melody"),
      "The G is above the tune: the melody must stay on top.",
      lambda: check_voicing(notes("C4 E4 G4"), Chord(0), C, WIDE, ceiling=n("F4"))),
    Q("voicing", "reasoning", "Salsa keys play Cmaj7 as E4 G4 B4: does it fit? And in a plain style?",
      (None, Has("root is missing")),
      "Salsa's keys play rootless, leaving the root to the bass; a plain style needs the root (it drops the fifth "
      "first when there's no room).",
      lambda: tuple(check_voicing(notes("E4 G4 B4"), Chord(0, "maj", "maj7"), C, WIDE, LEADING[s])
                    for s in ("salsa", "plain"))),
    Q("voicing", "reasoning", "C3 G3 moving to D3 A3: any parallels?", [("fifths", 0, 1)],
      "Both voices step up together a fifth apart: parallel fifths (power rock likes them, a plain style avoids them).",
      lambda: parallels(notes("C3 G3"), notes("D3 A3"))),
    Q("voicing", "reasoning", "C3 G3 moving to B2 A3: any parallels?", [],
      "The voices move in opposite directions: contrary motion, no parallels.",
      lambda: parallels(notes("C3 G3"), notes("B2 A3"))),
    Q("voicing", "reasoning", "Keys on C4 E4 G4 go to F major: the smoothest voicing?", (n("C4"), n("F4"), n("A4")),
      "Hold the common tone C, step E up to F and G up to A.",
      lambda: choose_voicing(rng(), chord(C, "F"), C, 3, RANGES["keys"], notes("C4 E4 G4"),
                             Leading(slack=0))),
    Q("voicing", "reasoning", "Keys on G3 B3 D4 go to C major: the smoothest voicing?", (n("G3"), n("C4"), n("E4")),
      "Hold G, the leading tone B rises to C, D steps up to E.",
      lambda: choose_voicing(rng(), Chord(0), C, 3, RANGES["keys"], notes("G3 B3 D4"),
                             Leading(slack=0))),
    Q("voicing", "reasoning", "Say the move C4 E4 G4 to C4 F4 A4 in words.", "C4 held, E4 a step up to F4, G4 a step "
      "up to A4", "Each voice's move, bottom up.", lambda: explain(notes("C4 E4 G4"), notes("C4 F4 A4"), C)),
    Q("voicing", "reasoning", "A pad on C5 while the melody plays G4: what's wrong?", Has("not under the melody"),
      "The pad rises over the tune and hides it.", lambda: " ".join(check_band({"pad": notes("C5"),
                                                                                "melody": notes("G4")}, C))),

    # rhythm
    Q("rhythm", "knowledge", "Steps in a bar of 4/4, 6/8 and 7/8 (24 a beat)?", (96, 72, 84),
      "Four quarters; six eighths (12 steps each); seven eighths.",
      lambda: tuple(meter(m).bar for m in ("4/4", "6/8", "7/8"))),
    Q("rhythm", "knowledge", "Where do the beats of 7/8 played 2+2+3 start?", (0, 24, 48),
      "Two eighths, two eighths, then three: beats of 24, 24 and 36 steps.", lambda: meter("7/8").beats),
    Q("rhythm", "knowledge", "Count steps 36, 8 and 66 of a 4/4 bar.", "2 and, 1 trip, 3 a",
      "36 is half a beat into beat 2; 8 a third into beat 1 (the triplet); 66 three quarters into beat 3.",
      lambda: ", ".join(M44.count(s) for s in (36, 8, 66))),
    Q("rhythm", "knowledge", "Count step 30 of a 6/8 bar.", "3 and", "6/8 counts eighths: 30 is half way through the third.",
      lambda: M68.count(30)),
    Q("rhythm", "knowledge", "Where does the snare's backbeat fall in 4/4, in half-time, in 6/8 and in 3/4?",
      ((24, 72), (48,), (36,), (24, 48)),
      "2 and 4; half-time moves it to 3 (trap); in 6/8 the second big beat; in 3/4 beats 2 and 3.",
      lambda: (M44.backbeat(), M44.backbeat("half"), M68.backbeat(), meter("3/4").backbeat())),
    Q("rhythm", "knowledge", "How strong are steps 0, 48, 24, 12, 6 and 8 of a 4/4 bar (0-5)?", [5, 4, 3, 2, 1, 0],
      "The downbeat, the middle of the bar, a beat, an 8th, a 16th, and a triplet between them.",
      lambda: [M44.weight(s) for s in (0, 48, 24, 12, 6, 8)]),
    Q("rhythm", "knowledge", "Son clave 3-2, counted.", "bar 1: 1, 2 and, 4 | bar 2: 2, 3",
      "Three notes in the first bar, two in the second.", lambda: explain_onsets(CLAVES["son_3-2"].onsets, M44)),
    Q("rhythm", "knowledge", "Son clave 2-3, counted.", "bar 1: 2, 3 | bar 2: 1, 2 and, 4",
      "The same clave starting from its other side.", lambda: explain_onsets(CLAVES["son_2-3"].onsets, M44)),
    Q("rhythm", "knowledge", "Rumba clave 3-2, counted.", "bar 1: 1, 2 and, 4 and | bar 2: 2, 3",
      "Like son, with the third note pushed half a beat later.",
      lambda: explain_onsets(CLAVES["rumba_3-2"].onsets, M44)),
    Q("rhythm", "knowledge", "Notes in a 32nd roll, a 16th-triplet roll and a 32nd-triplet roll over one beat?",
      (8, 6, 12), "Eight 32nds, six 16th triplets, twelve 32nd triplets to a quarter.",
      lambda: tuple(len(roll(0, 24, r)) for r in ("32nd", "16th_triplet", "32nd_triplet"))),
    Q("rhythm", "knowledge", "A note played at tick 487 (480 a beat): which step, and how far off?", (24, 7),
      "Beat 2 starts at tick 480: the note is 7 ticks late, and goes on the grid at step 24.", lambda: to_step(487)),
    Q("rhythm", "reasoning", "A part on son 3-2's notes, in a song in son 2-3: does it fit?", Has("crossed"),
      "It lines up with the other side: crossed clave, the one mistake salsa players don't forgive.",
      lambda: check_clave(CLAVES["son_3-2"].onsets, CLAVES["son_2-3"])),
    Q("rhythm", "reasoning", "A tumbao (2 and, 4, the same each bar) in son 2-3: does it fit?", None,
      "A part that repeats each bar sits with both sides of the clave alike.",
      lambda: check_clave((36, 72, 132, 168), CLAVES["son_2-3"])),
    Q("rhythm", "reasoning", "Triplet-swung 8ths: where does the 'and' (step 12) land?", 16,
      "Two thirds of the beat in: the third triplet.", lambda: swung(12, Feel(swing=4))),
    Q("rhythm", "reasoning", "Describe triplet swing and hard swing on 8ths.",
      "swung 8ths (67:33), on the grid; swung 8ths (75:25), on the grid",
      "Triplet swing splits the beat 2 to 1; hard swing 3 to 1, a dotted 8th and a 16th.",
      lambda: f"{explain_feel(Feel(swing=4))}; {explain_feel(Feel(swing=6))}"),
    Q("rhythm", "reasoning", "A bass swung by 3 steps plays the 16th after the beat: does it fit?", Has("off the grid"),
      "That swing would put the note between grid steps (7.5): every note lands on the grid (decision 13).",
      lambda: " ".join(check_band_rhythm({"bass": ([0, 6], Feel(swing=3))}, M44))),
    Q("rhythm", "reasoning", "Straight drums and a swung bass both play '1 and': does it fit?", Has("out of sync"),
      "They'd land on different steps: members playing the same note play it together.",
      lambda: " ".join(check_band_rhythm({"drums": ([12], Feel()), "bass": ([12], Feel(swing=4))}, M44))),

    # form
    Q("form", "reasoning", "A play opens with a Calm: does it fit?", Has("opens at Home"),
      "A play starts at Home, where the music lives.", lambda: check_section("calm", 0.3)),
    Q("form", "reasoning", "A Lift at energy 0.55 after a Home ending at 0.6: does it fit?", Has("doesn't lift"),
      "A Lift has to raise the energy.", lambda: check_section("lift", 0.55, section("home", 0.6))),
    Q("form", "reasoning", "A Calm at energy 0.8: does it fit?", Has("too loud"),
      "A calm moment needs to come down.", lambda: check_section("calm", 0.8, section("home", 0.7))),
    Q("form", "reasoning", "A Calm straight after a Calm: does it fit?", Has("the same journey twice"),
      "Back to back, two of the same kind tread the same ground.", lambda: check_section("calm", 0.3,
                                                                                       section("calm", 0.3))),
    Q("form", "reasoning", "A Turn jumping from 0.4 to 0.9: does it fit?", Has("too hard"),
      "Only a Lift may rise that fast.", lambda: check_section("turn", 0.9, section("home", 0.4))),
    Q("form", "reasoning", "A key lift up a semitone into a Calm: does it fit?", Has("belong on a Lift"),
      "The truck driver's change raises the energy: it goes where the music lifts.",
      lambda: check_key_change(C, key("Db major"), "step_up", "calm", 200, 1, FORM["plain"], 25)),
    Q("form", "reasoning", "A key change 10 bars after the last (at 25 bars a minute): does it fit?", Has("too soon"),
      "Key changes need minutes between them to land.",
      lambda: check_key_change(C, key("G major"), "fifth_up", "home", 10, 1, FORM["plain"], 25)),
    Q("form", "reasoning", "A motif turned upside down: still heard as the motif?", None,
      "The same interval sizes and rhythm, the other way up: still itself.",
      lambda: check_motif(DEVELOP["invert"](rng(), motif(0, 1, 2, 4)), motif(0, 1, 2, 4))),
    Q("form", "reasoning", "A motif played backwards: still heard as the motif?", None,
      "The same intervals in reverse order: still recognisable.",
      lambda: check_motif(DEVELOP["back"](rng(), motif(0, 1, 2, 4)), motif(0, 1, 2, 4))),
    Q("form", "reasoning", "A motif that leaps five scale steps (a sixth): does it fit?", Has("too wild"),
      "A leap that big breaks the figure apart.", lambda: check_motif(motif(0, 5, 4))),
    Q("form", "reasoning", "A motif spanning eight scale steps: does it fit?", Has("too wide"),
      "Wider than an octave: too wide to sing.", lambda: check_motif(motif(0, 4, 8))),
    Q("form", "reasoning", "A motif of one note: does it fit?", Has("isn't a motif"),
      "A motif needs at least two notes to have a shape.", lambda: check_motif(motif(0))),
    Q("form", "reasoning", "The same statement a third time running: does it fit?", Has("stale"),
      "Three the same in a row: it stops developing.",
      lambda: check_motif(motif(0, 1, 2), recent=[motif(0, 1, 2)] * 2)),
    Q("form", "knowledge", "A motif of 8ths, twice as slow: the lengths in steps?", (24, 24, 24),
      "8ths are 12 steps; twice as slow makes them quarters.",
      lambda: DEVELOP["augment"](rng(), motif(0, 1, 2)).lengths),
]


def run():
    """(question, the library's answer, right?) for every question; a crash is a wrong answer."""
    out = []
    for q in EXAM:
        try:
            got = q.ask()
        except Exception as e:   # the library can't answer: a wrong answer, not the end of the exam
            got = f"{type(e).__name__}: {e}"
        out.append((q, got, q.answer == got if isinstance(q.answer, Has) else got == q.answer))
    return out


def card(results):
    lines = []
    for label, groups, attr in (("topic", TOPICS, "topic"), ("level", LEVELS, "level")):
        for g in groups:
            rs = [ok for q, _, ok in results if getattr(q, attr) == g]
            if rs:
                lines.append(f"  {g:<10} {sum(rs):>3}/{len(rs):<3} {100 * sum(rs) // len(rs):>3}%")
        lines.append("")
    right = sum(ok for _, _, ok in results)
    lines.append(f"  score      {right:>3}/{len(results):<3} {100 * right // len(results):>3}%")
    return "\n".join(lines)


def main(argv):
    results = run()
    print("Maestro's theory exam\n")
    print(card(results))
    for q, got, ok in results:
        if ok and "--all" not in argv:
            continue
        print(f"\n[{'right' if ok else 'WRONG'}] {q.topic}, {q.level}: {q.question}")
        print(f"  answer: {q.answer!r}" + ("" if ok else f"\n  Maestro said: {got!r}"))
        print(f"  why: {q.why}")
        if q.gap:
            print(f"  gap: {q.gap}")


if __name__ == "__main__":
    main(sys.argv[1:])
