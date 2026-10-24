# SPDX-License-Identifier: GPL-3.0-or-later
"""What the Groove MIDI Dataset's drummers do, as tendencies for the drummer (task 3.3).

Reads GMD's MIDI (Google LLC, CC BY 4.0; download it into `private/gmd`, see `docs/data.md`) and writes
`maestro/data/grooves.json`: our own counts, never the performances. Every hit is rounded to the 16th grid (decision
13) after each take is lined up on its backbeat; a take counts up to 32 bars. For each GMD style:

Swung takes (shuffles) are counted and left out: the styles that draw on these are straight.

- **grooves:** the backbones (kick and accented snare on the 8ths) of the bars that have a backbeat, with how often
  each comes (%), the common ones only; `stay`: how often a bar keeps the bar before's backbone (%).
- **odds:** in those bars, how often each other hit falls on each 16th (%): kick pickups, snare off the backbone,
  ghost notes, open hat, crash, toms.
- **time:** what keeps time in a bar (closed hat, ride or crash) and how fast (16ths, 8ths, quarters), % of bars.
- **loud:** the mean velocity on each 16th of the kick, snare and timekeeper (0: never played there).
- **fills:** from the fill takes: how long (beats), how fast, which drums (% of hits) and how often a tom move
  goes down (%).

    python tools/groove_stats.py [--gmd private/gmd/groove] [--styles rock hiphop pop dance]
"""
import argparse, collections, csv, json, os, statistics

import mido

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "maestro", "data", "grooves.json")
STYLES = ("rock", "hiphop", "pop", "dance")   # what power rock, trap and synthwave draw on (PLAN.md 3.3)
GHOST = 60        # a snare hit softer than this is a ghost note (GMD's snare velocities part around 50-80)
COMMON = 2.0      # % of backbeat bars a backbone needs to be kept
MOST = 10         # backbones kept a style
TAKE = 32         # bars counted a take, so a long jam doesn't outweigh the other drummers

# GMD's kit (Roland TD-11, the dataset's own mapping) as the voices we count.
VOICE = {36: "kick", 38: "snare", 40: "snare", 37: "snare", 42: "hat", 22: "hat", 44: "pedal", 46: "open", 26: "open",
         49: "crash", 55: "crash", 57: "crash", 52: "crash", 51: "ride", 59: "ride", 53: "ride",
         48: "high tom", 50: "high tom", 45: "mid tom", 47: "mid tom", 43: "floor tom", 58: "floor tom"}
TOMS = ("high tom", "mid tom", "floor tom")
ODDS = ("kick", "snare", "ghost", "open", "crash") + TOMS
RATES = {6: "16th", 12: "8th", 4: "16th_triplet", 8: "8th_triplet"}   # a fill's pace, in steps of 24 a beat


def hits(path):
    """[(position in 24ths of a beat, voice, velocity)] of one take."""
    m, t, out = mido.MidiFile(path), 0, []
    for msg in mido.merge_tracks(m.tracks):
        t += msg.time
        if msg.type == "note_on" and msg.velocity and msg.note in VOICE:
            out.append((t * 24 / m.ticks_per_beat, VOICE[msg.note], msg.velocity))
    return out


def swung(take):
    """Whether the take is a shuffle: more of its off-beats sit on the 8th triplet's last third than on the 16ths."""
    near = lambda x, c: abs(x - c) <= 1.5
    sixteenths = sum(1 for t, _, _ in take if near(t % 24, 6) or near(t % 24, 18))
    triplets = sum(1 for t, _, _ in take if near(t % 24, 8) or near(t % 24, 16))
    return triplets > sixteenths


def snare(voice, vel):
    return "snare" if vel >= GHOST else "ghost"


def shift(take):
    """The whole 16ths that line the take up on its backbeat (snare on 2 and 4, kick on 1)."""
    def score(sh):
        sc = 0
        for t, v, vel in take:
            q = (round(t / 6) + sh) % 16
            if v == "snare" and vel >= GHOST:
                sc += {4: 2, 12: 2}.get(q, -0.3 if q % 4 == 0 else 0)
            elif v == "kick":
                sc += {0: 1, 8: 0.5}.get(q, 0)
        return sc
    return max(range(16), key=lambda sh: (score(sh), -sh))


