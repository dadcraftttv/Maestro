# SPDX-License-Identifier: GPL-3.0-or-later
"""The guitar member (task 3.4d, decision 11): power rock's rhythm guitar, and what makes its lead a guitar's.

**The rhythm guitar** plays power chords: the root and its fifth, the root an octave up on top, sliding as one shape
from chord to chord. It is doubled, the way rock records stack two takes left and right: each track ("tracks") sits
to one side and voices the shape in its own octave, so the two make one wide sound. A pattern names its hits:
[16th, its length in 16ths (null: rings to the next hit), the shape ("power": root, fifth and octave; "dyad": root
and fifth; "root"), "now" (the chord sounding) or "ahead" (the chord at the next half bar: a push)], over one or two
bars. A pattern belongs to a group ("mute": palm-muted chugs, short and softer; "drive": open 8ths; "open": big
ringing chords), and the song's part says which group plays (`arrange.py`: verse, pre-chorus, chorus); a phrase
draws one pattern of its group and mostly keeps it. A pattern may lock the bass to it ("bass": the bass plays its
rhythm on the roots, as rock bassists double a riff).

The check: every note a root or fifth of its chord (now, or the chord it pushes), each track inside its own octave
of the guitar's range, every hit on the grid.

**The lead** (the melody member) keeps to the pentatonic: off the chord's own tones, its notes leave the scale's two
extra degrees for the nearest of the five; some held notes bend up into their note from a step under, and long
ones get vibrato. Sources: Wikipedia's "Power chord", "Palm mute", "Pentatonic scale" and "String bending"
(CC BY-SA 4.0), the ideas in our own words."""
from dataclasses import dataclass

from ..stylebook import StyleError, part, per_style
from .flow import chord_at
from .form import _draw
from .voicing import member_range

SIXTEENTH = 6        # grid steps in a 16th
MUTE = 10            # steps a palm-muted hit rings (most of an 8th)
SHAPES = {"power": (0, 7, 12), "dyad": (0, 7), "root": (0,)}
VOICINGS = {"low": 40, "high": 52}   # the lowest root a track's voicing takes: E2, or E3 (an octave up)
SPAN = 12            # semitones over that lowest root a track's root may climb, so the shape slides


@dataclass(frozen=True)
class Riff:
    name: str
    hits: tuple          # ((16th, 16ths or None, shape, "now" or "ahead"), ...)
    bars: int = 1
    group: str = "drive"
    weight: int = 1
    bass: bool = False   # the bass locks to its rhythm
    why: str = ""

    @property
    def mute(self):
        return self.group == "mute"


@dataclass(frozen=True)
class Track:
    name: str
    pan: int = 0
    voicing: str = "low"
    sound: int = 30


@dataclass(frozen=True)
class GuitarFlow:
    patterns: tuple
    tracks: tuple
    stay: int = 4        # times likelier a phrase keeps the pattern before (of its group)


