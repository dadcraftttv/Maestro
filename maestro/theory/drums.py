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
GMD's, as a drummer's dynamics.

A programmed drummer (trap, task 3.4a's second round: GMD's human hip hop wasn't trap, DadCraft, Oct 24) plays the
entry's own written patterns instead (members.drums.patterns): kick patterns over two bars (the 808 follows them),
hat patterns an 8th at a time with the rolls written in, louder as they run, the clap fixed on 3; machine-steady
velocities. A section draws a kick and a hat pattern by its energy and mostly keeps them; the kick may vary a note
from round to round. The kick and clap drop out for the end of a section before the next one, and the play may open
on the hats alone (the 808 rests with them). Synthwave's (task 3.4b) puts its snare on 2 and 4, half time (on 3) where
a calm kick pattern says so, and fills into a section with the toms, high to floor. The check rules out a hit off the grid or outside the clip, two of one drum on one
step, more than two hands at once and a groove without its backbeat (with a fixed backbeat: a snare anywhere
else). Tendencies, never a fixed part (decision 9)."""
import json, os
from dataclasses import dataclass, field

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
HANDS = {"snare", "ghost", "hat", "open", "crash", "ride", "roll", "cascade"} | set(TOMS)
FX = {"swell": 52, "riser": 58, "roll": 40}       # the programmed drummer's own voices beyond the kit
CASCADE = tuple(range(67, 59, -1))               # the falling cascade's eight steps (synth.CASCADE_NOTES)
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
    loud_time: dict = field(default_factory=dict)   # the timekeeping when the energy is up (power rock: the ride
    #                                                 or the crash in a chorus), else `time` throughout


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
    loud_time = {}
    for field_, into in (("time", time), ("loud time", loud_time)):
        for k, w in d.get(field_, {}).items():
            if k == "why":
                continue
            if k not in TIMES or not isinstance(w, int) or w < 0:
                raise StyleError(f"{where}.{field_}.{k}: one of {', '.join(TIMES)}, a whole-number weight")
            into[k] = w
    return Drummer(grooves, stay, odds, time, loud, fills, tuple(s for s, _ in parts),
                   d.get("busy", 100), d.get("fills", 70), d.get("rolls", 0), backbeat == "fixed",
                   d.get("turns", 0), tuple(rates.items()), loud_time)


@dataclass(frozen=True)
class KickPattern:
    """Two bars of kicks, as the 16ths of each bar; `snare`: the beats its snare plays on (none: the drummer's)."""
    name: str
    bars: tuple
    weight: int = 1
    when: str = "any"
    why: str = ""
    snare: tuple = ()


@dataclass(frozen=True)
class HatPattern:
    """Two bars of hats, an 8th at a time (HAT_CELLS)."""
    name: str
    bars: tuple
    weight: int = 1
    when: str = "any"
    why: str = ""


# an 8th of hats: (16ths... as steps into the 8th, a roll's rate or None); "o" an open hat
HAT_CELLS = {"-": (), "x": (0,), "xx": (0, 6), "o": (0,), "3": (0, 4, 8), "4": (0, 3, 6, 9), "6": (0, 2, 4, 6, 8, 10)}
ROLLS = ("3", "4", "6")
STEADY = {"kick": 118, "snare": 112, "beat": 96, "eighth": 86, "sixteenth": 70, "open": 88}


@dataclass(frozen=True)
class Programmed:
    """A drummer playing the style's own written patterns (trap, synthwave)."""
    kicks: tuple
    hats: tuple
    stay: int = 4        # times more likely a section keeps the patterns of the one before
    vary: int = 25       # % of rounds the kick moves, adds or drops a note
    drop: int = 50       # % of section ends where the kick and clap (and the 808) drop out for the last bar
    intro: int = 4       # bars of hats alone at the play's start (0: none)
    fixed: tuple = ((3,),)   # the sets of beats a bar's snares may fall on (the check)
    turns: int = 0
    roll: int = 60       # % of section ends with a snare roll over the last two beats (16ths, then 32nds)
    cascade: int = 50    # % of 8-bar runs (a section's end, when it has no roll) ending in the falling cascade
    cymbals: int = 100   # % of new sections entered with a reversed cymbal swelling in and a crash
    riser: int = 50      # % of section ends with a riser over their last two bars
    snare: tuple = (3,)  # the beats the snare (or clap) plays on, unless a kick pattern says its own
    voice: str = "clap"  # what the backbeat is called in words
    toms: int = 0        # % of section ends with a tom fill (synthwave), when there's no roll


def _programmed(style, d, where):
    p = d["patterns"]
    kicks, hats = [], []
    for kind, out, cls in (("kicks", kicks, KickPattern), ("hats", hats, HatPattern)):
        for n, x in p.get(kind, {}).items():
            if n == "why":
                continue
            w = f"{where}.patterns.{kind}.{n}"
            bars = x.get("bars")
            if not isinstance(bars, list) or len(bars) != 2:
                raise StyleError(f"{w}: two bars")
            if kind == "kicks":
                if any(not isinstance(b, list) or b != sorted(set(b)) or any(not 0 <= i < 16 for i in b) for b in bars):
                    raise StyleError(f"{w}: each bar the kick's 16ths, 0-15, in order")
                bars = tuple(tuple(b) for b in bars)
            else:
                cells = [b.split() if isinstance(b, str) else None for b in bars]
                if any(c is None or len(c) != 8 or any(t not in HAT_CELLS for t in c) for c in cells):
                    raise StyleError(f"{w}: each bar eight 8ths, each one of {' '.join(HAT_CELLS)}")
                bars = tuple(tuple(c) for c in cells)
            if x.get("when", "any") not in ("low", "high", "any") or not isinstance(x.get("weight", 1), int):
                raise StyleError(f"{w}: when low, high or any; a whole-number weight")
            extra = set(x) - {"bars", "weight", "when", "why"} - ({"snare"} if kind == "kicks" else set())
            if extra:
                raise StyleError(f"{w}: unknown part {sorted(extra)[0]!r}")
            more = {"snare": _beats(x["snare"], f"{w}.snare")} if "snare" in x else {}
            out.append(cls(n, bars, x.get("weight", 1), x.get("when", "any"), x.get("why", ""), **more))
    if not kicks or not hats:
        raise StyleError(f"{where}.patterns: both kicks and hats")
    for k in ("stay", "vary", "drop", "intro", "roll", "cascade", "cymbals", "riser", "toms"):
        if k in p and (not isinstance(p[k], int) or isinstance(p[k], bool) or p[k] < 0):
            raise StyleError(f"{where}.patterns.{k}: a whole number, 0 or more")
    default = _beats(p.get("snare", [3]), f"{where}.patterns.snare")
    if p.get("voice", "clap") not in ("clap", "snare"):
        raise StyleError(f"{where}.patterns.voice: \"clap\" or \"snare\"")
    return Programmed(tuple(kicks), tuple(hats), p.get("stay", 4), p.get("vary", 25), p.get("drop", 50),
                      p.get("intro", 4), roll=p.get("roll", 60), cascade=p.get("cascade", 50),
                      cymbals=p.get("cymbals", 100), riser=p.get("riser", 50),
                      snare=default, voice=p.get("voice", "clap"),
                      toms=p.get("toms", 0), fixed=tuple(sorted({k.snare or default for k in kicks})))


def _beats(b, where):
    if not isinstance(b, list) or not b or b != sorted(set(b)) or any(x not in (1, 2, 3, 4) for x in b):
        raise StyleError(f"{where}: the beats, 1 to 4, in order")
    return tuple(b)


def _on(beats):
    """Beats in words: "3", "2 and 4"."""
    return " and ".join(str(b) for b in beats)


def snares_of(dr, kick):
    return kick.snare or dr.snare


def _fit(rng, pats, energy, prev, stay):
    """A pattern for the section: by energy (low under 0.5), the one before `stay` times likelier."""
    ok = [x for x in pats if x.when == "any" or (x.when == "low") == (energy < 0.5)] or list(pats)
    return ok[_draw(rng, {i: x.weight * (stay if x == prev else 1) for i, x in enumerate(ok)})]


def _vary_kick(rng, bars):
    """A kick pattern with one note moved a 16th, added (a pickup) or left out (never the bar's first)."""
    b = [list(x) for x in bars]
    i = rng.rnd(2)
    r = rng.rnd(3)
    spare = [p for p in range(1, 16) if p not in b[i] and p not in (7, 8, 9)]   # the clap's 16th stays clear
    if r == 0 and len(b[i]) > 1:
        b[i].pop(1 + rng.rnd(len(b[i]) - 1))
        how = "a kick left out"
    elif r == 1 and spare:
        b[i] = sorted(b[i] + [spare[rng.rnd(len(spare))]])
        how = "a kick added"
    else:
        moves = [(j, p + d) for j, p in enumerate(b[i]) if j for d in (-1, 1)
                 if 0 < p + d < 16 and p + d not in b[i] and p + d not in (7, 8, 9)]
        if not moves:
            return bars, None
        j, q = moves[rng.rnd(len(moves))]
        b[i][j] = q
        b[i].sort()
        how = "a kick moved a 16th"
    return tuple(tuple(x) for x in b), how


def programmed_part(rng, dr, recs, met, phrase, end):
    """The programmed drummer over `recs` (a record a bar), up to step `end`: ([(step, length, MIDI note,
    velocity, voice)], [(section, line)]). Two bars a round; the clap (or snare) on its beats each bar: trap's on 3,
    synthwave's on 2 and 4, or on 3 under a half-time kick pattern."""
    hits, lines = [], []
    sec, kick, hat, drops, swelling, crash_here = None, None, None, 0, False, False
    first = recs[0]["section"] if recs else None
    intro = dr.intro if first and first.end - first.start >= 2 * max(1, dr.intro) else 0
    for r in recs[::2]:
        b, s, e = r["bar"], r["section"], r["energy"]
        at = b * met.bar
        if s is not sec:
            sec = s
            kick, hat = _fit(rng, dr.kicks, e, kick, dr.stay), _fit(rng, dr.hats, e, hat, dr.stay)
            lines.append((s, f"  drums: programmed; kick {kick.name}, hats {hat.name}, the {dr.voice} on "
                             f"{_on(snares_of(dr, kick))}"))
            dropping = s.end - s.start >= 4 and _chance(rng, dr.drop)
            if dropping:
                drops += 1
                lines.append((s, f"  drums, bar {s.end}: the kick and {dr.voice}{' (and the 808)' if dr.voice == 'clap' else ''} "
                                 f"drop out for the last bar"))
            more = s.end * met.bar < end                  # another section follows inside the clip
            rolling = more and _chance(rng, dr.roll)
            falling = more and not rolling and _chance(rng, dr.cascade)       # or the cascade ends the section
            tumbling = more and not rolling and not falling and dr.toms > 0 and _chance(rng, dr.toms)   # or a tom fill
            tom_beats = 2 if e >= 0.6 else 1
            rising = more and s.end - s.start >= 8 and _chance(rng, dr.riser)
            if rolling:
                lines.append((s, f"  drums, bar {s.end}: a snare roll into the next section"))
            if falling:
                lines.append((s, f"  drums, bar {s.end}: the falling cascade into the next section"))
            if tumbling:
                lines.append((s, f"  drums, bar {s.end}: a tom fill over the last {'two beats' if tom_beats == 2 else 'beat'}"
                                 f", high to floor, into the next section"))
            if rising:
                lines.append((s, f"  drums, bar {s.end - 1}: a riser over the last two bars"))
            crash_here, swelling = swelling, more and _chance(rng, dr.cymbals)   # this section's crash, the next's swell
            if swelling:
                lines.append((s, f"  drums, bar {s.end}: a reversed cymbal swells into the next section, a crash "
                                 f"on its one"))
        bars = kick.bars
        if b > s.start and _chance(rng, dr.vary):
            bars, how = _vary_kick(rng, kick.bars)
        cells, long, notes = {}, {}, {}

        def add(step, voice, vel, length=SIXTEENTH, note=None):
            if step < end:
                cells.setdefault(step, {})[voice] = max(1, min(127, round(vel * (0.9 + 0.2 * e))))
                long[step, voice] = length
                if note is not None:
                    notes[step, voice] = note
        for i in range(2):
            bar = b + i
            if bar >= s.end:
                break
            b0 = at + i * met.bar
            quiet = bar < intro or (dropping and bar == s.end - 1)
            last = bar == s.end - 1
            fill = ("roll" if rolling else "cascade" if falling else "toms" if tumbling else None) if last else \
                "cascade" if (bar + 1 - s.start) % phrase == 0 and _chance(rng, dr.cascade) else None
            cut = b0 + met.beats[4 - tom_beats] if fill == "toms" else b0 + met.beats[2] if fill else b0 + met.bar
            #     from 3 on (the toms: 3 or 4), the fill alone (and the clap on its beat)
            if fill == "cascade" and not last:
                lines.append((s, f"  drums, bar {bar + 1}: the falling cascade, the end of an 8-bar run"))
            if not quiet:
                for p in bars[i]:
                    if b0 + p * SIXTEENTH < cut:
                        add(b0 + p * SIXTEENTH, "kick", STEADY["kick"])
                for beat in snares_of(dr, kick):
                    if b0 + met.beats[beat - 1] <= cut:
                        add(b0 + met.beats[beat - 1], "snare", STEADY["snare"])
            if fill == "roll":                            # 16ths on 3, 32nds on 4, louder as it goes
                steps = [cut + k * SIXTEENTH for k in range(4)] + [cut + 24 + k * 3 for k in range(8)]
                for k, st in enumerate(steps):
                    add(st, "roll", 40 + 70 * k / (len(steps) - 1))
            elif fill == "toms":                          # 16ths stepping down the toms, two a drum
                steps = [cut + k * SIXTEENTH for k in range(4 * tom_beats)]
                for k, st in enumerate(steps):
                    add(st, TOMS[min(2, 3 * k // len(steps))], 96 + 20 * k / max(1, len(steps) - 1))
            elif fill == "cascade":                       # 16ths stepping down, each hit short and separate
                for k in range(8):
                    add(cut + k * SIXTEENTH, "cascade", 104, note=CASCADE[k])
            if last and rising:
                add(b0 - met.bar, "riser", 96, 2 * met.bar)
            if last and swelling:
                add(b0, "swell", 100, met.bar)
            row = list(hat.bars[i])
            run = []
            for c, tok in enumerate(row):
                s8 = b0 + c * 2 * SIXTEENTH
                if s8 >= cut:
                    break
                if tok in ROLLS:
                    run.append((s8, tok))
                    continue
                if run:
                    _roll(add, run)
                    run = []
                for k, off in enumerate(HAT_CELLS[tok]):
                    v = "open" if tok == "o" else "hat"
                    add(s8 + off, v, STEADY["open"] if v == "open" else
                        STEADY["beat"] if c % 2 == 0 and k == 0 else STEADY["eighth"] if k == 0 else STEADY["sixteenth"])
            if run:
                _roll(add, run)
        if crash_here and b == s.start:                   # the crash takes the hat's place on the one
            cells.get(at, {}).pop("hat", None)
            cells.get(at, {}).pop("open", None)
            add(at, "crash", 100)
        for step in sorted(cells):
            hits += [(step, long[step, v], notes.get((step, v)) or KIT.get(v) or FX[v], vel, v)
                     for v, vel in cells[step].items()]
    if intro:
        lines.insert(1 if lines else 0, (recs[0]["section"], f"  drums, bar 1: the hats alone for {intro} bars, the "
                                                            f"kick, clap and 808 come in on bar {intro + 1}"))
    return hits, lines


def _roll(add, run):
    """A roll over consecutive 8ths: its hits, louder as it runs (55 up to 100)."""
    steps = [s8 + off for s8, tok in run for off in HAT_CELLS[tok]]
    for k, st in enumerate(steps):
        add(st, "hat", 55 + 45 * k / max(1, len(steps) - 1))


def quiet_spans(hits, met, end):
    """The half bars with neither kick nor snare (an intro, a drop-out): [(start, end)] steps, joined up."""
    half = met.bar // 2
    busy = {h[0] // half for h in hits if h[4] in ("kick", "snare")}
    out = []
    for i in range(end // half):
        if i not in busy:
            if out and out[-1][1] == i * half:
                out[-1] = (out[-1][0], (i + 1) * half)
            else:
                out.append((i * half, (i + 1) * half))
    return out


def _drummer_for(style):
    d = part(style, "members", "drums")
    if "patterns" in d:
        return _programmed(style, d, f"{style}: members.drums")
    return _drummer(style)


DRUMMER = {s: _drummer_for(s) for s in STYLES}   # None: the style's band has no kit (salsa)


def _chance(rng, pct):
    return rng.rnd(1000) < round(10 * pct)


def _vel(dr, voice, p16, energy):
    """GMD's velocity for the voice on that 16th (or a plain one), a little louder with more energy."""
    v = dr.loud.get(voice if voice != "open" else "hat", [0] * 16)[p16] or LOUD[voice]
    if voice == "ghost":
        v = min(v, LOUD["ghost"] + 15)
    return max(1, min(127, round(v * (0.8 + 0.4 * energy))))


def _time(rng, dr, energy, loud=None):
    """The section's timekeeping, (voice, rate): busier as the energy rises; its own when loud (power rock's: `loud`
    the section's part, else by the energy)."""
    lean = {"quarter": 1.5 - energy, "8th": 1.0, "16th": 0.5 + energy}
    time = dr.loud_time if dr.loud_time and (energy >= 0.5 if loud is None else loud) else dr.time
    k = _draw(rng, {k: round(10 * w * lean[k.split()[1]]) for k, w in time.items()})
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
    if isinstance(dr, Programmed):
        return programmed_part(rng, dr, recs, met, phrase, end)
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
            sec, keeper = s, _time(rng, dr, e, r.get("loud"))
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


# ---- double bass (power rock's second round, DadCraft, Oct 26: "double bass pedals and dueling guitars") ----

@dataclass(frozen=True)
class Double:
    """Two feet on two kicks: `runs` the kick patterns a loud phrase draws ({name: (16ths of a bar, weight)}), the
    parts that play them, and `bursts`: % of the other phrases whose last beat runs 16ths into the next."""
    runs: tuple
    parts: tuple
    bursts: int = 0
    stay: int = 3


def _double(style):
    d, where = part(style, "members", "drums").get("double"), f"{style}: members.drums.double"
    if not d:
        return None
    runs = []
    for n, r in d.get("runs", {}).items():
        if n == "why":
            continue
        ks, w = r.get("kicks", []), r.get("weight", 1)
        if not ks or ks != sorted(set(ks)) or ks[0] != 0 or ks[-1] >= 16 or not isinstance(w, int) or w < 1:
            raise StyleError(f"{where}.runs.{n}: kicks as a bar's 16ths in order from 0, a whole-number weight")
        runs.append((n, tuple(ks), w, r.get("why", "")))
    if not runs or not isinstance(d.get("parts"), list) or not 0 <= d.get("bursts", 0) <= 100:
        raise StyleError(f"{where}: runs, the parts that play them, bursts a share in %")
    return Double(tuple(runs), tuple(d["parts"]), d.get("bursts", 0))


DOUBLE = {s: _double(s) for s in STYLES}   # None: one foot


def double_kick(rng, dbl, dr, hits, phrases, met, skip=()):
    """The drums with both feet: in each phrase whose part plays double bass, its kicks swapped for a run (a run a
    phrase, the one before likelier kept); in the others, a burst of 16ths on some phrases' last beat. `phrases`:
    [(first step, last step, part's name, energy)]; `skip`: bars left alone (the stops and builds). (hits,
    [(first step, line)])."""
    out, lines, prev = list(hits), [], None

    def kick(st, e, strong):
        return (st, SIXTEENTH, KIT["kick"], max(1, round(_vel(dr, "kick", 0, e) * (1 if strong else 0.85))), "kick")
    for lo, hi, name, e in phrases:
        bars = [b for b in range(lo // met.bar, hi // met.bar) if b not in skip]
        if name in dbl.parts:
            k = _draw(rng, {i: w * (dbl.stay if n == prev else 1) for i, (n, _, w, _) in enumerate(dbl.runs)})
            n, ks, _, why = dbl.runs[k]
            prev = n
            for b in bars:
                b0 = b * met.bar
                out = [h for h in out if not (b0 <= h[0] < b0 + met.bar and h[4] == "kick")]
                out += [kick(b0 + x * SIXTEENTH, e, x % 4 == 0) for x in ks]
            lines.append((lo, f"  drums, bars {lo // met.bar + 1}-{hi // met.bar}: double bass, {n}"
                              + (f": {why}" if why else "")))
        elif bars and bars[-1] == hi // met.bar - 1 and _chance(rng, dbl.bursts):
            b0 = bars[-1] * met.bar + met.beats[-1]
            out = [h for h in out if not (b0 <= h[0] < b0 + 24 and h[4] == "kick")]
            out += [kick(b0 + x, e, x == 0) for x in range(0, 24, SIXTEENTH)]
            lines.append((lo, f"  drums, bar {bars[-1] + 1}: a burst of double-bass 16ths into the next phrase"))
    return sorted(out, key=lambda h: (h[0], h[2])), lines


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
        if any(v in TOMS for v in cells) or not {"kick", "snare"} & set(cells):   # a fill, or a drop-out
            continue
        if "snare" not in cells:
            return f"bar {u // met.bar + 1}: no backbeat"
    if fixed:   # each bar's snares on one of the allowed sets of beats, and on every one of that set
        sets = fixed if isinstance(fixed, tuple) else ((3,),) if half else ((2, 4),)
        half_bar = met.bar // 2
        loud = {s // half_bar for s, c in at.items() if {"kick", "snare"} & set(c)}
        for b0 in range(0, end - met.bar + 1, met.bar):
            on = {s for s, c in at.items() if b0 <= s < b0 + met.bar and "snare" in c}
            if not on:
                continue
            fit = next((bs for bs in sets if on <= {b0 + met.beats[x - 1] for x in bs}), None)
            if fit is None:
                step = min(on - {b0 + met.beats[x - 1] for x in sets[0]} or on)
                return f"a snare off the backbeat on {met.count(step)} (bar {step // met.bar + 1})"
            for x in fit:
                step = b0 + met.beats[x - 1]
                if step // half_bar in loud and not {"snare", "roll", "cascade", *TOMS} & set(at.get(step, [])):
                    return f"no snare on {met.count(step)} (bar {step // met.bar + 1})"
    return None
