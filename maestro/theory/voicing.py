# SPDX-License-Identifier: GPL-3.0-or-later
"""Voice leading: which notes of a chord each member plays, and how they move from chord to chord. Notes are MIDI
numbers (C4 = 60); chords are as in `chords.py`, in semitones from the key note.

The check rules out what doesn't fit (out of the member's range, a chord tone missing, above the melody, muddy low
intervals). Everything else is a tendency a style sets as a cost: smooth moves, parallels, leaps, spread. Parallel
fifths are not banned: power rock likes them, a plain style avoids them. The choose picks among the smoothest few,
seeded, so the voicing is never locked to one path (decision 9)."""
from dataclasses import dataclass
from itertools import combinations

from .chords import QUALITIES


@dataclass(frozen=True)
class Range:
    low: int
    high: int

    @property
    def mid(self):
        return (self.low + self.high) / 2


# Where each pitched member plays, in MIDI notes (drums and percussion are unpitched: their notes are GM drum
# notes). Wide on purpose: a member's register control narrows it, a style's sound may sit anywhere inside.
RANGES = {
    "bass": Range(24, 55),     # C1 (an 808's floor) to G3
    "guitar": Range(40, 76),   # E2 to E5: rhythm guitar, power chords low
    "keys": Range(43, 88),     # G2 to E6: comping, salsa's montuno in octaves
    "pad": Range(48, 84),      # C3 to C6
    "horns": Range(52, 84),    # E3 (trombone) to C6 (trumpet)
    "arp": Range(55, 91),      # G3 to G6
    "melody": Range(60, 96),   # C4 to C7: the top of the band
}


def member_range(role, register=None):
    """The member's range, narrowed by its register control ([low, high]) when it has one."""
    r = RANGES[role]
    if register is None:
        return r
    lo, hi = max(r.low, register[0]), min(r.high, register[1])
    if lo > hi:
        raise ValueError(f"register {register} is outside the {role}'s range {r.low}-{r.high}")
    return Range(lo, hi)


# The lowest note each interval (in semitones, under an octave) can start on before it turns to mud: the usual
# arranger's table of low interval limits. A fifth is clear down to Bb1, a third only from Bb2/C3.
LOW_LIMITS = {1: 52, 2: 51, 3: 48, 4: 46, 5: 45, 6: 47, 7: 34, 8: 43, 9: 41, 10: 41, 11: 41}


@dataclass(frozen=True)
class Leading:
    """A style's voice-leading tendencies. Costs are per occurrence; a negative cost means the style likes it."""
    fifths: int = 6          # two voices moving in parallel fifths
    octaves: int = 8         # ... in parallel octaves
    max_step: int = 4        # moves up to this (a major third) count as smooth
    leap: int = 2            # cost per semitone a move goes past max_step
    centre: int = 1          # pull back to the middle of the range (per 2 semitones away), so a long play can't drift
    spread: int | None = None   # preferred span bottom to top (semitones); None: no preference
    max_span: int = 24       # rule: never wider than this
    low_limits: bool = True  # rule: the low interval limits (taste.md: no mud)
    rootless: bool = False   # a coloured chord may leave its root to the bass
    slack: int = 3           # choose picks among voicings up to this much costlier than the smoothest (0: always it)


# First drafts for the four styles; the style book (bucket 3) refines them.
LEADING = {
    "plain": Leading(),
    "trap": Leading(fifths=2, octaves=4, spread=14),                  # dark, wide, sparse pads; little fuss
    "synthwave": Leading(fifths=0, octaves=0, spread=12),             # pads that glide as a block are fine
    "salsa": Leading(fifths=6, octaves=-4, max_step=3, rootless=True),  # montuno moves in octaves; smooth inside
    "power_rock": Leading(fifths=-4, octaves=-2, max_step=7, leap=1),  # power chords slide as one shape
}


def note_name(key, m):
    return f"{key.name((m - key.tonic) % 12)}{m // 12 - 1}"


