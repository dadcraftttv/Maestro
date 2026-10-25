# SPDX-License-Identifier: GPL-3.0-or-later
"""Maestro's own sounds, for what General MIDI can't play (task 3.4a's second round): trap's 808 and an 808-style
kit, made the way the Roland TR-808 made them, from oscillators and noise. The clip player mixes them in with
FluidSynth's General MIDI sounds; a member whose sound is named here (`SYNTHS`) is played by this module.

- **808** (a bass member): a sine, its pitch dropping two semitones into the note in its first 20 ms, a long
  decay (held notes fade over about two seconds), a light rounding (soft saturation) so the low notes are heard
  on small speakers, kept clean (DadCraft prefers trap without the fuzz). Pitch bends glide (the slides), the
  phase carried from note to note so a slide is one sound.
- **808 kit** (a kit member): the kick a short punchy sine sweep (the 808 bass carries the boom); on 3 a clap
  (three quick noise bursts and a tail) layered over a crisp snare; the roll on the clap; the falling cascade a
  snare stepping down, each hit cut short; the hats six square waves and a little noise, the closed one short, the
  open one longer, all through a band pass; a crash of high noise, a reversed cymbal swelling into a section and a
  riser sweeping up (DadCraft's picks from the auditions, Oct 24). GM drum notes, as on the kit channel.

Synthwave's (task 3.4b), after the 80s polysynths and drum machines its records were made on:

- **supersaw** (a pad): seven saws a note, detuned up to 28 cents and spread left and right, a slow attack and
  release, a warm low pass, a big reverb.
- **saw bass**: a saw over a sine sub, its filter snapping shut on each note (a pluck: bright, then round), centred.
- **pluck** (the arp): two saws a few cents apart, a fast filter and a short decay, a ping-pong echo on the dotted
  8th, some reverb.
- **saw lead** (the melody): two saws a few cents apart, a soft attack, vibrato coming in on held notes, an echo and
  reverb: it sits on top.
- **linn kit**: an 80s drum machine's way: a punchy kick, a snare with its big gated reverb (a burst of room cut off
  sharply), toms with the same gate, high to floor across the stereo, hats of filtered noise, a crash; the swell and
  riser as on the 808 kit.

The mix: a member may duck under the kick (`pump`: the pad and bass breathing with it, lightly), and its echo and
reverb are its own (`MIX`). Rendering is plain numpy, 44.1 kHz; the 808 and its kit mono, synthwave's sounds stereo.
Ouralia's own sounds (bucket 6) start from these settings."""
import numpy as np

RATE = 44100
SYNTHS = ("808", "808 kit", "supersaw", "saw bass", "pluck", "saw lead", "linn kit")   # the last five: synthwave

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
    s["clap"] = clap / np.max(np.abs(clap)) + 0.25 * np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.03)
    t = np.arange(int(0.25 * RATE)) / RATE                            # the snare: two tones and a crisp noise
    snare = (0.5 * np.sin(2 * np.pi * 185 * t) + 0.3 * np.sin(2 * np.pi * 330 * t)) * np.exp(-t / 0.05) \
        + 0.8 * _bandpass(_noise(len(t), rng), 2000, 12000) * np.exp(-t / 0.07)
    s["snare only"] = snare / np.max(np.abs(snare))
    n = len(s["clap"])                                                # on 3: the snare under the clap
    both = s["clap"] + np.pad(s["snare only"], (0, n - len(s["snare only"])))
    s["snare"] = both / np.max(np.abs(both))
    for name, dur, tau in (("hat", 0.12, 0.03), ("open", 0.6, 0.22)):
        t = np.arange(int(dur * RATE)) / RATE
        sq = sum(np.sign(np.sin(2 * np.pi * hz * t + k)) for k, hz in enumerate(HAT_HZ))
        h = _bandpass(sq + 0.6 * _noise(len(t), rng), 6500, 16000) * np.exp(-t / tau)
        s[name] = h / np.max(np.abs(h))
    t = np.arange(int(1.6 * RATE)) / RATE
    c = _bandpass(_noise(len(t), rng), 4000, 16000) * np.exp(-t / 0.5)
    s["crash"] = c / np.max(np.abs(c))
    return s


