# SPDX-License-Identifier: GPL-3.0-or-later
import math
import random
import pytest

T = pytest.importorskip('maestro.spike.transformer')
from maestro.spike.harness import propose
from maestro.spike.tokens import condition


def piece(pid, pitches):
    notes = [[i*24, (i+1)*24, p, 4] for i, p in enumerate(pitches)]
    return dict(id=pid, snapped=notes, runs=[(0, len(pitches)//4)], key='C',
                chords=[dict(root=0, quality='major')]*len(pitches))


def tiny(pieces):
    return T.fit(pieces, [piece('validation', [60, 62, 64, 65])], [p['id'] for p in pieces],
                 device='cpu', budget_s=3, patience=2, log=lambda s: None,
                 width=32, layers=1, heads=2, context=64, dropout=0.0)


def test_rare_events_pool_into_unk_and_loss_is_proper():
    train = [piece('a', [60, 62, 64, 65]*2), piece('b', [60, 62, 64, 67])]
    gen, run = tiny(train)
    assert ('NOTE', 72, 67, 24, 4, 0, 0) in gen.vocab.train          # seen once: pooled
    assert ('NOTE', 72, 67, 24, 4, 0, 0) not in gen.vocab.events
    assert gen.vocab.pooled == 2                                     # that event + "unseen"
    control = condition(train[0]['snapped'], train[0]['chords'], 'C', 1, 0, (0, 127), 4)
    d = gen.distribution(control, [], 0)
    special = 1 - sum(d.values())
    assert -1e-6 <= special < 1                                      # remainder sits on control tokens
    assert run['best_validation_nll'] == gen.loss([piece('validation', [60, 62, 64, 65])])['nll_nats_per_event']
    with pytest.raises(ValueError):
        gen.loss(train)
    notes, _ = propose(gen, dict(control, register=(60, 84)), 1, random.Random(0))
    assert all(60 <= p <= 84 for _, _, p, _ in notes)


def test_fit_rejects_non_train_pieces():
    with pytest.raises(ValueError):
        T.fit([piece('validation', [60]*4)], [piece('v', [60]*4)], ['train'], device='cpu')
