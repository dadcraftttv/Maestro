# SPDX-License-Identifier: GPL-3.0-or-later
"""The drummer (task 3.3), starting from the Groove MIDI Dataset.

`maestro/data/grooves.json` holds what GMD's drummers do (our own counts, `tools/groove_stats.py`): the backbones
they play (kick and snare on the 8ths), how often a bar keeps the one before, the odds of every other hit on each
16th (kick pickups, ghost notes, open hats), what keeps time and how fast, how loud each hit is, and their fills.
A style's entry (members.drums) names the GMD styles it draws on, with weights, and may lean the timekeeping its own
way (trap's 16th hats), make the drummer busier or plainer, and set how often a phrase ends in a fill or (trap) a
hat roll. Trap's also fixes the snare on the backbeat (on 3, at half time) and lets the hats turn: a beat at
another rate (triplets, 32nds) inside the bar (task 3.4a).

The choose: a section picks its timekeeping; each bar keeps its groove or draws another, by GMD's odds; the odds add
the small hits, more of them as the energy rises; a phrase's last bar may end in a fill (its length, pace and drums
drawn from GMD's fills, the toms mostly going down), and a crash marks each section's start and the bar after a
fill. Half-time (trap) spreads a groove over two bars; a turning hat changes its rate for a beat, more often with
more energy. Every hit is on the grid (decision 13); the velocities are
GMD's, as a drummer's dynamics. The check rules out a hit off the grid or outside the clip, two of one drum on one
step, more than two hands at once and a groove without its backbeat (with a fixed backbeat: a snare anywhere
else). Tendencies, never a fixed part (decision 9)."""
import json, os
from dataclasses import dataclass

from ..stylebook import STYLES, StyleError, part
from .form import _draw
from .rhythm import VALUES, roll

HERE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "grooves.json")
with open(HERE) as _f:
    GMD = json.load(_f)["styles"]

SIXTEENTH = 6
# GM drum notes, the stand-in kit (sounds are Ouralia's, bucket 6)
KIT = {"kick": 36, "snare": 38, "ghost": 38, "hat": 42, "pedal": 44, "open": 46, "crash": 49, "ride": 51,
       "high tom": 50, "mid tom": 47, "floor tom": 43}
TOMS = ("high tom", "mid tom", "floor tom")
HANDS = {"snare", "ghost", "hat", "open", "crash", "ride"} | set(TOMS)
LOUD = {"kick": 100, "snare": 105, "ghost": 40, "hat": 75, "open": 85, "crash": 100, "ride": 80,
        "high tom": 95, "mid tom": 95, "floor tom": 100}
TIMES = tuple(f"{v} {r}" for v in ("hat", "ride", "crash") for r in ("quarter", "8th", "16th"))
SMALL = ("kick", "snare", "ghost", "open")   # the odds the drummer plays (crashes and toms belong to fills)
TURN_RATES = ("8th_triplet", "16th", "16th_triplet", "32nd", "32nd_triplet")   # what a hat may turn to for a beat
BACKBEAT = (4, 12)   # the snare on 2 and 4 of a groove: on 3 of each bar at half time
BLOCKS = {"kick": {"kick"}, "snare": {"snare", "ghost"}, "ghost": {"snare", "ghost"}, "open": {"open"}}


@dataclass(frozen=True)
class Groove:
    """A backbone: the kick's and the snare's 16ths in a bar (in two bars at half time, as 8ths)."""
    kick: tuple
    snare: tuple
    weight: int

    def name(self, met, half=False):
        def at(p):
            step = p * SIXTEENTH * (2 if half else 1)
            return met.count(step) + (f" (bar {step // met.bar + 1})" if half else "")
        return f"kick on {', '.join(at(p) for p in self.kick) or 'none'}, snare on {', '.join(at(p) for p in self.snare)}"


@dataclass(frozen=True)
class Drummer:
    grooves: tuple
    stay: float        # % of bars keeping the bar before's groove
    odds: dict         # voice: 16 %
    time: dict         # "hat 8th": weight
    loud: dict         # voice: 16 velocities (0: GMD never played it there)
    fills: dict        # beats, rate, drums (%), down (%)
    sources: tuple     # the GMD styles, for the words
    busy: int = 100    # % of GMD's odds played
    every: int = 70    # % of phrases ending in a fill
    rolls: int = 0     # % of phrases ending in a hat roll instead (trap)
    fixed: bool = False   # the snare only on the backbeat (trap: on 3 at half time)
    turns: int = 0     # % of beats the hats turn to another rate, at energy 0.5 (trap)
    turn_rates: tuple = ()   # ((rate, weight), ...)


