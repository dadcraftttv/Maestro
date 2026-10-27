# SPDX-License-Identifier: GPL-3.0-or-later
"""DNA nudges (task 3.9, DadCraft, Oct 26, from Fase Groove Piano's "Musical DNA": `docs/research.md` round 5): a
few named directions, each up to five steps, a click a step, on the whole band or one member.

A step shifts the style's tendencies, never its notes. It leans the style's own weighted choices (patterns, kick
bars, hat bars, the arp's rates, the variants) towards the ones that measure more of what the direction asks, and
moves a few of its numbers (accent, level, the drummer's busyness and fills, the rhythm's lift) inside the book's
bounds. An option the style weighs 0 stays 0 and one it plays stays playable (decision 9: no trait is a lock), and
nothing the style doesn't hold is added, so the rules never have to fight a nudge (decision 6). The nudged entry
is a style of its own, made with `stylebook.derive`: each member's rules travel with it, so a nudge stacks with a
blend (decision 4, 17).

DadCraft's calls (Oct 27): the directions as planned, five clicks each, and opposites cancel (more energetic and
more minimal pull on the same measures). Register isn't moved yet: the members' ranges are the theory's, not the
style's, so a register step waits until a style can set them.

    nudged("synthwave", [("band", "energetic", 2), ("bass", "funky", 1)])   # -> "synthwave~energetic+2,bass:funky+1"
"""
import copy

from ..stylebook import BOOK, MEMBER, ROLES, derive

STEPS = 5
# direction: (axis, sign); opposites share an axis and cancel
DIRECTIONS = {"energetic": ("energy", 1), "minimal": ("energy", -1), "funky": ("funk", 1),
              "soulful": ("soul", 1), "sophisticated": ("polish", 1)}
TILT = 0.4          # a step's lean: at five steps the option measuring most weighs 4x the one measuring least
RATES = {"32nd": 8, "16th": 4, "triplet": 3, "8th": 2, "quarter": 1}   # the arp's notes a beat
HARMONY = ("pad", "keys")   # a member nudge here moves the chords too; the band's always does


def _bars(o):
    """An option's bars as lists of 16th onsets: a pattern's notes or hits (one bar), a kick or hat pattern's bars."""
    if "notes" in o or "hits" in o:
        return [[h[0] for h in o.get("notes") or o.get("hits")]]
    out = []
    for b in o.get("bars", []):
        if isinstance(b, str):         # hats: an 8th a token, "xx" two 16ths, "3" "4" "6" rolls
            hits = []
            for i, t in enumerate(b.split()):
                hits += [2 * i] if t in ("x", "o") else [2 * i, 2 * i + 1] if t == "xx" else \
                    [2 * i + k / int(t) * 2 for k in range(int(t))] if t.isdigit() else []
            out.append(hits)
        else:
            out.append(list(b))
    return out


def density(o):
    b = _bars(o)
    return sum(map(len, b)) / len(b) if b else None


