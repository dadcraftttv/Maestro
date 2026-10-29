# SPDX-License-Identifier: GPL-3.0-or-later
"""Train-only chord-conditioned event trigram; no tensor runtime."""
from collections import Counter, defaultdict
import math

from .tokens import TONIC, encode


def events(notes, bar, tonic):
    return [tuple(t) for t in encode(notes, bar, bar + 1, tonic)
            if t[0] in ('NOTE', 'REST')]


class NGram:
    """Longest observed context, then chord/position, then position, then unigram.

    Add-alpha probabilities over training event vocabulary plus one UNK outcome.
    Positions remain fields of the frozen records. No held-out vocabulary fitting.
    """
    def __init__(self, alpha=0.1):
        if alpha <= 0:
            raise ValueError('alpha must be positive')
        self.alpha = alpha
        self.counts = defaultdict(Counter)
        self.vocabulary = set()
        self.training_ids = set()

    @staticmethod
    def keys(control, prefix, pos):
        chord = tuple(control['upcoming_chords'][min(pos // 24, 3)])
        tail = tuple(tuple(t) for t in prefix[-2:])
        return [(chord, pos, tail), (chord, pos), (pos,), ()]

    def fit(self, pieces, train_ids):
        """Reject accidental non-train records; reset before fitting."""
        allowed = set(train_ids)
        self.counts.clear()
        self.vocabulary.clear()
        self.training_ids.clear()
        for piece in pieces:
            if piece['id'] not in allowed:
                raise ValueError('non-train piece passed to fit')
            self.training_ids.add(piece['id'])
            for lo, hi in piece['runs']:
                for bar in range(lo, hi):
                    control = {'upcoming_chords': [(c['root'], c['quality'])
                               for c in piece['chords'][bar*4:bar*4+4]]}
                    prefix = []
                    for event in events(piece['snapped'], bar, TONIC.get(piece['key'], 0)):
                        self.vocabulary.add(event)
                        for key in self.keys(control, prefix, event[1]):
                            self.counts[key][event] += 1
                        prefix.append(event)
        if not self.vocabulary:
            raise ValueError('empty training data')
        return self

    def distribution(self, control, prefix, pos):
        for key in self.keys(control, prefix, pos):
            if key in self.counts:
                return self.counts[key]
        raise RuntimeError('fit before generation')

    def probability(self, event, control, prefix, pos):
        counts = self.distribution(control, prefix, pos)
        return (counts.get(tuple(event), 0) + self.alpha) / (
            counts.total() + self.alpha * (len(self.vocabulary) + 1))

    def loss(self, pieces):
        """Teacher-forced unmasked event NLL in nats; includes unseen events."""
        nll = count = unknown = 0
        for piece in pieces:
            if piece['id'] in self.training_ids:
                raise ValueError('training piece passed to held-out evaluation')
            for lo, hi in piece['runs']:
                for bar in range(lo, hi):
                    control = {'upcoming_chords': [(c['root'], c['quality'])
                               for c in piece['chords'][bar*4:bar*4+4]]}
                    prefix = []
                    for event in events(piece['snapped'], bar, TONIC.get(piece['key'], 0)):
                        nll -= math.log(self.probability(event, control, prefix, event[1]))
                        count += 1
                        unknown += event not in self.vocabulary
                        prefix.append(event)
        if not count:
            raise ValueError('empty evaluation')
        return {'events': count, 'unknown_events': unknown, 'nll_nats_per_event': nll / count}