def _tone_word(chord, i):
    if i == 0:
        return "root"
    if chord.quality == "sus2" and i == 2:
        return "second"
    if chord.colour == "dim7" and i == 9:
        return "seventh"
    return {2: "ninth", 3: "third", 4: "third", 5: "fourth", 6: "fifth", 7: "fifth", 8: "fifth", 9: "sixth",
            10: "seventh", 11: "seventh"}[i]


def _needed(chord, n, leading):
    """The chord tones (pitch classes from the key note) a voicing of n notes must hold. One note is a bass line:
    the chord's bass note. A style that plays rootless leaves a coloured chord's root to the bass; then the fifth
    goes when there isn't room (only a perfect one: a diminished or augmented fifth is the chord's sound)."""
    if n == 1:
        return [chord.low]
    tones = list(chord.tones)
    if leading.rootless and chord.colour:
        tones.remove(chord.root)
    fifth = QUALITIES[chord.quality][-1] if chord.quality != "power" else None
    if len(tones) > n and fifth == 7:
        tones.remove((chord.root + 7) % 12)
    return tones


def check_voicing(notes, chord, key, span, leading=LEADING["plain"], on_bass=False, ceiling=None):
    """None when the notes fit, else the reason in plain words. `on_bass`: the member plays the chord's bass note
    at the bottom. `ceiling`: the melody's note, which everything else stays under."""
    v = sorted(notes)
    for m in v:
        if not span.low <= m <= span.high:
            side = "below" if m < span.low else "above"
            return f"{note_name(key, m)} is {side} the range ({note_name(key, span.low)}-{note_name(key, span.high)})"
        if (m - key.tonic) % 12 not in chord.tones:
            return f"{note_name(key, m)} is not in the chord"
    have = {(m - key.tonic) % 12 for m in v}
    for t in _needed(chord, len(v), leading):
        if t not in have:
            i = (t - chord.root) % 12
            if len(set(_needed(chord, len(v), leading))) > len(v):
                return f"{len(v)} notes can't hold every needed tone of the chord"
            return f"no {key.name(t)}: the chord's {_tone_word(chord, i)} is missing"
    if on_bass and (v[0] - key.tonic) % 12 != chord.low:
        return f"the bottom note should be {key.name(chord.low)}, not {note_name(key, v[0])}"
    if ceiling is not None and v[-1] >= ceiling:
        return f"{note_name(key, v[-1])} is not under the melody ({note_name(key, ceiling)})"
    if v[-1] - v[0] > leading.max_span:
        return f"spread over {v[-1] - v[0]} semitones, wider than {leading.max_span}"
    if leading.low_limits:
        why = _mud(v, key)
        if why:
            return why
    return None


def _mud(v, key):
    for a, b in zip(v, v[1:]):
        i = b - a
        if 0 < i < 12 and a < LOW_LIMITS[i]:
            return (f"{note_name(key, a)} and {note_name(key, b)} are too close that low "
                    f"(that interval needs {note_name(key, LOW_LIMITS[i])} or higher): muddy")
    return None


def voicings(chord, key, n, span, leading=LEADING["plain"], on_bass=False, ceiling=None):
    """Every voicing of n notes (distinct MIDI notes, so doublings are octaves) that passes the check."""
    pcs = {(key.tonic + t) % 12 for t in chord.tones}
    notes = [m for m in range(span.low, span.high + 1) if m % 12 in pcs]
    return [v for v in combinations(notes, n)
            if check_voicing(v, chord, key, span, leading, on_bass, ceiling) is None]


def parallels(prev, nxt):
    """Pairs of voices moving in parallel fifths or octaves: [(kind, i, j)], voices counted from the bottom. Both
    voicings sorted, same size."""
    out = []
    if len(prev) != len(nxt) or tuple(prev) == tuple(nxt):
        return out
    for i, j in combinations(range(len(prev)), 2):
        a, b = prev[j] - prev[i], nxt[j] - nxt[i]
        di, dj = nxt[i] - prev[i], nxt[j] - prev[j]
        if a % 12 == b % 12 and a % 12 in (0, 7) and di and dj and (di > 0) == (dj > 0):
            out.append(("fifths" if a % 12 == 7 else "octaves", i, j))
    return out


