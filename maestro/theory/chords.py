# SPDX-License-Identifier: GPL-3.0-or-later
"""Chords in a key: what they are (diatonic, borrowed, secondary, chromatic), their names and roman numerals, and
their function (home, away, tension). A chord is written as in `docs/format.md`: root, quality, colour and bass,
all in semitones from the key note.

Roman numerals count from the tonic's major scale, so a minor key reads i ii° bIII iv v bVI bVII, and rock's flat
seven is bVII in any key."""
from dataclasses import dataclass, replace
from functools import lru_cache

from ..stylebook import table
from .pitch import SCALES, Key

QUALITIES = {
    "maj": (0, 4, 7), "min": (0, 3, 7), "dim": (0, 3, 6), "aug": (0, 4, 8),
    "sus2": (0, 2, 7), "sus4": (0, 5, 7), "power": (0, 7),
}
# What each colour adds over the root, and the qualities it goes on. "7" is the seventh a step below the octave:
# on a diminished triad that is the half-diminished chord (m7b5); "dim7" is the fully diminished one.
COLOURS = {
    "6": ((9,), ("maj", "min")),
    "7": ((10,), ("maj", "min", "dim", "aug", "sus2", "sus4")),
    "maj7": ((11,), ("maj", "min", "aug")),
    "dim7": ((9,), ("dim",)),
    "add9": ((2,), ("maj", "min", "sus4")),
    "9": ((10, 2), ("maj", "min", "sus4")),
    "maj9": ((11, 2), ("maj", "min")),
}
KINDS = ("diatonic", "secondary", "borrowed", "chromatic")
FUNCTIONS = ("home", "away", "tension")

# Where borrowed chords come from: the other scales on the same tonic, the commonest sources first.
BORROW_ORDER = ("minor", "major", "dorian", "mixolydian", "harmonic_minor", "phrygian", "lydian", "melodic_minor",
                "phrygian_dominant", "locrian")

_NUMERALS = ("I", "II", "III", "IV", "V", "VI", "VII")
_MAJOR = SCALES["major"]


@dataclass(frozen=True)
class Chord:
    root: int                 # semitones from the key note, 0-11
    quality: str = "maj"
    colour: str | None = None
    bass: int | None = None   # None: the root

    def __post_init__(self):
        if self.quality not in QUALITIES:
            raise ValueError(f"unknown quality {self.quality!r}")
        if self.colour is not None and (self.colour not in COLOURS or self.quality not in COLOURS[self.colour][1]):
            raise ValueError(f"{self.colour!r} doesn't go on a {self.quality} chord")
        object.__setattr__(self, "root", self.root % 12)
        if self.bass is not None:
            object.__setattr__(self, "bass", None if self.bass % 12 == self.root else self.bass % 12)

    @property
    def intervals(self):
        """Semitones over the root, root first, each once."""
        iv = list(QUALITIES[self.quality])
        if self.colour:
            iv += [i for i in COLOURS[self.colour][0] if i not in iv]
        return tuple(iv)

    @property
    def tones(self):
        """Pitch classes from the key note, root first."""
        return tuple((self.root + i) % 12 for i in self.intervals)

    @property
    def low(self):
        return self.root if self.bass is None else self.bass


def stack(key, degree, sevenths=False):
    """The chord built in thirds on a degree of the key's chord scale (a pentatonic or blues key uses its parent
    seven-note scale, like the composer)."""
    steps = SCALES[key.chord_scale]
    n = len(steps)
    at = [(steps[(degree + k) % n] - steps[degree % n]) % 12 for k in (0, 2, 4, 6)]
    quality = next((q for q, iv in QUALITIES.items() if len(iv) == 3 and iv[1:] == tuple(at[1:3])), None)
    if quality is None:
        raise ValueError(f"degree {degree} of {key} stacks to no triad")
    colour = None
    if sevenths and n == 7:
        colour = {9: "dim7", 10: "7", 11: "maj7"}.get(at[3])
    return Chord(steps[degree % n], quality, colour)


def diatonic(key, sevenths=False):
    return [stack(key, d, sevenths) for d in range(len(SCALES[key.chord_scale]))]


def _fits(chord, steps):
    return all(t in steps for t in chord.tones)


