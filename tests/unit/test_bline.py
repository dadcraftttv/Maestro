"""Optional bass line: musical limits, memory and isolated random demand."""
from maestro.port import Composer, SCALE_N, NKINDS


def row(c, drive=0.5):
    c.bline(drive)
    return c.out.pop()[1]


def test_bline_limits_and_density():
    rests = [0, 0]
    notes = accents = slides = 0
    for drive in (0, 1):
        for seed in range(100):
            c = Composer(seed=seed)
            c.send("scale", seed % 8)
            n = SCALE_N[c.scale]
            p = row(c, drive)
            assert len(p) == 48
            for i in range(16):
                degree, slide, accent = p[3*i:3*i+3]
                assert degree in (-1, 0, 1, 4 if n == 7 else 3, n)
                assert slide in (0, 1) and accent in (0, 1)
                if degree < 0:
                    rests[drive] += 1
                    assert not slide and not accent
                else:
                    notes += 1
                    accents += accent
                    slides += slide
                    if slide:
                        assert p[3*((i+15) % 16)] >= 0
    assert 0.1 < rests[1]/1600 < 0.25 < rests[0]/1600 < 0.4
    assert 0.18 < accents/notes < 0.32
    assert 0.07 < slides/notes < 0.2


def test_bline_base_return_sections_and_reset():
    c = Composer(seed=47)
    first = row(c)
    for _ in range(3):
        row(c)
    assert row(c) == first
    bases = []
    for k in range(NKINDS):
        c.kind = k
        row(c)
        bases.append(c.bline_base[k])
    assert len({str(p) for p in bases}) == NKINDS
    c.send("scale", 3)
    assert not any(c.bline_have) and c.bline_kind == -1


def test_bline_handover_carries_then_renews():
    c = Composer(seed=47)
    c.kind = 1
    row(c)
    old = [p[:] for p in c.bline_base[1]]
    c._handover()
    row(c)
    assert c.bline_kind == 1 and c.bline_base[1] == old
    c.pos = 3
    c._advance()
    assert c.handover == 2 and not any(c.bline_have)
    row(c)
    assert c.bline_base[c.kind] != old


def test_no_bline_draws_until_requested():
    c = Composer(seed=47)
    c.send("start")
    for _ in range(200):
        c.send("bar")
        c.drums(0.5, 0.3)
    assert not any(c.bline_have)
    assert all(selector != "bline" for selector, _ in c.out)
