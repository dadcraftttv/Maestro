# SPDX-License-Identifier: GPL-3.0-or-later
"""Seed fuzzing (task 3.8): many seeds a style through the flow sketch, before any listen. A seed fails when a choose
has nothing left to pick (it raises), a member is empty in a clip of 8 bars or more (an opening may keep one out:
trap's 808 follows the kick, and its intro has none), a note (not a drum hit) runs past the clip's end or out of
its member's range, the melody sinks into the pad, a theory check still rules a part out after its redraws, or the
band check finds members out of sync. Notes off the grid can't be made (`song.Note` refuses them).

    .venv/bin/python tools/fuzz.py                     # 2000 seeds a style
    .venv/bin/python tools/fuzz.py synthwave --seeds 200 --first 1

prints a line a style and the first failing seeds, each replayable with `python -m maestro.sketch <style> --seed N
--seeds 1 --bars B`; exits 1 when any seed fails."""
import argparse, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from maestro.sketch import flow_sketch
from maestro.stylebook import part
from maestro.theory.form import FORM
from maestro.theory.nudge import nudged, parse
from maestro.theory.rhythm import METERS
from maestro.theory.voicing import RANGES

BARS = (16, 8, 32, 24, 40)  # a seed's bars, in turn: whole phrases (8 bars), some cutting a section. Not half a
#                             phrase: Ouralia never cuts one, and half a phrase can cross the clave


def faults(style, seed, bars):
    """What is wrong with one seed's clip, in plain words (empty when nothing is)."""
    try:
        song, lines = flow_sketch(style, seed, bars)
    except Exception as e:                        # a choose with nothing to pick, or any other break
        return [f"{type(e).__name__}: {e}"]
    end = bars * METERS["4/4"].bar
    out = [ln.strip() for ln in lines if " check: " in ln or ln.startswith("    ruled out")]   # as test_flow
    have = {m.role for m in song.members}
    out += [f"no {r}" for r in ("pad", "bass", "melody") if r not in have and part(style, "members", r).get("plays", True)]
    for m in song.members:
        if not m.notes and bars >= 8:
            out.append(f"{m.name} is empty")
        span = None if m.kit else RANGES.get(m.role)
        for n in m.notes:
            if not m.kit and n.step + n.steps > end:      # a kit hit's length is only its note-off
                out.append(f"{m.name}: a note runs past the end (step {n.step}, {n.steps} long)")
                break
            if span and not span.low <= n.pitch <= span.high:
                out.append(f"{m.name}: {n.pitch} out of its range {span.low}-{span.high}")
                break
    pads = [n for m in song.members if m.role == "pad" for n in m.notes]
    for n in (n for m in song.members if m.role == "melody" for n in m.notes):
        if any(p.step <= n.step < p.step + p.steps and p.pitch >= n.pitch for p in pads):
            out.append(f"melody: {n.pitch} at step {n.step} sinks into the pad")
            break
    return out


def fuzz(style, seeds, first=1, show=5):
    """(seeds that failed, the first few as lines)."""
    bad, shown = 0, []
    for seed in range(first, first + seeds):
        bars = BARS[seed % len(BARS)]
        f = faults(style, seed, bars)
        if f:
            bad += 1
            if len(shown) < show:
                shown.append(f"  seed {seed}, {bars} bars: {'; '.join(f[:3])}")
    return bad, shown


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("styles", nargs="*", choices=sorted(FORM), help="every style when left out")
    ap.add_argument("--seeds", type=int, default=2000)
    ap.add_argument("--first", type=int, default=1, help="the first seed")
    ap.add_argument("--nudge", help="DNA nudges on each style (task 3.9), as maestro.sketch takes them")
    a = ap.parse_args(argv)
    failed = False
    for style in a.styles or sorted(s for s in FORM if "~" not in s):
        style = nudged(style, parse(a.nudge)) if a.nudge else style
        bad, shown = fuzz(style, a.seeds, a.first)
        print(f"{style}: {a.seeds - bad}/{a.seeds} seeds clean")
        for line in shown:
            print(line)
        failed |= bad > 0
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
