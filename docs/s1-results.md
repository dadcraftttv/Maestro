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
models learned. Register 72-96 (DadCraft, Oct 29: the rules' own melody sits at 76-93 over a band topping out at
74-76; the earlier 60-84 forced the line under it). Chord-tone control 0.75 (middle of the card's 50-100%), pool
unset, both fixed before the run. The n-gram runs under the same controls.

| Measure | Gate | n-gram | Transformer (run 4) |
|---|---|---|---|
| Validation NLL (nats/event, 4,689 events, 884 unseen) | below n-gram | 7.2538 | **5.1503** pass |
| Test NLL, scored once for run 4 (5,572 events, 914 unseen) | reported | 7.6403 | 5.4282 |
| First try, 160 contexts | >=95% | 122 (49 of them rests) | **117 (73%)**, 6 rests: fail |
| Fallback, 160 contexts | <=1% | 5 | **8 (5%)**: fail |
| First try / fallback, free-running 16 bars x 10 seeds | as above | not run | 120 / 5, no rests: fail |
| p99 per bar CPU (6 threads), contexts / free | <667 ms (stretch 50) | 12 ms | 207 / 419 ms: pass, stretch fails |
| p99 per bar RTX 2070, contexts / free | <667 ms | n/a | 137 / 224 ms: pass |

Rejections (contexts): too few chord tones 43, under the band 33, too high 8. At the old register 60-84 the
transformer made 74 first try / 35 fallback, the n-gram 61 / 35 (`private/s1_train/report_reg60-84.json`).

## Novelty diagnostics (no gates)

`private/s1_train/novelty.py`, `novelty.json`. Matched choose: each phrase of the rule melody drawn again from
seeds 0-999 with the same chords, key, pad floor, phrase position and prior onsets (`phrase_melody` before the
later voicing steps, same octave as the final line); seed 1000+i is the independent draw for context i.

| | Transformer | n-gram | Choose, independent |
|---|---|---|---|
| Bars at choose frequency <=1/1000 (never drawn) | 152/152 (152) | 155/155 (155) | 102/160 (74) |
| Free runs: equal-pitch bar pairs, adjacent /150, any /1200 | 0 / 0 | 22 / 198 | |
| Free runs: equal-rhythm bar pairs, adjacent /150, any /1200 | 26 / 167 | 22 / 200 | |
| Free runs: rest bars /160 | 0 | 65 (its repeats) | |
| Nearest train 8-bar window, most identical bars (of 8), per seed | 0-2, mostly 0 | 1 each | |
| Exact 8-bar train matches, any transposition -24..+24 | 0 | 0 | |

Rarity is exact-signature: neither model reproduces a bar the rules would draw, and even the rules' own
independent draws are mostly unseen in 1,000, so it says little beyond "not a copy of the rules". No training
phrase is copied: the closest window shares 2 of 8 bars (seed 8, train 5729991, ours moved down 5 semitones).

## The runs

| Run | Change | Validation NLL | First try / fallback (register 60-84) |
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

## Blind listen (ready, Oct 29)

`clips/s1_listen/` (gitignored): 10 trials x A/B/C, the sheet in `listen.txt`; the key in
`private/s1_train/listen_key.json`, closed until DadCraft has answered. Made by `private/s1_train/listen.py`.
Lead notes in the 8 bars: rules 18-55, n-gram 10-31, model 25-103 (seeds 5, 7 and 9 run in sixteenths).
