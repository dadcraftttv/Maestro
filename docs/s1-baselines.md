# S.1 prep step 4: event baseline and next-bar harness

The frozen v12 corpus and step-2 codec are unchanged. No transformer training,
new music, downloads or listening verdict. This step does not freeze step-5 gates.

`maestro.spike.ngram.NGram` fits only explicitly supplied train IDs. The baseline
uses atomic NOTE/REST records from the frozen codec, including their position,
pitch, duration, coarse velocity and boundary ties. BAR/CHORDS/END are supplied
structure, not predicted outcomes. Context backs off from (current beat chord,
position, previous two events within this bar) to (chord, position), position,
then unigram. It does not learn eight-bar history, key, register, density or
phrase controls; register is enforced by the sampler. This intentionally small
baseline is not a substitute for testing those controls in the later model.

Teacher-forced loss is natural-log event NLL with add-0.1 smoothing over the
**training** vocabulary plus one UNK outcome. Every unseen validation event maps
to that outcome; no validation counts or vocabulary enter fitting. Sampling uses
observed counts without smoothing, so it can run out of legal support. Report
both facts when comparing a model: scalar-field/tensor losses cannot be compared
directly with this atomic-event loss without an agreed common likelihood unit.

`maestro.spike.harness.next_bar` takes a stateless generator with
`distribution(control, prefix, position) -> {event_tuple: nonnegative_weight}`, a
seeded Python RNG, an obligatory `check(notes) -> rejection_reasons`, and a
`fallback() -> rule_notes` for the exact context. `judge_bar` is the supplied
adapter: replace the melody bar inside a caller-provided `judge.Clip` and call
unchanged `judge.score` / `judge.passes` on the complete contextual clip. It
checks every member, using their existing cards and thresholds. A multi-bar card
can average over its context: these results are not a new per-bar style threshold.
The caller must supply the appropriate reference context; no style is inferred
from the mixed classical corpus. Clips use 96 ticks per 4/4 bar.

The mask enforces positions, positive bounded durations, MIDI/register bounds,
velocity bins, flags and continuity from a prior tied sustain. No interior tie-in
or premature tie-out is allowed. At most 96 events and 1–16 attempts are allowed
(default three). Lack of legal observed support rejects an attempt. The rules'
bar is checked too; failed fallback raises instead of returning unchecked music.
Rule generation stays outside the sampler: callers keep their original rule bar
available before starting generation. The sampler never invents a replacement
rule engine. Quantized velocities use bin midpoints when adapting to Song notes.

An independent unmasked first rollout uses a clone of the RNG. Logs distinguish
raw grammar/musical validity, rejected proposals, invalid draws replaced by the
mask, total decisions, removed probability mass, retries, generated acceptance,
and fallback. Failed attempts retain their mask counters. Per-bar wall time
includes raw audit, decoding, judge, retries, synchronization and fallback check;
it excludes fitting and preparing the existing rule context/fallback. GPU-backed
generators must supply a synchronization callback. CPU and GPU runs are separate;
this CPU n-gram has no GPU timing to report.

## Reproducible private evaluation (Oct 29)

From the repo root:
`PYTHONPATH=. .venv/bin/python private/s1_prep_step4/check.py`.
The script reads frozen v12, checks its SHA-256 after evaluation, and never reads
the test split's melodies. Detailed report and per-bar logs are in that folder.

- Fit: 496 train pieces; 6,384 observed event types. Validation: 50 pieces,
  4,689 target events, 884 unseen (18.85%); **7.253827 nats/event**.
- All 910 validation bars, fixed register 0–127 / requested density 4, true prior
  melody only: raw grammar **803/910 (88.24%)**, masked grammar **881/910 (96.81%)**.
  119 masked draws / 4,189 decisions; 29 masked proposals exhaust support.
  These are independent seeded rollouts, not musical acceptance or fallback rates.
- Separate harness integration benchmark: existing synthwave rule clips, seeds
  1–10, all 16 bars, fixed register 60–84 / density 4, original rule accompaniment,
  original rule melody as fallback. All checks use the complete 16-bar reference
  clip; each target substitution is independent, not a free-running continuation.
  Raw grammar plus judge: **95/160 (59.375%)**. Generated first try **137/160
  (85.625%)**; generated within three tries **159/160 (99.375%)**; fallback
  **1/160 (0.625%)**; 28 retries. 106 masked draws / 685 decisions. All 29 rejected
  attempts exhausted support. CPU p50 **4.23 ms**, p99 **7.54 ms** in this run.
- GPU: not applicable to this CPU baseline. These integration figures do not
  establish corpus musical acceptance, free-running quality, a sound verdict,
  transformer timing, or achievement of the pending step-5 measures.

Tests cover train/held-out isolation, OOV loss, illegal fields and ties, masks,
raw auditing, bounded retries, failed fallback, failure telemetry, unchanged full
judge rejection, and imports with torch blocked. No core module imports torch.

Step 5 supersedes the adapter acceptance definition above: `judge_bar` now also
requires target-bar card acceptance. Frozen measures and rerun: `s1-measures.md`.
The original step-4 figures remain historical full-context-only measurements.