def _pitched(x, semis):
    """x played faster (higher, shorter) or slower."""
    return np.interp(np.arange(0, len(x) - 1, 2 ** (semis / 12)), np.arange(len(x)), x)


def _gated(x, seconds):
    """Cut short, with a 5 ms fade: dry and separate (DadCraft: "staccato and deliberate")."""
    y = x[:int(seconds * RATE)].copy()
    f = min(len(y), int(0.005 * RATE))
    y[len(y) - f:] *= np.linspace(1, 0, f)
    return y


def _swell(seconds):
    """A reversed cymbal over `seconds`, swelling into the next section."""
    rng = np.random.default_rng(52)
    n = int(seconds * RATE)
    c = _bandpass(_noise(n, rng), 3500, 16000) * np.exp(-np.arange(n) / RATE / 0.6)
    return (c / np.max(np.abs(c)))[::-1]


def _riser(seconds):
    """A band of noise sweeping up two octaves over `seconds`, louder as it goes."""
    rng = np.random.default_rng(58)
    n = int(seconds * RATE)
    noise, out = _noise(n, rng), np.zeros(n)
    for k in range(16):
        a, b = k * n // 16, (k + 1) * n // 16
        out[a:b] = _bandpass(noise[a:b], 500 * 2 ** (k / 4), 1500 * 2 ** (k / 4))
    out *= np.linspace(0, 1, n) ** 2
    return out / np.max(np.abs(out))


# GM drum notes: the clap on 3 layered over a snare (38), the roll on the clap (40), the falling cascade's eight
# steps on 67 down to 60 (GM's bongos, congas and timbales: a falling run on another player too; DadCraft chose
# audition 11), the swell (52) and the riser (58) as long as their notes
CASCADE_NOTES = tuple(range(67, 59, -1))
KIT_NOTES = {36: "kick", 38: "snare", 39: "clap", 40: "roll", 42: "hat", 44: "hat", 46: "open", 49: "crash",
             57: "crash", 52: "swell", 58: "riser", **{n: "cascade" for n in CASCADE_NOTES}}
CASCADE_TOP, CASCADE_STEP, CASCADE_GATE = 3.0, 1.6, 0.08   # semitones: its first hit, each step down; seconds a hit
# the hats raised Oct 24, after DadCraft's listen: they were lost under the bell and the strings
LEVEL = {"kick": 0.45, "snare": 0.32, "clap": 0.32, "roll": 0.45, "hat": 0.38, "open": 0.33, "crash": 0.2,
         "cascade": 0.42, "swell": 0.26, "riser": 0.17}
_SOUNDS = None


def kit_808(hits, length):
    """The kit: hits as (start s, end s, MIDI note, velocity) into `length` samples. An open hat is cut by the next
    closed one, as on the machine; the swell and the riser last as long as their notes."""
    global _SOUNDS
    if _SOUNDS is None:
        _SOUNDS = _kit_sounds()
    out = np.zeros(length)
    closed = sorted(int(t * RATE) for t, _, n, _ in hits if KIT_NOTES.get(n) == "hat")
    for t, end, note, vel in hits:
        name = KIT_NOTES.get(note)
        if name is None:
            continue
        if name == "cascade":
            x = _gated(_pitched(_SOUNDS["snare only"], CASCADE_TOP - CASCADE_STEP * (CASCADE_NOTES[0] - note)), CASCADE_GATE)
        elif name == "swell":
            x = _swell(end - t)
        elif name == "riser":
            x = _riser(end - t)
        else:
            x = _SOUNDS["clap" if name == "roll" else name]
        x = x * LEVEL[name] * _amp(vel)
        a = int(t * RATE)
        if name == "open":
            cut = next((c for c in closed if c > a), None)
            if cut is not None:
                x = x[:cut - a]
        b = min(length, a + len(x))
        if b > a:
            out[a:b] += x[:b - a]
    return out



# ---- synthwave (task 3.4b) ----

def _hz(pitch):
    return 440.0 * 2 ** ((np.asarray(pitch, dtype=float) - 69) / 12)


