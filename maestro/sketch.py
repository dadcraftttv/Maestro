# SPDX-License-Identifier: GPL-3.0-or-later
"""The theory core's choices as rough clips, for checkpoint 2: what `explain.py` says, played. The pad holds its
voicing for the bar, the bass plays its note on the drawn rhythm, the melody states the motif every two bars, in
one register above the pad's highest note. A bare drum guide keeps time; it comes from the style's rhythm draft with its own seed and isn't explained
(the drummer is task 3.2). Salsa has no kit: the clave and a cowbell on the beats. Sounds are GM stand-ins.

    python -m maestro.sketch [style ...] [--out clips/checkpoint2] [--bars 8] [--seeds 2] [--seed N]

writes `<style>_<seed>.mid`, `.json` and the explanation as `.txt`, with a fresh seed each (decision 9)."""
import argparse, os

from .explain import SAY, choices
from .rng import ComposerRng, fresh_seed
from .song import Song
from .theory.chords import name
from .theory.form import FORM
from .theory.pitch import Key
from .theory.rhythm import CLAVES, METERS, RHYTHM, VALUES, check_band_rhythm, choose_onsets, feel_for, roll, \
    velocity
from .theory.voicing import RANGES

TEMPO = {"plain": 100, "trap": 140, "synthwave": 100, "salsa": 180, "power_rock": 130}   # DadCraft, Oct 24
SOUNDS = {   # GM programs: pad, bass, melody
    "plain": (89, 38, 11),        # warm pad, synth bass, vibraphone
    "trap": (89, 38, 10),         # warm pad, synth bass (808 stand-in), music box
    "synthwave": (90, 39, 81),    # polysynth, synth bass 2, saw lead
    "salsa": (0, 32, 56),         # piano, acoustic bass, trumpet
    "power_rock": (30, 34, 29),   # distortion guitar, picked bass, overdriven guitar
}
LEVELS = {"synthwave": (48, 76, 58)}   # velocities: pad, bass, melody (the saw lead and polysynth are loud)
KICKS = {"plain": 2, "trap": 3, "synthwave": 4, "power_rock": 3}   # kicks a bar, the downbeat included
HATS = {"plain": "8th", "trap": "16th", "synthwave": "8th", "power_rock": "8th"}
KICK, SNARE, HAT, CRASH, COWBELL, CLAVES_NOTE = 36, 38, 42, 49, 56, 75


def _melody_base(key, steps, top):
    """The MIDI note of the motif's first degree: the lowest octave that keeps every note above the pad."""
    for octave in range(4, 8):
        base = 12 * octave + key.tonic
        notes = [base + key.degree(d) for d in steps]
        if min(notes) > top and max(notes) <= RANGES["melody"].high:
            return base
    return 12 * 5 + key.tonic


def _drums(song, style, recs, met, seed):
    """The drum guide, seeded apart from the choices so the explanation stays the same with or without it."""
    rng = ComposerRng()
    rng.seed(seed ^ 0x5EED)
    rhythm, feel = RHYTHM[style], feel_for(style, "drums")
    kit = song.member("drums", "drums", kit=True)
    on = []
    if style == "salsa":
        clave = CLAVES[rhythm.clave]
        for r in recs[::2]:
            for s in clave.onsets:
                kit.add(r["bar"] * met.bar + s, VALUES["8th"], CLAVES_NOTE, 100)
                on.append(r["bar"] * met.bar + s)
        for r in recs:
            for s in met.beats:
                kit.add(r["bar"] * met.bar + s, VALUES["8th"], COWBELL, velocity(s, met, feel, 84))
        return on
    snares = set(met.backbeat(feel.pulse))
    for r in recs:
        at = r["bar"] * met.bar
        if r["section"].start == r["bar"] and style != "trap":
            kit.add(at, VALUES["quarter"], CRASH, 96)
        kicks = [s for s in choose_onsets(rng, met, KICKS[style], rhythm, feel.pulse, keep=(0,)) if s not in snares]
        for s in kicks:
            kit.add(at + s, VALUES["8th"], KICK, velocity(s, met, feel, 110))
        for s in snares:
            kit.add(at + s, VALUES["8th"], SNARE, 104)
        rate = VALUES[HATS[style]]
        hats = list(range(0, met.bar, rate))
        if style == "trap" and r["bar"] % 4 == 3:   # a roll into the next phrase on the last beat
            last = met.beats[-1]
            hats = [s for s in hats if s < last] + roll(last, met.bar - last, "32nd_triplet" if rng.rnd(2) else "32nd")
        for s in hats:
            kit.add(at + s, max(1, min(rate, met.bar - s)), HAT, velocity(s, met, feel, 80))
        on += [at + s for s in kicks + sorted(snares) + hats]
    return on


