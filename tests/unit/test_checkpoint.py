# SPDX-License-Identifier: GPL-3.0-or-later
"""Checkpoint 3's listening set: a member alone, cut from the full play."""
from maestro.checkpoint import alone, window
from maestro.song import Song


def test_a_member_alone_is_its_busiest_16_bars_moved_to_the_start():
    s = Song(tempo=112, source={"seed": 3})
    m = s.member("bass", "bass", 38)
    bar = s.bar_steps()
    m.add(0, 24, 40)                                  # bar 1: one note
    for k in range(20):                               # bars 17-36: one a bar, the last 4 past the window
        m.add((16 + k) * bar, bar + 24, 45)           # each rings into the next bar
    m.slide(16 * bar, 12, 2)
    assert window(m, bar, 48) == 16
    one = alone(s, m, 16)
    notes = one.members[0].notes
    assert len(notes) == 16 and notes[0].step == 0
    assert all(n.step + n.steps <= 16 * bar for n in notes)   # cut at the window's end
    assert one.members[0].slides == [(0, 12, 2, 0)] and one.source["bars"] == "17-32"
