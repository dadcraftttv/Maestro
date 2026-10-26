# What other music AI projects teach Maestro

Two research rounds, Oct 23 (web search, mostly papers and project pages; claims are the authors' own unless
noted). Ideas only: check a license before using any code, weights or data. "→ B3" = the bucket it informs.

## Round 1: the main systems

| Project | What it does | Lesson for Maestro |
|---|---|---|
| ACE-Step 1.5 (2026) | A language model writes a song blueprint (structure, metadata, lyrics), a diffusion model renders audio. Distilled to 4–8 steps; <4 GB VRAM | Plan, then play: Maestro plans, Pd plays. Work top-down: shape, then chords, then each member's notes → B1, B5 |
| YuE (ICLR 2026) | Long songs; vocals and backing as separate tracks; structure fed in step by step | Separate tracks per member; structure as conditioning → B1 |
| MIDI-GPT (AAAI 2025) | Each track its own event run, tracks joined; controls per track: instrument, style, density, polyphony, note length. Redo one track or bar. ~20M params | Our per-member format and controls; swap one member's style mid-song; phone-sized → B1, B5 |
| Anticipatory Music Transformer (Stanford) | Writes a part seeing the other parts, including what comes next | Each member written seeing the others keeps mixed styles together → B5. Trained on Lakh: ideas only |
| Magenta RealTime / RT2 (Google) | Live audio model; style as an embedding (MusicCoCa); weighted averages blend styles; RT2 follows held MIDI notes, labels made with MT3 transcription | A style is a mixable vector: 70% synthwave + 30% salsa → B1, B5. Transcribe open audio for labels → B4. RT2 details from secondary articles: confirm in Google's paper |
| MusicGen (Meta) | Classifier-free guidance: trained with the condition sometimes dropped; one number sets its strength | A free "how much style" knob → B5 |
| MuseCoco (Microsoft) | Text → attributes (genre, instruments, tempo, density...) → music; many labels pulled from MIDI by rules | Ouralia's settings are the attributes; label data automatically → B4 |
| Band-in-a-Box style study (ISMIR 2019) | Trained only on synthetic MIDI in 70 styles; worked on real music | Style book → practice MIDI is sound → B4 |
| Bucknell thesis (2025) | Transformers on MIDI don't learn form alone; rules and structure labels help | Rules stay as guardrails (decision 6) |
| MusicLang | Chord-conditioned MIDI model aimed at CPUs | GPL code, Lakh-trained, model license unclear: ideas only |

## Round 2: more to learn from

| Project | What it does | Lesson for Maestro |
|---|---|---|
| CLaMP 3 (2025) | MIDI, scores, audio and text in one embedding space; code and weights public | The style judge: scores how "synthwave" a part is before DadCraft listens; style vectors → B3, B5. License to check |
| NotaGen (IJCAI 2025) | Learns from 1.6M pieces, then ~9K picked ones, then CLaMP-DPO: CLaMP 2 ranks outputs, top 10% vs bottom 10% train it | Learn broadly, then specialize; improve against the judge, no hand labels → B5 |
| GETMusic (IJCAI 2025) | Tracks × time grid; fills any target tracks from any source tracks (665 combos of 6) | Any band lineup with one model; compare with MIDI-GPT style → B5 |
| ChatMusician / MusicTheoryBench | Language model on ABC notation; college-level theory exam; still makes up theory | Build our own theory exam → B2 |
| Moonbeam (2025) | Big MIDI model for adapting; notes partly by relative distance (any key) | Relative pitch idea; size bought little in a later study → B5 |
| Stable Audio Open Small (2025) | 341M audio model, 11 s in <8 s on a phone; weak on music | Phones carry models; note-level Maestro is far lighter → B6 |
| RAVE, DDSP | Small real-time models that make one sound behave like another instrument; one model per instrument | Later, a learned sound for the swap idea; parked |

## Round 3: DadCraft's list (Oct 24)

Twenty systems from DadCraft's list. ACE-Step, Stable Audio, MusicGen/AudioCraft, YuE, Magenta and MidiTok were
already here (rounds 1 and 2). Most of the new ones make audio of whole songs from text; Maestro makes notes per
member, so they are ideas only (code or weights checked before any use).

