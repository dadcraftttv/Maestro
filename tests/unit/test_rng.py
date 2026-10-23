# SPDX-License-Identifier: GPL-3.0-or-later
from maestro.rng import ComposerRng, fresh_seed


def test_composer_lcg():
    r = ComposerRng()
    r.seed(5)
    assert r.state == (5 * 2654435761 + 1) & 0xFFFFFFFF
    want = ((r.state * 1664525 + 1013904223) & 0xFFFFFFFF) >> 8
    assert r.rnd(1000) == want % 1000


def test_rnd_zero_still_advances():
    r = ComposerRng(7)
    before = r.state
    assert r.rnd(0) == 0 and r.state != before


def test_fresh_seeds_differ():
    assert len({fresh_seed() for _ in range(8)}) > 1