def _resolves_to(chord):
    """Where a dominant-shaped chord pulls: a fifth down for a major or dominant-seventh chord, a step up for a
    diminished one (the leading-tone chord). None for anything else."""
    if chord.quality == "maj" and chord.colour in (None, "7", "9"):
        return (chord.root + 5) % 12
    if chord.quality == "dim":
        return (chord.root + 1) % 12
    return None


def secondary_target(chord, key):
    """The degree a secondary chord leans toward (V/V leans to degree 4's root), or None. The target is a major or
    minor chord of the key other than the tonic, and the chord itself is outside the key."""
    steps = SCALES[key.chord_scale]
    if _fits(chord, steps):
        return None
    to = _resolves_to(chord)
    if to is None or to == 0 or to not in steps:
        return None
    target = stack(key, steps.index(to))
    return to if target.quality in ("maj", "min") else None


def borrowed_from(chord, key):
    """The scales on the same tonic whose notes hold this chord, commonest first ([] for none)."""
    return [s for s in BORROW_ORDER if s != key.chord_scale and _fits(chord, SCALES[s])]


def kind(chord, key):
    """diatonic, secondary (a dominant of another chord of the key), borrowed (from a scale on the same tonic) or
    chromatic. Secondary wins over borrowed: D major in C is V/V before it is lydian's II."""
    if _fits(chord, SCALES[key.chord_scale]):
        return "diatonic"
    if secondary_target(chord, key) is not None:
        return "secondary"
    if borrowed_from(chord, key):
        return "borrowed"
    return "chromatic"


def function(chord, key):
    """(home | away | tension, the reason in plain words). Tension pulls somewhere, home rests, away is the
    in-between that leads on."""
    r, q = chord.root, chord.quality
    to = secondary_target(chord, key)
    if to is not None:
        return "tension", f"a dominant of {roman(stack(key, SCALES[key.chord_scale].index(to)), key)}: leans there"
    if q == "aug" or (q == "dim" and (11 in chord.tones or chord.colour == "dim7")):
        return "tension", f"{'diminished' if q == 'dim' else 'augmented'}: unstable, wants to move"
    if q == "dim":
        return "away", "diminished without the leading tone: leads on to the dominant"
    if r == 7 and q in ("maj", "sus4", "power"):
        return "tension", "the dominant: pulls back home"
    if r == 1 and key.scale in ("phrygian", "phrygian_dominant"):
        return "tension", "a half step above home: falls straight back to it"
    if r == 0:
        return "home", "the tonic"
    if (r, q) in ((9, "min"), (4, "min")) and not key.minorish:
        return "home", "shares two notes with the tonic: a softer home"
    if (r, q) == (3, "maj") and key.minorish:
        return "home", "the relative major: home in a brighter light"
    if r == 7:
        return "away", "a dominant without the leading tone: a soft pull"
    if r == 10:
        return "away", "a step below home: often leads straight back"
    return "away", "moves away from home and leads on"


def _numeral(root, quality):
    """(accidental, number 1-7) for a root: b3 is a flat three, the tritone is #4 under a diminished chord, else b5."""
    number = {0: 1, 1: 2, 2: 2, 3: 3, 4: 3, 5: 4, 6: 4 if quality == "dim" else 5, 7: 5, 8: 6, 9: 6, 10: 7,
              11: 7}[root]
    d = (root - _MAJOR[number - 1] + 6) % 12 - 6
    return ("#" * d if d > 0 else "b" * -d), number


_FIGURES = {(False, 1): "6", (False, 2): "64", (True, 1): "65", (True, 2): "43", (True, 3): "42"}


def roman(chord, key):
    """The roman numeral: case for major or minor, ° diminished, ø half-diminished, + augmented, 5 power, inversions
    as figures (I6, V65), secondary chords as V7/ii."""
    to = secondary_target(chord, key)
    if to is not None:
        base = replace(chord, root=(chord.root - to) % 12, bass=None if chord.bass is None else chord.bass - to)
        return f"{_roman(base)}/{_roman(stack(key, SCALES[key.chord_scale].index(to)))}"
    return _roman(chord)