def _saw(f, phase=0.0):
    """A band-limited saw (polyBLEP) following the frequencies `f` (Hz, one a sample)."""
    dt = f / RATE
    t = (phase + np.cumsum(dt)) % 1.0
    y = 2 * t - 1
    lo, hi = t < dt, t > 1 - dt
    x = t[lo] / dt[lo]
    y[lo] -= x + x - x * x - 1
    x = (t[hi] - 1) / dt[hi]
    y[hi] -= x * x + x + x + 1
    return y


def _tone(x, hz, order=2):
    """A gentle low pass (12 dB an octave at order 2), by FFT, over the last axis."""
    n = x.shape[-1]
    f = np.fft.rfftfreq(n, 1 / RATE)
    return np.fft.irfft(np.fft.rfft(x) / np.sqrt(1 + (f / hz) ** (2 * order)), n)


def _high(x, hz):
    n = x.shape[-1]
    f = np.fft.rfftfreq(n, 1 / RATE)
    g = (f / hz) ** 2
    return np.fft.irfft(np.fft.rfft(x) * g / np.sqrt(1 + g * g), n)


def _env(n, attack, release_at, release):
    """An attack ramp, held, then a fade from `release_at` samples over `release` seconds."""
    t = np.arange(n) / RATE
    e = np.minimum(1.0, t / max(attack, 1e-4))
    return e * np.where(t < release_at / RATE, 1.0, np.exp(-(t - release_at / RATE) / max(release / 4, 1e-4)))


def _place(out, x, a, pan=0.0):
    """Adds the mono x at sample a, panned (-1 left, 1 right; equal power), into the stereo out."""
    b = min(out.shape[0], a + len(x))
    if b <= a:
        return
    ang = (pan + 1) * np.pi / 4
    out[a:b, 0] += np.cos(ang) * x[:b - a]
    out[a:b, 1] += np.sin(ang) * x[:b - a]


def _notes_of(notes, tail):
    """(start sample, held samples, samples with the tail, pitch, velocity) a note."""
    for on, off, pitch, vel in notes:
        a = int(on * RATE)
        held = max(1, int((off - on) * RATE))
        yield a, held, held + int(tail * RATE), pitch, vel


DETUNE = (-28, -17, -7, 0, 7, 17, 28)   # cents: the supersaw's seven saws


def supersaw(notes, length):
    out = np.zeros((length, 2))
    rng = np.random.default_rng(7)
    for a, held, n, pitch, vel in _notes_of(notes, 0.7):
        x = np.zeros((n, 2))
        for k, c in enumerate(DETUNE):
            saw = _saw(np.full(n, _hz(pitch + c / 100)), rng.random())
            pan = c / 28 * 0.8
            ang = (pan + 1) * np.pi / 4
            x[:, 0] += np.cos(ang) * saw
            x[:, 1] += np.sin(ang) * saw
        x = _high(_tone(x.T, 2200), 160).T * _env(n, 0.22, held, 0.7)[:, None] * _amp(vel) / len(DETUNE) ** 0.5
        b = min(length, a + n)
        out[a:b] += x[:b - a]
    return 0.22 * out


def _plucked(f, n, bright, dark, tau, rng):
    """A saw whose filter closes from `bright` to `dark` Hz with time constant `tau`: two filtered copies,
    crossfaded (no per-sample filter needed)."""
    raw = _saw(f, rng.random())
    e = np.exp(-np.arange(n) / RATE / tau)
    lo, hi = _tone(raw, dark), _tone(raw, bright)
    return lo + (hi - lo) * e


def saw_bass(notes, length):
    out = np.zeros((length, 2))
    rng = np.random.default_rng(39)
    for a, held, n, pitch, vel in _notes_of(notes, 0.03):
        f = np.full(n, _hz(pitch))
        x = 0.55 * _plucked(f, n, 2400, 380, 0.07, rng)
        x += 0.6 * np.sin(2 * np.pi * np.cumsum(f) / RATE)                     # the sub
        x *= _env(n, 0.003, held, 0.03) * _amp(vel)
        _place(out, x, a)
    return 0.45 * out


