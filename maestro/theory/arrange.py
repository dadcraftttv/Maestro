# SPDX-License-Identifier: GPL-3.0-or-later
"""Arrangement, a first piece of task 3.6 pulled forward for salsa (task 3.4c): what each phrase is, and so who
plays what in it.

A style's "arrange" names its parts. Each says when it plays (the energy: "low" under 0.5, "high" or "any"), its
weight, the part it must follow ("after"), what the lead does ("phrase": sings the whole phrase; "call": calls and
leaves the coro its bars; "out") and what the horns do ("punches", "coro", "riff" or "out"). Salsa's song runs from
its body (the cuerpo: the lead sings the verse, the horns punch its ends) into the montuno (the lead calls, the horns
answer with the coro) and its mambos (the horns' riff, the lead out). The play's first section keeps the part it
"opens" with; after it, each phrase draws its part. And a section may close on a break ("breaks", % of section
ends): the last bar, the band hitting the clave's strokes together, the lead silent. Tendencies, never a fixed order
(decision 9). Sources: Wikipedia's "Salsa music" and "Son montuno" (CC BY-SA 4.0), the ideas in our own words.

Power rock's (task 3.4d) runs verse to chorus: a part also says how the rhythm guitar plays ("guitar": a group of
its patterns, `theory/guitar.py`). A quiet section that leads into a loud one may turn its last phrase into a build
("build": the part, "builds": % of such sections), the pre-chorus; its break ("stop") is the band hitting the one
together and letting it ring while the drums fill in. Sources: Wikipedia's "Verse-chorus form" and "Arena rock"
(CC BY-SA 4.0), the ideas in our own words."""
from dataclasses import dataclass

from ..stylebook import StyleError, part, per_style
from .form import _draw

LEADS = ("phrase", "call", "out", "twin", "duel")   # twin, duel: power rock's two leads
HORN_PARTS = ("punches", "coro", "riff", "out")
HIGH = 0.5


@dataclass(frozen=True)
class Part:
    name: str
    when: str = "any"
    weight: int = 1
    after: str | None = None
    lead: str = "phrase"
    horns: str = "out"
    guitar: str | None = None   # the group of the rhythm guitar's patterns it plays (power rock)
    why: str = ""

    def fits(self, energy):
        return self.when == "any" or (self.when == "high") == (energy >= HIGH)


@dataclass(frozen=True)
class Arrange:
    parts: tuple
    opens: str | None = None
    breaks: int = 0
    build: str | None = None    # the part a quiet section's last phrase may turn into before a loud one
    builds: int = 0             # % of those sections that build
    stop: bool = False          # its breaks are stops (the one, ringing) rather than the clave's strokes


def _arrange(style):
    d, where = part(style, "arrange"), f"{style}: arrange"
    if not d:
        return None
    extra = set(d) - {"why", "parts", "opens", "breaks", "build", "builds", "stop"}
    if extra:
        raise StyleError(f"{where}: unknown part {sorted(extra)[0]!r} (known: parts, opens, breaks, build, builds, "
                         "stop)")
    parts = []
    for n, p in d.get("parts", {}).items():
        if n == "why":
            continue
        extra = set(p) - {"when", "weight", "after", "lead", "horns", "guitar", "why"}
        if extra:
            raise StyleError(f"{where}.parts.{n}: unknown part {sorted(extra)[0]!r}")
        x = Part(n, **{k: v for k, v in p.items()})
        if x.when not in ("low", "high", "any") or x.lead not in LEADS or x.horns not in HORN_PARTS or not (
                isinstance(x.weight, int) and x.weight >= 0):
            raise StyleError(f"{where}.parts.{n}: when low, high or any; lead among {', '.join(LEADS)}; horns among "
                             f"{', '.join(HORN_PARTS)}; a whole-number weight")
        parts.append(x)
    names = {p.name for p in parts}
    if not parts or d.get("opens") not in names | {None} or any(p.after not in names | {None} for p in parts):
        raise StyleError(f"{where}: at least one part; opens and after name parts")
    for k in ("breaks", "builds"):
        if not isinstance(d.get(k, 0), int) or not 0 <= d.get(k, 0) <= 100:
            raise StyleError(f"{where}.{k}: a share in %, 0 to 100")
    if d.get("build") not in names | {None} or bool(d.get("build")) != bool(d.get("builds")):
        raise StyleError(f"{where}.build: a part, with its share in \"builds\"")
    if not isinstance(d.get("stop", False), bool):
        raise StyleError(f"{where}.stop: true or false")
    return Arrange(tuple(parts), d.get("opens"), d.get("breaks", 0), d.get("build"), d.get("builds", 0),
                   d.get("stop", False))


ARRANGE = per_style(_arrange)   # None: every member plays throughout


def phrase_parts(rng, ar, sections, phrase, end):
    """(a part a phrase as [(first bar, Section, Part)], the bars that close on a break, lines). `end`: the play's
    last bar, which never breaks."""
    out, breaks, lines, prev = [], [], [], None
    by = {p.name: p for p in ar.parts}
    for i, s in enumerate(sections):
        for at in range(s.start, s.end, phrase):
            e = s.energy_at(at)
            if i == 0 and ar.opens:
                p = by[ar.opens]
            else:
                fits = [p for p in ar.parts if p.fits(e) and (p.after is None or prev and prev.name == p.after)]
                fits = fits or [p for p in ar.parts if p.fits(e)] or list(ar.parts)
                p = fits[_draw(rng, {k: q.weight for k, q in enumerate(fits)}) or 0]
            out.append((at, s, p))
            if p is not prev:
                lines.append(f"  bar {at + 1}: the {p.name}" + (f": {p.why}" if p.why else ""))
            prev = p
        if s.end < end and rng.rnd(100) < ar.breaks:
            breaks.append(s.end - 1)
            lines.append(f"  bar {s.end}: " + ("a stop, the band hitting the one together, the drums filling in"
                                               if ar.stop else "a break, the band hitting the clave's strokes together"))
    if ar.build:                         # a quiet section's last phrase builds into a loud one (the pre-chorus)
        build = by[ar.build]
        for i, s in enumerate(sections[:-1]):
            last = max(k for k, (at, x, _) in enumerate(out) if x is s)
            at, _, p = out[last]
            nxt = next(q for _, x, q in out if x is sections[i + 1])
            if p.when == "low" and nxt.when == "high" and p is not build and rng.rnd(100) < ar.builds:
                out[last] = (at, s, build)
                lines = [ln for ln in lines if not ln.startswith(f"  bar {at + 1}: the ")]
                lines.append(f"  bar {at + 1}: the {build.name}" + (f": {build.why}" if build.why else ""))
    return out, breaks, lines


def check_parts(parts, ar):
    """None when the parts follow the style's rules, else the reason."""
    for k, (at, s, p) in enumerate(parts):
        if k and p.after and parts[k - 1][2].name != p.after and any(
                q.fits(s.energy_at(at)) and q.after is None for q in ar.parts):
            return f"bar {at + 1}: the {p.name} not after the {p.after}"
    if ar.opens and parts and parts[0][2].name != ar.opens:
        return f"the play opens on the {parts[0][2].name}, not the {ar.opens}"
    return None


def cut(notes, lo, hi):
    """The notes with nothing sounding in [lo, hi): the ones starting there left out, the ones running in cut."""
    return [(st, min(length, lo - st) if st < lo else length, m) for st, length, m in notes
            if not lo <= st < hi]
