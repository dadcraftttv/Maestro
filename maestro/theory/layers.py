# SPDX-License-Identifier: GPL-3.0-or-later
"""Layering (task 3.6): which members play when, a phrase at a time, driven by the form's energy.

A style's "layers" gives each member the energy it tends to join at ("join"; the melody isn't listed: it sings
throughout). At each phrase's start the band holds as many members as the energy lets in: as it rises they join one
after another, the lower ones first, and as it eases they leave, the last in first out. The order is a tendency
("spread": how loose it is), never fixed (decision 9). The band is never thinner than "least" members, the melody
counted, and keeps one that carries the chords or the bass. A section that leads into a louder one may break down
for its last phrase ("breakdowns", % of such sections): only the "breakdown" members play, the melody rests.

From Tangerine (research round 6), for long plays: rotation ("rotate": [fewest, most] bars between swaps; [0, 0]
off): when the band's size holds, one member rests and one resting member comes back, the longest-playing likelier
to leave and the longest-resting likelier to come back; never on a section's first phrase. And slow change ("changes": [fewest, most] phrases between
changes): one detail of one member changes (a hit dropped, an arp note an octave or a chord tone away, a drum hit's
accent) and stays changed while the section's loop goes round, never two members at once.

Drawn after every member's notes, with its own seed, so the same seed with and without layering plays the same
notes (the A/B)."""
from dataclasses import dataclass, field

from ..stylebook import STYLES, StyleError, part
from .flow import chord_at
from .voicing import member_range

ANCHORS = ("bass", "pad", "keys", "guitar", "arp")   # members that carry the chords or the bass
CHANGES = {"arp": ("off", "octave", "note"), "bass": ("off",), "drums": ("off", "accent")}
ACCENT = 16   # velocity a changed drum hit gains or loses


@dataclass(frozen=True)
class Layers:
    join: dict                          # member: the energy (0-1) it tends to join at
    spread: float = 0.1                 # how loose the joining order is, in energy
    least: int = 2                      # members always playing, the melody counted (DadCraft, Oct 26)
    breakdowns: int = 0                 # % of sections before a louder one that break down for their last phrase
    breakdown: tuple = ()               # who plays in a breakdown
    rotate: tuple = (0, 0)              # bars between swaps
    changes: tuple = (0, 0)             # phrases between slow changes


@dataclass
class Phrase:
    at: int                             # its first bar
    bars: int
    section: object
    playing: frozenset                  # the listed members playing (the melody apart)
    melody: bool = True
    said: list = field(default_factory=list)


def _range(v, where):
    if not (isinstance(v, list) and len(v) == 2 and all(isinstance(x, int) and x >= 0 for x in v) and v[0] <= v[1]):
        raise StyleError(f"{where}: [fewest, most], whole numbers, 0 for off")
    return tuple(v)


def _layers(style):
    d = part(style, "layers")
    return layers_from(d, set(part(style, "members")) - {"why", "melody"}, f"{style}: layers") if d else None


