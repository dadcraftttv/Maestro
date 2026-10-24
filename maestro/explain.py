# SPDX-License-Identifier: GPL-3.0-or-later
"""Maestro's choices in plain words: a few bars drawn from the theory core, one choice at a time, each said the
way a player would say it (the section and its energy, the chord and why, how the pad and bass move, the bass
rhythm against the clave, how the motif develops). For spot checks (checkpoint 2); `sketch.py` plays the same
choices as a rough clip. The choices are the drafts' tendencies one by one, and making them into music is the style
book's work (bucket 3).

Task 3.2's flow (`theory/flow.py`) is the default: progressions as families, the bass on its pattern, the melody
shaped over the phrase. `--no-flow` gives Checkpoint 2's bar-by-bar draws, to compare.

    python -m maestro.explain salsa --seed 7 --bars 16 [--no-flow]"""
import argparse, re

from .rng import ComposerRng, fresh_seed
from .theory.chords import VOCAB, _resolves_to, choose_in_style, function, name, outside, roman
from .theory.flow import BASS, FLOW, bass_part, chart, check_bass, check_phrase, chord_at, held, phrase_melody, \
    progression
from .theory.drums import DRUMMER, check_drums, drum_part
from .theory.form import FORM, WORDS, Play, Theme, explain_section
from .theory.percussion import PERCUSSION, check_percussion, percussion_part
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


def passage(style="plain", seed=1, bars=8, home=Key(9, "minor"), bpm=100, room=0.5, flow=True):
    """The choices for `bars` bars, as lines of plain words."""
    return (flow_choices if flow else choices)(style, seed, bars, home, bpm, room)[0]


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



