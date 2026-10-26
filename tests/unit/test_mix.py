# SPDX-License-Identifier: GPL-3.0-or-later
import numpy as np

from maestro.mix import check, loudness
from maestro.stylebook import mix_targets


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


def test_the_check_says_what_is_off_and_the_gain_that_meets_it():
    roles = {"lead": "melody", "pad": "pad", "kick": "drums"}
    lines, fit = check({"lead": -20, "pad": -18, "kick": -21}, roles, mix_targets("synthwave"))
    assert any("pad" in ln and "OFF" in ln for ln in lines) and not any("kick" in ln and "OFF" in ln for ln in lines)
    assert fit["pad"] == -9.5                     # from +2 to the middle of -10..-5
    assert any("the melody -2.0 dB over" in ln and "OFF" in ln for ln in lines)
