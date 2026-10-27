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
import re

from ..stylebook import BOOK, MEMBER, ROLES, derive

STEPS = 5
# direction: (axis, sign); opposites share an axis and cancel
DIRECTIONS = {"energetic": ("energy", 1), "minimal": ("energy", -1), "funky": ("funk", 1),
              "soulful": ("soul", 1), "sophisticated": ("polish", 1)}
BUSY = 4             # a step of the drummer's busyness (minimal +5 at 80%: 60% lost power rock's backbeat)
ROTATE = 0.4         # minimal's step of the bars between rotation's swaps (+5: three times as long)
JOIN = 0.05         # a step of when the later members join (minimal later, energetic sooner)
LEAN = 0.04         # a step of the band's energy (minimal down, energetic up), as the room's 0-1
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


def length(o):
    """An option's mean note length in 16ths (a note left ringing counts a bar); None for kits' bars."""
    hits = o.get("notes") or o.get("hits")
    if not hits:
        return None
    return sum(16 if h[1] is None else h[1] for h in hits) / len(hits)


PUSHED = ("bass", "drums")
FLOOR = ("pad", "bass")   # the band's floor: it joins as it did, so a short calm play still has it   # funky's pushes: the bass's and kick's last hit on a beat a 16th early, ghost hats


def _pushed(o):
    """The option with its last hit on a beat (past the one) a 16th early, or None when it has none to push."""
    new = copy.deepcopy(o)
    if "notes" in new or "hits" in new:
        hits = new.get("notes") or new.get("hits")
        on = [i for i, h in enumerate(hits) if h[0] % 4 == 0 and h[0] > 0 and h[0] - 1 not in {x[0] for x in hits}]
        if not on:
            return None
        i = on[-1]
        hits[i][0] -= 1
        if i and hits[i - 1][1] is not None and hits[i - 1][0] + hits[i - 1][1] > hits[i][0]:
            hits[i - 1][1] = max(1, hits[i][0] - hits[i - 1][0])
        if hits[i][1] is not None:
            hits[i][1] += 1
        return new
    bars = new.get("bars", [])
    if bars and all(isinstance(b, str) for b in bars):     # hats: a ghost 16th before beats 3 and the next one
        out = []
        for b in bars:
            t = b.split()
            for j in (3, 7):
                if j < len(t) and t[j] == "x":
                    t[j] = "xx"
            out.append(" ".join(t))
        if out == bars:
            return None
        new["bars"] = out
        return new
    moved = False
    for b in bars:
        on = [s for s in b if s % 4 == 0 and s > 0 and s - 1 not in b]
        if on:
            b[b.index(on[-1])] -= 1
            moved = True
    return new if moved else None


def _push(d, funk):
    """Funky in a straight style (DadCraft, Oct 27: "small pushes"): beside each option, its pushed copy, weighed by
    the steps (at five half again the option's own weight)."""
    for k, o in [(k, o) for k, o in d.items() if isinstance(o, dict) and "weight" in o and o["weight"]]:
        p = _pushed(o)
        if p is not None and f"{k}, pushed" not in d:
            p["weight"] = max(1, round(o["weight"] * 0.3 * funk))
            p["why"] = f"funky's push of {k}"
            d[f"{k}, pushed"] = p


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
    clave = entry["time"].get("rhythm", {}).get("clave")   # a clave style's hits stay where its clave puts them
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
                _options(sub, length, soul)
                if funk and role in PUSHED and not clave:
                    _push(sub, funk)
    if isinstance(m.get("rate"), dict):
        m["rate"] = lean(m["rate"], lambda k: RATES.get(k), energy)
    if isinstance(m.get("variants"), dict):
        v = m["variants"]       # sophisticated: more of the variants, fewer plain repeats; minimal: the drops
        m["variants"] = {k: w if not w or k == "why" else max(1, round(w * (1 - 0.12 * polish if k == "again" else
                                                              1 + 0.25 * polish if k == "approach" else 1)
                                                         * (1 - 0.1 * energy if k == "drop" else 1)))
                         for k, w in v.items()}
    for k, per in (("busy", BUSY), ("fills", 4)):
        if k in m or role == "drums" and energy:
            m[k] = _clamp(m.get(k, {"busy": 100, "fills": 70}[k]) + per * energy, MEMBER[k])
    if "level" in m:
        m["level"] = _clamp(m["level"] + 3 * energy - soul, MEMBER["level"])
    if role == "melody" and soul:   # soulful: the lead bends into some notes and shakes its long ones
        m["bends"] = _clamp(m.get("bends", 0) + 6 * soul, MEMBER["bends"])
        m["vibrato"] = m.get("vibrato", False) or soul >= 2
    accent = 2 * energy + 2 * funk + 3 * soul
    if accent:
        _feel(entry, role, accent)


