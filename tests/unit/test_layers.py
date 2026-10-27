# SPDX-License-Identifier: GPL-3.0-or-later
"""Layering (task 3.6): who plays when, a phrase at a time by the energy; the band never thinner than two (DadCraft,
Oct 26), breakdowns, rotation and slow change (after Tangerine, research round 6). Synthwave first, then trap, then
salsa, then power rock."""
import pytest

from maestro.explain import flow_choices
from maestro.stylebook import StyleError
from maestro.theory.flow import check_arp, chord_at
from maestro.theory.layers import ANCHORS, LAYERS, check_layers, layers_from
from maestro.theory.pitch import Key
from maestro.theory.rhythm import METERS

MET = METERS["4/4"]
A_MINOR = Key(9, "minor")
LAYERED = {"synthwave": 112, "trap": 140, "salsa": 180, "power_rock": 130}   # the styles with a layer map, at their tempo


def _plays(style, n=30, bars=84):
    bpm = LAYERED[style]
    return [(flow_choices(style, seed, bars, A_MINOR, bpm)[1],
             flow_choices(style, seed, bars, A_MINOR, bpm, layers=False)[1]) for seed in range(1, 1 + n)]


ALL = {s: _plays(s) for s in LAYERED}
PLAYS, LY = ALL["synthwave"], LAYERS["synthwave"]
each = pytest.mark.parametrize("style", sorted(LAYERED))


@each
def test_every_phrase_keeps_two_members_one_carrying_the_chords_or_bass(style):
    for take, _ in ALL[style]:
        assert check_layers(take["layers"], LAYERS[style]) is None
        for x in take["layers"]:
            assert len(x.playing) + x.melody >= 2 and any(r in ANCHORS for r in x.playing)
        bands = [(x.playing, x.melody) for x in take["layers"]]       # the thinnest band holds one phrase
        assert not any(a == b and len(a[0]) + a[1] <= LAYERS[style].least for a, b in zip(bands, bands[1:]))


@each
def test_a_resting_member_plays_nothing_in_its_phrase_and_the_rest_is_the_same_notes(style):
    for take, plain in ALL[style]:
        for x in take["layers"]:
            lo, hi = x.at * MET.bar, (x.at + x.bars) * MET.bar
            for r in [*LAYERS[style].join, "melody"]:     # salsa's pad sits out unlisted (task 3.4c)
                rests = r not in x.playing if r != "melody" else not x.melody
                if rests:
                    notes = ([n for ns in take[r].values() for n in ns] if r == "guitar" else    # power rock's L and R
                             take[r] + take.get("lead2", []) * (r == "melody"))                # its second lead too
                    assert not [n for n in notes if lo <= n[0] < hi], (r, x.at)
        # the pad and melody aren't slowly changed: what plays is what was drawn
        for r in ("pad", "melody"):
            assert {(n[0], n[2]) for n in take[r]} <= {(n[0], n[2]) for n in plain[r]}


@pytest.mark.parametrize("style", sorted(s for s in LAYERED if any(LAYERS[s].join.values())))
def test_the_band_grows_with_the_energy(style):    # salsa's band plays throughout: its parts lead (DadCraft, Oct 26)
    sizes = {}
    for take, _ in ALL[style]:
        for x in take["layers"]:
            if not x.down and not x.first:   # breakdowns and power rock's opening aside
                e = x.section.energy_at(x.at)    # quiet: below the last member's join (power rock's drums, 0.3)
                if e >= 0.6 or e < max(LAYERS[style].join.values()):
                    sizes.setdefault(e >= 0.6, []).append(len(x.playing))
    low, high = (sum(v) / len(v) for v in (sizes[False], sizes[True]))
    full = len(LAYERS[style].join)              # trap lists three, synthwave four: less room to grow
    assert high > full - 0.5 and high > low + 0.3, (low, high)


