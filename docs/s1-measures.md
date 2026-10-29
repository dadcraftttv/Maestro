# S.1 frozen measures (Oct 29)

Frozen before transformer training. Scope: v12, unchanged splits and codec,
one causal transformer about 5M parameters from scratch, at most two GPU hours
in total (all training runs combined), early stopping on validation event NLL.
DadCraft must give the go before training. No phone performance claim.

## Loss and evaluation isolation

Train only on the 496 train IDs. Select checkpoints by validation NLL; evaluate
48 test IDs once after selection. Validation reference: 50 pieces, 4,689 atomic
NOTE/REST events, n-gram **7.253827488477954 nats/event**. Gate: strictly lower
validation NLL on the identical targets and controls. Sum natural-log conditional
field losses within each complete event, then divide by target event count;
exclude supplied BAR/CHORDS/END. Report unseen events separately and also compare
on the n-gram's frozen vocabulary plus UNK: sum transformer event probabilities
outside that vocabulary into UNK. The headline comparable gate uses this common
outcome space; report full-event transformer NLL beside it. Never compare a mean
per scalar field to event NLL. No test vocabulary, counts or melodies in fitting.

## Acceptance and latency

Use the step-4 160 contexts (synthwave seeds 1–10, 16 independent bar
substitutions each), identical chords, accompaniment, previous rule melody,
register 60–84, density 4 and RNG seeds 1000+seed*16+bar. These are contextual
substitutions, not a free-running test. Report a separate 16-bar free-running
run for every seed with actual generated history; do not pool the two regimes.

`judge_bar` requires BOTH the unchanged full-context judge and the target
melody card measured on the target bar's sounding notes. Absolute times,
chords and accompaniment remain available. Use existing card ranges, scoring
and existing 80% member gate. No new key-fit or density threshold: synthwave's
melody card contains register, chord tones and top. A target bar with no sounding
melody note (a rest bar) skips the card and needs only the full judge (DadCraft,
Oct 29). Notes that give no measurable card trait still fail explicitly. Report
the rest share of generated passes beside acceptance; references: rules 0/160,
train runs 1,536/8,816 bars (17.4%). Rests have no gate of their own. No acceptance claim outside tested styles and roles. A bar
can pass despite an individual out-of-range trait, as the existing judge allows.

Gate: >=95% of all requested bars pass on the first masked proposal;
<=1% require rule fallback after three attempts. Denominator includes support
failures. Record unmasked first-rollout
acceptance separately, masked draws/total choices, removed probability mass,
all rejection reasons and retries. Never count a successful fallback as generated
acceptance. Every fallback must pass both checks or the run fails.

Wall-clock per requested bar includes raw audit, proposal, masks, decode, both
checks, retries and fallback checks, excluding fit and prebuilt rule context.
Use nearest-rank p99 (sorted index ceil(.99*N)-1), no discarded slow bars.
Gate: p99 <667 ms; CPU stretch <50 ms. CPU and GPU runs reported separately,
with hardware, runtime, thread count and cold/warm status. Synchronize GPU before
and after every timed call; report cold first call separately and all 160 timed
bars. N-gram GPU timing is not applicable.

## Novelty diagnostics (no invented pass thresholds)

Matched controls means identical style, member, key, chord timeline, phrase
position, register, density and prior history for rules/choose, n-gram and model.
For each context, draw 1,000 seeded choose bars (seeds 0–999); freeze these before
model evaluation. Canonical bar signature: relative onset, duration and tonic-
relative pitch, excluding velocity. Empirical choose probability of a signature
is its count/1,000. Report the fraction of model bars with frequency <=1/1,000,
including zero-count separately, alongside the same statistic for n-gram and
independent choose seeds 1000–1159. This is empirical rarity, not an exact
probability or evidence of quality. Threshold defines a diagnostic only.

Repetition: for every 16-bar continuation report equal-signature adjacent bar
pairs /15 and equal-signature unordered pairs /120. Report rhythmic signatures
(onset/duration only) separately. For training similarity, enumerate every
contiguous eight-bar window inside each train run and generated continuation;
report maximum fraction of identical bars against any train window, both at
original pitch and after each constant semitone transposition -24 through +24.
Include exact-eight-bar match count, nearest train ID/window/transposition;
never search validation/test for training matches. No numeric novelty gate was
approved in S.0: report distributions and examples; novelty alone cannot pass.

## DadCraft's blind listen

Only after measured gates are reported: 10 matched held-out contexts (first ten
validation IDs in frozen split order with eight contiguous usable bars), seeds
1 and 2; if fewer qualify, report the shortfall without silently replacing them.
Compare model, rules/choose and n-gram over identical accompaniment and sounds.
Render eight bars each; loudness-match each whole mix to the same integrated
loudness with shared peak headroom, no per-method effects. Randomize A/B/C per
trial using seed 510, keep the mapping hidden until DadCraft records preference,
musical fit, phrasing and suspected copying. Include 'no preference' and
'inconclusive'; retain all 20 trials and comments. DadCraft decides sound:
no automatic win threshold or forced verdict. No listening is part of this prep.

## Step-5 baseline and sensitivity

Unchanged 160 rule contexts: **160/160** original bars pass both checks.
Corruption probe: seeds 1–5, all 16 bars, random.Random(0), sixteen sixteenth
notes/bar, randint(36,96), velocity bin 7: **80/80 rejected**. Requiring every
card row inside range would wrongly reject 100 rule bars; the existing 80%
member gate avoids inventing a stricter threshold.

N-gram rerun (rest bars allowed): raw accepted **51/160**; first try
**78/160 (48.75%)**, of which 35 are rests; generated within three attempts
**142/160 (88.75%)**, 69 rests; fallback **18/160 (11.25%)**, 117 retries. Masked
draws 148/1,004 decisions. Rejections: 80 chord-tone, 42 below-band, 38 empty
support. CPU p50/p99 **5.44/13.62 ms**. Acceptance/fallback gates fail; CPU
latency gates pass. GPU not applicable. Loss and corpus SHA unchanged. Before
rests were allowed: first try 43/160, fallback 67/160 (90 rests rejected).
Reproduce: `PYTHONPATH=. .venv/bin/python private/s1_prep_step5/check.py`;
private report/logs retain evidence. Tests retain the fixed corruption probe.