def layers_from(d, roles, where):
    """A style entry's "layers" as Layers, its members among `roles`; StyleError when it breaks the rules."""
    known = ("why", "join", "spread", "least", "breakdowns", "breakdown", "rotate", "changes")
    extra = set(d) - set(known)
    if extra:
        raise StyleError(f"{where}: unknown part {sorted(extra)[0]!r} (known: {', '.join(known[1:])})")
    join = d.get("join", {})
    if not join or any(r not in roles or not isinstance(e, (int, float)) or not 0 <= e <= 1 for r, e in join.items()):
        raise StyleError(f"{where}.join: the style's members (not the melody), each an energy 0 to 1")
    if not any(r in ANCHORS for r in join):
        raise StyleError(f"{where}.join: needs a member carrying the chords or the bass ({', '.join(ANCHORS)})")
    spread, least, breakdowns = d.get("spread", 0.1), d.get("least", 2), d.get("breakdowns", 0)
    if not (isinstance(spread, (int, float)) and 0 <= spread <= 0.5):
        raise StyleError(f"{where}.spread: an energy, 0 to 0.5")
    if not (isinstance(least, int) and 2 <= least <= len(join) + 1):
        raise StyleError(f"{where}.least: 2 up to the members listed, the melody counted")
    if not (isinstance(breakdowns, int) and 0 <= breakdowns <= 100):
        raise StyleError(f"{where}.breakdowns: a share in %, 0 to 100")
    breakdown = tuple(d.get("breakdown", ()))
    if any(r not in join for r in breakdown) or bool(breakdown) != bool(breakdowns) or (
            breakdown and (len(breakdown) < least or not any(r in ANCHORS for r in breakdown))):
        raise StyleError(f"{where}.breakdown: members from join, at least \"least\" of them and one carrying the "
                         "chords or bass, with its share in \"breakdowns\"")
    return Layers(dict(join), spread, least, breakdowns, breakdown, _range(d.get("rotate", [0, 0]), f"{where}.rotate"),
                  _range(d.get("changes", [0, 0]), f"{where}.changes"))


LAYERS = {s: _layers(s) for s in STYLES}   # None: every member plays throughout


def _the(roles, verb):
    """"the arp joins", "the arp, the drums join", "the drums join"."""
    many = len(roles) > 1 or roles[0] in ("drums", "keys", "horns")
    return f"the {', the '.join(roles)} {verb if many else verb + 's'}"


def _between(rng, lo_hi):
    lo, hi = lo_hi
    return lo + rng.rnd(hi - lo + 1)


def _weighted(rng, weights):
    """A key drawn by its whole-number weight (each at least 1)."""
    items = sorted(weights.items())
    r = rng.rnd(sum(w for _, w in items))
    for k, w in items:
        r -= w
        if r < 0:
            return k


def plan_layers(rng, ly, sections, phrase):
    """The band a phrase, over the whole play: [Phrase], each saying in words who joins, leaves or swaps."""
    listed = sorted(ly.join)
    playing, out = set(), []
    since = {r: 0 for r in listed}                   # phrases played or rested in a row
    swap_at = _between(rng, ly.rotate) if ly.rotate[1] else None

    def jitter(r):
        return ly.join[r] + ly.spread * (rng.rnd(201) - 100) / 100

    def anchored(band):
        return any(r in ANCHORS for r in band)

    for i, s in enumerate(sections):
        louder = i + 1 < len(sections) and sections[i + 1].energy > s.energy_at(s.end - 1)
        breaking = louder and s.bars > phrase and i > 0 and ly.breakdowns and rng.rnd(100) < ly.breakdowns
        for at in range(s.start, s.end, phrase):
            p = Phrase(at, min(phrase, s.end - at), s, frozenset())
            if breaking and at + phrase >= s.end:
                p.playing, p.melody = frozenset(ly.breakdown), False
                p.said.append(f"breakdown: {', '.join(sorted(ly.breakdown))} alone, the melody rests")
                out.append(p)
                continue
            e = s.energy_at(at)
            want = max(sum(1 for r in listed if ly.join[r] <= e), ly.least - 1)
            before = set(playing)
            while len(playing) < want:
                playing.add(min((r for r in listed if r not in playing), key=jitter))
            while len(playing) > want:
                keep = [r for r in playing if anchored(playing - {r})]
                playing.discard(max(keep, key=jitter))
            if not anchored(playing):
                playing.add(min((r for r in listed if r in ANCHORS), key=lambda r: ly.join[r]))
            back = leave = None
            if at > s.start and playing == before and swap_at is not None and at >= swap_at and \
                    len(playing) < len(listed):            # never a section's first phrase: the energy leads there
                back = _weighted(rng, {r: since[r] + 1 for r in listed if r not in playing})
                can = {r: since[r] + 1 for r in playing if anchored(playing - {r} | {back})}
                leave = _weighted(rng, can) if can else None   # one anchor and the melody: nothing can rest
            if leave:
                playing = (playing - {leave}) | {back}
                swap_at = at + _between(rng, ly.rotate)
                p.said.append(f"rotation: {_the([leave], 'rest')}, {_the([back], 'come')} back")
            else:
                joined, left = sorted(playing - before), sorted(before - playing)
                if before and joined:
                    p.said.append(_the(joined, "join"))
                if left:
                    p.said.append(_the(left, "rest"))
            for r in listed:
                since[r] = since[r] + 1 if (r in playing) == (r in before) else 1
            p.playing = frozenset(playing)
            out.append(p)
    return out


