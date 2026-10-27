# SPDX-License-Identifier: GPL-3.0-or-later
"""The percussion member (task 3.3, decision 11): congas, bongos, timbales, bells, clave and the like, its own member
apart from the kit. Written from theory (no open data yet: El Bongosero's data license is unclear, `docs/data.md`).

A style's entry (members.percussion.parts) names each part and its pattern families. A pattern lists its hits as
[16th, voice, velocity] over one or two bars, says when it plays ("low" energy, "high" or "any") and weighs against
the others. Two-bar patterns are written in the song's clave cycle: bar 1 of the pattern falls on the clave's first
bar. A section draws one pattern a part for its energy (the one before likelier); after its first pass a pass may
drop a soft hit (never one on the clave's own strokes). The timbales may close a section with an abanico, a roll on the last beat into the next section's
first beat, with a crash. The check rules out a hit off the grid or outside the clip and a part crossing the clave.
Sounds are GM stand-ins (Ouralia's own in bucket 6)."""
from dataclasses import dataclass

from ..stylebook import StyleError, part, per_style
from .form import _draw
from .rhythm import check_clave, roll

SIXTEENTH = 6
# GM drum notes, the stand-ins (the shell has no GM sound: a side stick)
VOICES = {"claves": 75, "conga muted": 62, "conga slap": 62, "conga open": 63, "tumba": 64, "bongo high": 60,
          "bongo low": 61, "bongo bell": 56, "timbale high": 65, "timbale low": 66, "shell": 37, "timbale bell": 53,
          "guiro short": 73, "guiro long": 74, "maracas": 70, "crash": 49}
WHEN = ("low", "high", "any")
HIGH = 0.5           # a section this loud or louder plays the "high" patterns
VARIANTS = {"again": 6, "drop": 1}


@dataclass(frozen=True)
class Pattern:
    name: str
    hits: tuple          # (16th, voice, velocity)
    bars: int = 1
    weight: int = 1
    when: str = "any"
    why: str = ""

    def __post_init__(self):
        if self.bars not in (1, 2) or self.weight < 1 or self.when not in WHEN:
            raise ValueError("1 or 2 bars, a weight from 1, when one of " + ", ".join(WHEN))
        for h in self.hits:
            if len(h) != 3 or not 0 <= h[0] < 16 * self.bars or h[1] not in VOICES or not 1 <= h[2] <= 127:
                raise ValueError(f"bad hit {list(h)}: [16th inside its {self.bars} bar(s), a voice, a velocity]")

    def fits(self, energy):
        return self.when == "any" or (self.when == "high") == (energy >= HIGH)


@dataclass(frozen=True)
class Part:
    name: str
    patterns: tuple
    variants: dict
    abanico: int = 0     # % of section ends the part closes with an abanico (timbales)
    why: str = ""


def _parts(style):
    d, where = part(style, "members", "percussion"), f"{style}: members.percussion"
    out = []
    for name, p in d.get("parts", {}).items():
        if name == "why":
            continue
        try:
            extra = set(p) - {"patterns", "variants", "abanico", "why"}
            if extra:
                raise ValueError(f"unknown part {sorted(extra)[0]!r} (known: patterns, variants, abanico, why)")
            pats = tuple(Pattern(n, tuple(tuple(h) for h in x["hits"]), x.get("bars", 1), x.get("weight", 1),
                                 x.get("when", "any"), x.get("why", ""))
                         for n, x in p["patterns"].items() if n != "why")
            if not pats:
                raise ValueError("no patterns")
            variants = {**VARIANTS, **{k: v for k, v in p.get("variants", {}).items() if k != "why"}}
            if set(variants) - set(VARIANTS) or not all(isinstance(v, int) and v >= 0 for v in variants.values()):
                raise ValueError(f"variants are {', '.join(VARIANTS)}, whole-number weights")
            out.append(Part(name, pats, variants, p.get("abanico", 0), p.get("why", "")))
        except (ValueError, TypeError, KeyError) as e:
            raise StyleError(f"{where}.parts.{name}: {e}") from None
    return tuple(out) or None


