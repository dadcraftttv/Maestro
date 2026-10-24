# SPDX-License-Identifier: GPL-3.0-or-later
"""Rhythm and meter: where notes fall in the bar, and how each member plays them against the grid. Positions are
steps on a grid of 24 a beat (a quarter note), so 16ths, 32nds and both kinds of triplet land on it (DadCraft,
Oct 23: 24 rather than 12, for trap's 32nd rolls). MIDI keeps 480 ticks a beat: 20 ticks a step.

The check rules out what doesn't fit (off the grid, outside the bar, a part crossing the clave, two members out of
sync): every note lands on point on a grid step (decision 13). Everything else is a tendency a style sets: which
subdivisions it uses, how much it leans on strong beats or plays across them. The feel (swing as a grid choice,
accents, half-time) is per member, so trap's half-time drums and a straight synthwave bass can share one beat. The
choose picks onsets seeded, so a pattern is never locked (decision 9)."""
from dataclasses import dataclass, replace
from itertools import combinations

STEPS = 24                 # grid steps a beat (quarter note)
TICKS = 480                # MIDI ticks a beat
TICK = TICKS // STEPS      # 20 ticks a step

# Note values in steps.
VALUES = {
    "quarter": 24, "8th": 12, "16th": 6, "32nd": 3,
    "quarter_triplet": 16, "8th_triplet": 8, "16th_triplet": 4, "32nd_triplet": 2,
}


def from_tick16(i):
    """Today's composer position (`tick16`, 0-15 in a 4/4 bar) as a step."""
    return i * VALUES["16th"]