def check_layers(phrases, ly):
    """None when every phrase keeps the style's rules, else the reason."""
    for p in phrases:
        size = len(p.playing) + p.melody
        if size < ly.least:
            return f"bar {p.at + 1}: {size} member{'s' * (size != 1)} playing, fewer than {ly.least}"
        if not any(r in ANCHORS for r in p.playing):
            return f"bar {p.at + 1}: nothing carrying the chords or the bass"
        if not p.melody and not any(s.startswith("breakdown") for s in p.said):
            return f"bar {p.at + 1}: the melody rests outside a breakdown"
    return None


def silence(notes, lo, hi):
    """Notes (step, length, ...) with nothing sounding in [lo, hi)."""
    return [(st, min(length, lo - st) if st < lo else length, *rest) for st, length, *rest in notes
            if not lo <= st < hi]


def slow_changes(rng, ly, phrases, take, spans, key_at, met):
    """One detail of one member changed every few phrases, kept while its section goes round (Tangerine's slow
    change). Changes the take's lists in place; returns the words, one a change, with its phrase."""
    if not ly.changes[1]:
        return []
    said, due, bar = [], _between(rng, ly.changes), met.bar
    for k, p in enumerate(phrases):
        due -= 1
        if due > 0:
            continue
        due = max(1, _between(rng, ly.changes))
        who = [r for r in sorted(p.playing) if r in CHANGES and take.get(r)]
        if not who:
            continue
        role = who[rng.rnd(len(who))]
        lo, hi = p.at * bar, (p.at + p.bars) * bar
        notes = take[role]
        here = [n for n in notes if lo <= n[0] < hi and n[0] % bar and (role != "drums" or n[4] != "snare")]
        if not here:
            continue
        pick, kind = here[rng.rnd(len(here))], CHANGES[role][rng.rnd(len(CHANGES[role]))]
        offset, up = (pick[0] - lo) % (p.bars * bar), rng.rnd(2) == 1
        later = [q for q in phrases[k:] if q.section is p.section and role in q.playing]
        at = {q.at * bar + offset for q in later if q.bars == p.bars} | {pick[0]}
        r = member_range(role) if role != "drums" else None
        changed = []
        for n in notes:
            if n[0] not in at or (role == "drums" and n[2] != pick[2]):
                changed.append(n)
                continue
            if kind == "off":
                continue
            if kind == "accent":
                n = (*n[:3], max(1, min(127, n[3] + (ACCENT if up else -ACCENT))), *n[4:])
            elif kind == "octave":
                m = n[2] + (12 if up else -12)
                n = (n[0], n[1], m) if r.low <= m <= r.high else n
            else:                                    # the next tone of its chord, up or down
                ch, key = chord_at(spans, n[0]).chord, key_at(n[0])
                tones = {(key.tonic + t) % 12 for t in ch.tones}
                step = 1 if up else -1
                m = n[2] + step
                while (m % 12) not in tones:
                    m += step
                n = (n[0], n[1], m) if r.low <= m <= r.high else n
            changed.append(n)
        take[role][:] = changed
        what = {"off": "a hit dropped", "accent": f"a hit {'louder' if up else 'softer'}",
                "octave": f"a note an octave {'up' if up else 'down'}",
                "note": f"a note a chord tone {'up' if up else 'down'}"}[kind]
        said.append((p, f"slow change: the {role}, {what} at beat {offset % bar // met.unit + 1} of bar "
                        f"{offset // bar + 1}, kept for the section"))
    return said
