# SPDX-License-Identifier: GPL-3.0-or-later
import numpy as np

from maestro.mix import loudness


def test_the_meter_reads_bs1770s_reference_tone():
    t = np.arange(44100 * 5) / 44100
    s = np.sin(2 * np.pi * 1000 * t)
    assert abs(loudness(np.stack([s, 0 * s], 1)) + 3.01) < 0.1    # a 1 kHz sine at full scale, one channel
    assert loudness(np.zeros((44100, 2))) is None


def test_a_member_resting_half_the_clip_reads_as_loud_as_when_it_plays():
    t = np.arange(44100 * 8) / 44100
    s = 0.25 * np.sin(2 * np.pi * 440 * t)
    half = s * (t < 4)
    assert abs(loudness(np.stack([s, s], 1)) - loudness(np.stack([half, half], 1))) < 0.5
