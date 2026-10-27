# SPDX-License-Identifier: GPL-3.0-or-later
"""The horns member (task 3.4c, decision 11): salsa's horn section, after the Fania records' two trombones.

What the horns play depends on the part of the song (`arrange.py`):
- **punches:** short hits on the clave's strokes at the end of the lead's phrase (and at its middle when the energy
  is up), the band underlining the cadence;
- **coro:** a two-bar refrain answering the lead, every other two bars of the phrase, the same refrain all section
  (the coro of a son montuno; the horns stand in for the voices);
- **riff:** the mambo, a busier riff going round every round, the lead out.
The coro and the riff are loops (`flow.loop_melody`): drawn from rhythm cells, each round's beat notes fitted to the
chord, the phrase's last round landing home. A loop that crosses the clave is drawn again; after a few tries the
horns punch instead. The top line is harmonised below it: the next chord tone down a third to a sixth, or a third
down the scale on a passing note, so the voices move together the way a horn section's do.

The check: inside the horns' range, no more voices than the section has, and the onsets sitting with the clave.
Sources: Wikipedia's "Salsa music" and "Mambo (music)" (CC BY-SA 4.0), the ideas in our own words."""
from dataclasses import dataclass

from ..stylebook import StyleError, part, per_style
from .flow import LoopFlow, _loop_words, chord_at, loop_flow, loop_melody
from .rhythm import check_clave
from .voicing import Range, member_range

TOP = (60, 77)       # C4 to F5: the top line, where two trombones ring
TRIES = 6            # loops drawn before the horns punch instead
PUNCH = 9            # steps: a punch is short, a dotted 16th


@dataclass(frozen=True)
class HornFlow:
    voices: int = 2
    coro: LoopFlow = LoopFlow(bars=((2, 1),), every=2)
    riff: LoopFlow = LoopFlow(bars=((2, 1),))


def _horn_flow(style):
    d, where = part(style, "members", "horns"), f"{style}: members.horns"
    if not d:
        return None
    for k in ("coro", "riff"):
        lp = d.get(k, {})
        if any(int(b) != 2 for b in lp.get("bars", {"2": 1}) if b != "why"):
            raise StyleError(f"{where}.{k}.bars: two bars, a clave's length")
    return HornFlow(d.get("voices", 2), loop_flow(d.get("coro", {"every": 2}), f"{where}.coro"),
                    loop_flow(d.get("riff", {}), f"{where}.riff"))


HORNS = per_style(_horn_flow)   # None: the band has no horns


def strokes(clave, bar, met):
    """The clave's strokes in bar `bar`, as steps from the bar's start (1, the and of 2 and 4 without a clave)."""
    if clave is None:
        return [0, 36, 72]
    side = bar % clave.bars
    return [o - side * met.bar for o in clave.onsets if o // met.bar == side]


def _scale(key):
    return {(key.tonic + key.degree(d)) % 12 for d in range(7)}


def harmonize(top, spans, key_at, voices):
    """The top line with its voices under it: the chord tone a third to a sixth down, or a third down the scale on
    a note that isn't the chord's."""
    low, out = member_range("horns").low, []
    for st, length, m in top:
        key = key_at(st)
        pcs = {(key.tonic + t) % 12 for t in chord_at(spans, st).chord.tones}
        out.append((st, length, m))
        v = m
        for _ in range(voices - 1):
            under = [n for n in range(v - 9, v - 2) if n % 12 in pcs] if v % 12 in pcs or v != m else []
            under = under or [n for n in (v - 4, v - 3) if n % 12 in _scale(key)]
            if not under or max(under) < low:
                break
            v = max(under)
            out.append((st, length, v))
    return out


def hits(spans, key_at, steps, probe=None):
    """The top line's short hits on `steps`: each the tone of the chord at `probe(step)` (the step itself) nearest
    the middle of the top line's room."""
    out, mid = [], (TOP[0] + TOP[1]) // 2
    for st in steps:
        at = probe(st) if probe else st
        key = key_at(at)
        pcs = {(key.tonic + t) % 12 for t in chord_at(spans, at).chord.tones}
        out.append((st, PUNCH, min((n for n in range(TOP[0], TOP[1] + 1) if n % 12 in pcs),
                                   key=lambda n: (abs(n - mid), n))))
    return out


def punches(spans, key_at, start, bars, met, energy, clave=None, phrase=8):
    """The top line's punches: on the strokes of each phrase's last bar, and of its middle bar when the energy is
    up."""
    steps = []
    for at in range(start, start + bars, phrase):
        for b in ([at + phrase // 2 - 1] if energy >= 0.5 else []) + [at + phrase - 1]:
            if b < start + bars:
                steps += [b * met.bar + s for s in strokes(clave, b, met)]
    return hits(spans, key_at, steps)


def horn_part(rng, hf, kind, spans, key_at, start, bars, met, energy, prev=None, clave=None, phrase=8, placed=()):
    """The horns over `bars` bars from `start` playing `kind` ("punches", "coro", "riff" or "out"): (notes as
    (step, length, MIDI note), what they played, lines). `prev`: {kind: its loop}, the loops so far, kept up to date; `placed`: the onsets already played, so a loop is checked
    against the clave with them."""
    if kind == "out":
        return [], kind, []
    if kind in ("coro", "riff"):
        lf, key = hf.coro if kind == "coro" else hf.riff, key_at(start * met.bar)
        keep = prev.get(kind) if prev is not None else None
        for tries in range(TRIES):
            top, loop, said = loop_melody(rng, lf, spans, key, start, bars, met, TOP[0] - 1,
                                          keep if keep and not tries else None, phrase, Range(TOP[0], TOP[1]))
            bad = clave and check_clave(sorted({st % clave.length for st in [*placed, *(n[0] for n in top)]}), clave)
            if not bad:
                n, notes = loop
                what = ("the coro, a two-bar refrain answering the lead" if kind == "coro" else
                        "the mambo, a riff going round")
                lines = [f"  horns: {what}{' (kept)' if keep and not tries else ''}, {_loop_words(n, notes, met)}"]
                lines += [ln.replace("melody", "horns") for ln in said[1:]]
                if prev is not None:
                    prev[kind] = loop
                return harmonize(top, spans, key_at, hf.voices), kind, lines
        lines = [f"  horns: every {kind} drawn crossed the clave; they punch instead"]
    else:
        lines = ["  horns: punches on the clave's strokes, closing the lead's phrases"]
    return harmonize(punches(spans, key_at, start, bars, met, energy, clave, phrase), spans, key_at, hf.voices), \
        "punches", lines


def check_horns(notes, voices, clave=None):
    """None when the horns fit, else the reason: inside their range, no more voices than the section has, and
    sitting with the clave."""
    r, at = member_range("horns"), {}
    for st, length, m in notes:
        if not r.low <= m <= r.high:
            return f"a horn note {m} outside their range"
        at[st] = at.get(st, 0) + 1
        if at[st] > voices:
            return f"{at[st]} horn notes at step {st}, for {voices} players"
    if clave is not None and notes:
        return check_clave(sorted({st % clave.length for st, _, _ in notes}), clave)
    return None