def _guitar_flow(style):
    d, where = part(style, "members", "guitar"), f"{style}: members.guitar"
    if not d:
        return None
    pats = []
    for n, p in d.get("patterns", {}).items():
        if n == "why":
            continue
        extra = set(p) - {"hits", "bars", "group", "weight", "bass", "why"}
        if extra:
            raise StyleError(f"{where}.patterns.{n}: unknown part {sorted(extra)[0]!r} (known: hits, bars, group, "
                             "weight, bass, why)")
        hits, bars = tuple(tuple(h) for h in p.get("hits", [])), p.get("bars", 1)
        ats = [h[0] for h in hits]
        if bars not in (1, 2) or not hits or ats != sorted(set(ats)) or ats[0] < 0 or ats[-1] >= 16 * bars or any(
                len(h) != 4 or h[1] is not None and not (isinstance(h[1], int) and h[1] >= 1) or h[2] not in SHAPES
                or h[3] not in ("now", "ahead") for h in hits):
            raise StyleError(f"{where}.patterns.{n}: 1 or 2 bars; hits in order, one a 16th inside them, each [16th, "
                             f"16ths or null, a shape ({', '.join(SHAPES)}), \"now\" or \"ahead\"]")
        w = p.get("weight", 1)
        if not isinstance(w, int) or w < 1 or not isinstance(p.get("group", "drive"), str) or not isinstance(
                p.get("bass", False), bool):
            raise StyleError(f"{where}.patterns.{n}: a whole-number weight from 1, a group's name, bass true or false")
        pats.append(Riff(n, hits, bars, p.get("group", "drive"), w, p.get("bass", False), p.get("why", "")))
    tracks = []
    for n, t in d.get("tracks", {}).items():
        if n == "why":
            continue
        extra = set(t) - {"pan", "voicing", "sound"}
        if extra or t.get("voicing", "low") not in VOICINGS or not -64 <= t.get("pan", 0) <= 63 or not \
                0 <= t.get("sound", 30) <= 127:
            raise StyleError(f"{where}.tracks.{n}: pan -64 to 63, voicing {' or '.join(VOICINGS)}, a GM sound")
        tracks.append(Track(n, t.get("pan", 0), t.get("voicing", "low"), t.get("sound", d.get("sound", 30))))
    if not pats or not tracks:
        raise StyleError(f"{where}: at least one pattern and one track")
    return GuitarFlow(tuple(pats), tuple(tracks), d.get("stay", 4))


GUITAR = per_style(_guitar_flow)   # None: no rhythm guitar