def _mix(parts):
    """GMD's numbers for several styles, weighted: [(gmd style, weight)]."""
    total = sum(w for _, w in parts)
    grooves = {}
    for s, w in parts:
        for g in GMD[s]["grooves"]:
            k = (tuple(g["kick"]), tuple(g["snare"]))
            grooves[k] = grooves.get(k, 0) + g["share"] * w / total
    odds = {v: [sum(GMD[s]["odds"][v][i] * w for s, w in parts) / total for i in range(16)]
            for v in GMD[parts[0][0]]["odds"]}
    loud = {v: [round(sum(GMD[s]["loud"][v][i] * w for s, w in parts) / total) for i in range(16)]
            for v in GMD[parts[0][0]]["loud"]}
    time = {}
    for s, w in parts:
        for v, rates in GMD[s]["time"].items():
            if v != "none":
                for r, share in rates.items():
                    time[f"{v} {r}"] = time.get(f"{v} {r}", 0) + share * w / total
    fs = [(GMD[s]["fills"], w) for s, w in parts if GMD[s]["fills"]["takes"]]
    ft = sum(w for _, w in fs) or 1
    fills = {"down": sum(f["down"] * w for f, w in fs) / ft}
    for k in ("beats", "rate", "drums"):
        fills[k] = {}
        for f, w in fs:
            for x, share in f[k].items():
                fills[k][x] = fills[k].get(x, 0) + share * w / ft
    return (tuple(Groove(k, s, max(1, round(10 * share))) for (k, s), share in grooves.items()),
            sum(GMD[s]["stay"] * w for s, w in parts) / total, odds, time, loud, fills)


def _drummer(style):
    d, where = part(style, "members", "drums"), f"{style}: members.drums"
    if "grooves" not in d:
        return None
    parts = []
    for s, w in d["grooves"].items():
        if s == "why":
            continue
        if s not in GMD:
            raise StyleError(f"{where}.grooves: no GMD style {s!r} (known: {', '.join(GMD)})")
        if not isinstance(w, int) or w < 1:
            raise StyleError(f"{where}.grooves.{s}: a whole-number weight from 1")
        parts.append((s, w))
    grooves, stay, odds, time, loud, fills = _mix(parts)
    backbeat = d.get("backbeat", "free")
    if backbeat not in ("free", "fixed"):
        raise StyleError(f"{where}.backbeat: \"free\" or \"fixed\"")
    if backbeat == "fixed":
        grooves = tuple(g for g in grooves if g.snare == BACKBEAT)
        if not grooves:
            raise StyleError(f"{where}: none of its grooves keeps a plain backbeat")
    rates = {k: w for k, w in d.get("turn rates", {}).items() if k != "why"}
    for k, w in rates.items():
        if k not in TURN_RATES or not isinstance(w, int) or w < 0:
            raise StyleError(f"{where}.turn rates.{k}: one of {', '.join(TURN_RATES)}, a whole-number weight")
    if d.get("turns", 0) and not any(rates.values()):
        raise StyleError(f"{where}: turns need their \"turn rates\"")
    time = {k: max(0, round(v)) for k, v in time.items()}
    for k, w in d.get("time", {}).items():
        if k == "why":
            continue
        if k not in TIMES or not isinstance(w, int) or w < 0:
            raise StyleError(f"{where}.time.{k}: one of {', '.join(TIMES)}, a whole-number weight")
        time[k] = w
    return Drummer(grooves, stay, odds, time, loud, fills, tuple(s for s, _ in parts),
                   d.get("busy", 100), d.get("fills", 70), d.get("rolls", 0), backbeat == "fixed",
                   d.get("turns", 0), tuple(rates.items()))


DRUMMER = {s: _drummer(s) for s in STYLES}   # None: the style's band has no kit (salsa)


def _chance(rng, pct):
    return rng.rnd(1000) < round(10 * pct)