def _coloured(chords, colours):
    """A family's chords with each plain triad coloured by one of the style's own colours (major: maj7, else add9;
    minor: 7, else add9); the rest as written."""
    def one(tok):
        m = re.fullmatch(r"([b#]?)([ivIV]+)", tok)
        if not m:
            return tok
        major = m.group(2).isupper()
        for c in (("maj7", "add9") if major else ("7", "add9")):
            if c in colours:
                return tok + c
        return tok
    return " ".join(one(t) for t in chords.split(" "))


def _harmony(entry, ax):
    prog = entry["harmony"].setdefault("progressions", {})
    v = dict(prog.get("variants", {}))
    from .flow import VARIANT_WEIGHTS
    full = {**VARIANT_WEIGHTS, **{k: w for k, w in v.items() if k != "why"}}
    polish, soul = ax["polish"], ax["soul"]
    if not polish and not soul:
        return
    prog["variants"] = {k: w if not w else max(1, round(4 * w * (1 - 0.12 * polish if k == "again" else
                                                                 1 + 0.25 * polish + (0.8 * polish + 0.05 * soul
                                                                                      if k == "colour" else 0))))
                        for k, w in full.items()}
    fams = prog.get("families")
    colours = set(entry["harmony"].get("vocabulary", {}).get("colours", []))
    if polish and isinstance(fams, dict):      # sophisticated: each loop beside its coloured copy
        for k, f in [(k, f) for k, f in fams.items() if isinstance(f, dict) and f.get("weight")]:
            c = _coloured(f["chords"], colours)
            if c != f["chords"] and f"{k}, coloured" not in fams:
                fams[f"{k}, coloured"] = {**copy.deepcopy(f), "chords": c, "weight": max(1, round(f["weight"] * 0.3 * polish)),
                                          "why": f"sophisticated's colouring of {k}"}
    if polish:      # sophisticated travels further: key changes a little more often
        form = entry.setdefault("form", {})
        form["change"] = min(100, form.get("change", 20) + 4 * polish)


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
    if band["energy"]:      # the band's energy: minimal plays calmer and thinner, energetic hotter and fuller
        entry.setdefault("form", {})["lean"] = round(LEAN * band["energy"], 2)
        ly = entry.get("layers")
        if ly:
            lean = entry["form"]["lean"]   # the floor joins at the same felt energy; the rest later (or sooner)
            ly["join"] = {k: v if k == "why" else round(max(0.0, min(1.0, v + lean if k in FLOOR
                                                                     else v - JOIN * band["energy"])), 2)
                          for k, v in ly["join"].items()}
            ly["breakdowns"] = _clamp(ly.get("breakdowns", 0) - 6 * band["energy"], (0, 100))
            if band["energy"] < 0 and any(ly.get("rotate", [0, 0])):   # minimal swaps less: a calm band stays put
                ly["rotate"] = [round(b * (1 - ROTATE * band["energy"])) for b in ly["rotate"]]
    rhythm = entry["time"].setdefault("rhythm", {})   # funkier plays across the beat: a lower lift
    if band["funk"]:
        rhythm["lift"] = max(0, rhythm.get("lift", 2) - round(0.4 * band["funk"]))
    return derive(new, entry)