def pluck(notes, length):
    out = np.zeros((length, 2))
    rng = np.random.default_rng(81)
    for a, held, n, pitch, vel in _notes_of(notes, 0.35):
        for c, pan in ((-6, -0.5), (6, 0.5)):
            y = _high(_plucked(np.full(n, _hz(pitch + c / 100)), n, 6500, 900, 0.05, rng), 250)
            y *= np.exp(-np.arange(n) / RATE / 0.16) * np.minimum(1, np.arange(n) / (0.002 * RATE)) * _amp(vel)
            _place(out, y, a, pan)
    return 0.3 * out


def saw_lead(notes, length):
    out = np.zeros((length, 2))
    rng = np.random.default_rng(80)
    for a, held, n, pitch, vel in _notes_of(notes, 0.2):
        t = np.arange(n) / RATE
        vib = 0.12 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.25) / 0.3, 0, 1)   # comes in on held notes
        for c, pan in ((-8, -0.3), (8, 0.3)):
            y = _tone(_saw(_hz(pitch + c / 100 + vib), rng.random()), 3200)
            y *= _env(n, 0.012, held, 0.2) * _amp(vel)
            _place(out, y, a, pan)
    return 0.3 * out


def _linn_sounds():
    rng = np.random.default_rng(1982)       # fixed: the kit sounds the same every time
    s = {}
    t = np.arange(int(0.45 * RATE)) / RATE
    f = 52 + 95 * np.exp(-t / 0.03)
    k = np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.exp(-t / 0.16)
    k[:60] += np.linspace(0.6, 0, 60) * _noise(60, rng)
    s["kick"] = k / np.max(np.abs(k))

    def gate(seconds, hold, lo, hi):        # the gated reverb: a burst of bright room, held, then cut off sharply
        n = int(seconds * RATE)
        room = _bandpass(_noise(n, rng), lo, hi)
        tt = np.arange(n) / RATE
        return room * np.minimum(1, tt / 0.004) * np.where(tt < hold, 1 - 0.3 * tt / hold,
                                                          0.7 * np.exp(-(tt - hold) / 0.012))
    t = np.arange(int(0.42 * RATE)) / RATE
    body = (0.7 * np.sin(2 * np.pi * 190 * t) + 0.35 * np.sin(2 * np.pi * 340 * t)) * np.exp(-t / 0.06)
    crack = _bandpass(_noise(len(t), rng), 1500, 11000) * np.exp(-t / 0.05)
    left, right = gate(0.42, 0.3, 700, 9000), gate(0.42, 0.3, 700, 9000)
    s["snare"] = np.stack([body + crack + 0.55 * left, body + crack + 0.55 * right], 1)
    s["snare"] /= np.max(np.abs(s["snare"]))
    for name, hz, pan in (("high tom", 196, -0.5), ("mid tom", 147, 0.0), ("floor tom", 104, 0.5)):
        t = np.arange(int(0.5 * RATE)) / RATE
        tom = np.sin(2 * np.pi * np.cumsum(hz * (1 + 0.5 * np.exp(-t / 0.04))) / RATE) * np.exp(-t / 0.22)
        x = tom + 0.35 * gate(0.5, 0.28, 300, 6000)
        ang = (pan + 1) * np.pi / 4
        s[name] = np.stack([np.cos(ang) * x, np.sin(ang) * x], 1) / np.max(np.abs(x))
    for name, dur, tau in (("hat", 0.1, 0.025), ("open", 0.5, 0.18)):
        t = np.arange(int(dur * RATE)) / RATE
        h = _bandpass(_noise(len(t), rng), 7000, 15000) * np.exp(-t / tau)
        s[name] = h / np.max(np.abs(h))
    t = np.arange(int(2.0 * RATE)) / RATE
    c = _bandpass(_noise(len(t), rng), 3000, 15000) * np.exp(-t / 0.7)
    s["crash"] = c / np.max(np.abs(c))
    return s


LINN_NOTES = {36: "kick", 38: "snare", 40: "roll", 42: "hat", 44: "hat", 46: "open", 49: "crash", 57: "crash",
              50: "high tom", 47: "mid tom", 45: "mid tom", 43: "floor tom", 52: "swell", 58: "riser"}