def _vel(dr, voice, p16, energy):
    """GMD's velocity for the voice on that 16th (or a plain one), a little louder with more energy."""
    v = dr.loud.get(voice if voice != "open" else "hat", [0] * 16)[p16] or LOUD[voice]
    if voice == "ghost":
        v = min(v, LOUD["ghost"] + 15)
    return max(1, min(127, round(v * (0.8 + 0.4 * energy))))


def _time(rng, dr, energy):
    """The section's timekeeping, (voice, rate): busier as the energy rises."""
    lean = {"quarter": 1.5 - energy, "8th": 1.0, "16th": 0.5 + energy}
    k = _draw(rng, {k: round(10 * w * lean[k.split()[1]]) for k, w in dr.time.items()})
    return tuple(k.split()) if k else ("hat", "8th")


def _fill(rng, dr, at, end, energy, big):
    """A fill from `at` to `end` (steps): [(step, voice)], with its words. A whole bar only into a new section
    (`big`), more likely with more energy; inside a section, a beat or two."""
    beats = _draw(rng, {b: round(10 * w * (energy * 2 if big else 0) if b == "4" else 10 * w)
                        for b, w in dr.fills["beats"].items()})
    beats = int(beats or 1)
    start = max(at, end - beats * 24)
    rate = _draw(rng, {r: round(10 * w) for r, w in dr.fills["rate"].items()}) or "16th"
    drums = {v: round(10 * w) for v, w in dr.fills["drums"].items() if v in ("snare", "kick") + TOMS}
    out, tom = [], 0
    for s in range(start, end, VALUES[rate]):
        v = _draw(rng, drums) or "snare"
        if v in TOMS:
            v, tom = TOMS[tom], min(2, tom + 1) if _chance(rng, dr.fills["down"]) else tom
        out.append((s, v))
    used = [v for v in ("snare",) + TOMS + ("kick",) if any(x == v for _, x in out)]
    return out, f"a fill of {beats} beat{'s' * (beats > 1)} in {rate.replace('_', ' ')}s ({', '.join(used)})"


