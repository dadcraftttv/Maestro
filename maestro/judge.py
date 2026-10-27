# SPDX-License-Identifier: GPL-3.0-or-later
"""The style judge (task 3.5b): measures a clip's members and scores each against its style's card (3.5a, the
"judge" part of a style file; the traits and what they mean in `stylebook.TRAITS`), naming the trait that's off
("trap drums hats: too few rolls"). The cross check scores the clip against every style's card: it should fit its
own style best.

A trait inside its range scores 1, one outside falls off with the distance (a range's width away scores 0). A
member's score is the mean of its traits' (a kit's over all its lanes); a card's fit is the mean of the members'
scores, the band's tempo and chords counted as one member, so a busy drum card doesn't outweigh the melody. A member
the style has no card for scores 0 (another style's band with no guitar can't claim power rock's guitars). A trait
the clip can't show (chord tones with no chords on the timeline) isn't scored. Shares are counted on the bars the
member (or lane) plays. A clip passes when every member scores WEAKEST (80%) or more: one wrong member hardly moves
the mean of a big band. Each member is scored against its own style (a member swapped in from another style, the
song file's `members.<name>.style`), so a hot-swapped band is judged by what each member is meant to be.

    python -m maestro.judge clip.mid [...]        # each clip's table (the JSON beside it gives roles and style)
    python -m maestro.judge clip.mid --all        # every trait, not only the ones off
    python -m maestro.judge clip.mid --style salsa   # against another style's card
"""
import argparse, json, os, statistics
from bisect import bisect_right
from dataclasses import dataclass, field

import mido

from .song import read_notes
from .stylebook import BOOK, DRUM_LANES, NOTE, STYLES, midi
from .theory.chords import COLOURS, QUALITIES, _SYMBOL
from .theory.percussion import PERCUSSION, VOICES
from .theory.rhythm import STEPS

SIXTEENTH = STEPS // 4
LANES = {"kick": {35, 36}, "snare": {37, 38, 39, 40}, "hats": {42, 44, 46},
         "cymbals": {49, 51, 52, 53, 55, 57, 59}, "toms": {41, 43, 45, 47, 48, 50}}   # GM kit notes
assert set(LANES) == set(DRUM_LANES)
KITS = ("drums", "percussion")
WEAKEST = 0.8        # a clip passes when every member scores this or more
FLOOR = {"notes": 1, "register": 12, "velocity": 5, "length": 0.5, "voices": 1, "tempo": 10, "chords": 0.25}
#        the least width a range counts as when scoring a miss (shares: 10 points)
WORDS = {   # (under, over)
    "notes": ("too few notes", "too many notes"), "syncopation": ("too little syncopation", "too much syncopation"),
    "triplets": ("too few triplets", "too many triplets"), "rolls": ("too few rolls", "too many rolls"),
    "register": ("too low", "too high"), "chord tones": ("too few chord tones", "too many chord tones"),
    "velocity": ("velocities too even", "velocities too uneven"), "repeats": ("repeats too little", "repeats too much"),
    "length": ("notes too short", "notes too long"), "voices": ("too few voices", "too many voices"),
    "slides": ("too few slides", "too many slides"), "top": ("under the band too often", "on top too often"),
    "tempo": ("too slow", "too fast"), "chords": ("chords change too seldom", "chords change too often"),
}
_SHAPES = {s: k for k, s in _SYMBOL.items()}


def chord_tones(symbol):
    """The pitch classes of a chord symbol as the timeline writes it ("Am7", "F#m7b5", "C/E"); None if it isn't one."""
    if not isinstance(symbol, str) or not symbol or symbol[0] not in NOTE:
        return None
    text, bass = symbol.split("/") if "/" in symbol else (symbol, None)
    root, rest = NOTE[text[0]], text[1:]
    if rest[:1] in ("#", "b"):
        root, rest = root + (1 if rest[0] == "#" else -1), rest[1:]
    if rest not in _SHAPES:
        return None
    quality, colour = _SHAPES[rest]
    tones = {(root + i) % 12 for i in QUALITIES[quality] + (COLOURS[colour][0] if colour else ())}
    if bass:
        b = midi(bass + "0")
        if b is None:
            return None
        tones.add(b % 12)
    return frozenset(tones)


@dataclass
class Player:
    role: str
    notes: list                  # [Note]
    slides: int = 0              # its slides (pitch bends into place)
    kit: bool = False


