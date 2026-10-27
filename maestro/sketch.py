# SPDX-License-Identifier: GPL-3.0-or-later
"""The theory core's choices as rough clips: what `explain.py` says, played. By default task 3.2's flow: the pad
holds each chord of the progression, the bass plays its pattern, the melody is shaped over the phrase, above the
pad; the clip's `.txt` opens with a short summary. `--no-flow` plays Checkpoint 2's bar-by-bar draws (the pad holds
its voicing for the bar, the bass plays its note on the drawn rhythm, the melody states the motif every two bars).
Trap's 808 (task 3.4a) slides by pitch bend. The drummer and the percussion member (task 3.3) play under them, as `explain` says: salsa has no kit, its
percussion keeps time. `--no-flow` keeps Checkpoint 2's bare drum guide (from the style's rhythm draft with its own
seed, unexplained; salsa's is the clave and a cowbell). Sounds are GM stand-ins.

    python -m maestro.sketch [style ...] [--out clips/flow] [--bars 16] [--seeds 2] [--seed N] [--no-flow]

writes `<style>_<seed>.mid`, `.json` and the explanation as `.txt`, with a fresh seed each (decision 9)."""
import argparse, os

from .explain import SAY, choices, flow_choices, summary
from .rng import ComposerRng, fresh_seed
from .song import Song
from .stylebook import StyleError, part, per_style
from .theory.nudge import nudged, parse
from .theory.chords import name
from .theory.form import FORM
from .theory.guitar import GUITAR
from .theory.pitch import Key
from .theory.rhythm import CLAVES, METERS, RHYTHM, VALUES, check_band_rhythm, choose_onsets, feel_for, roll, \
    velocity
from .theory.voicing import RANGES

# From the style book: each style's felt tempo (DadCraft, Oct 24) and its members' sounds (GM programs) and levels
# (velocities: pad, bass, melody), and the drum guide's kicks a bar (the downbeat included) and hats.
_PLAYED = ("pad", "bass", "melody")
TEMPO = per_style(lambda s: part(s, "time", "tempo"))
SOUNDS = per_style(lambda s: tuple(part(s, "members", r)["sound"] for r in _PLAYED))
LEVELS = per_style(lambda s: tuple(part(s, "members", r)["level"] for r in _PLAYED),
                   lambda s: all("level" in part(s, "members", r) for r in _PLAYED))
KICKS = per_style(lambda s: part(s, "members", "drums")["kicks"], lambda s: "kicks" in part(s, "members", "drums"))
HATS = per_style(lambda s: part(s, "members", "drums")["hats"], lambda s: "hats" in part(s, "members", "drums"))
for _s, _h in HATS.items():
    if _h not in VALUES:
        raise StyleError(f"{_s}: members.drums.hats: unknown note value {_h!r}")
KICK, SNARE, HAT, CRASH, COWBELL, CLAVES_NOTE = 36, 38, 42, 49, 56, 75
MUTED = 6    # velocity a palm-muted guitar hit gives up (task 3.4d)


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