| Project | What it does | Idea for Maestro (proposal, needs DadCraft's OK) |
|---|---|---|
| Mustango + MusicBench (2023) | text-to-music that follows chords, beats, key and tempo given in the prompt; its data are audio clips changed on purpose (pitch, tempo, loudness) and captioned with the theory MIR tools measure | Label practice MIDI with the controls Maestro takes (style, energy, chords, section), and grow data by changing it on purpose (transpose, tempo, swing) → B4 |
| HeartMuLa (2026) | open song models (codec, text-audio match, lyrics transcriber, generator); a style per section (intro, verse, chorus) | A style per section, not only per play: blends that shift as the song moves (the band could turn salsa for a breakdown) → B3 layering, 3.6 (accepted Oct 24) |
| LeVo (Tencent, 2025) | song model that can give vocals and backing as separate tracks | Parts kept apart is what Maestro does already; nothing new |
| Perceiver AR (2022), PerceiverS (2024) | long-context models: a small set of "latents" reads tens of thousands of past tokens; PerceiverS fixes how its masking leaks and segments | How the PC model could remember a 20-minute play (motifs coming back) without a huge model → B5 |
| Orpheus Music Transformer | large MIDI model, Apache-2.0 weights, trained on the scraped Godzilla MIDI set | Weights trained on fan MIDI: never used (decision 7); its separate drums and "humanizing" models are ideas only |
| Magenta DrumRNN / MelodyRNN | small RNNs (Apache-2.0) that continue drum and melody lines | A size reference for the phone model (decision 8): what a tiny per-member model can do → B6 |
| TinyMU (2026) | 229M music-understanding model (audio in, answers out), 35x smaller than its rivals for 82% of the score | A small local judge that could say what it hears ("is this salsa?") next to CLaMP 3 → 3.5, if its license allows (accepted Oct 24) |
| OpenMusic (QA-MDT), SongGen, DiffRhythm, MiniMax-Music, Amphion, Stable Audio 3.0 Small | audio song generators and an audio toolkit | Nothing for note-level parts; Stable Audio Small already noted as the phone size reference |
| Khala | not found under this name (searched with LeVo) | - |

## Round 4: outside reviews (Oct 26)

DadCraft asked six AI systems (ChatGPT, DeepSeek, Grok, Kimi, Meta, Mistral) to review the public repo and to list
open music-AI resources. The reviews stay private in `inbox/`; what they suggest is summed up here in our words. Their
resource lists went into `docs/data.md` ("The outside lists"). DadCraft took all nine proposals (Oct 26: "i'm fine
with 1 through 9"):

| # | Proposal (who raised it) | Where it went |
|---|---|---|
| 1 | Make the next bar ahead of time, with the rules as a fallback, so a slow model never drops a beat (5 of 6) | Decision 15; 6.1 |
| 2 | Check the mix before a listen: each member's loudness per style, the melody on top (Kimi, Mistral) | 3.8 |
| 3 | Seed fuzzing: thousands of seeds, nothing empty, out of range or off the grid (DeepSeek, Meta, Mistral) | 3.8 |
| 4 | A/B listens against the earlier round (ChatGPT, DeepSeek, Kimi, Meta) | 3.8 |
| 5 | The README's status was stale; decision 10 sat above 8 | Fixed Oct 26 |
| 6 | A small learned-model test before the desk and the training data: the real risk is bucket 5 (ChatGPT, Kimi, Mistral) | Bucket S |
| 7 | Say what the model must add over the rules' choose, as measures (Mistral) | 5.0 |
| 8 | Live inputs: smoothed, on phrase boundaries, who wins when the user and the room disagree (ChatGPT, Grok, Meta) | 6.0 |
| 9 | Tests on every push (DeepSeek, Meta) | 3.8 |

Not taken, each against a decision: testing the timing pocket now (13: only DadCraft brings it back); fewer styles
(1.4 picked four); an early in-app slice or streaming prototype (5, 12); one reader model instead of a team (14);
rules that suggest and a model that scores (6, 9); an MIT license for the player (10); a separate status file (PLAN.md
is the only one). Smaller points left for their bucket's plan step: per-file provenance with hashes (bucket 4), a
versioned Maestro-Ouralia interface (6.0), novelty past exact notes (contour, rhythm, chord-change variety: 5.5),
transpose and tempo augmentation (4.4), velocity variation on the grid (an idea, decision 13 covers timing only).
Some claims were off: one review couldn't read the files and took "bucket 2" from the stale README; the trap rounds
weren't mostly level tweaks (one round was).

## Round 5: DadCraft's ideas list (Oct 26)

From `inbox/ideas.md`. The **Fase Groove** family (wsx79: piano, guitar, drums, lead, arranger; AGPL-3.0, so ideas
only, no code) writes MIDI by rules, one engine per instrument on a shared key, tempo and swing, in song sections.
All 13 of its genres are house. DadCraft took two ideas (Oct 26): the **DNA nudges** (PLAN.md 3.9) and the guitar's
**scratch lane** (3.10). Noted for later: a fill library per instrument, per-lane timing feels, a voicing compare
(range, voice movement, top line) as a check for the judge, and stored takes with locks. The other links (LocalAI,
indra, soundbox, SoundForge Studio) don't serve Maestro; SoundForge's physical-model sound effects might interest
Ouralia's sounds.

## Data and tools found

| Name | License | Use |
|---|---|---|
| Groove MIDI Dataset | CC BY 4.0 | 1,150 drum performances, 10 drummers, genre-labeled, with feel (timing, velocity) → B3 drummer |
| PDMX | CC BY (dataset); ~12% license conflicts flagged, drop them | 250K public-domain scores, quality metadata; harmony, voice leading → B1, B4 |
| Aria-MIDI | CC BY-NC-SA (NC: keep apart) | 1M piano MIDI transcribed from audio; its find-transcribe-filter pipeline → B4 |
| FMA (CC0 subset), MTG-Jamendo, Musopen, Citizen DJ, Great 78 | per track | Open audio to transcribe → B4. See `music-info.md` |
| imslp-midi-cc0 | CC0 | ~1,100 MIDI, mostly classical |
| Lakh MIDI | fan MIDI of copyrighted songs | Not for training (decision 7) |
| MidiTok | MIT (checked Oct 23) | MIDI ↔ tokens; its MMM layout (MIDI-GPT's) is our token base, timeline and controls added: `docs/format.md` |
| Basic Pitch (Spotify) | Apache 2.0 | Audio → MIDI, ~17k params, best one instrument at a time → B4 |
| Demucs | to check | Split audio into stems before transcribing → B4 |
| Beat This! | MIT (secondary sources) | Beats and downbeats; avoid madmom's non-commercial beat step → B4 |

## Sources
- ACE-Step 1.5: https://arxiv.org/html/2602.00744v1
- YuE: https://arxiv.org/pdf/2503.08638
- MIDI-GPT: https://arxiv.org/html/2501.17011v1 · https://github.com/Metacreation-Lab/MIDI-GPT
- Anticipatory Music Transformer: https://crfm.stanford.edu/2023/06/16/anticipatory-music-transformer.html
- Magenta RT: https://simonwillison.net/2025/Jun/20/magenta-realtime · RT2: https://magenta.tensorflow.org/mrt2
- MusicGen: https://github.com/facebookresearch/audiocraft/blob/main/docs/MUSICGEN.md
- MuseCoco: https://arxiv.org/pdf/2306.00110
- Band-in-a-Box style study: https://arxiv.org/abs/1907.02265 · Bucknell thesis: https://digitalcommons.bucknell.edu/masters_theses/296
- MusicLang: https://github.com/MusicLang/musiclang
- CLaMP 3: https://arxiv.org/html/2502.10362v1 · NotaGen: https://arxiv.org/html/2502.18008v4
- GETMusic: https://arxiv.org/pdf/2305.10841 · ChatMusician: https://arxiv.org/abs/2402.16153
- Moonbeam: https://arxiv.org/html/2505.15559v1 · comparison: https://arxiv.org/pdf/2511.07268
- Stable Audio Open Small: https://stability.ai/news/stability-ai-and-arm-release-stable-audio-open-small-enabling-real-world-deployment-for-on-device-audio-control
- RAVE/DDSP: https://arxiv.org/pdf/2503.11562 · https://arxiv.org/pdf/2103.07220
- Groove MIDI: https://magenta.tensorflow.org/datasets/groove · PDMX: https://zenodo.org/records/15571083
- Aria-MIDI: https://arxiv.org/pdf/2504.15071 · MidiTok: https://github.com/Natooz/MidiTok
- Basic Pitch: https://github.com/spotify/basic-pitch · Beat This!: https://huggingface.co/cstr/beat-this-GGUF
- Fase Groove: https://github.com/wsx79/fasegroovearranger · https://github.com/wsx79/fasegroovepiano · https://github.com/wsx79/fasegrooveguitar