def to_step(tick):
    """A MIDI tick (480 a beat) as the nearest step, and how far off the grid it was (ticks, + late)."""
    s = (tick + TICK // 2) // TICK
    return s, tick - s * TICK


@dataclass(frozen=True)
class Meter:
    """A time signature and how its beats group: `groups` counts each beat in notes of the denominator (4/4 is
    1,1,1,1; 6/8 is 3,3; 7/8 is 2,2,3)."""
    num: int
    den: int
    groups: tuple

    def __post_init__(self):
        if sum(self.groups) != self.num:
            raise ValueError(f"groups {self.groups} don't add up to {self.num}")

    @property
    def name(self):
        return f"{self.num}/{self.den}"

    @property
    def unit(self):
        """Steps in one note of the denominator (a quarter: 24, an 8th: 12)."""
        return STEPS * 4 // self.den

    @property
    def bar(self):
        return self.num * self.unit

    @property
    def beats(self):
        """The step each beat starts on."""
        out, s = [], 0
        for g in self.groups:
            out.append(s)
            s += g * self.unit
        return tuple(out)

    @property
    def compound(self):
        return self.den == 8 and all(g == 3 for g in self.groups)

    def felt(self, pulse="full"):
        """The beats as they're felt: half-time feels every other beat, double-time adds the half beats between."""
        b = self.beats
        if pulse == "full":
            return b
        if pulse == "half":
            return b[::2]
        if pulse == "double":
            ends = b[1:] + (self.bar,)
            return tuple(sorted(set(b) | {(a + e) // 2 for a, e in zip(b, ends)}))
        raise ValueError(f"unknown pulse {pulse!r}")

    def backbeat(self, pulse="full"):
        """Where the snare falls: the felt beats between the strong ones (2 and 4 in 4/4; beat 3 in half-time; the
        second beat of each pair in 6/8 and 12/8; 2 and 3 in 3/4)."""
        f = self.felt(pulse)
        if len(f) == 1:
            return ()
        if len(f) % 2:
            return f[1:]
        return f[1::2]

    def weight(self, step, pulse="full"):
        """How strong a step is, 0-5: the bar's start 5, the middle beat 4 (when the felt beats split evenly), other
        felt beats 3, then the next two levels down (8ths 2 and 16ths 1 at full pulse), 32nds and triplets 0."""
        s = step % self.bar
        if s == 0:
            return 5
        f = self.felt(pulse)
        if s in f:
            return 4 if len(f) % 2 == 0 and s == f[len(f) // 2] else 3
        q = {"full": 12, "half": 24, "double": 6}[pulse]
        if s % q == 0:
            return 2
        if s % (q // 2) == 0:
            return 1
        return 0

    def count(self, step):
        """The step counted the way a player says it: "2 and", "3 e", "4 trip", "1 let"; in meters of 8ths the
        eighths are counted, "5 and"."""
        s = step % self.bar
        if self.den == 8:
            n, o = divmod(s, 12)
            return f"{n + 1}" + {0: "", 6: " and"}.get(o, f" +{o}/24")
        beat = max(i for i, b in enumerate(self.beats) if b <= s)
        o = s - self.beats[beat]
        return f"{beat + 1}" + {0: "", 6: " e", 12: " and", 18: " a", 8: " trip", 16: " let"}.get(o, f" +{o}/24")


METERS = {
    "4/4": Meter(4, 4, (1, 1, 1, 1)),
    "3/4": Meter(3, 4, (1, 1, 1)),
    "2/4": Meter(2, 4, (1, 1)),
    "5/4": Meter(5, 4, (1, 1, 1, 1, 1)),
    "6/8": Meter(6, 8, (3, 3)),
    "12/8": Meter(12, 8, (3, 3, 3, 3)),
    "7/8": Meter(7, 8, (2, 2, 3)),
}


def meter(text, groups=None):
    """"4/4", "6/8" ... from the table, or any n/d with its grouping given ("7/8" as 3,2,2)."""
    if groups is None and text in METERS:
        return METERS[text]
    num, den = (int(x) for x in text.split("/"))
    if groups is None:
        groups = (3,) * (num // 3) if den == 8 and num % 3 == 0 else (1,) * num
    return Meter(num, den, tuple(groups))


# ---- clave ----

@dataclass(frozen=True)
class Clave:
    """A timeline pattern the band lines up with. `onsets` in steps over `bars` bars of `meter`; a two-sided clave
    (son, rumba) has its 3-side in the first bar when the name says 3-2."""
    name: str
    meter: str
    bars: int
    onsets: tuple

    @property
    def length(self):
        return self.bars * METERS[self.meter].bar

    @property
    def two_sided(self):
        return self.bars == 2

    def flipped(self):
        """The other direction (3-2 to 2-3): the same pattern a bar later."""
        if not self.two_sided:
            return self
        a, b = self.name.rsplit("_", 1)
        half = self.length // 2
        return Clave(f"{a}_{b[::-1]}", self.meter, self.bars,
                     tuple(sorted((s + half) % self.length for s in self.onsets)))


def _clave(name, met, bars, eighths):
    return Clave(name, met, bars, tuple(e * 12 for e in eighths))


CLAVES = {c.name: c for base in (
    _clave("son_3-2", "4/4", 2, (0, 3, 6, 10, 12)),       # 1, 2 and, 4 | 2, 3
    _clave("rumba_3-2", "4/4", 2, (0, 3, 7, 10, 12)),     # 1, 2 and, 4 and | 2, 3
    _clave("bell_6/8", "12/8", 1, (0, 2, 4, 5, 7, 9, 11)),  # the standard bell, afro-cuban 6/8
) for c in (base, base.flipped())}


def _hits(onsets, clave):
    return sum(1 for s in {s % clave.length for s in onsets} if s in clave.onsets)


def check_clave(onsets, clave):
    """`onsets` in steps over the clave's bars. None when the part sits with the clave, else the reason: a two-sided part that fits the other direction
    better is crossed (cruzado), the one rhythm mistake salsa players don't forgive. A part that fits both sides
    the same (a tumbao repeating each bar) is fine."""
    if not clave.two_sided:
        return None
    other = clave.flipped()
    own, cross = _hits(onsets, clave), _hits(onsets, other)
    if cross > own:
        return (f"crossed: the part lines up with {other.name} ({cross} hits) better than the song's "
                f"{clave.name} ({own})")
    return None


# ---- the check ----

def check_onsets(onsets, met, bars=1, clave=None):
    """None when the onsets (steps from the first bar's start) fit, else the reason in plain words."""
    end = bars * met.bar
    for s in onsets:
        if s != int(s):
            return f"{s} is between grid steps"
        if not 0 <= s < end:
            return f"step {s} is outside the {bars} bar{'s' * (bars > 1)} of {met.name}"
    if len(set(onsets)) != len(onsets):
        return "two notes start on the same step"
    if clave is not None:
        return check_clave(onsets, clave)
    return None


# ---- style tendencies and the choose ----

@dataclass(frozen=True)
class Rhythm:
    """A style's rhythmic tendencies, as whole-number weights (0: the choose never picks it; the check still lets
    it through). A step weighs grid × (base + lift × its strength): high lift leans on the beat, low lift plays
    across it."""
    straight: int = 4    # steps on the straight grid (8ths, 16ths)
    triplet: int = 0     # steps only triplets reach
    fine: int = 0        # 32nds
    base: int = 1
    lift: int = 2
    clave: str | None = None   # the clave its members line up with

    def weigh(self, step, met, pulse="full"):
        s = step % met.bar
        if s % 6 == 0:
            g = self.straight
        elif s % 4 == 0:
            g = self.triplet
        elif s % 3 == 0:
            g = self.fine
        else:
            return 0
        return g * (self.base + self.lift * met.weight(s, pulse))


# First drafts for the four styles; the style book (bucket 3) refines them.
RHYTHM = {
    "plain": Rhythm(),
    "trap": Rhythm(triplet=2, fine=1, base=2, lift=1),       # 16ths with triplet and 32nd turns; sparse kicks
    "synthwave": Rhythm(lift=3),                              # straight 8ths and 16ths, on the beat
    "salsa": Rhythm(base=3, lift=1, clave="son_2-3"),         # anticipations; everything sits with the clave
    "power_rock": Rhythm(triplet=1, lift=3),                  # driving 8ths, the odd triplet fill
}


def _draw(rng, items):
    """One (item, weight) pair drawn by weight, seeded."""
    r = rng.rnd(sum(w for _, w in items))
    for i, (x, w) in enumerate(items):
        r -= w
        if r < 0:
            return i


def choose_onsets(rng, met, n, rhythm=RHYTHM["plain"], pulse="full", bars=1, keep=()):
    """n onsets over the bars, drawn by the style's weights without repeats, seeded; `keep` are onsets already
    placed (a downbeat, the clave's own notes) that count towards n. Sorted steps."""
    chosen = set(keep)
    pool = [(s, rhythm.weigh(s, met, pulse)) for s in range(bars * met.bar) if s not in chosen]
    pool = [(s, w) for s, w in pool if w > 0]
    while len(chosen) < n:
        if not pool:
            raise ValueError(f"the style can't place {n} onsets in {bars} bar{'s' * (bars > 1)} of {met.name}")
        chosen.add(pool.pop(_draw(rng, pool))[0])
    return sorted(chosen)


ROLL_RATES = ("16th", "16th_triplet", "32nd", "32nd_triplet")


def roll(start, steps, rate):
    """A run of repeated notes (trap's hat rolls) from `start` for `steps`, at one of ROLL_RATES."""
    if rate not in ROLL_RATES:
        raise ValueError(f"rolls go at {', '.join(ROLL_RATES)}")
    return list(range(start, start + steps, VALUES[rate]))


# ---- feel: how a member plays the grid ----

# DadCraft (Oct 23): every note lands on point on the grid. The members are machines, not human players: no
# member plays ahead or behind, nothing is loosened at random. Swing is a choice of grid point (the "and" moved to a
# later step), never an offset between steps.

@dataclass(frozen=True)
class Feel:
    """How one member plays the grid."""
    swing: int = 0       # steps the off-beat of each swung pair moves late, on the grid: 0 straight; for 8ths
                         # 4 is triplet swing and 6 hard (75:25); for 16ths 2 is triplet swing
    unit: int = 12       # the swung note in steps: 12 swings 8ths, 6 swings 16ths
    accent: int = 16     # velocity between the strongest step and the weakest
    pulse: str = "full"  # full, half (half-time) or double

    def __post_init__(self):
        if not 0 <= self.swing <= self.unit // 2:
            raise ValueError(f"swing goes from 0 to {self.unit // 2} steps for this unit")

    @property
    def ratio(self):
        return (self.unit + self.swing) / (2 * self.unit)


def swung(step, feel=Feel()):
    """Where the member plays a written step, in steps. Swing stretches the first half of each swung pair and
    squeezes the second, so the off-beat lands on its later step and everything between moves with it; a note that
    would land between steps is off the grid, and the check rules it out."""
    pair = 2 * feel.unit
    base, s = divmod(step, pair)
    split = feel.unit + feel.swing
    t = s * split / feel.unit if s < feel.unit else split + (s - feel.unit) * (pair - split) / feel.unit
    return base * pair + t


def place(step, feel=Feel()):
    """The MIDI tick a step is played on: exactly on the grid."""
    return round(swung(step, feel) * TICK)


def velocity(step, met, feel=Feel(), level=96):
    """The note's velocity: `level` on the bar's start, down by the accent as the step gets weaker."""
    w = met.weight(step, feel.pulse)
    return max(1, min(127, level - feel.accent * (5 - w) // 5))


# First feel drafts per style: "*" for every member, then a role's own. The style book (bucket 3) refines them.
FEEL = {
    "plain": {"*": Feel()},
    "trap": {"*": Feel(pulse="half"),                     # half-time
             "drums": Feel(pulse="half", accent=28)},     # hats ride 16ths under a half-time kick and snare
    "synthwave": {"*": Feel(accent=10)},                  # straight, even
    "salsa": {"*": Feel(accent=20),                       # straight, with the clave
              "percussion": Feel(accent=24)},
    "power_rock": {"*": Feel(accent=20),                  # straight, driving: big accents on the beat
                   "drums": Feel(accent=24),
                   "bass": Feel(accent=16)},
}


def feel_for(style, role, **override):
    """A member's feel: its style's draft for that role (or the style's "*"), with any control overriding it
    (`swing=4`)."""
    table = FEEL[style]
    return replace(table.get(role, table["*"]), **override)


def check_band_rhythm(parts, met, clave=None):
    """What's wrong with the band's timing over the same bars, as a list of reasons (empty: fine). `parts` is
    {role: (onsets, feel)}. Every note lands on a grid step; members playing the same written step land on the same
    step (a swung part over a straight one doesn't); with a two-sided clave on the timeline, every member lines up
    with it, whatever its style."""
    out = []
    for role, (on, f) in parts.items():
        off = [s for s in on if swung(s, f) != int(swung(s, f))]
        if off:
            out.append(f"the {role}'s note on {met.count(off[0])} lands between grid steps with its swing: off the grid")
    for (ra, (oa, fa)), (rb, (ob, fb)) in combinations(parts.items(), 2):
        apart = sorted(s for s in set(oa) & set(ob) if swung(s, fa) != swung(s, fb))
        if apart:
            out.append(f"the {ra} and the {rb} play {met.count(apart[0])} on different steps: out of sync")
    if clave is not None:
        for role, (on, _) in parts.items():
            why = check_clave(on, clave)
            if why:
                out.append(f"the {role} is {why}")
    return out


def explain_feel(feel):
    """The feel in plain words."""
    if feel.swing:
        what = "8ths" if feel.unit == 12 else "16ths" if feel.unit == 6 else f"{feel.unit}-step notes"
        text = f"swung {what} ({round(feel.ratio * 100)}:{round((1 - feel.ratio) * 100)})"
    else:
        text = "straight"
    text += ", on the grid"
    if feel.pulse != "full":
        text += f", {feel.pulse}-time"
    return text


def explain_onsets(onsets, met):
    """Onsets counted the way a player says them, bar by bar: "bar 1: 1, 2 and, 4 | bar 2: 2, 3"."""
    bars = {}
    for s in sorted(onsets):
        bars.setdefault(s // met.bar, []).append(met.count(s))
    return " | ".join(f"bar {b + 1}: " + ", ".join(c) for b, c in sorted(bars.items()))
