# SPDX-License-Identifier: GPL-3.0-or-later
"""The two drift measures (decision 9): staleness within a play and sameness between plays, with targets.

A bar is compared by its notes (where each starts in the bar, its length and pitch; loudness is left out), plus the
notes still sounding into it from before, so a held chord repeats like any other bar. A member's silent bars don't
count as copies. The whole band's bar is all its members' bars together.

Within a play (~20 minutes):
- **phrases copied:** the share of the band's 4-bar phrases (on the 4-bar line) that copy an earlier stretch;
- **longest copy:** the longest run of band bars that repeats bars heard before;
- **melody bars copied:** the share of the melody's bars that copy one of its last 16 (drums and bass groove: no cap);
- **fresh, worst window:** in each 2-minute window, the share of band bars new to the play; the lowest window.
Between two plays (same settings, fresh seeds):
- **same bar, same place:** bar i of one play is bar i of the other;
- **phrases shared:** the share of the second play's 4-bar phrases found anywhere in the first;
- **longest shared run:** the longest stretch of band bars the two plays have in common.

Repeats are allowed: a theme coming back and a groove holding are musical. The targets only flag too much.

    python -m maestro.drift [--minutes 20] [--seed N]      # today's composer, two plays per baseline preset
    python -m maestro.drift a.mid [b.mid]                  # song files (the JSON beside each gives tempo and roles)
"""
import argparse, json, os, random

from .song import read_notes
from .theory.rhythm import STEPS

PHRASE, WINDOW_MIN, RECENT = 4, 2, 16
TARGETS = {   # (most or least, value); DadCraft confirmed, Oct 24
    "phrases_copied": ("max", 0.10),
    "longest_copy": ("max", 8),
    "melody_bars_copied": ("max", 0.30),
    "fresh_worst_window": ("min", 0.25),
    "same_bar_same_place": ("max", 0.01),
    "phrases_shared": ("max", 0.05),
    "longest_shared_run": ("max", 4),
}
SAYS = {
    "phrases_copied": "band 4-bar phrases copied within the play",
    "longest_copy": "longest exact copy within the play (bars)",
    "melody_bars_copied": "melody bars copying one of the last 16",
    "fresh_worst_window": "new band bars, worst 2-minute window",
    "same_bar_same_place": "same bar, same place, two plays",
    "phrases_shared": "4-bar phrases shared by two plays",
    "longest_shared_run": "longest run shared by two plays (bars)",
}
GROOVE = ("drums", "bass", "pad")   # shown beside the targets, never capped (DadCraft, Oct 24: they groove)