PERCUSSION = per_style(_parts)   # None: the style has no percussion member yet


def _vel(v, energy):
    return max(1, min(127, round(v * (0.85 + 0.3 * energy))))


def percussion_part(rng, parts, recs, met, end, clave=None):
    """The percussion over the bars of `recs` (a record a bar: bar, section, energy), up to step `end`:
    ([(step, length, MIDI note, velocity, part)], [(section, line in words)]). A dropped hit is never on one of
    the clave's own strokes, so a variant can't cross it."""
    hits, lines = [], []
    chosen = {}
    for r in recs:
        b, s, e = r["bar"], r["section"], r["energy"]
        at = b * met.bar
        new = b == s.start or b == recs[0]["bar"]
        closing = b == s.end - 1 and (b + 1) * met.bar < end      # a next section starts inside the clip
        words = []
        for p in parts:
            if new:
                fits = [x for x in p.patterns if x.fits(e)] or list(p.patterns)
                prev = chosen.get(p.name)
                chosen[p.name] = fits[_draw(rng, {i: x.weight * (3 if x == prev else 1) for i, x in enumerate(fits)})]
                pat = chosen[p.name]
                words.append(f"{p.name}: {pat.name}" + (f" ({pat.why})" if pat.why else ""))
            pat = chosen[p.name]
            half = b % pat.bars           # which bar of the pattern: two-bar ones keep the clave cycle
            mine = [h for h in pat.hits if half * 16 <= h[0] < (half + 1) * 16]
            if not new and b % pat.bars == 0 and _draw(rng, p.variants) == "drop":
                soft = [h for h in mine if h[2] < 80 and not (
                    clave and (at + (h[0] - half * 16) * SIXTEENTH) % clave.length in clave.onsets)]
                if soft:
                    mine.remove(soft[rng.rnd(len(soft))])
            stop = at + met.bar
            if closing and p.abanico and rng.rnd(100) < p.abanico:
                stop = at + met.beats[-1]
                for i, st in enumerate(roll(stop, at + met.bar - stop, "32nd")):
                    hits.append((st, 3, VOICES["timbale high"], _vel(60 + 6 * i, e), p.name))
                hits += [(at + met.bar, SIXTEENTH, VOICES["timbale high"], _vel(115, e), p.name),
                         (at + met.bar, SIXTEENTH, VOICES["crash"], _vel(105, e), p.name)]
                lines.append((s, f"  percussion, bar {b + 1}: the {p.name} close the section with an abanico "
                                 f"(a roll on the last beat, a rim shot and a crash on the next one)"))
            for p16, voice, v in mine:
                st = at + (p16 - half * 16) * SIXTEENTH
                if st < stop:
                    hits.append((st, SIXTEENTH, VOICES[voice], _vel(v, e), p.name))
        if words:
            lines.append((s, "  percussion: " + "; ".join(words)))
    return sorted(h for h in hits if h[0] < end), lines


def check_percussion(hits, met, end, clave=None):
    """None when the percussion fits, else the reason: on the grid, inside the clip, one of each sound a step in a
    part, and no part crossing the clave."""
    seen, by_part = set(), {}
    for step, _, note, _, name in hits:
        if step != int(step) or not 0 <= step < end:
            return f"the {name} at step {step}: off the grid or outside the clip"
        if (step, note, name) in seen:
            return f"the {name} play one sound twice on {met.count(step)}"
        seen.add((step, note, name))
        by_part.setdefault(name, []).append(step)
    if clave is not None:
        for name, on in by_part.items():
            for c in range(0, end, clave.length):
                why = check_clave([s - c for s in on if c <= s < c + clave.length and s % SIXTEENTH == 0], clave)
                if why:
                    return f"the {name}, bars {c // met.bar + 1}-{c // met.bar + 2}: {why}"
    return None
