# SPDX-License-Identifier: GPL-3.0-or-later
from types import SimpleNamespace

import pytest

from maestro.explain import flow_choices
from maestro.rng import ComposerRng
from maestro.stylebook import STYLES, StyleError, part
from maestro.theory import drums as D
from maestro.theory.drums import DRUMMER, GMD, KIT, check_drums, drum_part
from maestro.theory.percussion import PERCUSSION, VOICES, Pattern, check_percussion, percussion_part
from maestro.theory.rhythm import CLAVES, METERS

MET = METERS["4/4"]


def _rng(seed):
    r = ComposerRng()
    r.seed(seed)
    return r


def _bars(*sections):
    """A record a bar for sections given as (bars, energy)."""
    out, start = [], 0
    for n, e in sections:
        s = SimpleNamespace(start=start, end=start + n, kind="home")
        out += [{"bar": b, "section": s, "energy": e} for b in range(start, start + n)]
        start += n
    return out


def test_gmds_counts_are_shares_and_every_groove_keeps_a_backbeat():
    for style, g in GMD.items():
        assert g["takes"] > 0 and g["bars"] > 0, style
        assert all(0 <= x <= 100 for row in g["odds"].values() for x in row), style
        for groove in g["grooves"]:
            assert {4, 12} & set(groove["snare"]), (style, groove)
            assert all(0 <= p < 16 and p % 2 == 0 for p in groove["kick"] + groove["snare"]), (style, groove)


def test_every_style_has_a_drummer_or_percussion_and_salsa_has_no_kit():
    assert DRUMMER["salsa"] is None and PERCUSSION["salsa"]
    for style in STYLES:
        assert DRUMMER[style] or PERCUSSION[style], style


@pytest.mark.parametrize("style", [s for s in STYLES if DRUMMER[s]])
def test_the_drummer_passes_its_check_and_varies(style):
    half = part(style, "time", "feel").get("drums", {}).get("pulse") == "half"
    recs, end = _bars((8, 0.3), (16, 0.8)), 24 * MET.bar
    plays = []
    for seed in range(1, 21):
        hits, lines = drum_part(_rng(seed), DRUMMER[style], recs, MET, 4, end, half)
        assert check_drums(hits, MET, end, half) is None, (style, seed)
        assert any(h[0] == 0 and h[4] == "crash" for h in hits) and any(h[0] == 8 * MET.bar and h[4] == "crash"
                                                                         for h in hits), (style, seed)
        plays.append(tuple(hits))
    assert len(set(plays)) == len(plays)   # no two seeds alike (decision 9)


def test_fills_and_rolls_come_only_at_a_phrases_end():
    recs, end = _bars((16, 0.6)), 16 * MET.bar
    for style in ("power_rock", "trap"):
        half = style == "trap"
        for seed in range(1, 21):
            hits, _ = drum_part(_rng(seed), DRUMMER[style], recs, MET, 4, end, half)
            for step, _, _, _, v in hits:   # a tom, or a roll's note between 16ths (trap's hats also turn mid-bar)
                if v in D.TOMS or step % 6 and not DRUMMER[style].turns:
                    assert step // MET.bar % 4 == 3, (style, seed, step, v)


def test_the_drum_check_says_what_is_wrong():
    ok = [(0, 6, KIT["kick"], 100, "kick"), (24, 6, KIT["snare"], 100, "snare")]
    assert check_drums(ok, MET, MET.bar) is None
    assert "off the grid" in check_drums(ok + [(30.5, 6, 42, 80, "hat")], MET, MET.bar)
    assert "three hands" in check_drums(ok + [(24, 6, 42, 80, "hat"), (24, 6, 49, 80, "crash")], MET, MET.bar)
    assert "no backbeat" in check_drums(ok[:1], MET, MET.bar)
    assert "two snares" in check_drums(ok + ok[1:], MET, MET.bar)


def test_the_style_book_names_only_gmd_styles(monkeypatch):
    monkeypatch.setitem(part("power_rock", "members", "drums"), "grooves", {"polka": 1})
    with pytest.raises(StyleError, match="no GMD style 'polka'"):
        D._drummer("power_rock")


def test_the_cascara_sits_with_its_clave_and_crosses_the_other():
    timbales = next(p for p in PERCUSSION["salsa"] if p.name == "timbales")
    cascara = next(x for x in timbales.patterns if x.name == "cáscara 2-3")
    on = [h[0] * 6 for h in cascara.hits]
    two_three = CLAVES["son_2-3"]
    assert check_percussion([(s, 6, 37, 90, "timbales") for s in on], MET, 2 * MET.bar, two_three) is None
    assert "crossed" in check_percussion([(s, 6, 37, 90, "timbales") for s in on], MET, 2 * MET.bar,
                                         two_three.flipped())


def test_salsas_percussion_sits_with_the_clave_and_moves_to_the_bells_when_loud():
    clave = CLAVES["son_2-3"]
    recs, end = _bars((8, 0.3), (8, 0.8)), 16 * MET.bar
    for seed in range(1, 31):
        hits, _ = percussion_part(_rng(seed), PERCUSSION["salsa"], recs, MET, end, clave)
        assert check_percussion(hits, MET, end, clave) is None, seed
        quiet = {h[2] for h in hits if h[0] < 8 * MET.bar - 24}
        loud = {h[2] for h in hits if h[0] >= 8 * MET.bar + 24}
        assert VOICES["shell"] in quiet and VOICES["bongo bell"] not in quiet, seed
        assert VOICES["timbale bell"] in loud and VOICES["shell"] not in loud, seed


def test_a_bad_percussion_pattern_says_why():
    with pytest.raises(ValueError, match="bad hit"):
        Pattern("x", ((0, "cowbell", 90),))
    with pytest.raises(ValueError, match="bad hit"):
        Pattern("x", ((16, "claves", 90),))


def test_the_flow_explains_the_drums_and_the_percussion():
    for style in ("power_rock", "salsa"):
        lines, take = flow_choices(style, seed=3, bars=16)
        role = "percussion" if style == "salsa" else "drums"
        assert take[role] and any(ln.startswith(f"  {role}: ") for ln in lines), style
        assert not any(" check: " in ln for ln in lines), style
