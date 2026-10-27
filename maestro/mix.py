# SPDX-License-Identifier: GPL-3.0-or-later
"""The mix check (task 3.8): each member's loudness in a rendered clip, before DadCraft listens. Every member is
rendered alone, on the clip player's own scale (before the mix's peak is set) and at its gain, and measured the way
ITU-R BS.1770 does: K-weighted (here by its response over the spectrum), in 400 ms blocks, gated at -70 and then
10 dB under the member's own level, so its rests don't count. The levels are said against the melody's and checked
against the style's targets (the style book's "mix"); the gains that would meet them are said too, for the members'
"gain".

    python -m maestro.mix clips/synthwave/synthwave_14.mid [...]"""
import argparse, json

import mido
import numpy as np

from . import play
from .stylebook import BOOK, mix_targets

BLOCK, HOP = 0.4, 0.1    # BS.1770's blocks: 400 ms, overlapping by 75%


def _k_weight(n, rate):
    """|H(f)|² of BS.1770's K-weighting (its high shelf and high pass, designed for `rate`) for an rfft of n."""
    w = 2 * np.pi * np.fft.rfftfreq(n, 1 / rate) / rate
    z = np.exp(-1j * w)

    def biquad(b, a):
        return np.abs((b[0] + b[1] * z + b[2] * z * z) / (a[0] + a[1] * z + a[2] * z * z)) ** 2

    k = np.tan(np.pi * 1681.974450955533 / rate)
    vh = 10 ** (3.999843853973347 / 20)
    vb, q = vh ** 0.4996667741545416, 0.7071752369554196
    shelf = biquad((vh + vb * k / q + k * k, 2 * (k * k - vh), vh - vb * k / q + k * k),
                   (1 + k / q + k * k, 2 * (k * k - 1), 1 - k / q + k * k))
    k, q = np.tan(np.pi * 38.13547087602444 / rate), 0.5003270373238773
    high = biquad((1, -2, 1), (1 + k / q + k * k, 2 * (k * k - 1), 1 - k / q + k * k))
    return shelf * high


def loudness(x, rate=play.RATE):
    """BS.1770's gated loudness (LUFS) of a stereo signal (samples × 2), or None when it's silent."""
    n, hop = int(BLOCK * rate), int(HOP * rate)
    if len(x) < n:
        return None
    starts = np.arange(0, len(x) - n + 1, hop)
    weight = _k_weight(n, rate)
    power = np.zeros(len(starts))
    for c in range(x.shape[1]):
        frames = np.lib.stride_tricks.sliding_window_view(x[:, c], n)[::hop][:len(starts)]
        spec = np.abs(np.fft.rfft(frames, axis=1)) ** 2 * weight
        power += (2 * spec[:, 1:].sum(1) + spec[:, 0]) / (n * n)   # Parseval: the block's mean square
    lufs = -0.691 + 10 * np.log10(np.maximum(power, 1e-20))
    gated = power[lufs > -70]
    if not len(gated):
        return None
    rel = -0.691 + 10 * np.log10(gated.mean()) - 10
    gated = power[(lufs > -70) & (lufs > rel)]
    return -0.691 + 10 * np.log10(gated.mean())


def members(mid, sf2=None):
    """{member: its loudness (LUFS) as the player mixes it, or None when silent}, each rendered alone."""
    midi, own, gains = mido.MidiFile(mid), play._own(mid), play._gains(mid)
    parts = play.gm_parts(midi, {t.name for t in midi.tracks[1:] if t.name not in own}, sf2)
    length = max((len(x) for x in parts.values()), default=int((midi.length + play.TAIL_S) * play.RATE))
    if own:
        parts.update(play.synth_parts(midi, own, length))
    return {n: loudness(x * gains.get(n, 1)) for n, x in parts.items()}


def check(levels, roles, targets):
    """(lines: each member's loudness against the melody's and its target; {member: the dB change to the middle of
    its target})."""
    top = next((v for n, v in levels.items() if roles.get(n) == "melody"), None)
    if top is None:
        return ["  no melody to measure against"], {}
    out, fit = [], {}
    others = {n: v - top for n, v in levels.items() if v is not None and roles.get(n) != "melody"}
    for n, rel in sorted(others.items(), key=lambda kv: -kv[1]):
        lo, hi = targets.get(roles.get(n), (None, None))
        off = lo is not None and not lo <= rel <= hi
        out.append(f"  {n:12s} {rel:+5.1f} dB against the melody"
                   + ("" if lo is None else f"  (target {lo:+g} to {hi:+g})") + ("  OFF" if off else ""))
        if lo is not None:
            fit[n] = (lo + hi) / 2 - rel
    if others and "top" in targets:
        over, (lo, hi) = -max(others.values()), targets["top"]
        out.append(f"  the melody {over:+.1f} dB over the loudest other member  (target {lo:+g} to {hi:+g})"
                   + ("" if lo <= over <= hi else "  OFF"))
    return out, fit


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("clips", nargs="+", help="MIDI clips (their JSON beside them)")
    a = ap.parse_args(argv)
    for mid in a.clips:
        info = json.load(open(mid[:-4] + ".json"))
        style = (info["source"].get("style") or "").split("~")[0] or None   # a nudge keeps its style's mix
        gains = {n: m.get("gain", 0) for n, m in info["members"].items()}
        lines, fit = check(members(mid), {n: m["role"] for n, m in info["members"].items()},
                           mix_targets(style) if style in BOOK else {})
        print(f"{mid} ({style})")
        print("\n".join(lines))
        moves = {n: round(gains[n] + d) for n, d in fit.items() if round(gains[n] + d) != gains[n]}
        if moves:
            print("  to meet the targets, the members' gain (dB): "
                  + ", ".join(f"{n} {g:+d}" for n, g in moves.items()))


if __name__ == "__main__":
    main()
