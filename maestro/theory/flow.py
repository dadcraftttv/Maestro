# SPDX-License-Identifier: GPL-3.0-or-later
"""Flow (task 3.2, Checkpoint 2's "no flow"): music that goes somewhere over a phrase, instead of one draw a bar.

- **Progressions** come in families: a loop of chords over 1, 2, 4 or 8 bars, in roman numerals with the bar lines
  ("i iv | V7 iv": two chords a bar, so the harmonic rhythm belongs to the family). A section keeps one family and
  plays it pass after pass. After the first pass, a pass may come back as a variant (a chord swapped for one doing
  the same job, a colour, a dominant leading into a chord, a ii-V turnaround), and a phrase's last pass ends on a
  cadence.
- **The bass** plays its style's pattern family (a tumbao, root eighths). Each note says where it falls (in 16ths),
  which chord tone it plays and whether it plays the chord sounding or the one coming ("ahead": salsa's anticipated
  bass). A pass may drop a note, add an approach note or jump an octave.
- **The melody** is shaped over the phrase: the motif's statements rise to a peak two-thirds in, the first half ends
  open (a chord tone that isn't home) and the second half lands home on the cadence. Notes on the beat lean to the
  chord's tones.

Like the other theory modules, each part has a check (what doesn't fit, and why) and a choose (seeded, among what
fits). Families and patterns are tendencies with weights, never fixed (decision 9); a style's file names its own
(harmony.progressions, members.bass) and the defaults here stand in for the rest. Sources (`docs/data.md`): Open
Music Theory (loops and schemas), jazznet (the ii-V), Wikipedia's tumbao, all in our own words."""
import re
from bisect import bisect_right
from collections import namedtuple
from dataclasses import dataclass, field

from ..stylebook import STYLES, StyleError, part
from .chords import Chord, _resolves_to, function, name, outside, parse_roman, pool, two_five
from .form import WORDS, _draw
from .rhythm import VALUES, check_clave
from .voicing import member_range

SIXTEENTH = 6        # grid steps in a 16th
Span = namedtuple("Span", "at length chord")   # a chord sounding from step `at` for `length` steps


# ---- progressions ----

_TONIC = re.compile(r"^[iI](?![iIvV])")


@dataclass(frozen=True)
class Family:
    """A progression family: its loop in roman numerals, bars split by "|", a bar's chords sharing it evenly."""
    name: str
    chords: str
    weight: int = 1
    why: str = ""

    def __post_init__(self):
        bars = self.bars
        if len(bars) not in (1, 2, 4, 8):
            raise ValueError(f"{self.name}: a loop is 1, 2, 4 or 8 bars, not {len(bars)}")
        for b in bars:
            if not 1 <= len(b) <= 4:
                raise ValueError(f"{self.name}: 1 to 4 chords a bar, not {len(b)}")
            for c in b:
                parse_roman(c)   # raises on a numeral it can't read
        if self.weight < 1:
            raise ValueError(f"{self.name}: weight must be at least 1")

    @property
    def bars(self):
        return [b.split() for b in self.chords.split("|")]

    @property
    def loop(self):
        return len(self.bars)

    @property
    def mode(self):
        """'minor' or 'major' from its tonic chord (the first i or I), None when it has none."""
        for b in self.bars:
            for c in b:
                if "/" not in c and _TONIC.match(c):
                    return "minor" if c[0] == "i" else "major"
        return None

    def spans(self, key, at, met):
        out = []
        for i, b in enumerate(self.bars):
            n = met.bar // len(b)
            out += [Span(at + i * met.bar + j * n, n, parse_roman(c, key)) for j, c in enumerate(b)]
        return out


# Common loops and schemas (Open Music Theory, "popular music" part; jazznet's ii-V), for styles that name none.
FAMILIES = (
    Family("doo-wop", "I | vi | IV | V", 2, "home, its softer twin, away, the pull back"),
    Family("axis", "I | V | vi | IV", 2, "the four-chord loop of a thousand pop songs"),
    Family("ii-V-I", "ii | V | I | I", 1, "the jazz cadence, settled for two bars"),
    Family("aeolian loop", "i | bVI | bIII | bVII", 2, "natural minor's own loop: no leading tone, it just circles"),
    Family("andalusian", "i | bVII | bVI | V", 1, "four steps down to the dominant"),
    Family("minor plagal", "i | iv | i | iv", 1, "home and its subdominant, rocking"),
)
VARIANT_WEIGHTS = {"again": 4, "swap": 2, "colour": 1, "approach": 2, "turnaround": 1}


@dataclass(frozen=True)
class Flow:
    """A style's progression tendencies: its families, how often a pass varies and how, and how much more often a
    section keeps the family of the section before (`stay`)."""
    families: tuple = FAMILIES
    variants: dict = field(default_factory=lambda: dict(VARIANT_WEIGHTS))
    stay: int = 3
    cadence: int = 100   # % of phrases whose last pass is made to land home (trap: few, its loops just go round)
    still: bool = False  # a loop of one chord allowed (trap)


def _families(d, where):
    out = []
    for n, f in d.items():
        if n == "why":
            continue
        if not isinstance(f, dict) or not isinstance(f.get("chords"), str):
            raise StyleError(f"{where}.{n}: a family needs its \"chords\", like \"i iv | V7 iv\"")
        extra = set(f) - {"chords", "weight", "why"}
        if extra:
            raise StyleError(f"{where}.{n}: unknown part {sorted(extra)[0]!r} (known: chords, weight, why)")
        try:
            out.append(Family(n, f["chords"], f.get("weight", 1), f.get("why", "")))
        except (ValueError, TypeError, IndexError) as e:
            raise StyleError(f"{where}.{n}: {e}") from None
    return tuple(out)