def drum_part(rng, dr, recs, met, phrase, end, half=False):
    """The drums over the bars of `recs` (a record a bar: bar, section, energy), up to step `end`: ([(step, length,
    MIDI note, velocity, voice)], [(section, line in words)]). `half`: half-time, a groove over two bars."""
    span = 2 if half else 1                      # bars a groove covers
    scale = SIXTEENTH * span                     # steps a groove 16th covers
    unit = span * met.bar
    hits, lines = [], []
    groove, sec, keeper, after_fill, turned = None, None, None, False, {}
    for r in recs[::span]:
        b, s, e = r["bar"], r["section"], r["energy"]
        at = b * met.bar
        first = s is not sec
        if first:                                # a new section: its timekeeping, a groove (the last one likelier)
            sec, keeper = s, _time(rng, dr, e)
            groove = _draw(rng, {g: g.weight * (3 if g == groove else 1) for g in dr.grooves})
            lines.append((s, f"  drums: {keeper[0]} in {keeper[1]}s; {groove.name(met, half)}"))
        elif not _chance(rng, dr.stay):          # the bar keeps its groove as often as GMD's drummers do
            groove = _draw(rng, {g: g.weight for g in dr.grooves if g != groove}) or groove
        cells = {}                               # step: {voice: velocity}

        def add(step, voice, vel):
            cells.setdefault(step, {})[voice] = vel
        # a phrase's (or section's) last bar may end in a fill, or (trap) a hat roll on its last beat
        fill, fill_at, rolled = [], at + unit, False
        if ((b + span - s.start) % phrase == 0 or b + span >= s.end) and at + unit <= end:
            if _chance(rng, dr.rolls):
                fill_at, rolled = at + unit - (met.bar - met.beats[-1]), True
            elif _chance(rng, dr.every):
                fill, words = _fill(rng, dr, at + unit - met.bar, at + unit, e, b + span >= s.end)
                fill_at = fill[0][0]
                lines.append((s, f"  drums, bar {fill_at // met.bar + 1}: {words}"))
        for v, ps in (("kick", groove.kick), ("snare", groove.snare)):
            for p in ps:
                if at + p * scale < fill_at:
                    add(at + p * scale, v, _vel(dr, v, p, e))
        for v in SMALL:                          # the small hits, by GMD's odds, more with more energy
            if v == "snare" and dr.fixed:
                continue
            for p in range(16):
                step = at + p * scale
                taken = BLOCKS[v] & set(cells.get(step, {}))
                if step < fill_at and not taken and \
                        _chance(rng, dr.odds[v][p] * dr.busy / 100 * (0.5 + e)):
                    add(step, v, _vel(dr, v, p, e))
        keeps = []                               # the timekeeping, at its rate in the real bar, a beat at a time
        for beat in range(at, fill_at, VALUES["quarter"]):
            rate = keeper[1]
            if keeper[0] == "hat" and dr.turns and _chance(rng, dr.turns * (0.5 + e)):
                rate = _draw(rng, dict(dr.turn_rates))
                turned[id(s)] = (s, turned.get(id(s), (s, 0))[1] + 1)
            keeps += range(beat, min(beat + VALUES["quarter"], fill_at), VALUES[rate])
        for step in keeps:
            cell = cells.get(step, {})
            if keeper[0] != "hat":
                cell.pop("open", None)
            if "open" not in cell:
                add(step, keeper[0], _vel(dr, keeper[0], (step % met.bar) // SIXTEENTH, e))
        for c in cells.values():                 # an open hat only where the hat keeps time
            if keeper[0] != "hat":
                c.pop("open", None)
        if rolled:
            for step in roll(fill_at, at + unit - fill_at, "32nd_triplet" if rng.rnd(2) else "32nd"):
                add(step, "hat", _vel(dr, "hat", (step % met.bar) // SIXTEENTH, e))
            lines.append((s, f"  drums, bar {fill_at // met.bar + 1}: a hat roll into the next phrase"))
        for step, v in fill:
            add(step, v, _vel(dr, v, (step % met.bar) // SIXTEENTH, e))
        if first or after_fill:                  # a crash on the section's first beat, and after a fill
            cell = cells.setdefault(at, {})
            for v in ("hat", "ride", "open"):
                cell.pop(v, None)
            cell["crash"] = _vel(dr, "crash", 0, e)
        after_fill = bool(fill)
        for step in sorted(cells):
            if step < end:
                hits += [(step, SIXTEENTH, KIT[v], vel, v) for v, vel in cells[step].items()]
    for s, n in turned.values():                 # said with the section's timekeeping
        i = next(i for i, (x, _) in enumerate(lines) if x is s)
        rates = " or ".join(r.replace("_", " ") + "s" for r, w in dr.turn_rates if w)
        lines[i] = (s, f"{lines[i][1]}; the hats turn to {rates} on {n} beat{'s' * (n > 1)}")
    return hits, lines


def check_drums(hits, met, end, half=False, fixed=False):
    """None when the drums fit, else the reason: on the grid and inside the clip, one of each drum a step, two hands
    at most, and every groove keeping its backbeat (a bar with a fill aside); `fixed`: the snare on the backbeat
    every time and nowhere else."""
    at = {}
    for step, _, note, _, voice in hits:
        if step != int(step) or not 0 <= step < end:
            return f"a {voice} at step {step}: off the grid or outside the clip"
        cell = at.setdefault(step, [])
        if voice in cell or voice in ("snare", "ghost") and {"snare", "ghost"} & set(cell):
            return f"two {voice}s at once on {met.count(step)}"
        cell.append(voice)
    for step, cell in at.items():
        if len(HANDS & set(cell)) > 2:
            return f"{', '.join(sorted(HANDS & set(cell)))} at once on {met.count(step)} (bar {step // met.bar + 1}): " \
                   f"three hands"
    unit = met.bar * (2 if half else 1)
    for u in range(0, end - unit + 1, unit):
        cells = [v for s, c in at.items() if u <= s < u + unit for v in c]
        if any(v in TOMS for v in cells):
            continue
        if "snare" not in cells:
            return f"bar {u // met.bar + 1}: no backbeat"
    if fixed:
        scale = unit // 16
        on = {u + p * scale for u in range(0, end - unit + 1, unit) for p in BACKBEAT}
        for step, cell in sorted(at.items()):
            if "snare" in cell and step not in on:
                return f"a snare off the backbeat on {met.count(step)} (bar {step // met.bar + 1})"
        for step in sorted(on):
            if "snare" not in at.get(step, []) and not any(v in TOMS for v in at.get(step, [])):
                return f"no snare on {met.count(step)} (bar {step // met.bar + 1})"
    return None
