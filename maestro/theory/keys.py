# SPDX-License-Identifier: GPL-3.0-or-later
"""The keys member (task 3.4c, decision 11): salsa's piano montuno (the guajeo).

The montuno is a two-bar figure in 8ths that goes round and round, sitting with the clave and pushing each chord in
early on an "and" (the anticipation, like the tumbao's). Its top line is doubled an octave below, the way salsa
pianists play it in octaves, and on the clave's strokes and the anticipations a chord tone fills in between. A
pattern names its hits: [8th over the two bars, the top line's chord tone counted up from the floor (0-3), "now" (the
chord sounding) or "ahead" (the chord at the next half bar)]. A section draws one pattern for its energy and keeps
it; the montuno repeats freely, as grooving members do (decision 9).

The check: every note a tone of its chord (now or ahead), inside the keys' range, and the figure sitting with the
clave. Sources: Wikipedia's "Guajeo" and "Montuno" (CC BY-SA 4.0), the ideas in our own words."""
from dataclasses import dataclass

from ..stylebook import STYLES, StyleError, part
from .flow import chord_at
from .form import _draw
from .rhythm import CLAVES, RHYTHM, check_clave
from .voicing import member_range

EIGHTH = 12          # grid steps in an 8th
FLOOR = 64           # E4: the top line climbs from its first chord tone at or over it
HOLD = 24            # steps: a montuno note rings at most a beat


@dataclass(frozen=True)
class Montuno:
    name: str
    hits: tuple          # ((8th, tone index, "now" or "ahead"), ...) over two bars
    weight: int = 1
    when: str = "any"    # "low" (energy under 0.5), "high" or "any"
    why: str = ""

    def steps(self):
        return [e * EIGHTH for e, _, _ in self.hits]


@dataclass(frozen=True)
class KeysFlow:
    patterns: tuple
    stay: int = 4        # times likelier a section keeps the pattern before


def _keys_flow(style):
    d, where = part(style, "members", "keys"), f"{style}: members.keys"
    if not d:
        return None
    clave = CLAVES.get(RHYTHM[style].clave) if RHYTHM[style].clave else None
    pats = []
    for n, p in d.get("patterns", {}).items():
        if n == "why":
            continue
        extra = set(p) - {"hits", "weight", "when", "why"}
        if extra:
            raise StyleError(f"{where}.patterns.{n}: unknown part {sorted(extra)[0]!r} (known: hits, weight, when, why)")
        hits = tuple(tuple(h) for h in p.get("hits", []))
        ats = [h[0] for h in hits]
        if not hits or ats != sorted(set(ats)) or ats[0] < 0 or ats[-1] >= 16 or any(
                len(h) != 3 or h[1] not in range(4) or h[2] not in ("now", "ahead") for h in hits):
            raise StyleError(f"{where}.patterns.{n}: hits in order, one an 8th inside two bars, each [8th, tone 0-3, "
                             "\"now\" or \"ahead\"]")
        if p.get("when", "any") not in ("low", "high", "any"):
            raise StyleError(f"{where}.patterns.{n}.when: low, high or any")
        m = Montuno(n, hits, p.get("weight", 1), p.get("when", "any"), p.get("why", ""))
        if clave is not None and check_clave(m.steps(), clave):
            raise StyleError(f"{where}.patterns.{n}: {check_clave(m.steps(), clave)}")
        pats.append(m)
    if not pats:
        raise StyleError(f"{where}.patterns: at least one montuno")
    return KeysFlow(tuple(pats))


KEYS = {s: _keys_flow(s) for s in STYLES}   # None: the band has no keys


def ladder(chord, key, floor=FLOOR):
    """The chord's tones from the floor up an octave and a bit, as MIDI notes."""
    pcs = {(key.tonic + t) % 12 for t in chord.tones}
    return [m for m in range(floor, member_range("keys").high + 1) if m % 12 in pcs]


def voice(chord, key, i, fill):
    """One montuno hit: the top line's tone `i` up the ladder, its octave below, and with `fill` a chord tone
    between them, the one nearest the middle."""
    top = ladder(chord, key)[i]
    out = [top - 12, top]
    if fill:
        pcs = {(key.tonic + t) % 12 for t in chord.tones}
        inner = [m for m in range(top - 10, top - 2) if m % 12 in pcs]
        if inner:
            out.insert(1, min(inner, key=lambda m: abs(m - (top - 6))))
    return out


def ahead(step, met):
    """The step whose chord an anticipated hit plays: the next half bar."""
    half = met.bar // 2
    return (step // half + 1) * half


def montuno_part(rng, kf, spans, key_at, start, bars, met, energy, prev=None, clave=None):
    """One section's montuno: (notes as (step, length, MIDI note), its pattern, lines)."""
    fits = [p for p in kf.patterns if p.when == "any" or (p.when == "low") == (energy < 0.5)] or list(kf.patterns)
    pat = fits[_draw(rng, {i: p.weight * (kf.stay if p == prev else 1) for i, p in enumerate(fits)})]
    lo, hi = start * met.bar, (start + bars) * met.bar
    strokes = set(clave.onsets) if clave else set()
    onsets = []
    for base in range(lo, hi, 2 * met.bar):
        for e, i, which in pat.hits:
            st = base + e * EIGHTH
            if st < hi:
                onsets.append((st, i, which))
    out = []
    for k, (st, i, which) in enumerate(onsets):
        probe = ahead(st, met) if which == "ahead" else st
        nxt = onsets[k + 1][0] if k + 1 < len(onsets) else hi
        length = min(nxt - st, HOLD)
        fill = which == "ahead" or (clave is not None and st % clave.length in strokes)
        for m in voice(chord_at(spans, probe).chord, key_at(probe), i, fill):
            out.append((st, length, m))
    lines = [f"  keys: the montuno, {pat.name}" + (f": {pat.why}" if pat.why else "") + (" (kept)" if pat == prev else "")]
    return out, pat, lines


def check_keys(notes, spans, key_at, met, clave=None):
    """None when the montuno fits, else the reason: inside the keys' range, each note a tone of the chord sounding
    or the one it anticipates, and the figure sitting with the clave."""
    r = member_range("keys")
    for st, length, m in notes:
        if not r.low <= m <= r.high:
            return f"a keys note {m} outside its range"
        if not any((m - key_at(p).tonic) % 12 in {t % 12 for t in chord_at(spans, p).chord.tones}
                   for p in (st, ahead(st, met))):
            return f"a keys note at step {st} off its chord"
    if clave is not None:
        return check_clave(sorted({st % clave.length for st, _, _ in notes}), clave)
    return None
