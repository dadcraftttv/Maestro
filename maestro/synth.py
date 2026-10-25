# SPDX-License-Identifier: GPL-3.0-or-later
"""Maestro's own sounds, for what General MIDI can't play (task 3.4a's second round): trap's 808 and an 808-style
kit, made the way the Roland TR-808 made them, from oscillators and noise. The clip player mixes them in with
FluidSynth's General MIDI sounds; a member whose sound is named here (`SYNTHS`) is played by this module.

- **808** (a bass member): a sine, its pitch dropping two semitones into the note in its first 20 ms, a long
  decay (held notes fade over about two seconds), a light rounding (soft saturation) so the low notes are heard
  on small speakers, kept clean (DadCraft prefers trap without the fuzz). Pitch bends glide (the slides), the
  phase carried from note to note so a slide is one sound.
- **808 kit** (a kit member): the kick a short punchy sine sweep (the 808 bass carries the boom); the snare a clap
  (three quick noise bursts and a tail) over a short body tone; the hats six square waves and a little noise, the
  closed one short, the open one longer, all through a band pass; a crash of high noise. GM drum notes, as on
  the kit channel.

Rendering is plain numpy, mono, 44.1 kHz. Ouralia's own 808 (bucket 6) starts from these settings."""
import numpy as np

RATE = 44100
SYNTHS = ("808", "808 kit")

# the 808 bass
DROP, DROP_S = 2.0, 0.02          # semitones the pitch falls from at the start, and how fast (s)
DECAY_S, RELEASE_S = 0.9, 0.04    # the note's fade (time constant) and its release after the note ends
DRIVE = 1.6                       # the soft saturation: a few harmonics so the low notes are heard
GAIN = 0.4                        # the 808 against FluidSynth's GM members (measured: the 808 about 15 dB over the bell, mostly its low end)
# hat oscillators (Hz): the TR-808's six square waves
HAT_HZ = (205.3, 304.4, 369.6, 522.7, 540.0, 800.0)


def _amp(velocity):
    return (velocity / 127) ** 1.5


def bass_808(notes, bends, length):
    """The 808's line: notes as (start s, end s, MIDI note, velocity), bends as (time s, semitones) steps (the
    MIDI pitch wheel), into `length` samples."""
    out = np.zeros(length)
    t_all = np.arange(length) / RATE
    if bends:
        bt, bv = zip(*sorted(bends))
        bend = np.interp(t_all, np.array(bt), np.array(bv), left=0.0)
    else:
        bend = np.zeros(length)
    phase = 0.0
    notes = sorted(notes)
    for i, (on, off, pitch, vel) in enumerate(notes):
        a = int(on * RATE)
        nxt = int(notes[i + 1][0] * RATE) if i + 1 < len(notes) else length
        b = min(length, int((off + RELEASE_S) * RATE), nxt)   # one voice: the next note takes over
        if b <= a:
            continue
        t = np.arange(b - a) / RATE
        semis = pitch - 69 + bend[a:b] + DROP * np.exp(-t / DROP_S)
        f = 440.0 * 2 ** (semis / 12)
        ph = phase + 2 * np.pi * np.cumsum(f) / RATE
        phase = ph[-1]
        env = np.exp(-t / DECAY_S) * np.minimum(1.0, t / 0.002)
        held = off - on
        env *= np.where(t < held, 1.0, np.exp(-np.maximum(0.0, t - held) / (RELEASE_S / 4)))
        tone = np.tanh(DRIVE * np.sin(ph)) / np.tanh(DRIVE)
        out[a:b] += GAIN * _amp(vel) * env * tone
    return out


def _noise(n, rng):
    return rng.uniform(-1.0, 1.0, n)


def _bandpass(x, lo, hi):
    """A band pass by FFT, for the short drum sounds."""
    spec = np.fft.rfft(x)
    hz = np.fft.rfftfreq(len(x), 1 / RATE)
    spec[(hz < lo) | (hz > hi)] = 0
    return np.fft.irfft(spec, len(x))


def _kit_sounds():
    rng = np.random.default_rng(808)        # fixed: the kit sounds the same every time
    s = {}
    t = np.arange(int(0.35 * RATE)) / RATE
    f = 48 + 110 * np.exp(-t / 0.025)
    s["kick"] = np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.exp(-t / 0.11)
    s["kick"][:80] += np.linspace(0.5, 0, 80) * _noise(80, rng)      # the click of the beater
    t = np.arange(int(0.4 * RATE)) / RATE
    burst = np.zeros_like(t)
    for k, d in enumerate((0.0, 0.011, 0.022)):                       # the clap: three hands, then the room
        burst += (t >= d) * np.exp(-np.maximum(0, t - d) / 0.006) * (0.8 if k < 2 else 1.0)
    burst += 0.5 * (t >= 0.022) * np.exp(-np.maximum(0, t - 0.022) / 0.12)
    clap = _bandpass(_noise(len(t), rng), 900, 5000) * burst
    body = np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.03)
    s["snare"] = 0.9 * clap / np.max(np.abs(clap)) + 0.25 * body
    for name, dur, tau in (("hat", 0.12, 0.03), ("open", 0.6, 0.22)):
        t = np.arange(int(dur * RATE)) / RATE
        sq = sum(np.sign(np.sin(2 * np.pi * hz * t + k)) for k, hz in enumerate(HAT_HZ))
        h = _bandpass(sq + 0.6 * _noise(len(t), rng), 6500, 16000) * np.exp(-t / tau)
        s[name] = h / np.max(np.abs(h))
    t = np.arange(int(1.6 * RATE)) / RATE
    c = _bandpass(_noise(len(t), rng), 4000, 16000) * np.exp(-t / 0.5)
    s["crash"] = c / np.max(np.abs(c))
    return s


KIT_NOTES = {36: "kick", 38: "snare", 39: "snare", 42: "hat", 44: "hat", 46: "open", 49: "crash", 57: "crash"}
# the hats raised Oct 24, after DadCraft's listen: they were lost under the bell and the strings
LEVEL = {"kick": 0.45, "snare": 0.32, "hat": 0.38, "open": 0.33, "crash": 0.1}
_SOUNDS = None


def kit_808(hits, length):
    """The kit: hits as (start s, MIDI note, velocity) into `length` samples. An open hat is cut by the next
    closed one, as on the machine."""
    global _SOUNDS
    if _SOUNDS is None:
        _SOUNDS = _kit_sounds()
    out = np.zeros(length)
    closed = sorted(int(t * RATE) for t, n, _ in hits if KIT_NOTES.get(n) == "hat")
    for t, note, vel in hits:
        name = KIT_NOTES.get(note)
        if name is None:
            continue
        x = _SOUNDS[name] * LEVEL[name] * _amp(vel)
        a = int(t * RATE)
        if name == "open":
            cut = next((c for c in closed if c > a), None)
            if cut is not None:
                x = x[:cut - a]
        b = min(length, a + len(x))
        if b > a:
            out[a:b] += x[:b - a]
    return out
