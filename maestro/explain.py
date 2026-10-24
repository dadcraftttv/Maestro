# SPDX-License-Identifier: GPL-3.0-or-later
"""Maestro's choices in plain words: a few bars drawn from the theory core, one choice at a time, each said the
way a player would say it (the section and its energy, the chord and why, how the pad and bass move, the bass
rhythm against the clave, how the motif develops). For spot checks (checkpoint 2), not for listening: the choices
are the drafts' tendencies one by one, and making them into music is the style book's work (bucket 3).

    python -m maestro.explain salsa --seed 7 --bars 8"""
import argparse

from .rng import ComposerRng, fresh_seed
from .theory.chords import VOCAB, _resolves_to, choose_in_style, function, name, outside, roman
from .theory.form import FORM, WORDS, Play, Theme, explain_section
from .theory.pitch import Key
from .theory.rhythm import CLAVES, METERS, RHYTHM, check_onsets, choose_onsets, explain_feel, explain_onsets, \
    feel_for
from .theory.voicing import LEADING, check_band, choose_voicing, explain, member_range, note_name

TRIES = 10   # draws of a bass rhythm before giving up on sitting with the clave
LEAN = 12   # how much more often a section opens on its tonic, and a tension chord goes where it leans


def _notes(key, v):
    return " ".join(note_name(key, m) for m in v)


def passage(style="plain", seed=1, bars=8, home=Key(9, "minor"), bpm=100, room=0.5):
    """The choices for `bars` bars, as lines of plain words."""
    rng = ComposerRng()
    rng.seed(seed)
    form, leading, rhythm = FORM[style], LEADING[style], RHYTHM[style]
    met = METERS["4/4"]
    clave = CLAVES[rhythm.clave] if rhythm.clave else None
    play = Play(rng, home, form, bpm, met)
    while play.bar < bars:
        play.next_section(room)
    theme = Theme(rng, life=form.life)
    out = [f"{style}, seed {seed}, home {home}, {bpm} bpm"]
    pad = bass = leans = None
    for b in range(bars):
        s = play.section_at(b)
        key = s.key
        if s.start == b:
            i = play.sections.index(s)
            out.append("")
            out.append(explain_section(s, play.sections[i - 1] if i else None))
        # the chord: a section leans to open on its tonic; after a tension chord, where it leans weighs most
        def lands(c):
            return c.root == leans and c.quality in ("maj", "min")
        ch = choose_in_style(rng, key, VOCAB[style],
                             lambda c: LEAN if lands(c) or (s.start == b and c.root == 0) else 1)
        fn, why = function(ch, key)
        line = f"bar {b + 1}: {name(ch, key)} ({roman(ch, key)}), {fn}: {why}"
        if lands(ch):
            line += "; the tension resolves"
        rare = outside(ch, key, VOCAB[style])
        if rare:
            line += f". Unusual: {rare}"
        out.append(line)
        leans = _resolves_to(ch) if fn == "tension" else None
        # the pad and the bass
        try:
            new = choose_voicing(rng, ch, key, 3, member_range("pad"), pad, leading)
            out.append("  pad: " + (_notes(key, new) if pad is None else explain(pad, new, key)))
            pad = new
        except ValueError as e:
            out.append(f"  pad: rests ({e})")
            pad = None
        new = choose_voicing(rng, ch, key, 1, member_range("bass"), bass, leading, on_bass=True)
        out.append("  bass: " + (_notes(key, new) if bass is None else explain(bass, new, key)))
        bass = new
        for why in check_band({"pad": pad or [], "bass": bass}, key):
            out.append(f"  ruled out: {why}")
        # the bass rhythm, two bars at a time (a clave's length), busier with more energy
        if b % 2 == 0:
            feel = feel_for(style, "bass")
            n = 3 + round(4 * s.energy_at(b))
            tries = 0
            while True:
                on = choose_onsets(rng, met, n, rhythm, feel.pulse, bars=2, keep=(0,))
                crossed = check_onsets(on, met, 2, clave)
                if crossed is None or tries == TRIES:
                    break
                tries += 1
            line = f"  bass rhythm, bars {b + 1}-{b + 2} ({explain_feel(feel)}): {explain_onsets([o + b * met.bar for o in on], met)}"
            if clave is not None:
                c = clave.name.replace("_", " ")
                again = "once" if tries == 1 else f"{tries} times"
                line += (f"; sits with the {c} clave" + (f" (drawn again {again}: crossed)" if tries else "")
                         if crossed is None else f"; still {crossed} after {TRIES} draws")
            out.append(line)
        # the melody's motif, once a phrase
        if b % form.phrase == 0:
            m, how = theme.next()
            out.append(f"  melody: {WORDS[how]}: " + " ".join(key.name(key.degree(d) % 12) for d in m.steps))
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("style", nargs="?", default="plain", choices=sorted(FORM))
    p.add_argument("--seed", type=int, default=None, help="a fresh one when left out")
    p.add_argument("--bars", type=int, default=8)
    a = p.parse_args(argv)
    print("\n".join(passage(a.style, fresh_seed() if a.seed is None else a.seed, a.bars)))


if __name__ == "__main__":
    main()