@each
def test_rotation_keeps_the_size_and_breakdowns_come_before_a_louder_section(style):
    swaps = downs = 0
    ly = LAYERS[style]
    for take, _ in ALL[style]:
        ls = take["layers"]
        for k, x in enumerate(ls):
            if any(w.startswith("rotation") for w in x.said):
                swaps += 1
                assert len(x.playing) == len(ls[k - 1].playing) and x.playing != ls[k - 1].playing
            if x.down:
                downs += 1
                assert x.playing == set(ly.breakdown) - {"melody"} and x.melody == ("melody" in ly.breakdown)
                assert x.at + x.bars == x.section.end
            else:
                assert x.melody
    assert downs and (swaps or not ly.rotate[1])


def test_slow_change_one_member_at_a_time_and_the_arp_stays_on_its_chords():
    changes = 0
    for (take, _), seed in zip(PLAYS, range(1, 31)):
        lines, _ = flow_choices("synthwave", seed, 84, A_MINOR, 112)
        said = [ln for ln in lines if "slow change" in ln]
        changes += len(said)
        bars_ = [ln.split(":")[0] for ln in said]
        assert len(bars_) == len(set(bars_))
        assert check_arp(take["arp"], take["spans"], lambda st: next(
            x.section.key for x in take["layers"] if x.at * MET.bar <= st < (x.at + x.bars) * MET.bar)) is None
    assert changes


def test_salsa_keeps_its_clave_and_breaks_down_to_the_montuno():
    for take, plain in ALL["salsa"]:
        clave = [h for h in take["percussion"] if h[4] == "clave"]
        downs = [(x.at * MET.bar, (x.at + x.bars) * MET.bar) for x in take["layers"] if x.down]
        assert clave == [h for h in plain["percussion"] if h[4] == "clave"]     # the percussion plays throughout
        for lo, hi in downs:
            assert not [n for r in ("bass", "horns", "melody") for n in take[r] if lo <= n[0] < hi]
            assert [n for n in take["keys"] if lo <= n[0] < hi]


def test_power_rock_opens_on_its_guitars_and_breaks_down_to_the_bass_and_drums():
    for take, _ in ALL["power_rock"]:
        first, *rest = take["layers"]
        assert first.first and first.playing == {"guitar"} and first.melody      # the rhythm guitars and the lead
        assert not [n for r in ("bass", "drums") for n in take[r] if n[0] < first.bars * MET.bar]
        assert not any(x.first for x in rest)
        for x in rest:
            if x.down:
                lo, hi = x.at * MET.bar, (x.at + x.bars) * MET.bar
                assert not [n for r in ("guitar L", "guitar R") for n in take["guitar"][r] if lo <= n[0] < hi]
                assert not [n for r in ("melody", "lead2") for n in take[r] if lo <= n[0] < hi]
                assert [n for n in take["drums"] if lo <= n[0] < hi]


def test_bad_entries_are_refused():
    roles = {"pad", "bass", "arp", "drums"}
    good = {"join": {"pad": 0, "drums": 0.5}, "breakdowns": 20, "breakdown": ["pad", "drums"]}
    assert layers_from(good, roles, "t").least == 2
    assert layers_from({**good, "breakdown": ["melody", "pad"]}, roles, "t").breakdown == ("melody", "pad")
    assert layers_from({**good, "opens": ["melody", "pad"]}, roles, "t").opens == ("melody", "pad")
    for bad in ({"join": {"melody": 0.2, "pad": 0}}, {"join": {"drums": 0.2}}, {"join": {"pad": 1.5}},
                {"least": 1}, {"breakdown": []}, {"breakdown": ["drums"]}, {"breakdown": ["pad", "bass"]},
                {"breakdown": ["melody", "drums"]}, {"breakdown": ["melody"]},
                {"opens": ["pad"]}, {"opens": ["melody", "drums"]}, {"opens": ["pad", "bass"]},
                {"rotate": [8]}, {"changes": [3, 2]}, {"loud": 1}):
        with pytest.raises(StyleError):
            layers_from({**good, **bad}, roles, "t")
