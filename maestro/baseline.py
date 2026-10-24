# SPDX-License-Identifier: GPL-3.0-or-later
"""Today's composer as clips: the baseline Maestro grows from (decision 1), heard on the PC.

The port (`port.py`) is driven the way Ouralia's patch drives the C, a bar at a time, and what it sends becomes
notes the way the patch plays it: the pad holds its four notes until the next chord; the bass holds one low note
(the key's root or the chord's, folded into 65-131 Hz as the patch does) and only changes when it moves; the drums
play the three lanes (kick, snare, hat; open hat coded as velocity + 2); the melody asks the composer for each note
of its rhythm cell. On the phone, the melody (chimes) and the walking notes come from the listener: chimes while
standing still, walking notes on the walking beat. A clip can't walk, so its first half stands (melody) and its
second half walks (walking notes, 8 a bar). The sounds are General MIDI stand-ins, not Ouralia's kits.

    python -m maestro.baseline [--out clips/baseline] [--bars 32] [--seed N]

writes four clips (four scales and tempos) with a fresh seed each, kept in each clip's JSON (decision 9)."""
import argparse, os, random

from .port import Composer, KIND_REG, SCALE_IV, SCALE_N
from .theory.pitch import COMPOSER_SCALES
from .theory.rhythm import STEPS, VALUES

KINDS = ("home", "lift", "calm", "turn")
S16 = VALUES["16th"]
KICK, SNARE, HAT, OPEN_HAT = 36, 38, 42, 46
SOUNDS = {"pad": 89, "bass": 38, "melody": 11, "arp": 10}   # GM: warm pad, synth bass, vibraphone, music box
NAMES = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")


def _deg(scale, d):
    """A scale degree (any octave) as semitones from the key note."""
    n = SCALE_N[scale]
    return SCALE_IV[scale][d % n] + 12 * (d // n)


def _bass(key, semis):
    """The patch's bass: the note an octave below the key's (C3 octave), folded into 65-131 Hz (MIDI 36-47)."""
    p = 48 + key + semis
    while p >= 48:
        p -= 12
    return p


def clip(seed, scale=1, key=9, bpm=92, bars=32, energy=0.5, bright=0.5, color=1, brk=0.3, breath=True, walk_from=None):
    """One baseline clip as a Song. It walks from bar `walk_from` on (halfway by default; `bars` never walks)."""
    from .song import Song
    song = Song(tempo=bpm, source={"set": "maestro baseline (today's composer, port.py)",
                                   "license": "GPL-3.0-or-later", "commercial_safe": True, "seed": seed})
    pad, bass = song.member("pad", "pad", SOUNDS["pad"]), song.member("bass", "bass", SOUNDS["bass"])
    mel, arp = song.member("melody", "melody", SOUNDS["melody"]), song.member("arp", "arp", SOUNDS["arp"])
    drums = song.member("drums", "drums", kit=True)
    c = Composer(seed=seed)
    for msg, v in (("tempo", bpm), ("color", color), ("bright", bright), ("energy", energy), ("seed", seed),
                   ("scale", scale)):
        c.send(msg, v)
    n, bar_steps = SCALE_N[scale], song.bar_steps()
    blocks16 = 60.0 / bpm / 4 * 48000 / 64   # Pd blocks a 16th (the port's default 48 kHz, 64 a block)
    owed = 0.0
    held_pad, held_bass, anchor, kind = None, None, 0, 0   # (start, notes) of what sounds now

    def end_pad(at):
        if held_pad:
            for p in held_pad[1]:
                pad.add(held_pad[0], at - held_pad[0], p, 72)

    def end_bass(at):
        if held_bass:
            bass.add(held_bass[0], at - held_bass[0], held_bass[1], 90)

    for b in range(bars):
        at = b * bar_steps
        c.send("start") if b == 0 else c.send("bar")
        drive = min(1.0, energy + 0.15 * (b % 8) / 7)   # a little lift toward each 8th bar, like The Band Plays
        c.send("drums", drive, brk)
        c.send("arp", 1 - drive, n)
        c.send("cell", drive, 3)
        lanes, figure, cell = {}, None, None
        for o, v in c.out:
            if o == "chord":
                anchor = v[0]
                notes = [48 + key + x for x in v[2:]]
                if not held_pad or held_pad[1] != notes:
                    end_pad(at)
                    held_pad = (at, notes)
                low = _bass(key, v[1])
                if not held_bass or held_bass[1] != low:
                    end_bass(at)
                    held_bass = (at, low)
            elif o == "sect":
                kind = v[0]
            elif o == "drum":
                lanes[v[0]] = v[1:]
            elif o == "arp":
                figure = v
            elif o == "cell":
                cell = v[:16]
        c.out.clear()
        song.timeline.append({"bar": b, "tempo": bpm, "meter": "4/4", "key": key, "scale": COMPOSER_SCALES[scale],
                              "chord": {"degree": anchor, "bass": held_bass[1] - 36 if held_bass else None},
                              "section": {"kind": KINDS[kind]}, "energy": round(drive, 3), "brightness": bright})
        for lane, row in lanes.items():
            for i, vel in enumerate(row):
                if vel > 0:
                    pitch = (KICK, SNARE, HAT)[lane]
                    if vel >= 2:
                        pitch, vel = OPEN_HAT, vel - 2
                    drums.add(at + i * S16, S16, pitch, max(1, min(127, round(vel * 127))))
        walking = b >= (bars // 2 if walk_from is None else walk_from)
        if walking and figure:
            for i, s in enumerate(figure):
                arp.add(at + i * 2 * S16, 2 * S16, 60 + key + _deg(scale, anchor + s), 80)
        for i in range(16):   # the composer's time runs on, a 16th at a time (a statement ends after a pause)
            owed += blocks16
            c.tick(int(owed))
            owed -= int(owed)
            if not walking and cell and cell[i] and not (breath and b % 4 == 3):   # (every 4th bar a breath)
                c.send("note", n, anchor, n)
                d = c.out.pop()[1] + KIND_REG[kind]
                mel.add(at + i * S16, cell[i] * S16, 60 + key + _deg(scale, d), 84)
        c.out.clear()
    end_pad(bars * bar_steps)
    end_bass(bars * bar_steps)
    song.listen = (f"Today's composer, {NAMES[key]} {COMPOSER_SCALES[scale]}, {bpm} BPM, seed {seed}. First half: "
                   "pad, bass, drums and the melody (standing still). Second half: walking notes in place of the "
                   "melody. Listen for: do the chords move somewhere and come home, does the melody sound like a "
                   "theme that comes back changed, do the drums sit with the chords. Sounds are GM stand-ins.")
    return song


PRESETS = ((1, 9, 92), (0, 0, 110), (4, 2, 100), (3, 4, 80))   # (scale, key, BPM): A minor, C major, D dorian, E min. pent.


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default="clips/baseline")
    ap.add_argument("--bars", type=int, default=32)
    ap.add_argument("--seed", type=int, help="the first clip's seed (the next ones count up); fresh by default")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    seed = a.seed if a.seed is not None else random.SystemRandom().randrange(1, 1 << 24)
    for i, (scale, key, bpm) in enumerate(PRESETS):
        stem = os.path.join(a.out, f"{i + 1}_{NAMES[key]}_{COMPOSER_SCALES[scale]}")
        clip(seed + i, scale, key, bpm, a.bars).write(stem)
        print(f"{stem}.mid  (seed {seed + i})")


if __name__ == "__main__":
    main()
