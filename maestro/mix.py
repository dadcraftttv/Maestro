# SPDX-License-Identifier: GPL-3.0-or-later
"""The mix check (task 3.8): each member's loudness in a rendered clip, before DadCraft listens. Every member is
rendered alone, on the clip player's own scale (before the mix's peak is set), and measured the way ITU-R BS.1770
does: K-weighted (here by its response over the spectrum), in 400 ms blocks, gated at -70 and then 10 dB under the
member's own level, so its rests don't count. The levels are said against the melody's.

    python -m maestro.mix clips/synthwave/synthwave_14.mid [...]"""
import argparse, os, tempfile, wave

import mido
import numpy as np

from . import play

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
    """{member: its loudness (LUFS), or None when silent} for a clip, each rendered alone."""
    midi, own = mido.MidiFile(mid), play._own(mid)
    with tempfile.TemporaryDirectory() as tmp:
        gm = {}
        for tr in midi.tracks[1:]:
            if tr.name in own:
                continue
            solo = mido.MidiFile(type=1, ticks_per_beat=midi.ticks_per_beat)
            solo.tracks = [midi.tracks[0], tr]
            part, out = os.path.join(tmp, "solo.mid"), os.path.join(tmp, "solo.wav")
            solo.save(part)
            play._fluid(part, out, sf2, midi.length)
            with wave.open(out) as w:
                ch, frames = w.getnchannels(), w.readframes(w.getnframes())
            x = np.frombuffer(frames, dtype="<i2").reshape(-1, ch).astype(float) / 32768
            gm[tr.name] = x if ch == 2 else x.repeat(2, 1)
    length = max((len(x) for x in gm.values()), default=int((midi.length + play.TAIL_S) * play.RATE))
    parts = {**gm, **play.synth_parts(midi, own, length)} if own else gm
    return {t.name: loudness(parts[t.name]) for t in midi.tracks[1:] if t.name in parts}


def report(levels):
    """Lines: each member's loudness and how far under the melody it sits."""
    top = levels.get("melody")
    out = []
    for name, v in sorted(levels.items(), key=lambda kv: -(kv[1] if kv[1] is not None else -999)):
        if v is None:
            out.append(f"  {name:12s} silent")
        else:
            out.append(f"  {name:12s} {v:6.1f} LUFS" + (f"  {v - top:+5.1f} dB against the melody" if top else ""))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("clips", nargs="+", help="MIDI clips (their JSON beside them)")
    a = ap.parse_args(argv)
    for mid in a.clips:
        print(mid)
        print("\n".join(report(members(mid))))


if __name__ == "__main__":
    main()