class Play:
    """A play's bars: `bars[member]` is a list of fingerprints (None when silent), `band` the whole band's."""

    def __init__(self, notes, bar_steps, bars_a_minute, roles=None):
        """`notes` {member: [Note]}; `roles` {member: role} (a member is its own role if missing)."""
        self.bars_a_minute, self.roles = bars_a_minute, roles or {}
        end = max((n.step + n.steps for ns in notes.values() for n in ns), default=0)
        count = -(-end // bar_steps)
        self.bars = {}
        for name, ns in notes.items():
            rows = [[] for _ in range(count)]
            for n in ns:
                first = n.step // bar_steps
                off = n.step - first * bar_steps
                rows[first].append((off, min(n.steps, bar_steps - off), n.pitch))
                for b in range(first + 1, -(-(n.step + n.steps) // bar_steps)):   # still sounding: "held"
                    left = n.step + n.steps - b * bar_steps
                    rows[b].append((-1, min(left, bar_steps), n.pitch))
            self.bars[name] = [tuple(sorted(r)) or None for r in rows]
        names = sorted(self.bars)
        self.band = [tuple(self.bars[m][b] for m in names) for b in range(count)]

    def member(self, role):
        return next((m for m in self.bars if self.roles.get(m, m) == role), None)


def from_song(song):
    num, den = song.meter
    return Play({m.name: m.notes for m in song.members}, song.bar_steps(), song.tempo / num * den / 4,
                {m.name: m.role for m in song.members})


def from_file(mid):
    info = json.load(open(os.path.splitext(mid)[0] + ".json"))
    num, den = (int(x) for x in info["meter"].split("/"))
    return Play(read_notes(mid), num * STEPS * 4 // den, info["tempo"] / num * den / 4,
                {m: v["role"] for m, v in info["members"].items()})


def _runs(a, b, same):
    """Longest common run of bars between lists a and b; with `same` (a is b), only earlier bars against later."""
    best, prev = 0, [0] * (len(b) + 1)
    for i, x in enumerate(a):
        row = [0] * (len(b) + 1)
        for j in range(i if same else len(b)):
            if x == b[j]:
                row[j + 1] = prev[j] + 1
                best = max(best, row[j + 1])
        prev = row
    return best


def _phrases(bars):
    return [tuple(bars[i:i + PHRASE]) for i in range(0, len(bars) - PHRASE + 1, PHRASE)]


def _stretches(bars):
    return {tuple(bars[i:i + PHRASE]) for i in range(len(bars) - PHRASE + 1)}


def staleness(p):
    """The within-a-play measures, as {name: value}."""
    out = {}
    phrases = _phrases(p.band)
    copied = 0
    for i, ph in enumerate(phrases):   # copies an earlier stretch (any start), not overlapping itself
        start = i * PHRASE
        copied += any(tuple(p.band[j:j + PHRASE]) == ph for j in range(start - PHRASE + 1))
    out["phrases_copied"] = copied / max(1, len(phrases))
    out["longest_copy"] = _runs(p.band, p.band, True)
    for role in ("melody",) + GROOVE:
        m = p.member(role)
        if m:
            rows = p.bars[m]
            sounding = [i for i, r in enumerate(rows) if r]
            hits = sum(rows[i] in rows[max(0, i - RECENT):i] for i in sounding)
            out[f"{role}_bars_copied"] = hits / max(1, len(sounding))
    win = max(1, round(WINDOW_MIN * p.bars_a_minute))
    heard, fresh = set(), []
    for w in range(0, len(p.band), win):
        chunk = p.band[w:w + win]
        new = 0
        for bar in chunk:
            new += bar not in heard
            heard.add(bar)
        if len(chunk) * 2 >= win:   # a short last window says little
            fresh.append(new / len(chunk))
    out["fresh_worst_window"] = min(fresh, default=1.0)
    return out


def sameness(a, b):
    """The between-two-plays measures, as {name: value}."""
    n = min(len(a.band), len(b.band))
    found = _stretches(a.band)
    phrases = _phrases(b.band)
    return {"same_bar_same_place": sum(a.band[i] == b.band[i] for i in range(n)) / max(1, n),
            "phrases_shared": sum(ph in found for ph in phrases) / max(1, len(phrases)),
            "longest_shared_run": _runs(a.band, b.band, False)}


def verdict(measures):
    """{name: (value, target, met)} for each measure that has a target."""
    out = {}
    for k, v in measures.items():
        if k not in TARGETS:
            continue
        side, t = TARGETS[k]
        out[k] = (v, t, v <= t if side == "max" else v >= t)
    return out


def table(rows):
    """rows: [(label, measures)] → printable lines, one per measure, a column per label."""
    labels = [r[0] for r in rows]
    lines = ["  ".join([f"{'measure':44}{'target':>8}"] + [f"{x:>12}" for x in labels])]
    for k in TARGETS:
        side, t = TARGETS[k]
        cells = []
        for _, m in rows:
            if k not in m:
                cells.append(f"{'-':>12}")
                continue
            v, _, ok = verdict({k: m[k]})[k]
            cells.append(f"{(f'{v:.0%}' if isinstance(t, float) else str(v)) + (' ok' if ok else ' NO'):>12}")
        tgt = ("<= " if side == "max" else ">= ") + (f"{t:.0%}" if isinstance(t, float) else str(t))
        lines.append("  ".join([f"{SAYS[k]:44}{tgt:>8}"] + cells))
    for role in GROOVE:
        k = f"{role}_bars_copied"
        cells = [f"{f'{m[k]:.0%}' if k in m else '-':>12}" for _, m in rows]
        lines.append("  ".join([f"{role + ' bars copying one of the last 16':44}{'free':>8}"] + cells))
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="*", help="one song file (staleness) or two (and sameness)")
    ap.add_argument("--minutes", type=float, default=20)
    ap.add_argument("--seed", type=int, help="the first play's seed; fresh by default")
    a = ap.parse_args(argv)
    if a.files:
        plays = [from_file(f) for f in a.files[:2]]
        m = staleness(plays[0])
        if len(plays) == 2:
            m.update(sameness(*plays))
        print("\n".join(table([(os.path.basename(a.files[0]), m)])))
        return
    from . import baseline
    seed = a.seed if a.seed is not None else random.SystemRandom().randrange(1, 1 << 24)
    rows = []
    for i, (scale, key, bpm) in enumerate(baseline.PRESETS):
        bars = round(a.minutes * bpm / 4)
        one, two = (baseline.clip(s, scale, key, bpm, bars, walk_from=bars) for s in (seed + 2 * i, seed + 2 * i + 1))
        p, q = from_song(one), from_song(two)
        m = staleness(p)
        m.update(sameness(p, q))
        rows.append((f"{baseline.NAMES[key]} {bpm}", m))
    print(f"today's composer, {a.minutes:g} minutes a play, seeds from {seed} (two plays per preset)")
    print("\n".join(table(rows)))


if __name__ == "__main__":
    main()
