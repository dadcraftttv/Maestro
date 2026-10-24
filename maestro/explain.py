# SPDX-License-Identifier: GPL-3.0-or-later
"""Maestro's choices in plain words: a few bars drawn from the theory core, one choice at a time, each said the
way a player would say it (the section and its energy, the chord and why, how the pad and bass move, the bass
rhythm against the clave, how the motif develops). For spot checks (checkpoint 2); `sketch.py` plays the same
choices as a rough clip. The choices are the drafts' tendencies one by one, and making them into music is the style
book's work (bucket 3).

    python -m maestro.explain salsa --seed 7 --bars 8"""
import argparse

from .rng import ComposerRng, fresh_seed
from .theory.chords import VOCAB, _resolves_to, choose_in_style, function, name, outside, roman
from .theory.form import FORM, WORDS, Play, Theme, explain_section
from .theory.pitch import Key
from .theory.rhythm import CLAVES, METERS, RHYTHM, check_clave, check_onsets, choose_onsets, explain_feel, explain_onsets, \
    feel_for
from .theory.voicing import LEADING, check_band, choose_voicing, explain, member_range, note_name, voicings

TRIES = 10   # draws of a bass rhythm before giving up on sitting with the clave
LEAN = 12   # how much more often a section opens on its tonic, and a tension chord goes where it leans
SAY = 2     # bars between statements of the motif (a statement and its answer)
UNDER = 77  # the pad stays under F5, leaving the melody its own register on top


def _notes(key, v):
    return " ".join(note_name(key, m) for m in v)


def _melody_on(m, at, end):
    """The statement's onsets from step `at`, the ones before `end` (the clip's end)."""
    on, t = [], at
    for length in m.lengths:
        if t < end:
            on.append(t)
        t += length
    return on


def _crosses(m, at, clave, end, before):
    """Whether the melody crosses the clave once this statement joins the notes `before` it."""
    return check_clave([t % clave.length for t in before + _melody_on(m, at, end)], clave) is not None


def passage(style="plain", seed=1, bars=8, home=Key(9, "minor"), bpm=100, room=0.5):
    """The choices for `bars` bars, as lines of plain words."""
    return choices(style, seed, bars, home, bpm, room)[0]


def choices(style="plain", seed=1, bars=8, home=Key(9, "minor"), bpm=100, room=0.5):
    """The choices for `bars` bars: (lines of plain words, one record a bar). A record holds the bar's section,
    key, energy, chord, pad and bass notes, and on the bars they start, the bass onsets (steps from bar 1) and the
    motif; `sketch.py` plays them, so what is heard is what the words say."""
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
    recs, sung = [], []   # sung: the melody's onsets so far
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
        rec = {"bar": b, "section": s, "key": key, "energy": s.energy_at(b), "chord": ch}
        recs.append(rec)
        leans = _resolves_to(ch) if fn == "tension" else None
        # the bass, then the pad over it (drawn again while the two are muddy together)
        new_bass = choose_voicing(rng, ch, key, 1, member_range("bass"), bass, leading, on_bass=True)
        try:
            n = 3 if voicings(ch, key, 3, member_range("pad"), leading, ceiling=UNDER) else 4   # four for a 9th
            for tries in range(TRIES + 1):
                new = choose_voicing(rng, ch, key, n, member_range("pad"), pad, leading, ceiling=UNDER)
                muddy = check_band({"pad": new, "bass": new_bass}, key)
                if not muddy:
                    break
            line = _notes(key, new) if pad is None else explain(pad, new, key)
            if tries:
                line += f" (drawn again {'once' if tries == 1 else f'{tries} times'}: muddy with the bass)"
            out.append("  pad: " + line)
            pad = new
        except ValueError as e:
            out.append(f"  pad: rests ({e})")
            pad = None
        out.append("  bass: " + (_notes(key, new_bass) if bass is None else explain(bass, new_bass, key)))
        bass = new_bass
        rec["pad"], rec["bass"] = pad, bass
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
            rec["bass_on"] = [o + b * met.bar for o in on]
        # the melody's motif, every SAY bars
        if b % SAY == 0:
            m, how = theme.next()
            at, where = b * met.bar, ""
            if clave is not None and _crosses(m, at, clave, bars * met.bar, sung):   # a statement sits with the clave, a bar later if need be
                if b + 1 < bars and not _crosses(m, at + met.bar, clave, bars * met.bar, sung):
                    at, where = at + met.bar, " (a bar later, to sit with the clave)"
                else:
                    where = " (crosses the clave either way)"
            rec["motif"], rec["motif_at"] = m, at
            sung += _melody_on(m, at, bars * met.bar)
            out.append(f"  melody{where}: {WORDS[how]}: " + " ".join(key.name(key.degree(d) % 12) for d in m.steps))
    return out, recs


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("style", nargs="?", default="plain", choices=sorted(FORM))
    p.add_argument("--seed", type=int, default=None, help="a fresh one when left out")
    p.add_argument("--bars", type=int, default=8)
    a = p.parse_args(argv)
    print("\n".join(passage(a.style, fresh_seed() if a.seed is None else a.seed, a.bars)))


if __name__ == "__main__":
    main()