def sketch(style="plain", seed=1, bars=8, home=Key(9, "minor"), room=0.5):
    """(the Song, the explanation lines) for one style and seed."""
    bpm = TEMPO[style]
    lines, recs = choices(style, seed, bars, home, bpm, room)
    met = METERS["4/4"]
    song = Song(tempo=bpm, source={"set": "maestro sketch (theory core drafts, explain.py)",
                                   "license": "GPL-3.0-or-later", "commercial_safe": True, "seed": seed,
                                   "style": style})
    p_pad, p_bass, p_mel = SOUNDS[style]
    pad, bass, mel = song.member("pad", "pad", p_pad), song.member("bass", "bass", p_bass), \
        song.member("melody", "melody", p_mel)
    v_pad, v_bass, v_mel = LEVELS.get(style, (70, 100, 84))
    bass_on, mel_on = [], []
    top = max((max(r["pad"]) for r in recs if r["pad"]), default=RANGES["melody"].low - 1)   # the melody sits above
    for r in recs:
        at = r["bar"] * met.bar
        for n in r["pad"] or []:
            pad.add(at, met.bar, n, v_pad)
        if "bass_on" in r:
            bass_on += r["bass_on"]
        if "motif" in r:
            m = r["motif"]
            base, t = _melody_base(r["key"], m.steps, top), r["motif_at"]
            for d, length in zip(m.steps, m.lengths):
                if t >= bars * met.bar:
                    break
                mel.add(t, length, base + r["key"].degree(d), velocity(t % met.bar, met, feel_for(style, "melody"), v_mel))
                mel_on.append(t)
                t += length
        song.timeline.append({"bar": r["bar"], "tempo": bpm, "meter": met.name, "key": str(r["key"]),
                              "chord": name(r["chord"], r["key"]), "section": {"kind": r["section"].kind},
                              "energy": round(r["energy"], 3)})
    feel = feel_for(style, "bass")
    end = bars * met.bar
    for i, s in enumerate(bass_on):   # each onset sounds its bar's bass note, up to the next onset or the bar line
        b = s // met.bar
        stop = min(bass_on[i + 1] if i + 1 < len(bass_on) else end, (b + 1) * met.bar)
        bass.add(s, stop - s, recs[b]["bass"][0], velocity(s % met.bar, met, feel, v_bass))
    drum_on = _drums(song, style, recs, met, seed)
    clave = CLAVES[RHYTHM[style].clave] if RHYTHM[style].clave else None
    parts = {"bass": (bass_on, feel), "melody": (mel_on, feel_for(style, "melody")),
             "drums": (drum_on, feel_for(style, "drums"))}
    for why in check_band_rhythm(parts, met, clave if clave and clave.two_sided else None):
        lines.append(f"  band check: {why}")
    song.listen = (f"{style.replace('_', ' ')}, {home}, {bpm} BPM, seed {seed}: the theory core's choices, not yet "
                   "the style. Listen for: do the chords move somewhere and come home in a way that fits the style, "
                   "does the bass rhythm feel like the style, does the melody grow from its motif. The drums are a "
                   "bare guide; sounds are GM stand-ins.")
    return song, lines


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("styles", nargs="*", choices=sorted(FORM), help="the four styles when left out")
    ap.add_argument("--out", default="clips/checkpoint2")
    ap.add_argument("--bars", type=int, default=8)
    ap.add_argument("--seeds", type=int, default=2, help="clips per style")
    ap.add_argument("--seed", type=int, help="the first seed (the next ones count up); fresh by default")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    seed = a.seed if a.seed is not None else fresh_seed()
    for style in a.styles or [s for s in FORM if s != "plain"]:
        for _ in range(a.seeds):
            song, lines = sketch(style, seed, a.bars)
            stem = os.path.join(a.out, f"{style}_{seed}")
            song.write(stem)
            with open(f"{stem}.txt", "w") as f:
                f.write("\n".join(lines) + "\n")
            print(f"{stem}.mid")
            seed += 1


if __name__ == "__main__":
    main()
