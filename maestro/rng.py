# SPDX-License-Identifier: GPL-3.0-or-later
"""Seeded randomness. Every choice Maestro makes draws from one of these, so a seed replays a piece exactly (for
tests and the parity check) and a fresh seed each play keeps plays apart (decision 9)."""
import os

MASK = 0xFFFFFFFF


class ComposerRng:
    """dcs_composer's generator, bit for bit: a 32-bit LCG (Numerical Recipes constants), drawn from bits 8-31."""

    def __init__(self, state=0):
        self.state = state & MASK

    def seed(self, f):
        """The composer's `seed <f>` message: (unsigned)f * 2654435761 + 1."""
        self.state = (int(f) * 2654435761 + 1) & MASK

    def rnd(self, n):
        """0..n-1 (0 when n <= 0, still advancing, like the C)."""
        self.state = (self.state * 1664525 + 1013904223) & MASK
        return (self.state >> 8) % n if n > 0 else 0


def fresh_seed():
    """A new seed for a new play (decision 9: no two plays alike)."""
    return int.from_bytes(os.urandom(4), "little")
