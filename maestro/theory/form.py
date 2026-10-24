# SPDX-License-Identifier: GPL-3.0-or-later
"""Form: sections, energy and key over a long play (~20 minutes), and motifs that develop as it goes (decision 9).

A play is planned one section at a time, as it goes, so the room (Ouralia's energy) keeps leaning it. Under the room
runs an energy arc of waves, each a few minutes of build and release, drawn fresh: no two plays rise and fall alike.
Each section sits on the arc by its kind (the composer's four: Home, Lift, Calm, Turn), may grow heavier as it goes
(a style's tendency, a draft from one S3&K zone in `docs/taste.md`, not a rule), and may move the key at its start. Motifs live in scale steps, so they carry across key
changes, and develop each time they come back: early statements stay close, later ones travel further, and an old
motif is reborn from its own fragment.

The checks rule out what doesn't fit, with the reason (a Lift that doesn't lift, a Calm too loud for a calm moment,
a key change too soon or too far from home, a motif off the grid or no longer heard as itself). Everything else is a
tendency a style sets, never a lock: a style's modes are the ones it leans to, and a bright key over trap stays
possible (DadCraft, Oct 23). The choose picks among what's left, seeded."""
from dataclasses import dataclass, field

from ..stylebook import table
from .pitch import PARENT, SCALES, Key
from .rhythm import METERS, STEPS, VALUES

KINDS = ("home", "lift", "calm", "turn")
SHIFT = {"home": 0.0, "lift": 0.15, "calm": -0.25, "turn": 0.05}   # energy against the arc: the composer's KIND_DRIVE

CALM_MAX = 0.65      # a Calm above this is too loud for a calm moment
JUMP_MAX = 0.35      # a rise this big hits too hard, unless it's into a Lift