def _roman(chord):
    q, c = chord.quality, chord.colour
    acc, number = _numeral(chord.root, q)
    text = _NUMERALS[number - 1]
    if q in ("min", "dim"):
        text = text.lower()
    suffix = {"dim": "°", "aug": "+", "power": "5", "sus2": "sus2", "sus4": "sus4"}.get(q, "")
    seventh = c in ("7", "maj7", "dim7")
    if q == "dim" and c == "7":
        suffix, c = "ø", "7"
    elif c == "dim7":
        c = "7"
    if chord.bass is not None:
        iv = chord.intervals
        at = iv.index((chord.bass - chord.root) % 12) if (chord.bass - chord.root) % 12 in iv else None
        fig = _FIGURES.get((seventh, at)) if at is not None and q not in ("power", "sus2", "sus4") else None
        if fig:
            return acc + text + suffix + fig
        b_acc, b_num = _numeral(chord.bass, "")
        return f"{acc}{text}{suffix}{c or ''} over {b_acc}{b_num}"
    if c and q.startswith("sus"):
        return acc + text + c + suffix   # V7sus4
    return acc + text + suffix + (c or "")


_SYMBOL = {
    ("maj", None): "", ("maj", "7"): "7", ("maj", "maj7"): "maj7", ("maj", "6"): "6", ("maj", "add9"): "add9",
    ("maj", "9"): "9", ("maj", "maj9"): "maj9",
    ("min", None): "m", ("min", "7"): "m7", ("min", "maj7"): "m(maj7)", ("min", "6"): "m6",
    ("min", "add9"): "m(add9)", ("min", "9"): "m9", ("min", "maj9"): "m(maj9)",
    ("dim", None): "dim", ("dim", "7"): "m7b5", ("dim", "dim7"): "dim7",
    ("aug", None): "aug", ("aug", "7"): "aug7", ("aug", "maj7"): "aug(maj7)",
    ("sus2", None): "sus2", ("sus2", "7"): "7sus2", ("sus4", None): "sus4", ("sus4", "7"): "7sus4",
    ("sus4", "add9"): "sus4(add9)", ("sus4", "9"): "9sus4", ("power", None): "5",
}


def name(chord, key):
    """The chord symbol in the key's spelling: Bb in C major (bVII), F#dim in C (#iv°), G/B."""
    text = key.name(chord.root, _numeral(chord.root, chord.quality)[1]) + _SYMBOL[(chord.quality, chord.colour)]
    if chord.bass is not None:
        text += "/" + key.name(chord.bass)
    return text


def parse_roman(text, key=None):
    """A chord from a roman numeral as `roman` writes it (no figures): bVII, iiø7, V7/V, ivmaj7, bVI5, V7sus4.
    Secondary numerals take the target's root from the key (major when none is given)."""
    if "/" in text:
        head, target = text.split("/")
        t = parse_roman(target, key)
        c = parse_roman(head, key)
        return replace(c, root=c.root + t.root)
    i = 0
    acc = 0
    while text[i] in "b#":
        acc += 1 if text[i] == "#" else -1
        i += 1
    for number in range(7, 0, -1):   # VII before V before I
        word = _NUMERALS[number - 1]
        if text[i:i + len(word)].upper() == word:
            lower = text[i:i + len(word)].islower()
            i += len(word)
            break
    else:
        raise ValueError(f"no numeral in {text!r}")
    root = _MAJOR[number - 1] + acc
    rest = text[i:]
    quality = "min" if lower else "maj"
    colour = None
    for mark, q in (("°", "dim"), ("ø", "dim"), ("+", "aug"), ("sus2", "sus2"), ("sus4", "sus4")):
        if mark in rest:
            quality = q
            if mark == "ø":
                colour = "7"
            rest = rest.replace(mark, "")
    if rest == "5" and quality == "maj":
        return Chord(root, "power")
    if rest:
        colour = "dim7" if quality == "dim" and rest == "7" and "°7" in text else rest
    return Chord(root, quality, colour)


# ---- a style's vocabulary: a lean, never a ban ----