def _moves(prev, nxt):
    """How far each new note moved: voice by voice when the sizes match, else from the nearest old note."""
    if len(prev) == len(nxt):
        return [b - a for a, b in zip(prev, nxt)]
    return [min((m - p for p in prev), key=abs) for m in nxt]


def cost(prev, nxt, span, leading=LEADING["plain"], chord=None, key=None):
    """How rough a move is, in this style (lower is smoother). With no previous voicing, only the voicing's own
    place counts (middle of the range, preferred spread, root position)."""
    v = sorted(nxt)
    c = leading.centre * int(abs(sum(v) / len(v) - span.mid) // 2)
    if leading.spread is not None:
        c += abs((v[-1] - v[0]) - leading.spread) // 2
    for a, b in zip(v[1:], v[2:]):   # wide holes between the upper voices
        c += 2 * max(0, b - a - 12)
    if prev is None:
        if chord is not None and key is not None and (v[0] - key.tonic) % 12 != chord.root:
            c += 2
        return c
    p = sorted(prev)
    for d in _moves(p, v):
        c += abs(d) + leading.leap * max(0, abs(d) - leading.max_step)
    for k, _, _ in parallels(p, v):
        c += leading.fifths if k == "fifths" else leading.octaves
    return c


def choose_voicing(rng, chord, key, n, span, prev=None, leading=LEADING["plain"], on_bass=False, ceiling=None):
    """Voice the chord: among the voicings that fit, the smoothest ones in this style, picked seeded (whole-number
    weights, the smoothest weighing most). `span` is the member's Range."""
    vs = voicings(chord, key, n, span, leading, on_bass, ceiling)
    if not vs:
        raise ValueError(f"no {n}-note voicing of the chord fits")
    cs = [cost(prev, v, span, leading, chord, key) for v in vs]
    best = min(cs)
    pick = [(v, best + leading.slack + 1 - c) for v, c in zip(vs, cs) if c <= best + leading.slack]
    r = rng.rnd(sum(w for _, w in pick))
    for v, w in pick:
        r -= w
        if r < 0:
            return v


def _move_word(d):
    a = abs(d)
    if a == 0:
        return "held"
    way = "up" if d > 0 else "down"
    if a <= 2:
        return f"a step {way}"
    if a <= 4:
        return f"a third {way}"
    return f"{a} semitones {way}"


def explain(prev, nxt, key):
    """The move in plain words: what each voice did, and any parallels."""
    p, v = sorted(prev), sorted(nxt)
    if len(p) == len(v):
        parts = [f"{note_name(key, a)} {_move_word(b - a)}" + (f" to {note_name(key, b)}" if a != b else "")
                 for a, b in zip(p, v)]
    else:
        parts = [f"{note_name(key, b)} ({_move_word(d)})" for b, d in zip(v, _moves(p, v))]
    text = ", ".join(parts)
    for k, i, j in parallels(p, v):
        text += (f"; parallel {k}: {note_name(key, p[i])}-{note_name(key, p[j])} to "
                 f"{note_name(key, v[i])}-{note_name(key, v[j])}")
    return text


UNPITCHED = ("drums", "percussion")


def check_band(sounding, key):
    """What's wrong with the band's notes at one moment ({role: [notes]}), as a list of reasons (empty: fine): the
    melody stays on top (taste.md), and the low end isn't mud across members."""
    out = []
    mel = sounding.get("melody") or []
    if mel:
        top = min(mel)
        for role, notes in sounding.items():
            if role == "melody" or role in UNPITCHED:
                continue
            over = [m for m in notes if m >= top]
            if over:
                out.append(f"the {role}'s {note_name(key, max(over))} is not under the melody ({note_name(key, top)})")
    every = sorted({m for role, notes in sounding.items() if role not in UNPITCHED for m in notes})
    why = _mud(every, key)
    if why:
        out.append(why)
    return out