def bars(take):
    """{bar: {16th: {voice: velocity}}}, lined up, the last (partial) bar and near-empty bars left out."""
    sh, out = shift(take), collections.defaultdict(lambda: collections.defaultdict(dict))
    for t, v, vel in take:
        q = round(t / 6) + sh
        v = snare(v, vel) if v == "snare" else v
        cell = out[q // 16][q % 16]
        cell[v] = max(cell.get(v, 0), vel)
    last = max(out, default=0)
    kept = [b for b in sorted(out) if b != last and sum(len(x) for x in out[b].values()) >= 3][:TAKE]
    return {b: out[b] for b in kept}


def backbone(bar):
    return (tuple(s for s in range(0, 16, 2) if "kick" in bar.get(s, {})),
            tuple(s for s in range(0, 16, 2) if "snare" in bar.get(s, {})))


def timekeeper(bar):
    """(voice, rate) keeping time in the bar, or None."""
    n = {v: len({s for s, c in bar.items() if v in c or v == "hat" and "open" in c}) for v in ("hat", "ride", "crash")}
    v = max(n, key=n.get)
    rate = "16th" if n[v] >= 12 else "8th" if n[v] >= 6 else "quarter" if n[v] >= 3 else None
    return (v, rate) if rate else None


def pct(n, total):
    return round(100 * n / total, 1) if total else 0


def grooves(takes):
    """The beat takes' numbers (see the module's notes)."""
    shapes, stays, pairs, kept = collections.Counter(), 0, 0, []
    for take in takes:
        prev = None
        for b, bar in sorted(bars(take).items()):
            k, s = backbone(bar)
            if not s or not {4, 12} & set(s):
                prev = None
                continue
            shapes[(k, s)] += 1
            kept.append((bar, (k, s)))
            if prev is not None:
                pairs += 1
                stays += prev == (k, s)
            prev = (k, s)
    total = sum(shapes.values())
    common = [(sh, n) for sh, n in shapes.most_common(MOST) if pct(n, total) >= COMMON]
    odds, loud, time = {v: [0] * 16 for v in ODDS}, {v: [[] for _ in range(16)] for v in ("kick", "snare", "hat")}, \
        collections.Counter()
    for bar, (k, s) in kept:
        for step, cell in bar.items():
            for v, vel in cell.items():
                if v in odds and not (v == "kick" and step in k or v == "snare" and step in s):
                    odds[v][step] += 1
                if v in ("kick", "snare"):
                    loud[v][step].append(vel)
        tk = timekeeper(bar)
        time[tk or "none"] += 1
        if tk:
            for step, cell in bar.items():
                if tk[0] in cell or tk[0] == "hat" and "open" in cell:
                    loud["hat"][step].append(cell.get(tk[0], cell.get("open")))
    t = {"hat": {}, "ride": {}, "crash": {}}
    for key, n in time.items():
        if key != "none":
            t[key[0]][key[1]] = pct(n, total)
    t["none"] = pct(time["none"], total)
    return {"bars": total,
            "grooves": [{"kick": list(k), "snare": list(s), "share": pct(n, total)} for (k, s), n in common],
            "stay": pct(stays, pairs),
            "odds": {v: [pct(n, total) for n in row] for v, row in odds.items()},
            "time": t,
            "loud": {v: [round(statistics.mean(x)) if x else 0 for x in row] for v, row in loud.items()}}


def fills(takes):
    """The fill takes' numbers: length in beats, pace, drums and the way the toms move."""
    beats, rates, voices, down, moves = collections.Counter(), collections.Counter(), collections.Counter(), 0, 0
    for take in takes:
        body = sorted((t, v) for t, v, _ in take if v in ("snare", "kick") + TOMS)
        if len(body) < 3:
            continue
        span = (body[-1][0] - body[0][0]) / 24
        beats["1" if span <= 1.5 else "2" if span <= 3 else "4"] += 1
        gaps = [b[0] - a[0] for a, b in zip(body, body[1:]) if b[0] - a[0] >= 2]
        if gaps:
            g = statistics.median(gaps)
            rates[RATES[min(RATES, key=lambda r: abs(r - g))]] += 1
        voices.update(v for _, v in body)
        toms = [TOMS.index(v) for _, v in body if v in TOMS]
        for a, b in zip(toms, toms[1:]):
            if a != b:
                moves += 1
                down += b > a
    n, h = sum(beats.values()), sum(voices.values())
    return {"takes": n, "beats": {k: pct(v, n) for k, v in sorted(beats.items())},
            "rate": {k: pct(v, sum(rates.values())) for k, v in rates.most_common()},
            "drums": {k: pct(v, h) for k, v in voices.most_common()}, "down": pct(down, moves)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--gmd", default=os.path.join(ROOT, "private", "gmd", "groove"))
    ap.add_argument("--styles", nargs="+", default=STYLES)
    a = ap.parse_args(argv)
    with open(os.path.join(a.gmd, "info.csv")) as f:
        rows = [r for r in csv.DictReader(f) if r["time_signature"] == "4-4"]
    out = {"why": "What the Groove MIDI Dataset's drummers do: our own counts from its 4/4 takes, rounded to the 16th "
                  "grid, made by tools/groove_stats.py. Positions are 16ths of a bar (0-15), shares and odds %.",
           "source": "Groove MIDI Dataset v1.0.0, Google LLC (Gillick et al., 2019), CC BY 4.0, "
                     "https://magenta.tensorflow.org/datasets/groove",
           "styles": {}}
    for style in a.styles:
        mine = [r for r in rows if r["style"].split("/")[0] == style]
        takes = {k: [hits(os.path.join(a.gmd, r["midi_filename"])) for r in mine if r["beat_type"] == k]
                 for k in ("beat", "fill")}
        straight = [x for x in takes["beat"] if not swung(x)]
        out["styles"][style] = {"takes": len(straight), "swung": len(takes["beat"]) - len(straight),
                                **grooves(straight), "fills": fills(takes["fill"])}
        g = out["styles"][style]
        print(f"{style}: {g['takes']} straight takes ({g['swung']} swung, left out), {g['bars']} backbeat bars, "
              f"{len(g['grooves'])} grooves, "
              f"{g['fills']['takes']} fills")
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
        f.write("\n")


if __name__ == "__main__":
    main()