def flow_choices(style="plain", seed=1, bars=8, home=Key(9, "minor"), bpm=100, room=0.5):
    """Task 3.2's choices for `bars` bars: (lines of plain words, the take). The take holds the notes ("pad",
    "bass", "melody": (step, length, MIDI note)), a record a bar like `choices`' (bar, section, key, energy, its
    first chord) and a record a section ("plan": its family, its passes in words, its bass pattern, its phrases)
    for the summary. Whole sections are drawn, then cut at the clip's end."""
    rng = ComposerRng()
    rng.seed(seed)
    form, leading, rhythm, vocab = FORM[style], LEADING[style], RHYTHM[style], VOCAB[style]
    met = METERS["4/4"]
    end = bars * met.bar
    clave = CLAVES[rhythm.clave] if rhythm.clave else None
    play = Play(rng, home, form, bpm, met)
    while play.bar < bars:
        play.next_section(room)
    theme = Theme(rng, life=form.life)

    def key_at(step):
        return play.section_at(min(step, play.bar * met.bar - 1) // met.bar).key

    # the chords, section by section
    spans, plan, fam = [], [], None
    for s in play.sections:
        sp, fam, lines = progression(rng, FLOW[style], s.key, vocab, s.start, s.bars, met, form.phrase, fam)
        spans += sp
        plan.append({"section": s, "family": fam, "lines": lines,
                     "passes": [ln.split(": ", 2)[-1] for ln in lines if ln.startswith("  bars ")]})
    # the bass on its pattern, carrying on from section to section
    bass, pat, near = [], None, None
    for p in plan:
        s = p["section"]
        notes, pat, lines = bass_part(rng, BASS[style], spans, key_at, s.start, s.bars, met, s.energy, pat, clave,
                                      [n[0] for n in bass], near)
        bass += notes
        near = notes[-1][2] if notes else near
        p["pattern"], p["lines"] = pat, p["lines"] + lines
    bass = held(bass, play.bar * met.bar)
    why = check_bass(bass, met, clave)
    # the pad: each chord voiced under the melody's room, moving smoothly, not muddy with the bass under it
    pad, prev, again, rests = [], None, 0, 0
    for sp in spans:
        key, ch = key_at(sp.at), sp.chord
        under = [m for st, length, m in bass if st <= sp.at < st + length] or [bass[0][2]]
        try:
            n = 3 if voicings(ch, key, 3, member_range("pad"), leading, ceiling=UNDER) else 4   # four for a 9th
            for tries in range(TRIES + 1):
                v = choose_voicing(rng, ch, key, n, member_range("pad"), prev, leading, ceiling=UNDER)
                if not check_band({"pad": v, "bass": under}, key):
                    break
            again += tries
            pad += [(sp.at, sp.length, m) for m in v]
            prev = v
        except ValueError:
            rests, prev = rests + 1, None
    # the melody, a phrase at a time, over the pad
    melody = []
    for p in plan:
        s, p["phrases"] = p["section"], []
        for at in range(s.start, s.end, form.phrase):
            lo, hi = at * met.bar, (at + form.phrase) * met.bar
            floor = max((m for st, length, m in pad if st < hi and st + length > lo), default=UNDER)
            notes, lines = phrase_melody(rng, theme, spans, s.key, at, form.phrase, met, floor, clave,
                                         [n[0] for n in melody])
            bad = check_phrase(notes, spans, s.key, met, form.phrase, at)
            p["lines"] += lines + ([f"    ruled out: {bad}"] if bad else [])
            p["phrases"].append(lines)
            melody += notes
    # the drums and the percussion over the whole play (task 3.3), their words with each section
    every = [{"bar": b, "section": play.section_at(b), "energy": play.section_at(b).energy_at(b)}
             for b in range(play.bar)]
    whole, half = play.bar * met.bar, feel_for(style, "drums").pulse == "half"
    drums, percussion, kit_why = [], [], []
    for p in plan:
        p["drums"], p["percussion"] = [], []
    if DRUMMER[style]:
        drums, said = drum_part(rng, DRUMMER[style], every, met, form.phrase, whole, half)
        for s, line in said:
            next(p for p in plan if p["section"] is s)["drums"].append(line)
        kit_why.append(("drums", check_drums(drums, met, whole, half)))
    if PERCUSSION[style]:
        percussion, said = percussion_part(rng, PERCUSSION[style], every, met, whole, clave)
        for s, line in said:
            next(p for p in plan if p["section"] is s)["percussion"].append(line)
        kit_why.append(("percussion", check_percussion(percussion, met, whole, clave)))
    for p in plan:
        p["lines"] += p["drums"] + p["percussion"]
    # cut at the clip's end, in words and notes
    out = [f"{style}, seed {seed}, home {home}, {bpm} bpm (flow)"]
    for i, p in enumerate(plan):
        s = p["section"]
        if s.start >= bars:
            break
        out += ["", explain_section(s, plan[i - 1]["section"] if i else None)] + p["lines"]
    if why:
        out.append(f"  bass check: {why}")
    out += [f"  {role} check: {why}" for role, why in kit_why if why]
    out.append(f"  pad: each chord voiced under the melody, moving the shortest way"
               + (f"; drawn again {again} times (muddy with the bass)" if again else "")
               + (f"; rests under {rests} chords" if rests else ""))

    def cut(notes):
        return [(st, min(length, end - st), m) for st, length, m in notes if st < end]
    recs = []
    for b in range(bars):
        s = play.section_at(b)
        recs.append({"bar": b, "section": s, "key": s.key, "energy": s.energy_at(b),
                     "chord": chord_at(spans, b * met.bar).chord})
    take = {"pad": cut(pad), "bass": cut(bass), "melody": cut(melody), "bars": recs,
            "drums": [h for h in drums if h[0] < end], "percussion": [h for h in percussion if h[0] < end],
            "plan": [p for p in plan if p["section"].start < bars], "spans": [s for s in spans if s.at < end]}
    return out, take


def _bar_of(line):
    """The bar a line of words is about ("  drums, bar 8: ...")."""
    m = re.search(r"bar (\d+):", line)
    return int(m[1]) if m else 0


def _bars_said(lines, last):
    return [f"bar {_bar_of(ln)}, {ln.split(': ', 1)[1]}" for ln in lines if _bar_of(ln) <= last]


def summary(style, seed, bars, bpm, take, met=METERS["4/4"]):
    """The clip in a few plain lines (3.7's shape, a first draft): style, bars, key, tempo; the chords as a loop and
    how they vary; the bass; the pad; the melody's phrase; what to listen for."""
    plan = take["plan"]
    home = plan[0]["section"].key
    out = [f"{style.replace('_', ' ')}, {bars} bars, {home}, {bpm} BPM, seed {seed}"]
    for p in plan:
        s, f = p["section"], p["family"]
        a, b = s.start + 1, min(s.end, bars)
        per = {len(x) for x in f.bars}
        pace = ("a chord a bar" if per == {1} else "two chords a bar" if per == {2} else
                "chords changing every bar or half bar")
        passes = p["passes"][:(b - s.start) // f.loop]
        varied = [w for w in passes if w != "as written"]
        line = (f"Chords, bars {a}-{b}{f' (in {s.key})' if s.key != home else ''}: {f.name}, "
                f"{chart(f.spans(s.key, 0, met), s.key, met)} ({f.chords}), {pace}, round every "
                f"{f.loop} bar{'s' * (f.loop > 1)}. ")
        line += (f"{len(varied)} of its {len(passes)} rounds vary: " + "; ".join(varied) + "."
                 if varied else "Every round as written.")
        out.append(line)
        out.append(f"Bass, bars {a}-{b}: {p['pattern'].name}" + (f": {p['pattern'].why}." if p['pattern'].why else "."))
        if p.get("drums"):
            said = _bars_said(p["drums"][1:], b)
            out.append(f"Drums, bars {a}-{b}: {p['drums'][0].split('drums: ', 1)[1]}"
                       + (f"; then {'; '.join(said)}" if said else "") + ".")
        if p.get("percussion"):
            parts = re.sub(r" \([^)]*\)", "", p["percussion"][0].split("percussion: ", 1)[1])
            closes = [ln for ln in p["percussion"][1:] if _bar_of(ln) <= b]
            out.append(f"Percussion, bars {a}-{b}: {parts}" + ("; an abanico into the next section" if closes else "")
                       + ".")
    out.append("Pad: holds each chord, its voices moving the shortest way, under the melody.")
    phrases = [ph for p in plan for ph in p["phrases"]][:max(1, bars // FORM[style].phrase)]
    n = FORM[style].phrase
    out.append(f"Melody: {len(phrases)} phrase{'s' * (len(phrases) > 1)} of {n} bars. Each states the motif, "
               f"climbs to a peak about two-thirds in, ends its first half open and lands home on the cadence: "
               + "; ".join(ln.strip() for ph in phrases for ln in ph[1:] if "then" in ln) + ".")
    if take.get("drums"):
        kicks = {h[0] for h in take["drums"] if h[4] == "kick"}
        locked = sum(1 for n in take["bass"] if n[0] in kicks)
        out.append(f"Kick and bass: the kick lands with {round(100 * locked / max(1, len(take['bass'])))}% of the bass "
                   f"notes.")
    out.append("Listen for: does it flow, chords going round and coming home rather than wandering; does the bass "
               "feel like the style; does each phrase sound like a question and its answer"
               + ("; does the drummer feel like the style, its fills leading into the next phrase"
                  if take.get("drums") else "")
               + ("; does the percussion sit with the clave and lift in the loud sections"
                  if take.get("percussion") else "") + ".")
    return out

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("style", nargs="?", default="plain", choices=sorted(FORM))
    p.add_argument("--seed", type=int, default=None, help="a fresh one when left out")
    p.add_argument("--bars", type=int, default=8)
    p.add_argument("--no-flow", dest="flow", action="store_false", help="Checkpoint 2's bar-by-bar draws")
    a = p.parse_args(argv)
    print("\n".join(passage(a.style, fresh_seed() if a.seed is None else a.seed, a.bars, flow=a.flow)))


if __name__ == "__main__":
    main()