@dataclass
class Clip:
    tempo: float
    bar_steps: int
    bars: int
    chords: list                 # the chord changes, [(step, its tones or None when the timeline doesn't say)]
    players: dict                # {name: Player}
    style: str | None = None
    styles: dict = field(default_factory=dict)   # {name: style} for a member of another style (a blend)

    def style_of(self, name):
        return self.styles.get(name, self.style)

    def chord_at(self, step):
        """The chord tones sounding at a step (None before the first change, or where the timeline doesn't say)."""
        i = bisect_right([at for at, _ in self.chords], step) - 1
        return self.chords[i][1] if i >= 0 else None

    def known(self):
        """Whether the timeline names a chord all the way through."""
        return bool(self.chords) and self.chords[0][0] == 0 and all(c is not None for _, c in self.chords)


def _chords(timeline, bar, unit):
    """The timeline's chord changes as [(step, tones)]: an entry from a bar, or a beat in it (in the meter's unit)."""
    out = []
    for e in sorted(timeline, key=lambda e: (e["bar"], e.get("beat", 0))):
        at = e["bar"] * bar + round(e.get("beat", 0) * unit)
        if e.get("beat") and "chord" not in e:
            continue                       # a change of something else inside the bar: the chord carries on
        out = [x for x in out if x[0] != at] + [(at, chord_tones(e.get("chord")))]
    return out