@dataclass(frozen=True)
class Vocabulary:
    """What a style usually lets into its harmony. Never a ban (decision 9: no style trait is a lock; DadCraft, Oct
    23): a chord outside it is only rarer. `outside` is the % of choices that step out, near chords (borrowed,
    secondary, other qualities and colours) more often than remote chromatic ones."""
    kinds: frozenset = frozenset(("diatonic",))
    qualities: frozenset = frozenset(("maj", "min", "dim"))
    colours: frozenset = frozenset((None,))
    borrow: tuple | None = None   # the scales it borrows from; None for any
    outside: int = 5

    def __post_init__(self):
        for what, names, known in (("kind", self.kinds, KINDS), ("quality", self.qualities, QUALITIES),
                                   ("colour", self.colours - {None}, COLOURS), ("scale", self.borrow or (), SCALES)):
            for n in names:
                if n not in known:
                    raise ValueError(f"unknown {what} {n!r}")


# The style book's files hold each style's vocabulary (harmony.vocabulary).
VOCAB = table(Vocabulary, "harmony", "vocabulary")


def outside(chord, key, vocab):
    """None when the chord is in the style's usual vocabulary for this key, else why not, in plain words."""
    k = kind(chord, key)
    if k not in vocab.kinds:
        why = f" (from {borrowed_from(chord, key)[0].replace('_', ' ')})" if k == "borrowed" else ""
        return f"{name(chord, key)} ({roman(chord, key)}) is {k}{why}, which this style rarely uses"
    if k == "borrowed" and vocab.borrow is not None and not set(borrowed_from(chord, key)) & set(vocab.borrow):
        src = borrowed_from(chord, key)[0].replace("_", " ")
        return f"{name(chord, key)} is borrowed from {src}, not a scale this style usually borrows from"
    if chord.quality not in vocab.qualities:
        return f"{name(chord, key)} is a {chord.quality} chord, rare in this style"
    if chord.colour not in vocab.colours:
        return f"{name(chord, key)} has a {chord.colour} colour, rare in this style"
    return None


def every_chord():
    """Every root-position chord: each root, quality and colour that goes with it."""
    return [Chord(root, q, c) for root in range(12) for q in QUALITIES for c in (None, *COLOURS)
            if c is None or q in COLOURS[c][1]]


@lru_cache(maxsize=256)
def _split(key, vocab):
    usual, rare = [], []
    for ch in every_chord():
        if outside(ch, key, vocab) is None:
            usual.append(ch)
        else:
            rare.append((ch, 1 if kind(ch, key) == "chromatic" else 4))
    return tuple(usual), tuple(rare)


def pool(key, vocab):
    """The chords the style usually plays in this key."""
    return list(_split(key, vocab)[0])


def beyond(key, vocab):
    """The chords it only now and then reaches for, as (chord, weight): near ones 4, remote chromatic ones 1."""
    return list(_split(key, vocab)[1])


def choose_chord(rng, chords, weight=lambda ch: 1):
    """Pick one chord, seeded, with whole-number weights (a style's tendencies; 0 leaves a chord out)."""
    ws = [weight(ch) for ch in chords]
    total = sum(ws)
    if total <= 0:
        raise ValueError("no chord left to choose from")
    r = rng.rnd(total)
    for ch, w in zip(chords, ws):
        r -= w
        if r < 0:
            return ch


def choose_in_style(rng, key, vocab, weight=lambda ch: 1):
    """A chord the style's way: from its usual pool, or `vocab.outside`% of the time from beyond it, seeded.
    `weight` (a style's or the moment's tendencies) applies to both; if it leaves nothing on one side, the other."""
    usual = [(ch, weight(ch)) for ch in pool(key, vocab)]
    rare = [(ch, w * weight(ch)) for ch, w in beyond(key, vocab)]
    sides = [rare, usual] if rng.rnd(100) < vocab.outside else [usual, rare]
    for side in sides:
        side = [(ch, w) for ch, w in side if w > 0]
        if side:
            ws = dict(side)
            return choose_chord(rng, [ch for ch, _ in side], ws.__getitem__)
    raise ValueError("no chord left to choose from")


def two_five(target, minor=False, sevenths=True):
    """The ii and V that lead to a chord rooted on `target` (semitones from the key note): salsa's ii7-V7-I, or
    iiø7-V7-i to a minor chord. Aimed at a chord other than the tonic it is a secondary ii-V."""
    c7 = "7" if sevenths else None
    two = Chord(target + 2, "dim" if minor else "min", c7)
    return two, Chord(target + 7, "maj", c7)
