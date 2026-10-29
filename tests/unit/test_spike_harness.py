# SPDX-License-Identifier: GPL-3.0-or-later
import random
import pytest
from maestro import judge
from maestro.sketch import flow_sketch
from maestro.spike.harness import legal, next_bar, judge_bar, summarize
from maestro.spike.ngram import NGram


def control(previous=None):
    return dict(upcoming_chords=[(0, 'major')]*4, key='C', register=(60, 84),
                density=4, previous=previous or [['END']])


class Generator:
    def __init__(self, weights):
        self.weights = weights
    def distribution(self, control, prefix, pos):
        return self.weights


@pytest.mark.parametrize('event', [
    ('NOTE',0,60,97,4,0,0), ('NOTE',0,60,24,4,0,1),
    ('NOTE',0,60,96,4,1,0), ('NOTE',0,59,96,4,0,0),
    ('REST',0,0), ('REST',1,95), ('END',), ('NOTE',0,60,96,8,0,0),
    ('NOTE',0,60,96,4,False,0)])
def test_invalid_events_masked(event):
    assert not legal(event, 0, control())


def test_prior_tie_is_required_and_pitch_velocity_fixed():
    c = control([['BAR',0], ['NOTE',0,60,96,4,0,1], ['END']])
    assert legal(('NOTE',0,60,96,4,1,1),0,c)
    for e in [('REST',0,96), ('NOTE',0,60,96,4,0,0), ('NOTE',0,61,96,4,1,0)]:
        assert not legal(e,0,c)


def test_masking_and_raw_rollout_are_separate():
    g = Generator({('REST',0,96): 1, ('NOTE',0,128,96,4,0,0): 1000000})
    notes, log = next_bar(g, control(),0,random.Random(1),lambda n: [],lambda: [])
    assert notes == [] and log['accepted'] and not log['raw_valid']
    assert log['masked_choices']==1 and not log['fallback']


def test_retry_exhaustion_checks_rule_fallback_and_preserves_failure_counts():
    g = Generator({('NOTE',0,60,96,4,0,0):1})
    check = lambda notes: ['wrong melody'] if notes else []
    notes, log = next_bar(g,control(),0,random.Random(1),check,lambda: [],attempts=3)
    assert notes == [] and log['fallback'] and log['attempts']==3
    assert log['retries']==2 and len(log['rejections'])==3
    assert summarize([log])['rejection_reasons']=={'wrong melody':3}
    with pytest.raises(ValueError,match='fallback failed'):
        next_bar(g,control(),0,random.Random(1),lambda n:['bad'],lambda: [])


def test_empty_mask_support_is_bounded_and_counted():
    _, log = next_bar(Generator({('REST',1,95):1}),control(),0,random.Random(1),
                      lambda n:[],lambda:[],attempts=2)
    assert log['fallback'] and log['masked_choices']==2 and log['choices']==2


def test_existing_full_judge_rejects_broken_context_and_accepts_rules():
    clip = judge.from_song(flow_sketch('synthwave',1,16)[0])
    name = next(n for n,p in clip.players.items() if p.role=='melody')
    bar = next(n.step//96 for n in clip.players[name].notes)
    notes = [[max(n.step,bar*96),min(n.step+n.steps,(bar+1)*96),n.pitch,n.velocity//16]
             for n in clip.players[name].notes if n.step<(bar+1)*96 and n.step+n.steps>bar*96]
    assert not judge_bar(clip,name,bar,notes)
    bass = next(p for p in clip.players.values() if p.role=='bass')
    bass.notes = [type(n)(n.step,n.steps,1,n.velocity) for n in bass.notes]
    assert judge_bar(clip,name,bar,notes)


def piece(pid='train'):
    return dict(id=pid, snapped=[[0,96,60,4]],runs=[(0,1)],key='C',
                chords=[dict(root=0,quality='major')]*4)


def test_train_only_and_heldout_loss_no_mutation():
    model=NGram().fit([piece()],['train'])
    before=dict(model.counts[()])
    assert model.loss([piece('validation')])['events']==1
    assert dict(model.counts[()])==before
    with pytest.raises(ValueError,match='non-train'):
        NGram().fit([piece('validation')],['train'])
    with pytest.raises(ValueError,match='training piece'):
        model.loss([piece()])
    unknown=piece('validation');unknown['snapped'][0][2]=61
    assert model.loss([unknown])['unknown_events']==1


def test_target_bar_cards_reject_random_corruption_and_keep_rule_bars():
    rng = random.Random(0)
    rule_ok = random_rejected = 0
    for seed in range(1, 11):
        clip = judge.from_song(flow_sketch('synthwave', seed, 16)[0])
        name = next(n for n, p in clip.players.items() if p.role == 'melody')
        for bar in range(16):
            lo, hi = bar*96, (bar+1)*96
            notes = [[max(n.step, lo), min(n.step+n.steps, hi), n.pitch, n.velocity//16]
                     for n in clip.players[name].notes if n.step < hi and n.step+n.steps > lo]
            rule_ok += not judge_bar(clip, name, bar, notes)
            if seed <= 5:
                noise = [[lo+i*6, lo+(i+1)*6, rng.randint(36,96), 7] for i in range(16)]
                random_rejected += bool(judge_bar(clip, name, bar, noise))
    assert rule_ok == 160
    assert random_rejected >= 76


def test_rest_bar_skips_target_card_but_not_full_judge():
    clip = judge.from_song(flow_sketch('synthwave', 1, 16)[0])
    name = next(n for n, p in clip.players.items() if p.role == 'melody')
    rested = sum(not judge_bar(clip, name, bar, []) for bar in range(16))
    assert rested == 16