def syncopation(o):
    """The judge's syncopation (`maestro/judge.py`): the share of onsets off the beat with none on the next beat (the
    bar taken as a loop), a hit played ahead of its chord counting as one too. A straight run of 16ths has none."""
    bars = _bars(o)
    if not any(bars):
        return None
    hits = [h for h in (o.get("notes") or o.get("hits") or [])]
    sync = n = 0
    for bar in bars:
        on = set(bar)
        for i, s in enumerate(bar):
            n += 1
            ahead = i < len(hits) and hits[i][-1] == "ahead"
            sync += ahead or s % 4 != 0 and (int(s) // 4 * 4 + 4) % 16 not in on
    return sync / n


def lean(weights, measure, axis):
    """Whole-number weights leaned by `axis` steps towards the options measuring most. 0 stays 0; a weight over 0
    stays 1 or more; with nothing to tell the options apart they keep their weights."""
    note = {k: w for k, w in weights.items() if k == "why"}
    weights = {k: w for k, w in weights.items() if k != "why"}
    got = {k: measure(k) for k, w in weights.items()}
    vals = [v for v in got.values() if v is not None]
    if not axis:
        return {**weights, **note}
    if len(set(vals)) < 2:      # nothing to lean on: scaled like the leaned ones, so groups keep their balance
        return {**{k: 4 * w for k, w in weights.items()}, **note}
    lo, hi = min(vals), max(vals)
    mid = (lo + hi) / 2
    out = {}
    for k, w in weights.items():
        z = 0 if got[k] is None else (got[k] - mid) / (hi - lo) * 2     # -1 the least, 1 the most
        out[k] = 0 if w == 0 else max(1, round(4 * w * 2 ** (TILT * axis * z)))
    return {**out, **note}


def _options(d, measure, axis):
    """Lean a dict of named options (each with a "weight") in place, each "when" group (the high and low energy
    options) on its own: which group plays is the sections' call, not the nudge's."""
    opts = {k: o for k, o in d.items() if isinstance(o, dict) and "weight" in o}
    for when in {o.get("when") for o in opts.values()}:
        group = {k: o for k, o in opts.items() if o.get("when") == when}
        new = lean({k: o["weight"] for k, o in group.items()}, lambda k: measure(group[k]), axis)
        for k, w in new.items():
            group[k]["weight"] = w


def _clamp(v, rule):
    return max(rule[0], min(rule[1], v))


def _feel(entry, role, accent):
    feel = entry["time"].setdefault("feel", {})
    mine = feel.setdefault(role, {k: v for k, v in feel.get("*", {}).items() if k != "why"})
    mine["accent"] = max(0, mine.get("accent", 16) + accent)


def _member(entry, role, ax):
    m = entry["members"].get(role)
    if not isinstance(m, dict):
        return
    energy, funk, soul, polish = ax["energy"], ax["funk"], ax["soul"], ax["polish"]
    for kind in ("patterns", "shapes"):
        d = m.get(kind)
        if isinstance(d, dict):
            for sub in [d] + [v for v in d.values() if isinstance(v, dict) and "weight" not in v]:  # drums: kicks, hats
                _options(sub, density, energy)
                _options(sub, syncopation, funk)
    if isinstance(m.get("rate"), dict):
        m["rate"] = lean(m["rate"], lambda k: RATES.get(k), energy)
    if isinstance(m.get("variants"), dict):
        v = m["variants"]       # sophisticated: more of the variants, fewer plain repeats; minimal: the drops
        m["variants"] = {k: w if not w or k == "why" else max(1, round(w * (1 - 0.12 * polish if k == "again" else
                                                              1 + 0.25 * polish if k == "approach" else 1)
                                                         * (1 - 0.1 * energy if k == "drop" else 1)))
                         for k, w in v.items()}
    for k, per in (("busy", 8), ("fills", 6)):
        if k in m or role == "drums" and energy:
            m[k] = _clamp(m.get(k, {"busy": 100, "fills": 70}[k]) + per * energy, MEMBER[k])
    if "level" in m:
        m["level"] = _clamp(m["level"] + 3 * energy - soul, MEMBER["level"])
    accent = 2 * energy + 2 * funk + 3 * soul
    if accent:
        _feel(entry, role, accent)


def _harmony(entry, ax):
    prog = entry["harmony"].setdefault("progressions", {})
    v = dict(prog.get("variants", {}))
    from .flow import VARIANT_WEIGHTS
    full = {**VARIANT_WEIGHTS, **{k: w for k, w in v.items() if k != "why"}}
    polish, soul = ax["polish"], ax["soul"]
    if not polish and not soul:
        return
    prog["variants"] = {k: w if not w else max(1, round(4 * w * (1 - 0.12 * polish if k == "again" else
                                                                 1 + 0.25 * polish + (0.5 * soul if k == "colour"
                                                                                       else 0))))
                        for k, w in full.items()}


def axes(steps):
    """[(direction, steps)] -> {axis: steps}, opposites cancelled, each held to -5..5 (only energy goes below 0)."""
    ax = dict.fromkeys(("energy", "funk", "soul", "polish"), 0)
    for d, n in steps:
        a, sign = DIRECTIONS[d]
        ax[a] += sign * n
    return {a: max(-STEPS if a == "energy" else 0, min(STEPS, v)) for a, v in ax.items()}


def name(base, nudges):
    return base + "~" + ",".join(("" if t == "band" else f"{t}:") + f"{d}+{n}" for t, d, n in nudges)


def parse(spec):
    """"energetic=2,bass:funky=1" -> [("band", "energetic", 2), ("bass", "funky", 1)]."""
    out = []
    for item in filter(None, spec.split(",")):
        target, _, rest = item.rpartition(":")
        d, _, n = rest.partition("=")
        out.append((target or "band", d, int(n or 1)))
    return out


def nudged(base, nudges):
    """The style `base` nudged, as a style of its own in the book (made once); its name. `nudges`:
    [(target, direction, steps)], the target "band" or a member's role."""
    for t, d, n in nudges:
        if d not in DIRECTIONS:
            raise ValueError(f"no direction {d!r} (known: {', '.join(DIRECTIONS)})")
        if t != "band" and t not in ROLES:
            raise ValueError(f"no member {t!r} (known: band, {', '.join(ROLES)})")
        if not 0 <= n <= STEPS:
            raise ValueError(f"a nudge goes from 0 to {STEPS} steps, got {n}")
    new = name(base, nudges)
    if new in BOOK:
        return new
    entry = copy.deepcopy(BOOK[base])
    entry["style"] = new
    roles = [r for r in entry["members"] if r != "why"]
    band = axes([(d, n) for t, d, n in nudges if t == "band"])
    for role in roles:
        ax = axes([(d, n) for t, d, n in nudges if t in ("band", role)])
        _member(entry, role, ax)
    harmony = axes([(d, n) for t, d, n in nudges if t == "band" or t in HARMONY])
    _harmony(entry, harmony)
    rhythm = entry["time"].setdefault("rhythm", {})   # funkier plays across the beat: a lower lift
    if band["funk"]:
        rhythm["lift"] = max(0, rhythm.get("lift", 2) - round(0.4 * band["funk"]))
    return derive(new, entry)