def _weights(d, known, where):
    w = {k: v for k, v in d.items() if k != "why"}
    for k, v in w.items():
        if k not in known:
            raise StyleError(f"{where}.{k}: unknown variant (known: {', '.join(known)})")
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            raise StyleError(f"{where}.{k}: a weight is a whole number, 0 or more")
    return w


def _flow(style):
    d, where = part(style, "harmony", "progressions"), f"{style}: harmony.progressions"
    known = ("families", "variants", "stay", "cadence", "still")
    extra = set(d) - {"why", *known}
    if extra:
        raise StyleError(f"{where}: unknown part {sorted(extra)[0]!r} (known: {', '.join(known)})")
    cad, still = d.get("cadence", 100), d.get("still", False)
    if not isinstance(cad, int) or isinstance(cad, bool) or not 0 <= cad <= 100:
        raise StyleError(f"{where}.cadence: a share in %, 0 to 100")
    if not isinstance(still, bool):
        raise StyleError(f"{where}.still: true or false")
    fams = _families(d["families"], f"{where}.families") if "families" in d else FAMILIES
    variants = {**VARIANT_WEIGHTS, **_weights(d.get("variants", {}), VARIANT_WEIGHTS, f"{where}.variants")}
    return Flow(fams, variants, d.get("stay", 3), cad, still)


FLOW = {s: _flow(s) for s in STYLES}


def check_family(fam, key, vocab, still=False):
    """None when the family fits this key and style, else the reason. `still`: a loop of one chord is allowed."""
    if fam.mode and (fam.mode == "minor") != key.minorish:
        return f"a {fam.mode} loop; the key is {'minor' if key.minorish else 'major'}"
    chords = [parse_roman(c, key) for b in fam.bars for c in b]
    for ch in chords:
        why = outside(ch, key, vocab)
        if why:
            return why
    if len({c.root for c in chords}) < 2 and not still:
        return "one chord: it doesn't move"
    return None