def flow_sketch(style="plain", seed=1, bars=16, home=Key(9, "minor"), room=0.5):
    """(the Song, the summary and explanation lines) for task 3.2's flow: what `explain.flow_choices` says, played."""
    bpm = TEMPO[style]
    lines, take = flow_choices(style, seed, bars, home, bpm, room)
    met = METERS["4/4"]
    song = Song(tempo=bpm, source={"set": "maestro sketch (flow, tasks 3.2-3.3)", "license": "GPL-3.0-or-later",
                                   "commercial_safe": True, "seed": seed, "style": style})
    v_pad, v_bass, v_mel = LEVELS.get(style, (70, 100, 84))
    for role, program, level in zip(_PLAYED, SOUNDS[style], (v_pad, v_bass, v_mel)):
        if not part(style, "members", role).get("plays", True):      # salsa's pad sits out (task 3.4c)
            continue
        member, feel = song.member(role, role, program), feel_for(style, role)
        member.pump = part(style, "members", role).get("pump", 0)
        member.gain = part(style, "members", role).get("gain", 0)
        member.pan = part(style, "members", role).get("pan", 0)          # power rock's first lead, to one side
        bent = {st: (steps, semis) for st, steps, semis in take["bends"]} if role == "melody" else {}
        for st, length, m in take[role]:
            vel = level if role == "pad" else velocity(st % met.bar, met, feel, level)
            if st in bent:                   # power rock's lead bends up into its note
                steps, semis = bent[st]
                member.add(st, length, m - semis, vel)
                member.slide(st, steps, semis, length - steps)
            else:
                member.add(st, length, m, vel)
        if role == "bass":                   # trap's 808 slides, as pitch bends
            for sl in take["slides"]:
                member.slide(*sl)
        if role == "melody":
            for sh in take["vibrato"]:
                member.shake(*sh)
    if take["lead2"]:                        # power rock's second lead, on the other side (its second round)
        member, feel = song.member("lead 2", "melody", SOUNDS[style][2]), feel_for(style, "melody")
        member.pan, member.gain = -part(style, "members", "melody").get("pan", 0), \
            part(style, "members", "melody").get("gain", 0)
        bent = {st: (steps, semis) for st, steps, semis in take["bends2"]}
        for st, length, m in take["lead2"]:
            vel = velocity(st % met.bar, met, feel, v_mel)
            if st in bent:
                steps, semis = bent[st]
                member.add(st, length, m - semis, vel)
                member.slide(st, steps, semis, length - steps)
            else:
                member.add(st, length, m, vel)
        for sh in take["vibrato2"]:
            member.shake(*sh)
    if take["guitar"]:                       # power rock's doubled rhythm guitar (task 3.4d), palm mutes softer
        g, feel, muted = part(style, "members", "guitar"), feel_for(style, "guitar"), set(take["muted"])
        scratched, soft = set(take.get("scratch", ())), GUITAR[style].scratch.soft if GUITAR[style].scratch else 0
        for t in GUITAR[style].tracks:
            member = song.member(t.name, "guitar", t.sound)
            member.pan, member.gain = t.pan, g.get("gain", 0)
            for st, length, m in take["guitar"][t.name]:
                v = velocity(st % met.bar, met, feel, g.get("level", 90))
                member.add(st, length, m, max(1, v - MUTED - soft) if st in scratched else
                           max(1, v - MUTED) if st in muted else v)
    for role in ("keys", "horns"):            # salsa's montuno and horns (task 3.4c)
        if take[role]:
            a = part(style, "members", role)
            member, feel = song.member(role, role, a.get("sound", 0)), feel_for(style, role)
            member.gain = a.get("gain", 0)
            for st, length, m in take[role]:
                member.add(st, length, m, velocity(st % met.bar, met, feel, a.get("level", 80)))
    if take["arp"]:                          # synthwave's arp (task 3.4b)
        a = part(style, "members", "arp")
        member, feel = song.member("arp", "arp", a.get("sound", 81)), feel_for(style, "arp")
        member.gain = a.get("gain", 0)
        for st, length, m in take["arp"]:
            member.add(st, length, m, velocity(st % met.bar, met, feel, a.get("level", 64)))
    for r in take["bars"]:
        song.timeline.append({"bar": r["bar"], "tempo": bpm, "meter": met.name, "key": str(r["key"]),
                              "chord": name(r["chord"], r["key"]), "section": {"kind": r["section"].kind},
                              "energy": round(r["energy"], 3)})
    for c in take["changes"]:                # a chord changing inside a bar: from its beat, the rest carried on
        song.timeline.append({"bar": c["bar"], "beat": c["at"] // met.unit if c["at"] % met.unit == 0 else c["at"] / met.unit,
                              "chord": name(c["chord"], c["key"])})
    song.timeline.sort(key=lambda e: (e["bar"], e.get("beat", 0)))
    clave = CLAVES[RHYTHM[style].clave] if RHYTHM[style].clave else None
    parts = {"bass": ([n[0] for n in take["bass"]], feel_for(style, "bass")),
             "melody": ([n[0] for n in take["melody"]], feel_for(style, "melody"))}
    for role in ("drums", "percussion"):     # the drummer and the percussion (task 3.3), each on the kit channel
        if take[role]:
            kit = song.member(role, role, part(style, "members", role).get("sound", 0), kit=True)
            kit.gain = part(style, "members", role).get("gain", 0)
            for st, length, note, vel, _ in take[role]:
                kit.add(st, length, note, vel)
    if take["drums"]:
        parts["drums"] = ([h[0] for h in take["drums"]], feel_for(style, "drums"))
    for name_ in sorted({h[4] for h in take["percussion"]}):
        parts[f"percussion's {name_}"] = ([h[0] for h in take["percussion"] if h[4] == name_],
                                          feel_for(style, "percussion"))
    for why in check_band_rhythm(parts, met, clave if clave and clave.two_sided else None):
        lines.append(f"  band check: {why}")
    short = summary(style, seed, bars, bpm, take)
    gm = [m.name for m in song.members if not isinstance(m.program, str)]
    song.listen = " ".join(short[1:]) + (f" Sounds: Maestro's own, {', '.join(gm)} GM stand-ins." if gm and len(gm) <
                                         len(song.members) else " Sounds are GM stand-ins." if gm else
                                         " Sounds are Maestro's own (synth.py).")
    return song, short + ["", "In detail:"] + lines


def sketch(style="plain", seed=1, bars=8, home=Key(9, "minor"), room=0.5):
    """(the Song, the explanation lines) for one style and seed: Checkpoint 2's bar-by-bar draws."""
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
    ap.add_argument("--out", help="clips/flow, or clips/checkpoint2 with --no-flow")
    ap.add_argument("--bars", type=int, help="16, or 8 with --no-flow")
    ap.add_argument("--no-flow", dest="flow", action="store_false", help="Checkpoint 2's bar-by-bar draws")
    ap.add_argument("--seeds", type=int, default=2, help="clips per style")
    ap.add_argument("--seed", type=int, help="the first seed (the next ones count up); fresh by default")
    ap.add_argument("--nudge", help="DNA nudges (task 3.9), e.g. energetic=2,bass:funky=1; directions: "
                    "energetic, minimal, funky, soulful, sophisticated, 0-5 steps each")
    a = ap.parse_args(argv)
    a.out = a.out or ("clips/flow" if a.flow else "clips/checkpoint2")
    a.bars = a.bars or (16 if a.flow else 8)
    os.makedirs(a.out, exist_ok=True)
    seed = a.seed if a.seed is not None else fresh_seed()
    for style in a.styles or [s for s in FORM if s != "plain" and "~" not in s]:
        style = nudged(style, parse(a.nudge)) if a.nudge else style
        for _ in range(a.seeds):
            song, lines = (flow_sketch if a.flow else sketch)(style, seed, a.bars)
            stem = os.path.join(a.out, f"{style.translate(str.maketrans('~:,', '_-_'))}_{seed}")
            song.write(stem)
            with open(f"{stem}.txt", "w") as f:
                f.write("\n".join(lines) + "\n")
            print(f"{stem}.mid")
            seed += 1


if __name__ == "__main__":
    main()