def _bars(timeline, players, bar_steps):
    """The clip's bars: the timeline's (a roll ringing past the end adds none), else to the last note's end."""
    if timeline:
        return max(e["bar"] + 1 for e in timeline)
    return -(-max((n.step + n.steps for p in players.values() for n in p.notes), default=0) // bar_steps)


def from_song(song, styles=None):
    """A Clip from a Song in memory (`source["style"]` its style; `styles` {member: style} for a blend)."""
    players = {m.name: Player(m.role, list(m.notes), len(m.slides), m.kit) for m in song.members if m.notes}
    styles = {**{m.name: m.style for m in song.members if m.style}, **(styles or {})}
    bar = song.bar_steps()
    bars = _bars(song.timeline, players, bar)
    return Clip(song.tempo, bar, bars, _chords(song.timeline, bar, bar // song.meter[0]), players,
                song.source.get("style"),
                styles or {})


def _slides(path):
    """{track: slides}: each run of the pitch wheel away from rest is one slide."""
    out = {}
    for tr in mido.MidiFile(path).tracks:
        runs, bent = 0, False
        for msg in tr:
            if msg.type == "pitchwheel":
                runs += msg.pitch != 0 and not bent
                bent = msg.pitch != 0
        out[tr.name] = runs
    return out


def from_file(mid, styles=None):
    """A Clip from a song file (the JSON beside it gives tempo, meter, roles, the timeline and the style)."""
    info = json.load(open(os.path.splitext(mid)[0] + ".json"))
    own = {name: max(m["style"], key=m["style"].get) for name, m in info["members"].items() if m.get("style")}
    styles = {**own, **(styles or {})}    # a member's own style (format.md: {"salsa": 1.0}), its strongest
    num, den = (int(x) for x in info["meter"].split("/"))
    notes, slides = read_notes(mid), _slides(mid)
    players = {name: Player(m["role"], notes[name], slides.get(name, 0), m["sound"] == "kit" or m["role"] in KITS)
               for name, m in info["members"].items() if name in notes}
    bar = num * STEPS * 4 // den
    bars = _bars(info["timeline"], players, bar)
    return Clip(info["tempo"], bar, bars, _chords(info["timeline"], bar, STEPS * 4 // den), players,
                info.get("source", {}).get("style"), styles or {})


# --- the measures ---

def _onsets(notes):
    return sorted({n.step for n in notes})


def _played(notes, bar):
    return sorted({n.step // bar for n in notes})


def _pct(part, whole):
    return 100 * part / whole if whole else None


def _quantile(xs, q):
    xs = sorted(xs)
    return xs[round(q * (len(xs) - 1))]


def measure(trait, notes, clip, name, slides=0, steps=None):
    """One trait of a member's (or lane's) notes; None when the clip can't show it."""
    if not notes:
        return None
    bar, on = clip.bar_steps, _onsets(notes)
    played = _played(notes, bar)
    if trait == "notes":
        return len(on) / len(played)
    if trait == "syncopation":
        hit = set(on)
        return _pct(sum(s % STEPS and (s // STEPS + 1) * STEPS not in hit for s in on), len(on))
    if trait == "triplets":
        return _pct(sum(s % SIXTEENTH != 0 for s in on), len(on))
    if trait == "rolls":
        rolled = set()
        for a, b, c in zip(on, on[1:], on[2:]):
            if b - a < SIXTEENTH and c - b < SIXTEENTH:
                rolled.add(a // bar)
        return _pct(len(rolled), len(played))
    if trait == "register":
        pitches = [n.pitch for n in notes]
        return (_quantile(pitches, 0.1), _quantile(pitches, 0.9))
    if trait == "chord tones":
        if not clip.known():
            return None
        on_beat, end = [n for n in notes if n.step % STEPS == 0], clip.bars * bar
        changes = [at for at, _ in clip.chords]
        good = 0
        for n in on_beat:
            # the chord there, the one it's held into and, on the last beat before a change, the coming one
            # (the anticipation, held over or not)
            coming = [at for at in changes if 0 < at - n.step <= STEPS]
            held = [clip.chord_at(st) for st in [n.step, n.step + n.steps - 1] + coming if st < end]
            good += any(n.pitch % 12 in c for c in held)
        return _pct(good, len(on_beat))
    if trait == "velocity":
        return statistics.pstdev(n.velocity for n in notes)
    if trait == "repeats":
        rows = {}
        for n in notes:
            rows.setdefault(n.step // bar, set()).add(n.step % bar)   # where it strikes, not what: a montuno
        seen = [tuple(sorted(rows[b])) for b in played]                 # going round follows the chords
        return _pct(sum(seen[i] in seen[max(0, i - 2):i] for i in range(1, len(seen))), len(seen) - 1)
    if trait == "length":
        return statistics.median(n.steps for n in notes) / STEPS
    if trait == "voices":
        at = {}
        for n in notes:
            at.setdefault(n.step, set()).add(n.pitch % 12)
        return statistics.median(len(v) for v in at.values())
    if trait == "slides":
        return _pct(slides, len(notes))
    if trait == "top":
        others = [n for k, p in clip.players.items() if k != name and not p.kit for n in p.notes]
        high = {}
        for n in notes:
            high[n.step] = max(high.get(n.step, 0), n.pitch)
        over = sum(all(o.pitch < p for o in others if o.step <= s < o.step + o.steps) for s, p in high.items())
        return _pct(over, len(high))
    if trait == "steps":
        hit = {(n.step // bar, n.step % bar) for n in notes}
        return {i: _pct(sum((b, i * SIXTEENTH) in hit for b in played), len(played)) for i in steps}
    raise ValueError(f"no measure for {trait!r}")


# --- scoring ---

@dataclass
class Row:
    member: str          # the member's name, or "band"
    lane: str            # a drum lane or percussion part ("" for the whole member)
    trait: str
    value: object        # what it measured (register: the (low, high) pitches)
    low: object
    high: object
    score: float         # 1 inside, falling to 0 a range's width outside
    source: str

    @property
    def ok(self):
        return self.score == 1

    def says(self):
        """The miss in words ("too few rolls"), "" when inside."""
        if self.ok:
            return ""
        if self.trait == "member":
            return self.source
        trait, step = (self.trait.split(" ", 1) + [""])[:2] if self.trait.startswith("step ") else (self.trait, "")
        if trait == "step":
            under = self.value < self.low
            return f"hits 16th {step} too {'seldom' if under else 'often'}"
        under = (self.value[0] < midi(self.low)) if self.trait == "register" else self.value < self.low
        return WORDS[self.trait][0 if under else 1]

    def shown(self):
        if self.trait == "member":
            return self.value, "-"
        if self.trait == "register":
            return f"{_name(self.value[0])}-{_name(self.value[1])}", f"{self.low}-{self.high}"
        share = self.trait.startswith("step ") or self.trait in _SHARES
        value = f"{self.value:.0f}" if share else f"{self.value:.3g}"
        if not self.ok and float(value) in (self.low, self.high):   # rounding would hide the miss
            value = f"{self.value:.1f}" if share else f"{self.value:.4g}"
        pct = "%" if share else ""
        return value + pct, f"{self.low:g}{pct}-{self.high:g}{pct}"


_SHARES = ("syncopation", "triplets", "rolls", "chord tones", "repeats", "slides", "top")


def _name(m):
    return f"{('C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B')[m % 12]}{m // 12 - 1}"


def _score(trait, value, low, high):
    if trait == "register":
        lo, hi = midi(low), midi(high)
        miss = max(lo - value[0], value[1] - hi, 0)
    else:
        lo, hi = low, high
        miss = max(lo - value, value - hi, 0)
    width = max(hi - lo, FLOOR.get(trait.split(" ")[0] if trait.startswith("step ") else trait, 10))
    return max(0.0, 1 - miss / width)


def _card_rows(card, notes, clip, name, lane, slides):
    rows = []
    for trait, v in card.items():
        if trait == "why":
            continue
        if trait == "steps":
            for idxs, low, high, src in v:
                got = measure("steps", notes, clip, name, steps=idxs)
                if got is None:
                    continue
                for i in idxs:
                    rows.append(Row(name, lane, f"step {i}", got[i], low, high,
                                    _score("step", got[i], low, high), src))
            continue
        low, high, src = v
        got = measure(trait, notes, clip, name, slides)
        if got is not None:
            rows.append(Row(name, lane, trait, got, low, high, _score(trait, got, low, high), src))
    return rows


def _lanes(role, style, notes):
    """{lane: its notes} of a kit member: the drums by GM lane, the percussion by its style's parts."""
    if role == "drums":
        groups = LANES
    else:
        groups = {p.name: {VOICES[h[1]] for pat in p.patterns for h in pat.hits} for p in PERCUSSION[style] or ()}
    return {lane: [n for n in notes if n.pitch in keys] for lane, keys in groups.items()}


def score(clip, style=None):
    """The rows of a clip against a style's cards (its own by default; a blend's members each against their own)."""
    rows = []
    band_style = style or clip.style
    band = BOOK[band_style].get("judge", {}).get("band", {})
    for trait in ("tempo", "chords"):
        if trait not in band:
            continue
        low, high, src = band[trait]
        if trait == "tempo":
            got = clip.tempo
        elif not clip.known() or not clip.bars:
            continue
        else:
            tones = [c for _, c in clip.chords]
            got = sum(c != p for c, p in zip(tones, [None] + tones)) / clip.bars
        rows.append(Row("band", "", trait, got, low, high, _score(trait, got, low, high), src))
    for name, p in clip.players.items():
        s = style or clip.style_of(name)
        card = BOOK[s].get("judge", {}).get(p.role)
        if not card:
            if "judge" in BOOK[s]:
                rows.append(Row(name, "", "member", p.role, None, None, 0.0, f"{s}'s card has no {p.role}"))
            continue
        if p.role in KITS:
            notes = _lanes(p.role, s, p.notes)
            for lane, c in card.items():
                if lane != "why":
                    rows += _card_rows(c, notes.get(lane, []), clip, name, lane, 0)
        else:
            rows += _card_rows(card, p.notes, clip, name, "", p.slides)
    return rows


def members(rows):
    """{member: its score (0-1), the mean of its rows'}."""
    by = {}
    for r in rows:
        by.setdefault(r.member, []).append(r.score)
    return {m: sum(v) / len(v) for m, v in by.items()}


def fit(rows):
    """The mean of the members' scores (0-1); None with nothing scored."""
    by = members(rows)
    return sum(by.values()) / len(by) if by else None


def weakest(rows):
    """(member, score) of the member scoring lowest: one wrong member hardly moves the mean of a big band, so a
    clip passes only when every member scores WEAKEST or more (DadCraft, Oct 26)."""
    by = members(rows)
    return min(by.items(), key=lambda kv: kv[1]) if by else None


def passes(rows):
    w = weakest(rows)
    return w is not None and w[1] >= WEAKEST


def cross(clip):
    """{style: (fit, traits scored)} of the clip against every style's cards, best first."""
    out = {}
    for s in STYLES:
        if "judge" in BOOK[s]:
            rows = score(clip, s)
            out[s] = (fit(rows), len(rows))
    return dict(sorted(out.items(), key=lambda kv: -(kv[1][0] or 0)))


def table(rows, everything=False):
    lines = []
    for r in rows:
        if r.ok and not everything:
            continue
        value, rng = r.shown()
        who = f"{r.member} {r.lane}".strip()
        lines.append(f"  {who:<22} {r.trait:<12} {value:>9}  [{rng}]  " + (r.says() or "ok"))
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("clips", nargs="+", help="song files (.mid, the .json beside each)")
    ap.add_argument("--style", choices=STYLES, help="judge against this style's cards (the clip's own by default)")
    ap.add_argument("--all", action="store_true", help="every trait, not only the ones off")
    a = ap.parse_args(argv)
    for path in a.clips:
        clip = from_file(path)
        style = a.style or clip.style
        if style not in BOOK or "judge" not in BOOK[style]:
            print(f"{path}: no card for style {style!r}")
            continue
        rows = score(clip, style)
        off = sum(not r.ok for r in rows)
        who, low = weakest(rows)
        print(f"{os.path.basename(path)} against {style}: fit {fit(rows):.0%}, {len(rows) - off} of {len(rows)} "
              f"traits inside, weakest {who} {low:.0%}" + ("" if passes(rows) else f" (FAILS: under {WEAKEST:.0%})"))
        print("\n".join(table(rows, a.all)) or "  every trait inside its range")
        c = cross(clip)
        best = next(iter(c))
        print("  cross check: " + ", ".join(f"{s} {f:.0%}" for s, (f, _) in c.items()) +
              (f"; fits {best} best" if best == clip.style else f"; fits {best} best, not its own {clip.style}"))


if __name__ == "__main__":
    main()
