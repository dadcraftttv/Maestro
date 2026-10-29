# S.1 results (Oct 29)

First training run against the frozen measures in `s1-measures.md`. Code: `maestro/spike/transformer.py`; run
script, weights, logs and per-bar records in `private/s1_train/` (run 1 in `run1_no_position/`). Data: v12, the
frozen 496/50/48 split, corpus SHA unchanged.

## The model

Causal transformer, 5,085,184 parameters (width 256, 5 layers, 4 heads, dropout 0.2, tied output), trained from
scratch on the 496 train pieces with AdamW 3e-4, batch 64, early stop after 5 epochs without a better validation
NLL. Inputs: key mode, phrase position, onset-count control (hidden half the time in training, hidden in loss),
history bars (up to eight, from `condition()`), the bar's four chords relative to the tonic, and for every token
the bar position where the next event starts (the n-gram keys on it too). Register is not an input; the harness
mask enforces it.

Outputs are the n-gram's atomic NOTE/REST events, so both models predict the same outcomes. The 2,607 train events
seen only once are pooled into UNK; UNK's probability is split evenly over them plus "never seen in train", a
proper distribution over the n-gram's vocabulary + UNK. Limitation: it cannot make an event unseen in train.

GPU time: run 1 332 s, run 2 334 s, smoke 30 s: about 12 minutes of the 2 hours. Run 2 best at epoch 27 (280 s).

## Measured (run 2, the selected run)

| Measure | Gate | n-gram | Transformer |
|---|---|---|---|
| Validation NLL (nats/event, 4,689 events, 884 unseen) | below n-gram | 7.2538 | **5.6822** pass |
| Test NLL (5,572 events, 914 unseen) | reported | 7.6403 | 6.1971 |
| First try, 160 contexts | >=95% | 78/160 (35 rests) | **87/160 (54%)**, 11 rests: fail |
| Fallback, 160 contexts | <=1% | 18/160 | **18/160 (11%)**: fail |
| First try / fallback, free-running 16 bars x 10 seeds | as above | not run | 97/160 / 13/160: fail |
| p99 per bar, CPU (6 threads), contexts / free | <667 ms, stretch 50 | 13.6 ms | 289 / **707 ms**: free fails |
| p99 per bar, RTX 2070, contexts / free | <667 ms | n/a | 196 / 401 ms: pass |

Rejections (contexts): too few chord tones 86, under the band too often 83. Masked draws 847/1,316 decisions in
contexts, 335/1,484 free-running. Cold first call 3.2 ms CPU, 7.8 ms GPU.

Run 1 had no position input: validation 6.3376, first try 83/160, fallback 21/160, masked 1,206/1,424 (most mass
on events at the wrong bar position). Selection between runs used validation NLL only. Protocol slip: run 1 also
scored the test split (6.8326), so test has been looked at twice; no choice was made from it.

## What it says

- The transformer clearly beats the n-gram on held-out loss.
- It fails acceptance because it learned the corpus (mostly classical and folk, no style input), and the
  synthwave melody card wants chord tones and a line above the band. Nothing in its inputs says "synthwave".
- CPU time is mostly the harness walking a 3,778-event dict through `legal()` at every decision, not the network
  (one forward is about 3 ms).

Not yet measured: novelty diagnostics (rarity against 1,000 choose bars, repetition, nearest train phrase), and
DadCraft's blind listen. Both wait for his call on the next step.
