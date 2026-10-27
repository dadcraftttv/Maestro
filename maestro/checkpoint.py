# SPDX-License-Identifier: GPL-3.0-or-later
"""Checkpoint 3's listening set for one style (decision 16; DadCraft, Oct 27: one style a session, plain as a
reference, the pocket A/B built now). Into `clips/checkpoint3/<style>`:

    1_full_<seed>        the full play, its summary and the judge's table (`.txt`)
    2_<member>_<seed>    each member alone, the 16 bars of that same play where it plays most, with its 2-3 lines
    3_pocket_<seed>      the full play again with the reserve pocket (decision 13): the same notes, the band nudged
                         off the grid together, up to `--pocket` ms either way
    4_second_<seed+1>    a second play of the same settings: never the same play twice (decision 9)
    5_long_<seed+2>      a long play (`--long` bars)
    0_plain_<seed>       plain, dcs_composer's sound, for reference (once, with `--plain`)

    python -m maestro.checkpoint synthwave [--seed 12] [--pocket 5] [--long 240] [--plain] [--no-wav]

The drift measures (`maestro.drift --flow <style>`) and the mix check (`maestro.mix`) run apart, before he listens."""
import argparse, contextlib, io, os
from dataclasses import replace

from . import judge, play
from .explain import flow_choices, member_summary
from .sketch import TEMPO, flow_sketch
from .song import Song
from .theory.pitch import Key

BARS = 84      # the full play (about 3 minutes)
SOLO = 16      # a member alone: one 16-bar stretch of the full play


def window(member, bar, bars, solo=SOLO):
    """The first bar (from 0) of the phrase-aligned `solo` bars where the member plays the most notes."""
    starts = range(0, max(bars - solo, 0) + 1, solo)
    return max(starts, key=lambda s: (sum(s * bar <= n.step < (s + solo) * bar for n in member.notes), -s))


def alone(song, member, first, solo=SOLO):
    """A song of one member, bars first+1 .. first+solo of `song`, moved to the start."""
    bar = song.bar_steps()
    lo, hi = first * bar, (first + solo) * bar
    one = Song(tempo=song.tempo, meter=song.meter, source=dict(song.source, bars=f"{first + 1}-{first + solo}"),
               timeline=[dict(e, bar=e["bar"] - first) for e in song.timeline if first < e["bar"] <= first + solo])
    one.members.append(replace(
        member, notes=[replace(n, step=n.step - lo, steps=min(n.steps, hi - n.step))
                       for n in member.notes if lo <= n.step < hi],
        slides=[(a - lo, st, se, h) for a, st, se, h in member.slides if lo <= a and a + st + h <= hi],
        vibrato=[(a - lo, min(st, hi - a)) for a, st in member.vibrato if lo <= a < hi]))
    return one


def _judged(mid):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        judge.main([mid])
    return out.getvalue().rstrip().splitlines()


def _write(song, stem, lines, wav):
    mid = song.write(stem)
    with open(f"{stem}.txt", "w") as f:
        f.write("\n".join(lines) + "\n")
    if wav:
        play.render(mid, f"{stem}.wav")
    return mid


def build(style, seed=12, out=None, pocket=5, long=240, plain=False, wav=True):
    """Writes the set; returns the judge's lines for the full, second and long plays."""
    out = out or os.path.join("clips", "checkpoint3", style)
    os.makedirs(out, exist_ok=True)
    said = []
    song, lines = flow_sketch(style, seed, BARS)
    mid = _write(song, os.path.join(out, f"1_full_{seed}"), lines, wav)
    table = _judged(mid)
    with open(os.path.join(out, f"1_full_{seed}.txt"), "a") as f:
        f.write("\nThe judge:\n" + "\n".join(table) + "\n")
    said += table
    _, take = flow_choices(style, seed, BARS, Key(9, "minor"), TEMPO[style], 0.5)
    for member in song.members:
        if not member.notes:
            continue
        first = window(member, song.bar_steps(), BARS)
        lines = member_summary(style, seed, BARS, TEMPO[style], take, member.role)
        lines[0] += f" (bars {first + 1}-{first + SOLO} of the full play)"
        _write(alone(song, member, first), os.path.join(out, f"2_{member.name.replace(' ', '_')}_{seed}"),
               lines, wav)
    song.pocket = pocket
    _write(song, os.path.join(out, f"3_pocket_{seed}"),
           [f"The full play (seed {seed}) with the reserve pocket: the same notes, each step moved up to {pocket} ms "
            "either way, the whole band together. Listen for: does it breathe more than 1_full, or just sound "
            "loose; does the kick and bass still lock."], wav)
    for name, s, bars in (("4_second", seed + 1, BARS), ("5_long", seed + 2, long)):
        song, lines = flow_sketch(style, s, bars)
        mid = _write(song, os.path.join(out, f"{name}_{s}"), lines, wav)
        said += _judged(mid)
    if plain:
        song, lines = flow_sketch("plain", seed, BARS)
        _write(song, os.path.join(out, f"0_plain_{seed}"), lines, wav)
    return said


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("style", choices=sorted(TEMPO))
    ap.add_argument("--seed", type=int, default=12, help="the full play's seed; the second and long plays count up")
    ap.add_argument("--out", help="clips/checkpoint3/<style>")
    ap.add_argument("--pocket", type=int, default=5, help="the pocket clip's ms either way")
    ap.add_argument("--long", type=int, default=240, help="the long play's bars")
    ap.add_argument("--plain", action="store_true", help="also plain's clip, for reference")
    ap.add_argument("--no-wav", dest="wav", action="store_false", help="MIDI and text only")
    a = ap.parse_args(argv)
    print("\n".join(build(a.style, a.seed, a.out, a.pocket, a.long, a.plain, a.wav)))


if __name__ == "__main__":
    main()