def chart(spans, key, met):
    """The chords by bar: "Am Dm | E7 Dm"."""
    bars = {}
    for s in spans:
        bars.setdefault(s.at // met.bar, []).append(name(s.chord, key))
    return " | ".join(" ".join(b) for _, b in sorted(bars.items()))


def _fits(ch, key, vocab):
    return outside(ch, key, vocab) is None


def _swap(rng, sp, key, vocab, met):
    i = 1 + rng.rnd(len(sp) - 1)
    old = sp[i].chord
    job = function(old, key)[0]
    near = {sp[i - 1].chord.root, sp[(i + 1) % len(sp)].chord.root, old.root}
    cands = [c for c in pool(key, vocab) if c.root not in near and c.colour == old.colour and c.bass is None
             and c.quality in ("maj", "min", "dim") and function(c, key)[0] == job
             and (job != "tension" or _resolves_to(c) == _resolves_to(old))]   # tension still leads the same way
    if not cands:
        return None
    new = cands[rng.rnd(len(cands))]
    return (sp[:i] + [sp[i]._replace(chord=new)] + sp[i + 1:],
            f"{name(old, key)} swapped for {name(new, key)} (the same job: {job})")


def _colour(rng, sp, key, vocab, met):
    i = rng.rnd(len(sp))
    old = sp[i].chord
    cands = []
    for col in sorted(vocab.colours, key=str):
        if col == old.colour:
            continue
        try:
            c = Chord(old.root, old.quality, col, old.bass)
        except ValueError:
            continue
        if _fits(c, key, vocab):
            cands.append(c)
    if not cands:
        return None
    new = cands[rng.rnd(len(cands))]
    return sp[:i] + [sp[i]._replace(chord=new)] + sp[i + 1:], f"{name(old, key)} coloured as {name(new, key)}"


def _dominant(target, key, vocab):
    for col in ("7", None):
        d = Chord(target + 7, "maj", col)
        if _fits(d, key, vocab):
            return d
    return None


def _approach(rng, sp, key, vocab, met):
    """A dominant of the next chord takes the second half of the chord before it (the loop's last chord leads into
    the next pass's first)."""
    slots = [j for j in range(1, len(sp) + 1) if sp[j % len(sp)].chord.quality in ("maj", "min")
             and sp[j - 1].length >= 2 * met.unit and sp[j - 1].length % 2 == 0]
    while slots:
        j = slots.pop(rng.rnd(len(slots)))
        target = sp[j % len(sp)].chord
        dom = _dominant(target.root, key, vocab)
        if dom is None or sp[j - 1].chord.root == dom.root:
            continue
        before, half = sp[j - 1], sp[j - 1].length // 2
        split = [before._replace(length=half), Span(before.at + half, half, dom)]
        return sp[:j - 1] + split + sp[j:], f"{name(dom, key)} leads into {name(target, key)}"
    return None


def _turnaround(rng, sp, key, vocab, met):
    last, first = sp[-1], sp[0].chord
    if last.length < 2 * met.unit or last.length % 2:
        return None
    for sevenths in (True, False):
        two, five = two_five(first.root, first.quality == "min", sevenths)
        if _fits(two, key, vocab) and _fits(five, key, vocab):
            break
    else:
        return None
    if last.chord.root in (two.root, five.root):
        return None
    half = last.length // 2
    return (sp[:-1] + [Span(last.at, half, two), Span(last.at + half, half, five)],
            f"a ii-V turnaround ({name(two, key)} {name(five, key)}) back to {name(first, key)}")


VARIANTS = {"swap": _swap, "colour": _colour, "approach": _approach, "turnaround": _turnaround}


def vary(rng, sp, key, vocab, met, weights):
    """(the pass, in words how it varies, or None when it plays as written): a variant drawn by weight, among
    those that fit."""
    weights = dict(weights)
    while True:
        v = _draw(rng, weights)
        if v is None or v == "again":
            return sp, None
        got = VARIANTS[v](rng, sp, key, vocab, met)
        if got is not None:
            return got
        weights[v] = 0


def _home(c):
    return c.root == 0 and c.quality in ("maj", "min")


def _pulls_home(c):
    return _resolves_to(c) == 0


# What can take a cadence home, strongest first: V7, V, bVII, iv, IV; the first the style plays wins.
PULLS = (Chord(7, "maj", "7"), Chord(7, "maj"), Chord(10, "maj"), Chord(5, "min"), Chord(5, "maj"))


def cadence(sp, key, vocab, met):
    """The pass that ends a phrase, landing home: (spans, the cadence in words, or None when it lands already)."""
    last, prev = sp[-1], sp[-2]
    if _home(last.chord) and (_pulls_home(prev.chord) or prev.chord.root in (5, 10)):
        return sp, None
    own = next((s.chord for s in sp if _home(s.chord)), None)
    tonic = own if own is not None and _fits(own, key, vocab) else Chord(0, "min" if key.minorish else "maj")
    if _pulls_home(prev.chord):
        out, pull = sp[:-1] + [last._replace(chord=tonic)], prev.chord
    else:
        pull = next((c for c in PULLS if _fits(c, key, vocab)), PULLS[0])
        if last.length >= 2 * met.unit and last.length % 2 == 0:
            half = last.length // 2
            out = sp[:-1] + [Span(last.at, half, pull), Span(last.at + half, half, tonic)]
        else:
            out = sp[:-2] + [prev._replace(chord=pull), last._replace(chord=tonic)]
    return out, f"lands home: {name(pull, key)} to {name(tonic, key)}"


def progression(rng, flow, key, vocab, start, bars, met, phrase, prev=None):
    """One section's chords: (spans, its family, lines). The family is drawn among those that fit (the one before
    weighs `stay` times more); its first pass plays as written, later ones may vary, a phrase's last pass lands."""
    lines, fits = [], []
    for f in flow.families:
        why = "its loop doesn't divide the phrase" if phrase % f.loop else check_family(f, key, vocab, flow.still)
        if why is None:
            fits.append(f)
        else:
            lines.append(f"  ruled out: {f.name} ({why})")
    if not fits:
        raise ValueError(f"no progression family fits {key} in this style")
    fam = fits[_draw(rng, {i: f.weight * (flow.stay if f == prev else 1) for i, f in enumerate(fits)})]
    lines.insert(0, f"  progression: {fam.name}, {fam.chords} ({chart(fam.spans(key, 0, met), key, met)})"
                    + (f": {fam.why}" if fam.why else "") + (" (kept from the section before)" if fam == prev else ""))
    out = []
    for p in range(bars // fam.loop):
        at = start + p * fam.loop
        sp, words = fam.spans(key, at * met.bar, met), []
        if p:
            sp, w = vary(rng, sp, key, vocab, met, flow.variants)
            words += [w] if w else []
        if (p + 1) * fam.loop % phrase == 0 and (flow.cadence == 100 or rng.rnd(100) < flow.cadence):
            sp, w = cadence(sp, key, vocab, met)
            words += [w] if w else []
        out += sp
        lines.append(f"  bars {at + 1}-{at + fam.loop}: {chart(sp, key, met)}: {'; '.join(words) or 'as written'}")
    return out, fam, lines


def chord_at(spans, step):
    """The span sounding at a step (the last one past the end)."""
    return spans[max(0, bisect_right([s.at for s in spans], step) - 1)]


# ---- the bass ----

TONES = ("root", "third", "fifth", "octave")


@dataclass(frozen=True)
class Pattern:
    """A bass pattern: its notes as (at, length, tone, which), at and length in 16ths (length None: held to the
    next note), tone one of TONES, which "now" (the chord sounding) or "ahead" (the chord at the next half bar)."""
    name: str
    notes: tuple
    bars: int = 1
    weight: int = 1
    why: str = ""
    when: str = "any"    # the energy it plays at: "low" (under 0.5), "high" or "any" (synthwave's moods)

    def __post_init__(self):
        if self.bars not in (1, 2) or self.weight < 1:
            raise ValueError(f"{self.name}: 1 or 2 bars, weight at least 1")
        if self.when not in ("low", "high", "any"):
            raise ValueError(f"{self.name}: when low, high or any")
        ats = [n[0] for n in self.notes]
        if not ats or ats != sorted(set(ats)) or ats[0] < 0 or ats[-1] >= 16 * self.bars:
            raise ValueError(f"{self.name}: notes go in order, one a 16th, inside its {self.bars} bar(s) of 4/4")
        for at, length, tone, which in self.notes:
            if length is not None and length < 1 or tone not in TONES or which not in ("now", "ahead"):
                raise ValueError(f"{self.name}: bad note {[at, length, tone, which]}")


# Plain bass lines (any style that names none): roots on the strong beats, root and fifth, driving eighths.
PATTERNS = (
    Pattern("roots on 1 and 3", ((0, 8, "root", "now"), (8, 8, "root", "now")), 1, 2, "the root on the strong beats"),
    Pattern("root and fifth", ((0, 8, "root", "now"), (8, 8, "fifth", "now")), 1, 2, "root, then its fifth"),
    Pattern("root eighths", tuple((i, 2, "root", "now") for i in range(0, 16, 2)), 1, 1, "eighths on the root"),
)
BASS_VARIANTS = {"again": 6, "drop": 1, "approach": 2, "octave": 1}


@dataclass(frozen=True)
class BassFlow:
    patterns: tuple = PATTERNS
    variants: dict = field(default_factory=lambda: dict(BASS_VARIANTS))
    stay: int = 3
    kick: bool = False      # an 808: no pattern of its own, a note on every kick (trap, task 3.4a)
    tones: tuple = ()       # the 808's tones, ((tone, weight), ...)
    slides: int = 0         # % of the 808's notes sliding into the next


SLIDE = 12                  # steps: an 808 slides over the last 8th of its note, and only a note that long slides


def _bass_flow(style):
    d, where = part(style, "members", "bass"), f"{style}: members.bass"
    if d.get("with", "pattern") == "kick":
        tones = {k: w for k, w in d.get("tones", {"root": 1}).items() if k != "why"}
        for k, w in tones.items():
            if k not in TONES or not isinstance(w, int) or w < 0:
                raise StyleError(f"{where}.tones.{k}: one of {', '.join(TONES)}, a whole-number weight")
        slides = d.get("slides", 0)
        if not isinstance(slides, int) or not 0 <= slides <= 100:
            raise StyleError(f"{where}.slides: a share in %, 0 to 100")
        return BassFlow(kick=True, tones=tuple(tones.items()), slides=slides)
    if d.get("with", "pattern") != "pattern":
        raise StyleError(f"{where}.with: \"pattern\" (its own) or \"kick\" (an 808 on the drummer's kicks)")
    pats = []
    for n, p in d.get("patterns", {}).items():
        if n == "why":
            continue
        try:
            extra = set(p) - {"notes", "bars", "weight", "why", "when"}
            if extra:
                raise ValueError(f"unknown part {sorted(extra)[0]!r} (known: notes, bars, weight, why, when)")
            pats.append(Pattern(n, tuple(tuple(x) for x in p["notes"]), p.get("bars", 1), p.get("weight", 1),
                                p.get("why", ""), p.get("when", "any")))
        except (ValueError, TypeError, KeyError) as e:
            raise StyleError(f"{where}.patterns.{n}: {e}") from None
    variants = {**BASS_VARIANTS, **_weights(d.get("variants", {}), BASS_VARIANTS, f"{where}.variants")}
    return BassFlow(tuple(pats) or PATTERNS, variants)


BASS = {s: _bass_flow(s) for s in STYLES}


def _tone(chord, tone):
    """The tone's pitch class from the key note."""
    iv = chord.intervals
    if tone in ("root", "octave"):
        return chord.low
    if tone == "third":
        return chord.root + next((i for i in iv if i in (3, 4)), iv[1])
    return chord.root + next((i for i in iv if i in (6, 7, 8)), 7)


def _nearest(pc, near, r):
    """The bass note of pitch class `pc` (absolute) nearest `near`, inside the range `r`."""
    cands = [m for m in range(r.low, r.high + 1) if m % 12 == pc % 12]
    return min(cands, key=lambda m: (abs(m - near), m))


def _bass_vary(rng, notes, weights):
    """(the pass's notes, the variant in words or None)."""
    weights = dict(weights)
    while True:
        v = _draw(rng, weights)
        if v is None or v == "again":
            return notes, None
        if v == "drop" and len(notes) > 1:
            i = 1 + rng.rnd(len(notes) - 1)
            return notes[:i] + notes[i + 1:], "one note left out"
        if v == "octave":
            roots = [i for i, n in enumerate(notes) if n[2] == "root"]
            if roots:
                i = roots[rng.rnd(len(roots))]
                return notes[:i] + [(notes[i][0], notes[i][1], "octave", notes[i][3])] + notes[i + 1:], \
                    "one root jumps up an octave"
        if v == "approach":
            slots = [i for i in range(1, len(notes)) if notes[i][0] - notes[i - 1][0] >= 4]
            if slots:
                i = slots[rng.rnd(len(slots))]
                at = notes[i][0] - 2
                return notes[:i] + [(at, 2, "approach", "now")] + notes[i:], "an approach note into the next"
        weights[v] = 0


def bass_part(rng, bf, spans, key_at, start, bars, met, energy, prev=None, clave=None, placed=(), near=None):
    """One section's bass: (notes as [step, length or None, MIDI note], its pattern, lines). `placed`: the onsets
    already played, so a pass is checked against the clave with what came before it in the cycle; `near`: the
    last bass note, so the line carries on from it. `key_at(step)`: the key there (a note ahead may fall in the
    next section, after a key change)."""
    fits = [p for p in bf.patterns if bars % p.bars == 0]
    fits = [p for p in fits if p.when == "any" or (p.when == "low") == (energy < 0.5)] or fits   # by the mood
    pat = fits[_draw(rng, {i: p.weight * (bf.stay if p == prev else 1) for i, p in enumerate(fits)})]
    weights = dict(bf.variants)
    for k in ("approach", "octave"):
        weights[k] = weights.get(k, 0) * (1 + round(2 * energy))
    if energy >= 0.5:
        weights["drop"] = 0
    lines = [f"  bass: {pat.name}" + (f": {pat.why}" if pat.why else "") + (" (kept)" if pat == prev else "")]
    out, onsets = [], list(placed)
    for p in range(bars // pat.bars):
        base = (start + p * pat.bars) * met.bar
        notes, w = list(pat.notes), None
        if p:
            notes, w = _bass_vary(rng, notes, weights)
        if clave is not None:
            cycle = base - base % clave.length
            rest = range(base + pat.bars * met.bar, cycle + clave.length, pat.bars * met.bar)

            def crossed(ns):   # the whole cycle: what's played, this pass, the passes still to come as written
                on = [s for s in onsets if s >= cycle] + [base + n[0] * SIXTEENTH for n in ns] + \
                     [r + n[0] * SIXTEENTH for r in rest for n in pat.notes]
                return check_clave([s % clave.length for s in on], clave)
            if w and crossed(notes):
                notes, w = list(pat.notes), None
                lines.append(f"  bass, bar {start + p * pat.bars + 1}: the variant crossed the clave; as written")
            why = crossed(notes)
            if why:
                lines.append(f"  bass, bar {start + p * pat.bars + 1}: {why}")
        if w:
            lines.append(f"  bass, bar {start + p * pat.bars + 1}: {w}")
        for at, length, tone, which in notes:
            step = base + at * SIXTEENTH
            onsets.append(step)
            out.append([step, None if length is None else length * SIXTEENTH, tone, which])
    # the pitches: each tone of its chord, the nearest note to the one before; an approach note a half step under
    # (or a step over) the note it leads into
    r = member_range("bass")
    for n in out:
        step, _, tone, which = n
        if tone == "approach":
            continue
        probe = step if which == "now" else (step // (met.bar // 2) + 1) * (met.bar // 2)
        pc = key_at(probe).tonic + _tone(chord_at(spans, probe).chord, tone)
        if near is None:
            near = round(r.mid) - 4
        m = _nearest(pc, near, r)
        if tone == "octave" and m + 12 <= r.high:
            m += 12
        n.append(m)
        near = m if tone != "octave" else m - 12
    for i, n in enumerate(out):
        if n[2] == "approach":
            nxt = next((x[4] for x in out[i + 1:] if len(x) == 5), None) or near
            up = rng.rnd(3) == 0 and nxt + 2 <= r.high
            n.append(nxt + 2 if up else max(r.low, nxt - 1))
    return [(s, length, m) for s, length, _, _, m in out], pat, lines


def _chance(rng, pct):
    return rng.rnd(1000) < round(10 * pct)


def bass_808(rng, bf, spans, key_at, kicks, start, bars, met, energy, near=None, quiet=()):
    """One section's 808 (trap): (notes as [step, None, MIDI note], slides as [(step, steps, semitones)], lines). A
    note on each of the drummer's `kicks` and on each chord change, held to the next; the first note of a chord its
    root, the others drawn from the style's tones (roots mostly, fifths, octave jumps up). The style's share of the
    notes (more with more energy) slide into the next over their last 8th, drawn among the notes an 8th or longer
    with another note after them. `quiet`: the (start, end) steps where the drums drop out; the 808 rests there,
    its note before cut at the drop."""
    lo, hi = start * met.bar, (start + bars) * met.bar
    changes = {sp.at for sp in spans if lo <= sp.at < hi}

    def hush(st):
        return next((q0 for q0, q1 in quiet if q0 <= st < q1), None)
    steps = sorted(st for st in {k for k in kicks if lo <= k < hi} | changes if hush(st) is None)
    r, out = member_range("bass"), []
    if near is None:
        near = round(r.mid) - 4
    home = None
    for st in steps:
        sp = chord_at(spans, st)
        tone = "root" if st == sp.at or home is None else _draw(rng, dict(bf.tones)) or "root"
        m = _nearest(key_at(st).tonic + _tone(sp.chord, tone), near if home is None else home, r)
        if st == sp.at or home is None:
            home = m                               # the chord's root: the octave the 808 jumps from
        if tone == "octave" and m + 12 <= r.high:
            m += 12
        drop = next((q0 for q0, _ in quiet if q0 > st), None)
        nxt = next((x for x in steps if x > st), None)
        out.append([st, drop - st if drop is not None and (nxt is None or drop < nxt) else None, m])
        near = home
    # the slides: `slides` % of all the notes, drawn among those that can (another note next, an 8th of room)
    can = [i for i in range(len(out) - 1) if out[i + 1][2] != out[i][2] and abs(out[i + 1][2] - out[i][2]) <= 12
           and out[i + 1][0] - out[i][0] >= SLIDE and out[i][1] is None]
    pct = min(100, bf.slides * (0.5 + energy) * len(out) / len(can)) if can else 0
    slides = [(out[i + 1][0] - SLIDE, SLIDE, out[i + 1][2] - out[i][2]) for i in can if _chance(rng, pct)]
    words = "a note on every kick, held to the next" + ("; resting where the drums drop out" if any(
        lo <= q0 < hi for q0, _ in quiet) else "")
    if slides:
        words += f"; {len(slides)} slide{'s' * (len(slides) > 1)} into the next note"
    return out, slides, [f"  bass: an 808, {words}"]


def check_808(notes, slides, kicks, spans, key_at, quiet=()):
    """None when the 808 fits, else the reason: every note on a kick or a chord change, none sounding where the
    drums drop out (`quiet`), and every slide ending on the next note, a tone of its chord."""
    on = set(kicks) | {sp.at for sp in spans}
    for s, length, _ in notes:
        if s not in on:
            return f"an 808 note at step {s}, on no kick or chord change"
        if any(s < q1 and s + length > q0 for q0, q1 in quiet):
            return f"an 808 note at step {s} sounds where the drums drop out"
    starts = {s: m for s, _, m in notes}
    order = [s for s, _, _ in notes]
    for at, length, semis in slides:
        nxt = at + length
        if nxt not in starts:
            return f"a slide at step {at} lands on no note"
        prev = max(s for s in order if s < nxt)
        m = starts[prev] + semis
        if m != starts[nxt]:
            return f"a slide at step {at} lands on {m}, not the note {starts[nxt]}"
        ch = chord_at(spans, nxt).chord
        if (m - key_at(nxt).tonic) % 12 not in {(ch.root + i) % 12 for i in ch.intervals} | {ch.low % 12}:
            return f"a slide at step {at} lands off its chord"
    return None


def check_bass(notes, met, clave=None):
    """None when the bass line fits, else the reason: in its range, on the grid, one note a step, with the clave."""
    r = member_range("bass")
    for s, _, m in notes:
        if not r.low <= m <= r.high:
            return f"{m} is outside the bass range"
        if s % SIXTEENTH:
            return f"step {s} isn't on a 16th"
    steps = [s for s, _, _ in notes]
    if len(set(steps)) != len(steps):
        return "two bass notes start together"
    if clave is not None:
        for c in range(0, max(steps, default=0) + 1, clave.length):
            why = check_clave([s % clave.length for s in steps if c <= s < c + clave.length], clave)
            if why:
                return f"bars {c // met.bar + 1}-{c // met.bar + 2}: {why}"
    return None


def held(notes, end):
    """The bass notes with every length set: a held note (None) lasts to the next note, none past `end`."""
    out = []
    for i, (s, length, m) in enumerate(notes):
        nxt = notes[i + 1][0] if i + 1 < len(notes) else end
        out.append((s, max(1, min(length or nxt - s, nxt - s, end - s)), m))
    return out


# ---- the melody over a phrase ----

ARC = (0, 1, 2, 1, 2, 3, 4, 2)   # where each bar of an 8-bar phrase centres, in scale steps over the tonic: up to
#                                  a peak two-thirds in, down to the cadence
CHORD_TONES = 0.6                # the share of notes on the beat that should be chord tones
TRIES = 3                        # starts an 8th apart a statement may try, to sit with the clave


def _degree_near(key, pcs, near):
    """The scale degree nearest `near` whose pitch class is one of `pcs`."""
    cands = [d for d in range(near - 7, near + 8) if key.degree(d) % 12 in pcs]
    return min(cands, key=lambda d: (abs(d - near), d)) if cands else near


def phrase_melody(rng, theme, spans, key, start, bars, met, floor, clave=None, sung=()):
    """One phrase's melody: (notes as [step, length, MIDI note], lines). Statements of the theme fill the bars;
    the bar at the half lands open, the last lands home on the cadence, the bar after the half brings the phrase's
    opening back, higher; the line follows ARC. `floor`: the melody stays above it (the pad's top)."""
    half = bars // 2
    arc = [ARC[i * len(ARC) // bars] for i in range(bars)]
    notes, words, first, onsets = [], [], None, list(sung)
    prev = 0
    for i in range(bars):
        b0 = (start + i) * met.bar
        if i == half and first is not None:
            m, how = first, "the phrase's opening again, higher"
        else:
            m, how = theme.next()
            how = WORDS[how]
        if i == 0:
            first = m
        landing = i in (half - 1, bars - 1)
        land_at = None
        if landing:
            last = [s for s in spans if b0 <= s.at < b0 + met.bar] or [chord_at(spans, b0)]
            land_at = max(last[-1].at, b0 + met.bar // 2)
        stop = land_at if landing else b0 + met.bar
        shift = arc[i] - round(sum(m.steps) / len(m.steps))
        degs = [d + shift for d in m.steps]
        best = None
        for t in range(TRIES if clave is not None else 1):
            at, line = b0 + t * met.unit // 2, []
            for d, length in zip(degs, m.lengths):
                if at >= stop:
                    break
                line.append([at, min(length, stop - at), d])
                at += length
            if not line:
                continue
            if best is None:
                best = line
            if clave is None:
                break
            cyc = line[0][0] - line[0][0] % clave.length
            if check_clave([s % clave.length for s in [x for x in onsets if x >= cyc] + [x[0] for x in line]],
                           clave) is None:
                best = line
                break
        line = best or []
        for n in line:   # a note on the beat leans to the chord's tones, a step at most
            if n[0] % met.unit == 0:
                tones = {t % 12 for t in chord_at(spans, n[0]).chord.tones}
                if key.degree(n[2]) % 12 not in tones:
                    for d in ((n[2] + 1, n[2] - 1) if rng.rnd(2) else (n[2] - 1, n[2] + 1)):
                        if key.degree(d) % 12 in tones:
                            n[2] = d
                            break
        if landing:
            ch = chord_at(spans, land_at).chord
            near = line[-1][2] if line else prev
            if i == bars - 1:
                d = _degree_near(key, {0}, near)
                word = "lands home"
            else:
                d = _degree_near(key, {t % 12 for t in ch.tones} - {0}, near)
                word = "ends open"
            line.append([land_at, b0 + met.bar - land_at, d])
            words.append(f"bar {start + i + 1}: {how}, then {word} on {key.name(key.degree(d) % 12)} "
                         f"over {name(ch, key)}")
        else:
            words.append(f"bar {start + i + 1}: {how}")
        if line:
            prev = line[-1][2]
        notes += line
        onsets += [n[0] for n in line]
    # the register: the lowest octave that keeps the phrase over the floor
    lo, hi = min(key.degree(n[2]) for n in notes), max(key.degree(n[2]) for n in notes)
    top = member_range("melody").high
    base = next((b for b in range(key.tonic, 128, 12) if b + lo > floor and b + hi <= top),
                next(b for b in range(key.tonic, 128, 12) if b + lo > floor))
    out = [(s, length, base + key.degree(d)) for s, length, d in notes]
    peak = max(range(len(out)), key=lambda j: out[j][2])
    lines = [f"  melody, bars {start + 1}-{start + bars}: a phrase of {bars}, its peak in bar "
             f"{out[peak][0] // met.bar + 1}"] + ["    " + w for w in words]
    return out, lines


def check_phrase(notes, spans, key, met, bars, start):
    """None when the phrase is shaped, else the reason: it ends home, its half ends open, and most notes on the
    beat are chord tones."""
    if not notes:
        return "no melody"
    if (notes[-1][2] - key.tonic) % 12:
        return "the phrase doesn't end home"
    half = (start + bars // 2) * met.bar
    before = [n for n in notes if n[0] < half]
    if before and (before[-1][2] - key.tonic) % 12 == 0:
        return "the first half ends home already: no question for the answer"
    on = [n for n in notes if n[0] % met.unit == 0]
    good = sum((n[2] - key.tonic) % 12 in {t % 12 for t in chord_at(spans, n[0]).chord.tones} for n in on)
    if on and good / len(on) < CHORD_TONES:
        return f"only {good} of {len(on)} notes on the beat are chord tones"
    return None



# ---- the melody as a loop (trap, task 3.4a's second round) ----

# a beat of the loop's rhythm: (at, length) in steps; triplets are 8th triplets (Duinker's triplet flow)
CELLS = {"q": ((0, 24),), "8 8": ((0, 12), (12, 12)), "8 r": ((0, 12),), "r 8": ((12, 12),),
         "16 16 8": ((0, 6), (6, 6), (12, 12)), "8 16 16": ((0, 12), (12, 6), (18, 6)),
         "t t t": ((0, 8), (8, 8), (16, 8)), "r": ()}
LOOP_SPAN = (-2, 7)              # scale steps over the tonic the loop keeps to


@dataclass(frozen=True)
class LoopFlow:
    bars: tuple = ((1, 1), (2, 3))       # (bars, weight)
    cells: tuple = tuple((c, 1) for c in CELLS)
    stay: int = 2                        # times likelier a section keeps the loop before
    vary: int = 20                       # % of rounds with one note moved a step
    every: int = 1                       # the riff plays one round in this many, resting the others (trap: 2)


def _loop_flow(style):
    d, where = part(style, "members", "melody"), f"{style}: members.melody"
    shape = d.get("shape", "phrase")
    if shape not in ("phrase", "loop"):
        raise StyleError(f"{where}.shape: \"phrase\" (shaped over the phrase) or \"loop\" (a riff going round)")
    if shape == "phrase":
        return None
    lp = d.get("loop", {})
    extra = set(lp) - {"why", "bars", "cells", "stay", "vary", "every"}
    if extra:
        raise StyleError(f"{where}.loop: unknown part {sorted(extra)[0]!r} (known: bars, cells, stay, vary, every)")
    if not isinstance(lp.get("every", 1), int) or lp.get("every", 1) < 1:
        raise StyleError(f"{where}.loop.every: a whole number from 1")
    bars = tuple((int(k), w) for k, w in lp.get("bars", {"2": 1}).items() if k != "why")
    cells = tuple((k, w) for k, w in lp.get("cells", {c: 1 for c in CELLS}).items() if k != "why")
    if any(b not in (1, 2) for b, _ in bars) or any(c not in CELLS for c, _ in cells):
        raise StyleError(f"{where}.loop: bars 1 or 2; cells among {', '.join(CELLS)}")
    return LoopFlow(bars, cells, lp.get("stay", 2), lp.get("vary", 20), lp.get("every", 1))


LOOPS = {s: _loop_flow(s) for s in STYLES}   # None: the melody is shaped over the phrase


def make_loop(rng, lf, met):
    """A new loop: [(at, length, scale step)] over 1 or 2 bars, mostly steps, narrow, starting on a chord tone of
    home; the last beat may breathe."""
    n = _draw(rng, dict(lf.bars))
    beats = n * len(met.beats)
    out, d = [], (0, 2, 4)[rng.rnd(3)]
    for b in range(beats):
        cell = _draw(rng, dict(lf.cells))
        if not CELLS[cell] and b == 0:
            cell = "8 8"
        for at, length in CELLS[cell]:
            if out:
                r = rng.rnd(10)
                step = 0 if r < 3 else (1 if r < 8 else 2) * (1 if rng.rnd(2) else -1)
                d = min(LOOP_SPAN[1], max(LOOP_SPAN[0], d + step))
            out.append((b * met.unit + at, length, d))
    return n, tuple(out)


def _loop_words(n, loop, met):
    cells = []
    for b in range(n * len(met.beats)):
        ats = [at - b * met.unit for at, _, _ in loop if b * met.unit <= at < (b + 1) * met.unit]
        cells.append(next((c for c, v in CELLS.items() if [a for a, _ in v] == ats), "?"))
    return " | ".join(" ".join(f"[{c}]" for c in cells[i:i + len(met.beats)])
                      for i in range(0, len(cells), len(met.beats)))


def loop_melody(rng, lf, spans, key, start, bars, met, floor, prev=None, phrase=8):
    """One section's melody as a loop going round: (notes as [step, length, MIDI note], the loop, lines). Each
    round the notes on the beat move to the nearest tone of the chord under them; now and then a round moves one
    note a step; the last round of each phrase lands home on its last note. With `every`, the riff plays only one
    round in that many (the last of each group), resting between."""
    if prev is not None and rng.rnd(lf.stay + 1):
        n, loop = prev
        kept = True
    else:
        n, loop = make_loop(rng, lf, met)
        kept = False
    lines = [f"  melody: a {n}-bar loop{' (kept)' if kept else ''}, {_loop_words(n, loop, met)}"
             + (f", played one round in {lf.every}" if lf.every > 1 else "")]
    lo_deg = min(min(d for _, _, d in loop), 0) - 1       # room for the chord fitting and the landing
    hi_deg = max(d for _, _, d in loop) + 1
    base = next((12 * o + key.tonic for o in range(3, 8)
                 if 12 * o + key.tonic + key.degree(lo_deg) > floor
                 and 12 * o + key.tonic + key.degree(hi_deg) <= member_range("melody").high),
                12 * 5 + key.tonic)
    notes, rounds = [], bars // n
    for k in range(rounds):
        if (k + 1) % lf.every:                 # a round of rest: space around the riff (the last always plays)
            continue
        at0 = (start + k * n) * met.bar
        ds = [d for _, _, d in loop]
        if k and _chance(rng, lf.vary):
            i = 1 + rng.rnd(len(ds) - 1) if len(ds) > 1 else 0
            ds[i] = min(LOOP_SPAN[1], max(LOOP_SPAN[0], ds[i] + (1 if rng.rnd(2) else -1)))
            lines.append(f"  melody, bar {start + k * n + 1}: one note moved a step")
        last = (k + 1) * n % phrase == 0 or k == rounds - 1
        for j, ((at, length, _), d) in enumerate(zip(loop, ds)):
            st = at0 + at
            if st % met.unit == 0:
                pcs = {t % 12 for t in chord_at(spans, st).chord.tones}
                d = _degree_near(key, pcs, d)
            if last and j == len(loop) - 1:
                d = 0 if abs(d) < abs(d - 7) else 7
            m = base + key.degree(d)
            while m <= floor and m + 12 <= member_range("melody").high:   # never down in the pad
                m += 12
            while m > member_range("melody").high and m - 12 > floor:     # nor over the top
                m -= 12
            notes.append([st, length, m])
        if last and k != rounds - 1:
            lines.append(f"  melody, bar {start + k * n + n}: the round lands home")
    return notes, (n, loop), lines


def check_loop(notes, spans, key, floor):
    """None when the loop's melody fits, else the reason: on the grid, above the pad, in range, and most notes on
    the beat chord tones."""
    r = member_range("melody")
    for st, length, m in notes:
        if not r.low <= m <= r.high:
            return f"{m} is outside the melody's range"
        if m <= floor:
            return f"{m} sinks into the pad"
    on = [n for n in notes if n[0] % 24 == 0]
    good = sum((n[2] - key.tonic) % 12 in {t % 12 for t in chord_at(spans, n[0]).chord.tones} for n in on)
    if on and good / len(on) < CHORD_TONES:
        return f"only {good} of {len(on)} notes on the beat are chord tones"
    return None


# ---- the arp (synthwave, task 3.4b) ----

# a shape: which of the chord's tones (counted up from the arp's floor) it plays, in order, round and round
ARP_SHAPES = {"up": (0, 1, 2, 3), "down": (3, 2, 1, 0), "up and down": (0, 1, 2, 3, 2, 1), "broken": (0, 2, 1, 3)}
ARP_FLOOR = 60                   # C4: the arp's tones climb from the first chord tone at or over it
ARP_RATES = ("8th", "16th")


@dataclass(frozen=True)
class ArpFlow:
    shapes: tuple = tuple((n, s, 1) for n, s in ARP_SHAPES.items())   # (name, tones, weight)
    rates: tuple = (("16th", 1),)  # (note value, weight) when the energy is up
    calm: str = "8th"              # its rate under energy 0.5: slower, colder (the dreamy sections)
    stay: int = 3                  # times likelier a section keeps the shape before
    floor: int = ARP_FLOOR


def _arp_flow(style):
    d, where = part(style, "members", "arp"), f"{style}: members.arp"
    if not d:
        return None
    shapes = []
    for n, x in d.get("shapes", {k: {"tones": list(v)} for k, v in ARP_SHAPES.items()}).items():
        if n == "why":
            continue
        t = x.get("tones") if isinstance(x, dict) else None
        if not isinstance(t, list) or not 2 <= len(t) <= 8 or any(not isinstance(i, int) or not 0 <= i <= 6 for i in t):
            raise StyleError(f"{where}.shapes.{n}: \"tones\", 2 to 8 of the chord's tones counted up from the floor, 0-6")
        shapes.append((n, tuple(t), x.get("weight", 1)))
    rates = tuple((k, w) for k, w in d.get("rate", {"16th": 1}).items() if k != "why")
    if any(k not in ARP_RATES for k, _ in rates) or d.get("calm", "8th") not in ARP_RATES:
        raise StyleError(f"{where}: rate and calm among {', '.join(ARP_RATES)}")
    return ArpFlow(tuple(shapes), rates, d.get("calm", "8th"))


ARPS = {s: _arp_flow(s) for s in STYLES}   # None: the band has no arp


def _ladder(chord, key, floor, top):
    """The chord's tones from the floor up to `top`, as MIDI notes."""
    pcs = {(key.tonic + t) % 12 for t in chord.tones}
    return [m for m in range(floor, top + 1) if m % 12 in pcs]


def arp_part(rng, af, spans, key_at, start, bars, met, energy, prev=None):
    """One section's arp: (notes as (step, length, MIDI note), its shape, lines). A shape and a rate a section (the
    slower rate when the energy is low), round and round over each chord's tones, starting again on each chord."""
    shape = af.shapes[_draw(rng, {i: s[2] * (af.stay if s == prev else 1) for i, s in enumerate(af.shapes)})]
    rate = af.calm if energy < 0.5 else _draw(rng, dict(af.rates))
    step, r = VALUES[rate], member_range("arp")
    lo, hi = start * met.bar, (start + bars) * met.bar
    out = []
    for sp in spans:
        if not lo <= sp.at < hi:
            continue
        ladder = _ladder(sp.chord, key_at(sp.at), max(af.floor, r.low), r.high)
        for k, at in enumerate(range(sp.at, sp.at + sp.length, step)):
            out.append((at, step, ladder[min(shape[1][k % len(shape[1])], len(ladder) - 1)]))
    lines = [f"  arp: {shape[0]} in {rate}s over each chord's tones" + (" (kept)" if shape == prev else "")
             + (", slower for the low energy" if energy < 0.5 else "")]
    return out, shape, lines


def check_arp(notes, spans, key_at):
    """None when the arp fits, else the reason: one note at a time, each a tone of its chord, inside its range."""
    r = member_range("arp")
    for i, (st, length, m) in enumerate(notes):
        if i + 1 < len(notes) and st + length > notes[i + 1][0]:
            return f"two arp notes at once at step {st}"
        if not r.low <= m <= r.high:
            return f"an arp note {m} outside its range"
        ch, key = chord_at(spans, st).chord, key_at(st)
        if (m - key.tonic) % 12 not in {t % 12 for t in ch.tones}:
            return f"an arp note at step {st} off its chord"
    return None
