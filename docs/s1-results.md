# S.1 results (Oct 29)

Training against the frozen measures in `s1-measures.md`. Code: `maestro/spike/transformer.py`; run script,
weights, logs and per-bar records in `private/s1_train/` (earlier runs in `run1_no_position/`, `run2_position/`,
`run3_style/`). Data: v12, the frozen 496/50/48 split, corpus SHA unchanged. GPU time, all runs: about 21 minutes
of the 2 hours.

## The selected model (run 4)

Causal transformer, 5,034,240 parameters (width 256, 6 layers, 4 heads, dropout 0.2), from scratch on the 496
train pieces, AdamW 3e-4, batch 64, early stop after 5 epochs without a better validation NLL (best epoch 5,
64 s). Inputs: key mode, phrase position, history bars (up to eight, from `condition()`), the bar's four chords
relative to the tonic, the bar position where the next event starts, and caller controls: onset count,
register middle, chord-tone share, source pool (each hidden part of the time in training, all hidden in the loss).

Outputs are the n-gram's atomic NOTE/REST events, so both models predict the same outcomes. Each event's embedding
is the sum of its fields' (kind, start, pitch, duration, velocity, ties), on input and output, so what is learned
about a pitch or duration is shared, and history events unseen in train still have an embedding. The 2,607 train
events seen once are pooled into UNK as an outcome; its probability is split evenly over them plus "never seen in
train", a proper distribution over the n-gram's vocabulary + UNK. It cannot make an event unseen in train.

## Measured

Benchmark key: v12 names keys by signature (241 pieces 'C', 6 with minor names), so the synthwave A minor
contexts are passed as 'C', the corpus's name for them; 'Am' put the chords nine semitones from anything the
models learned. The n-gram is rerun the same way. Chord-tone control 0.75 (middle of the card's 50-100%), pool
unset, both fixed before the run.

| Measure | Gate | n-gram | Transformer (run 4) |
|---|---|---|---|
| Validation NLL (nats/event, 4,689 events, 884 unseen) | below n-gram | 7.2538 | **5.1503** pass |
| Test NLL, scored once for run 4 (5,572 events, 914 unseen) | reported | 7.6403 | 5.4282 |
| First try / fallback, 160 contexts, register 60-84 | >=95% / <=1% | 61 / 35 | 74 / 35: fail |
| Same, free-running 16 bars x 10 seeds | as above | not run | 90 / 19: fail |
| p99 per bar CPU (6 threads), contexts / free | <667 ms (stretch 50) | 18.6 ms | 262 / 227 ms: pass, stretch fails |
| p99 per bar RTX 2070, contexts / free | <667 ms | n/a | 177 / 158 ms: pass |

Rejections at 60-84 (contexts): under the band 144, too few chord tones 88.

**Register diagnostic (not a gate change).** The rules' own synthwave melody sits at MIDI 76-93 (median 84) over a
band that tops out at 74-76; the frozen register 60-84 caps every generated note at 84, which pushes the line into
the band. With register 72-96 (the same width, an octave up):

| 160 contexts | First try | Rests in first try | Fallback | p99 CPU |
|---|---|---|---|---|
| n-gram | 122 | 49 | 5 | 12 ms |
| Transformer | 117 | about 7 | 8 | 222 ms (free-running 120 first try, 5 fallback, 438 ms) |

Both still miss 95% / 1%; the transformer passes with sounding bars far more often than the n-gram.

## The runs

| Run | Change | Validation NLL | First try / fallback (60-84) |
|---|---|---|---|
| 1 | atomic event embeddings, key 'Am' | 6.3376 | 83 / 21 |
| 2 | + bar position input | 5.6822 | 87 / 18 |
| 3 | + register, chord-tone and pool controls; harness sees only events at the current position | 5.6875 | 79 / 31 |
| 4 | events as sums of field embeddings; key 'C' | 5.1503 | 74 / 35 (key 'C' moves the n-gram too: 78 / 18 at 'Am', 61 / 35 at 'C') |

Run 3 showed the cause of the weak chord fit: with one embedding per atomic event the model reached 0.47 chord
tones on its own validation contexts (the data has 0.68) and ignored the chord-tone control. Run 4's shared fields
improved loss and chord tones; the rest of the gap is the register.

Selection used validation NLL only. Protocol slip: runs 1 and 2 also scored the test split (6.8326, 6.1971), so
test has been looked at three times in all; no choice was made from it.

Not yet measured: novelty diagnostics (rarity against 1,000 choose bars, repetition, nearest train phrase), and
DadCraft's blind listen.