LINN_LEVEL = {"kick": 0.62, "snare": 0.5, "roll": 0.35, "hat": 0.16, "open": 0.15, "crash": 0.16,
              "high tom": 0.45, "mid tom": 0.45, "floor tom": 0.5, "swell": 0.2, "riser": 0.12}
LINN_PAN = {"hat": 0.3, "open": 0.3, "crash": -0.25}
_LINN = None


def linn_kit(hits, length):
    global _LINN
    if _LINN is None:
        _LINN = _linn_sounds()
    out = np.zeros((length, 2))
    closed = sorted(int(t * RATE) for t, _, n, _ in hits if LINN_NOTES.get(n) == "hat")
    for t, end, note, vel in hits:
        name = LINN_NOTES.get(note)
        if name is None:
            continue
        x = _swell(end - t) if name == "swell" else _riser(end - t) if name == "riser" else \
            _LINN["snare" if name == "roll" else name]
        x = x * LINN_LEVEL[name] * _amp(vel)
        a = int(t * RATE)
        if name == "open":
            cut = next((c for c in closed if c > a), None)
            if cut is not None:
                x = x[:cut - a]
        if x.ndim == 2:
            b = min(length, a + len(x))
            if b > a:
                out[a:b] += x[:b - a]
        else:
            _place(out, x, a, LINN_PAN.get(name, 0.0))
    return out


# ---- the mix: echo, reverb, the pump ----

# each sound's own space: (echo wet, echo feedback, reverb wet, reverb seconds)
MIX = {"supersaw": (0.0, 0.0, 0.35, 2.8), "saw bass": (0.0, 0.0, 0.0, 0.0), "pluck": (0.32, 0.38, 0.22, 1.8),
       "saw lead": (0.2, 0.3, 0.28, 2.2), "linn kit": (0.0, 0.0, 0.1, 1.2)}
_IRS = {}


def _ir(seconds):
    """A stereo room: two decaying noises (one an ear), a little dark, after a 20 ms gap."""
    if seconds not in _IRS:
        rng = np.random.default_rng(int(seconds * 100))
        n = int(seconds * RATE)
        t = np.arange(n) / RATE
        ir = rng.standard_normal((2, n)) * np.exp(-t * 6.9 / seconds)
        ir = _high(_tone(ir, 6000), 180)
        ir = np.concatenate([np.zeros((2, int(0.02 * RATE))), ir], 1)
        _IRS[seconds] = ir / np.sqrt(np.sum(ir ** 2) / 2)
    return _IRS[seconds]


def reverb(x, seconds, wet):
    ir = _ir(seconds)
    n = x.shape[0] + ir.shape[1]
    size = 1 << (n - 1).bit_length()
    dry = (x[:, 0] + x[:, 1]) / 2
    spec = np.fft.rfft(dry, size)
    tails = np.stack([np.fft.irfft(spec * np.fft.rfft(ir[c], size), size)[:x.shape[0]] for c in range(2)], 1)
    return x + wet * 0.35 * tails


def echo(x, beat_s, wet, feedback, repeats=6):
    """A ping-pong echo on the dotted 8th: left, right, left..., each `feedback` quieter, darker."""
    d = int(0.75 * beat_s * RATE)
    out = x.copy()
    mono = _tone((x[:, 0] + x[:, 1]) / 2, 4000)
    for k in range(1, repeats + 1):
        if k * d >= len(x):
            break
        out[k * d:, (k + 1) % 2] += wet * feedback ** (k - 1) * mono[:len(x) - k * d]
    return out


def pump(length, kicks, depth):
    """The gain of a member ducking under the kick: down `depth` (0-1) on each kick, back over about 180 ms."""
    g = np.ones(length)
    t = np.arange(int(0.25 * RATE)) / RATE
    shape = 1 - depth * np.exp(-t / 0.09) * np.minimum(1, t / 0.004)
    for k in sorted(kicks):
        a = int(k * RATE)
        b = min(length, a + len(shape))
        if b > a:
            g[a:b] = np.minimum(g[a:b], shape[:b - a])
    return g
