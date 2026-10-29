"""Public fixtures for the frozen corpus representation and causal controls."""
import pytest
from maestro.spike.tokens import clipped, condition, decode, encode


def test_exact_events_and_transposition():
    notes = [[0, 24, 60, 0], [48, 96, 67, 7]]
    tokens = [['BAR', 0], ['NOTE', 0, 58, 24, 0, 0, 0],
              ['REST', 24, 24], ['NOTE', 48, 65, 48, 7, 0, 0], ['END']]
    assert encode(notes, 0, 1, 2) == tokens
    assert decode(tokens, 2) == notes
    assert decode(tokens, 3) == [[0, 24, 61, 0], [48, 96, 68, 7]]


def test_clipping_ties_rests_and_empty_bars():
    notes = [[-12, 20, 57, 2], [30, 250, 65, 7], [275, 288, 69, 4]]
    assert decode(encode(notes, 0, 3, 9), 9) == clipped(notes, 0, 3)
    assert decode(encode(notes, 1, 2, 9), 9) == [[96, 192, 65, 7]]
    assert encode([], 2, 3, 0) == [['BAR', 2], ['REST', 0, 96], ['END']]
    assert encode([], 0, 0, 0) == [['END']]
    assert decode([['END']], 0) == []


def test_chords_and_nonzero_bar():
    chords = [{'root': 2, 'quality': 'minor'}] * 8
    events = encode([[96, 192, 62, 4]], 1, 2, 2, chords)
    assert events[1] == ['CHORDS', (2, 'minor'), (2, 'minor'), (2, 'minor'), (2, 'minor')]
    assert decode(events, 2) == [[96, 192, 62, 4]]


@pytest.mark.parametrize('events', [
    [['BAR', 0], ['REST', 1, 96], ['END']],
    [['BAR', 0], ['REST', 0, 97], ['END']],
    [['BAR', 0], ['REST', 0, 95], ['END']],
    [['BAR', 0], ['NOTE', 0, 60, 96, 8, 0, 0], ['END']],
    [['BAR', 0], ['REST', 0, 96]],
    [['BAR', 0], ['REST', 0, 96], ['BAR', 2]],
])
def test_existing_decoder_assertions(events):
    with pytest.raises(AssertionError):
        decode(events, 0)


def test_condition_history_is_eight_bars_and_causal():
    chords = [{'root': 0, 'quality': 'dom7'}] * 48
    notes = [[i * 96, (i + 1) * 96, 60 + i, 4] for i in range(12)]
    c = condition(notes, chords, 'C', 10, 0, (48, 84), 4)
    assert c['history_bars'] == 8
    assert c['bar_in_phrase'] == 2
    assert decode(c['previous'], 0) == notes[2:10]
    assert c['upcoming_chords'] == [(0, 'dom7')] * 4
    assert c == condition(notes[:10] + [[960, 1056, 100, 7]], chords, 'C', 10, 0, (48, 84), 4)
    first = condition(notes, chords, None, 5, 5, (0, 127), 0)
    assert first['previous'] == [['END']]
    assert first['history_bars'] == first['bar_in_phrase'] == 0
    assert first['key'] is None
    assert condition(notes, chords, 'C', 7, 5, (0, 127), 0)['history_bars'] == 2


@pytest.mark.parametrize('change', [dict(key='bogus'), dict(register=(80, 40)),
    dict(density=97), dict(run_start=11), dict(chords=[None] * 48)])
def test_bad_controls(change):
    args = dict(notes=[], chords=[{'root': 0, 'quality': 'major'}] * 48,
                key='C', bar=10, run_start=0, register=(48, 84), density=4)
    args.update(change)
    with pytest.raises(ValueError):
        condition(**args)