def _clamp(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def _draw(rng, weights):
    """A key of {key: whole-number weight} drawn by weight, seeded; None when nothing weighs."""
    items = [(k, w) for k, w in weights.items() if w > 0]
    if not items:
        return None
    r = rng.rnd(sum(w for _, w in items))
    for k, w in items:
        r -= w
        if r < 0:
            return k


# ---- the energy arc ----

@dataclass(frozen=True)
class Wave:
    """One build and release: from 0 up to `peak` over the first `rise` of its bars, then back down."""
    start: int
    bars: int
    peak: float
    rise: float

    @property
    def end(self):
        return self.start + self.bars

    def at(self, bar):
        t = (bar - self.start) / self.bars
        u = t / self.rise if t < self.rise else (1 - t) / (1 - self.rise) if self.rise < 1 else 1.0
        u = _clamp(u)
        return self.peak * u * u * (3 - 2 * u)    # eased, so it turns rather than corners


# ---- key moves ----

def _major_minor(key):
    """The key as major or minor (pentatonics and blues by their parent; modes by their third)."""
    s = PARENT.get(key.scale, key.scale)
    if s not in ("major", "minor"):
        s = "minor" if key.minorish else "major"
    return Key(key.tonic, s)


def _relative(key):
    k = _major_minor(key)
    return Key((k.tonic + 3) % 12, "major") if k.scale == "minor" else Key((k.tonic + 9) % 12, "minor")


def _parallel(key):
    k = _major_minor(key)
    return Key(k.tonic, "major" if k.scale == "minor" else "minor")


MOVES = {
    "relative": _relative,                                        # same notes, the other mode (A minor <-> C major)
    "parallel": _parallel,                                        # same tonic, the other mode (C major <-> C minor)
    "fifth_up": lambda k: Key((k.tonic + 7) % 12, k.scale),       # to the dominant
    "fifth_down": lambda k: Key((k.tonic + 5) % 12, k.scale),     # to the subdominant
    "step_up": lambda k: Key((k.tonic + 1) % 12, k.scale),        # up a semitone: the lift
    "tone_up": lambda k: Key((k.tonic + 2) % 12, k.scale),        # up a whole tone
}
LIFTS = ("step_up", "tone_up")   # a key lift belongs on a Lift


def fifths_apart(a, b):
    """Steps round the circle of fifths between two keys, each read by its relative major (A minor = C major: 0)."""
    def pos(k):
        k = _major_minor(k)
        return ((k.tonic + 3 * (k.scale == "minor")) * 7) % 12
    d = abs(pos(a) - pos(b))
    return min(d, 12 - d)


# ---- a style's form ----

@dataclass(frozen=True)
class Form:
    """A style's tendencies over a long play. Weights are whole numbers (0: the choose never picks it)."""
    phrase: int = 4                         # bars a phrase
    phrases: dict = field(default_factory=lambda: {2: 3, 3: 1})   # phrases a section, by weight
    wave: tuple = (3, 6)                    # minutes one build and release lasts, low to high
    depth: float = 0.5                      # how far the arc moves the room's energy (0: the room alone)
    opening: str = "swell"                  # "swell": starts low and builds; "full": full energy from the first beat
    change: int = 20                        # % chance of a key change at a section start, when one may happen
    moves: dict = field(default_factory=lambda: {"relative": 2, "fifth_up": 1, "fifth_down": 1})
    modes: tuple = ("major", "minor")       # the modes its key changes lean to (others stay possible, less often)
    grow: dict = field(default_factory=lambda: {"home": 0.05, "lift": 0.1, "calm": 0.0, "turn": 0.05})   # how much
    #                                         heavier each kind of section ends than it starts
    gap: float = 3.0                        # minutes between key changes, at least
    hops: int = 2                           # key changes away from home before it has to come back
    life: int = 8                           # statements before a motif is reborn from its own fragment

    def __post_init__(self):
        if self.opening not in ("swell", "full"):
            raise ValueError(f"unknown opening {self.opening!r}")
        for what, names, known in (("key move", self.moves, MOVES), ("mode", self.modes, SCALES),
                                   ("section kind", self.grow, KINDS)):
            for n in names:
                if n not in known:
                    raise ValueError(f"unknown {what} {n!r}")


# The style book's files hold each style's form.
FORM = table(Form, "form")


# ---- sections ----

@dataclass(frozen=True)
class Section:
    kind: str
    start: int           # bar
    bars: int
    key: Key
    energy: float        # at its first bar
    grow: float          # how much heavier its last bar is
    move: str | None = None   # the key move it opened with

    @property
    def end(self):
        return self.start + self.bars

    def energy_at(self, bar):
        return _clamp(self.energy + self.grow * (bar - self.start) / max(1, self.bars - 1))


def check_section(kind, energy, prev=None):
    """None when the section fits after `prev` (a Section), else the reason."""
    if prev is None:
        return None if kind == "home" else "a play opens at Home"
    if kind == prev.kind and kind != "home":
        return f"a {kind.title()} straight after a {kind.title()}: the same journey twice"
    end = prev.energy_at(prev.end - 1)
    if kind == "calm" and energy > CALM_MAX:
        return f"a Calm at energy {energy:.2f}: too loud for a calm moment"
    if kind == "lift" and energy <= end:
        return f"a Lift at {energy:.2f} after {end:.2f}: it doesn't lift"
    if kind != "lift" and energy - end > JUMP_MAX:
        return f"a {kind.title()} jumping from {end:.2f} to {energy:.2f}: hits too hard, too fast"
    return None


def check_key_change(old, new, move, kind, bars_since, hops, form, bars_a_minute):
    """None when the key may move from `old` to `new` at the start of a `kind` section, else the reason. `hops`
    counts the changes since the play was last in its home key (this one included)."""
    if bars_since < form.gap * bars_a_minute:
        return f"a key change {bars_since} bars after the last: too soon"
    if move in LIFTS and kind != "lift":
        return f"a key lift into a {kind.title()}: lifts belong on a Lift"
    if hops > form.hops:
        return f"{hops} key changes away from home: too far to find the way back"
    return None


class Play:
    """A long play planned a section at a time. Draw sections with `next_section(room)`, where `room` is the
    room's energy (0-1) as that section starts; `energy_at(bar)` reads the plan back."""

    def __init__(self, rng, home, form=FORM["plain"], bpm=100, meter=METERS["4/4"]):
        self.rng, self.home, self.form = rng, home, form
        self.bars_a_minute = bpm * STEPS / meter.bar
        self.sections, self.waves = [], []
        self.key, self.last_change, self.hops = home, 0, 0

    @property
    def bar(self):
        return self.sections[-1].end if self.sections else 0

    def arc(self, bar):
        """The arc (0-1) at a bar, drawing waves as the play reaches them."""
        while not self.waves or bar >= self.waves[-1].end:
            lo, hi = self.form.wave
            minutes = lo + self.rng.rnd(int((hi - lo) * 60) + 1) / 60
            start = self.waves[-1].end if self.waves else 0
            first = not self.waves
            rise = 0.0 if first and self.form.opening == "full" else 0.5 + self.rng.rnd(31) / 100
            peak = 0.6 + self.rng.rnd(41) / 100
            self.waves.append(Wave(start, max(1, round(minutes * self.bars_a_minute)), peak, rise))
        return next(w for w in self.waves if w.start <= bar < w.end).at(bar)

    def _energy(self, kind, bar, room):
        return _clamp(room + self.form.depth * (self.arc(bar) - 0.5) + SHIFT[kind])

    def _kind(self, bar, room):
        prev = self.sections[-1] if self.sections else None
        if prev is None:
            return "home"
        rising = self.arc(bar) >= self.arc(max(0, bar - self.form.phrase))
        weights = {"home": 7 if prev.kind != "home" else 0,
                   "lift": 3 + 3 * rising, "calm": 3 + 3 * (not rising), "turn": 2}
        if prev.kind != "home":
            weights = {k: w * (3 if k == "home" else 1) for k, w in weights.items()}
        while True:
            k = _draw(self.rng, weights)
            if k is None:
                return "home"
            if check_section(k, self._energy(k, bar, room), prev) is None:
                return k
            weights[k] = 0

    def _key_move(self, kind, bar):
        if not self.sections:
            return None, self.key
        f = self.form
        moves = dict(f.moves)
        if self.key != self.home:
            moves["home"] = 2 + 2 * self.hops    # the further away, the stronger home pulls
        for m in f.moves:                        # its own modes three times as often; the rest stay possible
            new = MOVES[m](self.key)
            moves[m] *= 3 if new.scale in f.modes or PARENT.get(new.scale) in f.modes else 1
        if self.rng.rnd(100) >= f.change + 15 * self.hops:
            return None, self.key
        while True:
            m = _draw(self.rng, moves)
            if m is None:
                return None, self.key
            new = self.home if m == "home" else MOVES[m](self.key)
            hops = 0 if new == self.home else self.hops + 1
            if new != self.key and check_key_change(self.key, new, m, kind, bar - self.last_change, hops, f,
                                                    self.bars_a_minute) is None:
                self.last_change, self.hops = bar, hops
                return m, new
            moves[m] = 0

    def next_section(self, room=0.5):
        bar = self.bar
        kind = self._kind(bar, room)
        move, self.key = self._key_move(kind, bar)
        bars = _draw(self.rng, self.form.phrases) * self.form.phrase
        s = Section(kind, bar, bars, self.key, self._energy(kind, bar, room), self.form.grow[kind], move)
        self.sections.append(s)
        return s

    def plan(self, minutes, room=0.5):
        """Sections for a play of about `minutes` at a steady room: for tests and the drift measures."""
        while self.bar < minutes * self.bars_a_minute:
            self.next_section(room)
        return self.sections

    def section_at(self, bar):
        return next(s for s in self.sections if s.start <= bar < s.end)

    def energy_at(self, bar):
        return self.section_at(bar).energy_at(bar)


# ---- motifs ----

@dataclass(frozen=True)
class Motif:
    """A short figure: scale steps from its first note, and how long each note lasts in grid steps."""
    steps: tuple
    lengths: tuple

    def __post_init__(self):
        if len(self.steps) != len(self.lengths):
            raise ValueError("a motif needs a length for every note")


SPAN = 7          # scale steps from lowest to highest note, at most (an octave)
LEAP = 4          # scale steps one move may leap (a fifth)
SHORTEST = VALUES["32nd"]
STALE = 3         # the same statement this many times running is stale
KIN = 0.5         # how related a development must stay to the motif it grew from


def _intervals(m):
    return [b - a for a, b in zip(m.steps, m.steps[1:])]


def kinship(a, b):
    """How related two motifs sound, 0-1: interval sizes (so an inversion still counts) and the rhythm's proportions
    (so twice as slow still counts), matched from the start, or end to end for a figure played backwards."""
    def score(ia, la, ib, lb):
        n = max(len(ia) + len(la), len(ib) + len(lb))
        same = sum(abs(x) == abs(y) for x, y in zip(ia, ib)) + sum(x == y for x, y in zip(la, lb))
        return same / n if n else 1.0
    ia, ib = _intervals(a), _intervals(b)
    la, lb = [n / min(a.lengths) for n in a.lengths], [n / min(b.lengths) for n in b.lengths]
    return max(score(ia, la, ib, lb), score(ia[::-1], la[::-1], ib, lb))


def check_motif(m, origin=None, recent=(), bar=STEPS * 4):
    """None when the motif fits, else the reason: every note on the grid (decision 13) and inside a `bar`-step bar
    (two at most), a narrow span and no wild leaps, not stale, and still heard as the motif it grew from."""
    if len(m.steps) < 2:
        return "one note isn't a motif"
    if any(not isinstance(n, int) or n < SHORTEST for n in m.lengths):
        return "a note shorter than a 32nd or between grid steps: off the grid"
    if sum(m.lengths) > 2 * bar:
        return "longer than two bars: more a phrase than a motif"
    if max(m.steps) - min(m.steps) > SPAN:
        return f"it spans {max(m.steps) - min(m.steps)} scale steps: too wide to sing"
    leaps = [abs(i) for i in _intervals(m) if abs(i) > LEAP]
    if leaps:
        return f"a leap of {leaps[0]} scale steps: too wild"
    if len(recent) >= STALE - 1 and all(r == m for r in recent[-(STALE - 1):]):
        return f"the same statement {STALE} times running: stale"
    if origin is not None and kinship(m, origin) < KIN:
        return "no longer heard as the motif it grew from"
    return None


def _from(steps, lengths):
    steps = list(steps)
    return Motif(tuple(s - steps[0] for s in steps), tuple(lengths))


def make_motif(rng, n=None, unit=VALUES["8th"]):
    """A new motif: 3-6 notes, mostly steps with the odd skip, turning back before it runs away; 8ths with the
    odd longer note."""
    n = n or 3 + rng.rnd(4)
    steps, d = [0], 1 if rng.rnd(2) else -1
    for _ in range(n - 1):
        r = rng.rnd(10)
        size = 1 if r < 6 else 2 if r < 9 else 0
        if rng.rnd(100) < 35:
            d = -d
        if abs(steps[-1] + d * size) > SPAN // 2:
            d = -d
        steps.append(steps[-1] + d * size)
    lengths = [unit * (2 if rng.rnd(4) == 0 else 1) for _ in range(n)]
    return _from(steps, lengths)


def _nudge(rng, m):
    s = list(m.steps)
    i = 1 + rng.rnd(len(s) - 1)
    s[i] += 1 if rng.rnd(2) else -1
    return _from(s, m.lengths)


DEVELOP = {
    "again": lambda rng, m: m,
    "nudge": _nudge,                                                            # one note a step off
    "invert": lambda rng, m: _from([-s for s in m.steps], m.lengths),          # upside down
    "back": lambda rng, m: _from(m.steps[::-1], m.lengths[::-1]),              # backwards
    "shorter": lambda rng, m: _from(m.steps[:-1], m.lengths[:-1]),             # without its last note
    "longer": lambda rng, m: _from(m.steps + (m.steps[-1] + (1 if m.steps[-1] >= m.steps[-2] else -1),),
                                   m.lengths + (m.lengths[-1],)),              # one more step the way it was going
    "augment": lambda rng, m: _from(m.steps, [n * 2 for n in m.lengths]),      # twice as slow
    "diminish": lambda rng, m: _from(m.steps, [n // 2 for n in m.lengths]),    # twice as fast
}

WORDS = {
    "again": "the motif again", "nudge": "the motif with one note moved", "invert": "the motif upside down",
    "back": "the motif backwards", "shorter": "the motif cut short", "longer": "the motif stretched by a note",
    "augment": "the motif twice as slow", "diminish": "the motif twice as fast",
    "reborn": "a new motif grown from the old one's opening",
}


def _develop_weights(age):
    """Young motifs come back close; older ones travel further."""
    near = max(1, 6 - age)
    far = min(4, 1 + age // 2)
    return {"again": near, "nudge": 3, "invert": far, "back": far, "shorter": 2, "longer": 2,
            "augment": far, "diminish": far}


class Theme:
    """A motif living through a play: each statement develops it a little more, checked against the motif it grew
    from and the statements before; after `life` statements it's reborn from its own opening."""

    def __init__(self, rng, motif=None, life=FORM["plain"].life):
        self.rng, self.life = rng, life
        self.origin = motif or make_motif(rng)
        self.current, self.age, self.recent = self.origin, 0, []

    def _fallback(self, m):
        """When nothing else fits: the motif with a note moved, or failing that a new one (which always fits)."""
        for _ in range(8):
            n = _nudge(self.rng, m)
            if check_motif(n, recent=self.recent) is None:
                return n
        return make_motif(self.rng)

    def _reborn(self):
        keep = self.current.steps[:2 + self.rng.rnd(2)]
        tail = make_motif(self.rng, n=max(2, len(self.current.steps) - len(keep) + 1))
        m = _from(keep + tuple(keep[-1] + s for s in tail.steps[1:]),
                  self.current.lengths[:len(keep)] + tail.lengths[1:])
        if check_motif(m, self.current, self.recent) is not None:   # close enough to be heard growing from it
            m = self._fallback(self.current)
        self.origin, self.age = m, 0
        return m

    def next(self):
        """The next statement and how it was made (a key of `WORDS`)."""
        if self.age >= self.life:
            how, m = "reborn", self._reborn()
        else:
            weights = _develop_weights(self.age)
            while True:
                how = _draw(self.rng, weights)
                if how is None:
                    how, m = "nudge", self._fallback(self.origin)
                    break
                m = DEVELOP[how](self.rng, self.current)
                if check_motif(m, self.origin, self.recent) is None:
                    break
                weights[how] = 0
        self.current, self.age = m, self.age + 1
        self.recent = (self.recent + [m])[-STALE:]
        return m, how


# ---- in plain words ----

def explain_section(s, prev=None):
    """A section in plain words: "bar 33: a Lift in A minor for 16 bars, energy 0.62 growing to 0.72, up from 0.48;
    the key lifts a semitone (from G# minor)"."""
    end = s.energy_at(s.end - 1)
    text = f"bar {s.start + 1}: a {s.kind.title()} in {s.key} for {s.bars} bars, energy {s.energy:.2f}"
    text += f" growing to {end:.2f}" if end > s.energy + 0.005 else " held"
    if prev is not None:
        before = prev.energy_at(prev.end - 1)
        text += f", {'up' if s.energy > before else 'down'} from {before:.2f}"
    if s.move:
        what = {"relative": "to its relative", "parallel": "to its parallel mode", "fifth_up": "up a fifth",
                "fifth_down": "down a fifth", "step_up": "up a semitone", "tone_up": "up a whole tone",
                "home": "back home"}[s.move]
        text += f"; the key moves {what}" + (f" (from {prev.key})" if prev is not None else "")
    return text