def _probe(step, which, met):
    return step if which == "now" else (step // (met.bar // 2) + 1) * (met.bar // 2)


def _root(pc, near, low):
    """The root of pitch class `pc` in the track's span, nearest the one before."""
    cands = [m for m in range(low, low + SPAN + 1) if m % 12 == pc % 12]
    return min(cands, key=lambda m: (abs(m - near), m)) if near is not None else cands[0]


def power(chord, root):
    """The power chord's notes over `root` (MIDI): its root, the chord's own fifth (a perfect one unless the chord
    has another), the octave."""
    fifth = next((i for i in chord.intervals if i in (6, 7, 8)), 7)
    return {0: root, 7: root + fifth, 12: root + 12}


def guitar_part(rng, gf, group, spans, key_at, start, bars, met, prev=None, near=None):
    """One phrase's rhythm guitar: ({track: [(step, length, MIDI note)]}, the steps of its muted hits, the pattern,
    the last roots {track: MIDI}, lines). `group`: the part's (mute, drive or open); `prev`: the pattern before,
    likelier kept; `near`: each track's last root, so the shape slides on from it."""
    fits = [p for p in gf.patterns if p.group == group and bars % p.bars == 0] or \
        [p for p in gf.patterns if bars % p.bars == 0]
    pat = fits[_draw(rng, {i: p.weight * (gf.stay if p == prev else 1) for i, p in enumerate(fits)})]
    lines = [f"  guitar, bars {start + 1}-{start + bars}: {pat.name}" + (f": {pat.why}" if pat.why else "")
             + (" (kept)" if pat == prev else "")]
    end = (start + bars) * met.bar
    hits = []
    for p in range(bars // pat.bars):
        base = (start + p * pat.bars) * met.bar
        hits += [(base + at * SIXTEENTH, length, shape, which) for at, length, shape, which in pat.hits]
    out, muted, near = {t.name: [] for t in gf.tracks}, [], dict(near or {})
    for i, (st, length, shape, which) in enumerate(hits):
        nxt = hits[i + 1][0] if i + 1 < len(hits) else end
        steps = nxt - st if length is None else min(length * SIXTEENTH, nxt - st)
        if pat.mute:
            steps = min(steps, MUTE)
            muted.append(st)
        probe = min(_probe(st, which, met), end - 1)
        key, ch = key_at(probe), chord_at(spans, probe).chord
        for t in gf.tracks:
            root = _root(key.tonic + ch.root, near.get(t.name), VOICINGS[t.voicing])
            near[t.name] = root
            notes = power(ch, root)
            out[t.name] += [(st, steps, notes[iv]) for iv in SHAPES[shape]]
    return out, muted, pat, near, lines


def lock_bass(notes, spans, key_at, met, near, r=None):
    """The bass on the guitar's rhythm (one track's notes): the root of each hit's chord, the nearest to the note
    before, held to the next hit, inside `r` (the bass's range). (notes, the last bass note)."""
    r, out = r or member_range("bass"), []
    near = round(r.mid) - 4 if near is None else near
    for st in sorted({n[0] for n in notes}):
        length = max(n[1] for n in notes if n[0] == st)
        lowest = min(n[2] for n in notes if n[0] == st)
        cands = [m for m in range(r.low, r.high + 1) if m % 12 == lowest % 12]
        near = min(cands, key=lambda m: (abs(m - near), m))
        out.append((st, length, near))
    return out, near


def check_guitar(tracks, gf, spans, key_at, met):
    """None when the rhythm guitar fits, else the reason: every note a root or fifth of the chord sounding or the
    one it pushes (within the half bar), each track inside its octave of the guitar's range, every hit on the
    grid."""
    r = member_range("guitar")
    for t in gf.tracks:
        low = VOICINGS[t.voicing]
        for st, length, m in tracks.get(t.name, []):
            if st != int(st) or length < 1:
                return f"{t.name}: a note at step {st} off the grid"
            if not (r.low <= m <= r.high and low <= m <= low + SPAN + 12):
                return f"{t.name}: {m} outside its voicing ({low} to {min(r.high, low + SPAN + 12)})"
            ok = set()
            for which in ("now", "ahead"):
                probe = _probe(st, which, met)
                key, ch = key_at(probe), chord_at(spans, probe).chord
                fifth = next((i for i in ch.intervals if i in (6, 7, 8)), 7)
                ok |= {(key.tonic + ch.root) % 12, (key.tonic + ch.root + fifth) % 12}
            if m % 12 not in ok:
                return f"{t.name}: {m} at step {st} is neither a root nor a fifth of its chord"
    return None


# ---- the lead ----

def scale_of(key):
    """The pentatonic's pitch classes from the key note: minor's (1 b3 4 5 b7) in a minor key, else major's."""
    return {0, 3, 5, 7, 10} if key.minorish else {0, 2, 4, 7, 9}


def pentatonic(notes, spans, key):
    """The lead on the pentatonic: a note that isn't one of its chord's tones moves off the scale's two extra
    degrees to the nearest of the five (down when both are as near); the range is the phrase's to keep (the pad
    gives way, or the check rules it out). (notes, how many moved)."""
    five, out, moved = scale_of(key), [], 0
    for st, length, m in notes:
        pc = (m - key.tonic) % 12
        tones = {t % 12 for t in chord_at(spans, st).chord.tones}
        if pc not in five and pc not in tones:
            for d in (-1, 1, -2, 2):
                if (pc + d) % 12 in five:
                    m, moved = m + d, moved + 1
                    break
        out.append((st, length, m))
    return out, moved


HELD = 24            # steps: a lead note this long or longer may bend
BEND = 12            # steps a bend takes, an 8th
SHAKE = 48           # steps: a note this long gets vibrato, after its first 8th


def bends(rng, notes, key_at, pct):
    """Which held notes bend up into their note: [(step, steps, semitones)], about `pct`% of the held ones; a
    whole step when the note a whole step under is in the key, else a half step."""
    out, low = [], member_range("melody").low
    for st, length, m in notes:
        if length >= HELD and rng.rnd(100) < pct:
            key = key_at(st)
            semis = 2 if (m - 2 - key.tonic) % 12 in {key.degree(d) % 12 for d in range(7)} else 1
            if m - semis >= low:
                out.append((st, min(BEND, length // 2), semis))
    return out


def vibrato(notes):
    """[(step, steps)]: each long note shaking after its first 8th."""
    return [(st + BEND, length - BEND) for st, length, _ in notes if length >= SHAKE]


# ---- two leads (power rock's second round, DadCraft, Oct 26: "dueling guitars, akin to Bill and Ted") ----
#
# A second lead guitar on the other side. In a chorus the two play the hook in twin harmony, the second a third under
# the first in the key (over it where it would sink under the lead's floor). In a duel (the solo pulled forward from
# task 3.6) they trade shred licks, the turns getting shorter and hotter: two bars each, then one, then half a bar,
# and both land home together in harmony. A lick is a fast run on the pentatonic (16ths, or 16th triplets), a pedal
# lick (a high chord tone struck between the notes of a line falling under it) or a sweep (the chord's tones up and
# down in 16th triplets), each ending on a held chord tone. Sources: Wikipedia's "Twin lead guitar", "Shred guitar"
# and "Guitar solo" (CC BY-SA 4.0), the ideas in our own words.

LICKS = ("run", "pedal", "sweep")
FAST = {"16th": 6, "16th_triplet": 4}
TURNS = ((0, 2, 0), (2, 2, 1), (4, 1, 0), (5, 1, 1), (6, 0.5, 0), (6.5, 0.5, 1))   # (bar, bars, which lead) of 8
LICK_LOW, LICK_HIGH = 64, 93   # E4 to A6: where the licks run, under the melody's top


def _in_key(key):
    return {key.degree(d) % 12 for d in range(7)}


def third_under(m, key, floor):
    """The note a third under `m` in the key (a third over when that sinks to `floor` or under)."""
    scale = _in_key(key)
    under = next((m - k for k in (3, 4) if (m - k - key.tonic) % 12 in scale), m - 3)
    if under > floor:
        return under
    return next((m + k for k in (3, 4) if (m + k - key.tonic) % 12 in scale), m + 3)


def twin(notes, key_at, floor):
    """The second lead in twin harmony with the first: each note a third under it in the key."""
    return [(st, length, third_under(m, key_at(st), floor)) for st, length, m in notes]


def _tones_near(spans, key, st, near):
    """The chord tone sounding at `st` nearest `near`, in the licks' span."""
    pcs = {(key.tonic + t) % 12 for t in chord_at(spans, st).chord.tones}
    cands = [m for m in range(LICK_LOW, LICK_HIGH + 1) if m % 12 in pcs]
    return min(cands, key=lambda m: (abs(m - near), m))


def lick(rng, kind, rate, spans, key, st, steps, near):
    """One lick from `st` for `steps`: fast notes, then a held chord tone on the last beat (on the last span when a
    turn is half a bar). (notes, the last note)."""
    hold = 24 if steps >= 48 else steps // 2
    end, out = st + steps - hold, []
    pool = [m for m in range(LICK_LOW, LICK_HIGH + 1) if (m - key.tonic) % 12 in scale_of(key)]
    i = min(range(len(pool)), key=lambda k: abs(pool[k] - near))
    if kind == "run":                         # up or down the pentatonic, turning at the edges
        step = 1 if rng.rnd(2) else -1
        for t in range(st, end, rate):
            out.append((t, rate, pool[i]))
            if not 0 <= i + step < len(pool):
                step = -step
            i += step
    elif kind == "pedal":                     # a high chord tone struck between a line falling under it
        top = _tones_near(spans, key, st, near + 5)
        line = [m for m in pool if m < top][::-1] or [top - 12]
        k = 0
        for n, t in enumerate(range(st, end, rate)):
            out.append((t, rate, top if n % 2 == 0 else line[min(k, len(line) - 1)]))
            k += n % 2
    else:                                     # a sweep: the chord's tones up and down, a beat at a time
        rate = FAST["16th_triplet"]
        for b in range(st, end, 24):
            ch = chord_at(spans, b).chord
            tones = sorted(m for m in range(LICK_LOW, LICK_HIGH + 1)
                           if (m - key.tonic) % 12 in {t % 12 for t in ch.tones} and abs(m - near) <= 12)[:4]
            shape = tones + tones[-2:0:-1] or [near]
            for n, t in enumerate(range(b, min(b + 24, end), rate)):
                out.append((t, rate, shape[n % len(shape)]))
    last = _tones_near(spans, key, end, out[-1][2] if out else near)
    out.append((end, hold, last))
    return out, last


def duel(rng, weights, fast, spans, key_at, start, bars, met, near):
    """A duel over a phrase: (the first lead's notes, the second's, lines). The turns follow TURNS (scaled to the
    phrase), then both land home together in harmony on the phrase's last chord."""
    one, two, lines = [], [], []
    scale = bars / 8
    for at, length, who in TURNS:
        st = (start * met.bar) + round(at * scale * met.bar)
        steps = round(length * scale * met.bar)
        kind = LICKS[_draw(rng, {i: weights.get(k, 0) for i, k in enumerate(LICKS)}) or 0]
        rate = FAST["16th_triplet"] if rng.rnd(100) < fast else FAST["16th"]
        notes, near = lick(rng, kind, rate, spans, key_at(st), st, steps, near)
        (two if who else one).extend(notes)
        lines.append(f"    bar {st // met.bar + 1}{' (half)' if length < 1 else ''}: the {'second' if who else 'first'} "
                     f"lead, a {kind}" + (" in 16th triplets" if rate == 4 and kind != "sweep" else ""))
    b0 = (start + bars - 1) * met.bar
    last = [s for s in spans if b0 <= s.at < b0 + met.bar] or [chord_at(spans, b0)]
    land = max(last[-1].at, b0 + met.bar // 2)
    key = key_at(land)
    run, near = lick(rng, "run", FAST["16th"], spans, key, b0, land - b0 + 24, near)
    one += run[:-1]
    home = min((m for m in range(LICK_LOW, LICK_HIGH + 1) if (m - key.tonic) % 12 == 0), key=lambda m: abs(m - near))
    one.append((land, b0 + met.bar - land, home))
    pcs = {(key.tonic + t) % 12 for t in chord_at(spans, land).chord.tones}
    two.append((land, b0 + met.bar - land, next((home - k for k in (8, 9) if (home - k) % 12 in pcs),
                                                 third_under(home, key, LICK_LOW - 1))))   # a sixth under: its third
    lines.append(f"    bar {start + bars}: a run, then both land home in harmony")
    return one, two, [f"  duel, bars {start + 1}-{start + bars}: the two leads trade licks, the turns getting "
                      "shorter"] + lines


def check_leads(one, two, key_at, spans, licks=()):
    """None when the two leads fit, else the reason: inside the melody's range, the two never sounding at once
    unless in twin harmony (a third apart in the key, or a sixth where the second sits over), and a held note in
    a duel's licks (`licks`: its [(first step, last step)]) on a tone of its chord."""
    r = member_range("melody")
    for st, length, m in one + two:
        if not r.low <= m <= r.high:
            return f"{m} at step {st} outside the leads' range"
    at = {st: m for st, _, m in one}
    for st, length, m in two:
        if st in at:
            if (at[st] - m) % 12 not in (3, 4, 8, 9):
                return f"step {st}: the leads {at[st]} and {m}, not a third apart"
        elif any(s <= st < s + n for s, n, _ in one):
            return f"step {st}: the second lead over the first's held note"
    for st, length, m in one + two:
        if length >= 12 and any(lo <= st < hi for lo, hi in licks):
            pcs = {(key_at(st).tonic + t) % 12 for t in chord_at(spans, st).chord.tones}
            if m % 12 not in pcs:
                return f"a held {m} at step {st} off its chord"
    return None
