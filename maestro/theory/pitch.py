# SPDX-License-Identifier: GPL-3.0-or-later
"""Keys and scales. Everything is in semitones from the key note (like the composer: the key is added last), with
pitch classes 0-11. A key is a tonic (C = 0) and a scale; note names are spelled from the key, so Bb in F, A# in B."""
from dataclasses import dataclass

# Scales as semitones from the tonic. The first eight are the composer's, in its order (`COMPOSER_SCALES`).
SCALES = {
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),
    "major_pent": (0, 2, 4, 7, 9),
    "minor_pent": (0, 3, 5, 7, 10),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),
    "lydian": (0, 2, 4, 6, 7, 9, 11),
    "whole": (0, 2, 4, 6, 8, 10),
    # added in 2.2
    "phrygian": (0, 1, 3, 5, 7, 8, 10),
    "locrian": (0, 1, 3, 5, 6, 8, 10),
    "harmonic_minor": (0, 2, 3, 5, 7, 8, 11),
    "melodic_minor": (0, 2, 3, 5, 7, 9, 11),
    "phrygian_dominant": (0, 1, 4, 5, 7, 8, 10),
    "blues": (0, 3, 5, 6, 7, 10),
}
COMPOSER_SCALES = ("major", "minor", "major_pent", "minor_pent", "dorian", "mixolydian", "lydian", "whole")

# The seven-note scale a smaller one takes its chords from (as the composer's PARENT does). Whole tone keeps its own:
# stacked in thirds it gives augmented triads.
PARENT = {"major_pent": "major", "minor_pent": "minor", "blues": "minor"}

# Spelling: letters C..B, their pitch classes, and which tonic name each pitch class gets (major-ish, minor-ish).
LETTERS = "CDEFGAB"
LETTER_PC = (0, 2, 4, 5, 7, 9, 11)
_TONIC_MAJOR = ("C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
_TONIC_MINOR = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B")


def spell(letter, pc):
    """The name of pitch class pc written on a letter: spell('B', 10) is Bb, spell('E', 6) is E## (rare)."""
    d = (pc - LETTER_PC[LETTERS.index(letter)] + 6) % 12 - 6
    return letter + ("#" * d if d > 0 else "b" * -d)


@dataclass(frozen=True)
class Key:
    tonic: int              # 0-11, C = 0
    scale: str = "major"

    def __post_init__(self):
        if self.scale not in SCALES:
            raise ValueError(f"unknown scale {self.scale!r}")

    @property
    def steps(self):
        return SCALES[self.scale]

    @property
    def minorish(self):
        """Has a minor third: names the key like a minor one (C# minor, not Db minor)."""
        return 3 in self.steps and 4 not in self.steps

    @property
    def chord_scale(self):
        """The seven-note scale (or whole tone) this key's chords are built from."""
        return PARENT.get(self.scale, self.scale)

    def degree(self, d):
        """Semitones of scale degree d (0 = tonic), over octaves."""
        n = len(self.steps)
        return self.steps[d % n] + 12 * (d // n)

    def degree_of(self, pc):
        """The degree a pitch class sits on, or None when it is outside the scale."""
        pc %= 12
        return self.steps.index(pc) if pc in self.steps else None

    def contains(self, pc):
        return pc % 12 in self.steps

    def tonic_name(self):
        return (_TONIC_MINOR if self.minorish else _TONIC_MAJOR)[self.tonic % 12]

    def name(self, pc, number=None):
        """The note pc (semitones from the tonic) spelled in this key. `number` (1-7) forces the letter: the 3rd
        degree up from the tonic's letter, as a chord's roman numeral says."""
        t = self.tonic_name()[0]
        if number is None:
            number = _WRITTEN.get(self.scale, {}).get(pc % 12) or _number_of(pc % 12, self.steps)
        letter = LETTERS[(LETTERS.index(t) + number - 1) % 7]
        return spell(letter, (self.tonic + pc) % 12)

    def __str__(self):
        return f"{self.tonic_name()} {self.scale.replace('_', ' ')}"


# For a chromatic pitch class, the scale number it is written as (b3 is a 3, #4 a 4): from the major scale.
_NUMBER = {0: 1, 1: 2, 2: 2, 3: 3, 4: 3, 5: 4, 6: 4, 7: 5, 8: 6, 9: 6, 10: 7, 11: 7}
# Scales that write a note on another number: the blues' blue note is a flat five (Eb in A), not a sharp four.
_WRITTEN = {"blues": {6: 5}}


def _number_of(pc, steps):
    if len(steps) == 7 and pc in steps:
        return steps.index(pc) + 1   # a seven-note scale: each letter once
    return _NUMBER[pc]


def check_note(key, pc):
    """None when the note is in the key's scale, else the reason. Notes outside are not banned (passing notes,
    blue notes, borrowed chords); a style decides how often it lets one through."""
    if key.contains(pc):
        return None
    return f"{key.name(pc)} is outside {key}"


def choose_scale(rng, options):
    """Pick a scale from {name: weight} (a style's tendencies), seeded. Weights are whole numbers."""
    names = [s for s, w in options.items() if w > 0]
    if not names:
        raise ValueError("no scale left to choose from")
    r = rng.rnd(sum(options[s] for s in names))
    for s in names:
        r -= options[s]
        if r < 0:
            return s
