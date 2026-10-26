# SPDX-License-Identifier: GPL-3.0-or-later
"""What rock's chords do, from the Rock Corpus, as tendencies for power rock's harmony (task 3.4d).

Reads the Rock Corpus's timed chord lists (Trevor de Clercq and David Temperley, CC BY 4.0; download
`rs200_harmony_clt.zip` and `overview/rs200.txt` from rockcorpus.midside.com into `private/rockcorpus`, see
`docs/data.md`) and writes `maestro/data/rock.json`: our own counts, never the songs' analyses. One analyst's files
(dt), so no song counts twice. Every chord is its root against the key at that point (0-11) and its quality from the
numeral (upper case major, lower case minor).

- **roots:** each root's share of the time (% of measures), the common ones only.
- **moves:** from one chord to the next, how far the root moves (semitones up, 0-11), % of changes.
- **loops:** the four-chord runs that come again at once in a song (the next four chords the same), how many songs
  have each; the two-chord vamps the same way.
- **flat sides:** how many songs use bVII, bVI and bIII at all (%).

    python tools/rock_stats.py [--corpus private/rockcorpus] [--era 1975 1991]
"""
import argparse, collections, glob, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "maestro", "data", "rock.json")
NAMES = {0: "I", 1: "bII", 2: "II", 3: "bIII", 4: "III", 5: "IV", 6: "#IV", 7: "V", 8: "bVI", 9: "VI", 10: "bVII",
         11: "VII"}
COMMON = 1.0      # % a root, a move or a loop needs to be kept
MOST = 12         # loops kept
ERA = (1975, 1991)   # around 80s arena rock: its own counts beside the whole corpus's


def chords(path):
    """[(root against the key, minor?, measures it lasts)] of one song, repeats of the same chord merged."""
    rows = []
    for ln in open(path, encoding="latin-1"):
        f = ln.split()
        if len(f) >= 7 and f[2] not in ("R", "End"):
            rows.append((float(f[1]), int(f[3]) % 12, f[2].lstrip("b#")[:1].islower()))
    out = []
    for (at, root, minor), nxt in zip(rows, rows[1:] + [None]):
        length = (nxt[0] - at) if nxt else 1.0
        if out and out[-1][:2] == (root, minor):
            out[-1] = (root, minor, out[-1][2] + length)
        else:
            out.append((root, minor, length))
    return out


def label(c):
    n = NAMES[c[0]]
    return n.lower() if c[1] else n


def loops(seq, n):
    """The n-chord runs that the song plays again straight after, each once a song."""
    found = set()
    for i in range(len(seq) - 2 * n + 1):
        run = tuple(seq[i:i + n])
        if run == tuple(seq[i + n:i + 2 * n]) and len(set(run)) > 1:
            k = run.index("I") if "I" in run else run.index("i") if "i" in run else 0
            found.add(run[k:] + run[:k])   # from the tonic, when it is in the loop
    return found


def count(paths, years, lo, hi):
    """Our counts over the songs from `lo` to `hi` (years, both included)."""
    roots, moves, fours, twos, flats = collections.Counter(), collections.Counter(), collections.Counter(), \
        collections.Counter(), collections.Counter()
    songs = 0
    for p in paths:
        name = os.path.basename(p)[:-len("_dt.clt")]
        if not lo <= years.get(name, 0) <= hi:
            continue
        cs = chords(p)
        if len(cs) < 2:
            continue
        songs += 1
        for r, _, length in cs:
            roots[r] += length
        for x, y in zip(cs, cs[1:]):
            moves[(y[0] - x[0]) % 12] += 1
        seq = [label(c) for c in cs]
        fours.update(loops(seq, 4))
        twos.update(loops(seq, 2))
        for r in (10, 8, 3):
            if any(c[0] == r and not c[1] for c in cs):
                flats[NAMES[r]] += 1

    def share(c, say=str):
        total = sum(c.values())
        return {say(k): round(100 * v / total, 1) for k, v in c.most_common() if 100 * v / total >= COMMON}
    return {"songs": songs, "roots": share(roots, NAMES.get), "moves": share(moves),
            "loops": {" ".join(k): v for k, v in fours.most_common(MOST)},
            "vamps": {" ".join(k): v for k, v in twos.most_common(MOST)},
            "flat_sides": {k: round(100 * v / songs) for k, v in flats.most_common()}}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--corpus", default=os.path.join(ROOT, "private", "rockcorpus"))
    ap.add_argument("--era", type=int, nargs=2, default=ERA, help="the years counted on their own as well")
    a = ap.parse_args(argv)
    years = {}
    for ln in open(os.path.join(a.corpus, "rs200.txt"), encoding="latin-1"):
        f = ln.rstrip("\n").split("\t")
        if len(f) >= 5 and f[4].isdigit():
            years[f[0]] = int(f[4])
    paths = sorted(glob.glob(os.path.join(a.corpus, "clt", "**", "*_dt.clt"), recursive=True))
    out = {"why": "Our own counts from the Rock Corpus (de Clercq and Temperley, CC BY 4.0), tools/rock_stats.py: "
                  "the RS 200's chords, one analyst's files (dt), never the analyses themselves. 'all': every song; "
                  f"'era': {a.era[0]}-{a.era[1]}, around 80s arena rock (task 3.4d).",
           "license": "CC BY 4.0 (the Rock Corpus), our counts CC BY-SA 4.0",
           "all": count(paths, years, 0, 9999), "era": count(paths, years, *a.era)}
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
        f.write("\n")
    print(f"{out['all']['songs']} songs, {out['era']['songs']} in the era -> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
