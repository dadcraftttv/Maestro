# SPDX-License-Identifier: GPL-3.0-or-later
from maestro.explain import flow_choices, passage
from maestro.sketch import TEMPO, flow_sketch
from maestro.stylebook import STYLES
from maestro.theory.chords import VOCAB, Chord
from maestro.theory.flow import BASS, FLOW, Family, cadence, check_bass, check_family, check_phrase, chord_at, \
    progression, _home, _pulls_home
from maestro.theory.form import FORM
from maestro.theory.pitch import Key
from maestro.theory.rhythm import CLAVES, METERS
from maestro.rng import ComposerRng

MET = METERS["4/4"]
A_MINOR, C_MAJOR = Key(9, "minor"), Key(0, "major")


def _rng(seed):
    r = ComposerRng()
    r.seed(seed)
    return r


def test_every_style_has_a_family_for_a_major_and_a_minor_key():
    for style in STYLES:
        for key in (A_MINOR, C_MAJOR):
            assert any(check_family(f, key, VOCAB[style]) is None for f in FLOW[style].families), (style, key)


def test_the_check_rules_out_the_wrong_mode_and_chords_outside_the_style():
    montuno = next(f for f in FLOW["salsa"].families if f.name == "montuno vamp")
    assert "major" in check_family(montuno, C_MAJOR, VOCAB["salsa"])
    assert check_family(Family("phrygian", "i | bII"), A_MINOR, VOCAB["salsa"])   # bII isn't salsa's
    assert check_family(Family("vamp", "i | i"), A_MINOR, VOCAB["salsa"]) == "one chord: it doesn't move"


def test_a_cadence_lands_home_on_every_family():
    for style in STYLES:
        for key in (A_MINOR, C_MAJOR):
            for f in FLOW[style].families:
                if check_family(f, key, VOCAB[style]) is None:
                    sp, _ = cadence(f.spans(key, 0, MET), key, VOCAB[style], MET)
                    assert _home(sp[-1].chord), (style, f.name)
                    assert _pulls_home(sp[-2].chord) or sp[-2].chord.root in (5, 10), (style, f.name)


def test_a_section_plays_its_loop_round_and_round_landing_each_phrase():
    for seed in range(1, 30):
        sp, fam, _ = progression(_rng(seed), FLOW["salsa"], A_MINOR, VOCAB["salsa"], 0, 16, MET, 8)
        assert [s.at for s in sp] == sorted(s.at for s in sp)
        assert all(a.at + a.length == b.at for a, b in zip(sp, sp[1:])) and sp[-1].at + sp[-1].length == 16 * MET.bar
        for end in (8, 16):   # each phrase's last chord is home
            assert _home(chord_at(sp, end * MET.bar - 1).chord)
        first = fam.spans(A_MINOR, 0, MET)
        assert sp[:len(first)] == first   # the first pass as written


def test_the_tumbao_skips_the_one_and_sits_with_the_clave():
    clave = CLAVES["son_2-3"]
    for seed in range(1, 8):
        lines, take = flow_choices("salsa", seed, 32, A_MINOR, TEMPO["salsa"])
        bass = take["bass"]
        assert check_bass(bass, MET, clave) is None, seed
        plan = take["plan"][0]
        if plan["pattern"].name != "tumbao on the one":
            first = plan["section"]
            ones = [s for s, _, _ in bass if s % MET.bar == 0 and first.start * MET.bar <= s < first.end * MET.bar]
            assert not ones, seed


def test_every_phrase_is_shaped():
    for style in STYLES:
        phrase = FORM[style].phrase
        for seed in (1, 2, 3):
            _, take = flow_choices(style, seed, 32, A_MINOR, TEMPO[style])
            for p in take["plan"]:
                s = p["section"]
                for at in range(s.start, min(s.end, 32), phrase):
                    lo, hi = at * MET.bar, (at + phrase) * MET.bar
                    notes = [n for n in take["melody"] if lo <= n[0] < hi]
                    if hi <= 32 * MET.bar:
                        assert check_phrase(notes, take["spans"], s.key, MET, phrase, at) is None, (style, seed, at)


def test_a_flow_sketch_plays_what_it_says_and_the_melody_is_on_top():
    for style in STYLES:
        song, lines = flow_sketch(style, seed=4, bars=16)
        assert lines[0].startswith(style.replace("_", " ")) and "In detail:" in lines
        assert not any(" check: " in ln or ln.startswith("    ruled out") for ln in lines), style
        parts = {m.name: m.notes for m in song.members}
        assert all(parts[n] for n in ("pad", "bass", "melody")), style
        assert parts.get("drums") or parts.get("percussion"), style   # salsa: percussion, no kit
        for m in parts["melody"]:
            under = [p for p in parts["pad"] if p.step <= m.step < p.step + p.steps]
            assert all(m.pitch > p.pitch for p in under), style


def test_a_seed_replays_its_flow_and_another_differs():
    assert passage("salsa", seed=5, bars=16) == passage("salsa", seed=5, bars=16)
    assert passage("salsa", seed=5, bars=16) != passage("salsa", seed=6, bars=16)
