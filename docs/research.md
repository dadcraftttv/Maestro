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

## Data and tools found

| Name | License | Use |
|---|---|---|
| Groove MIDI Dataset | CC BY 4.0 | 1,150 drum performances, 10 drummers, genre-labeled, with feel (timing, velocity) → B3 drummer |
| PDMX | CC BY (dataset); ~12% license conflicts flagged, drop them | 250K public-domain scores, quality metadata; harmony, voice leading → B1, B4 |
| Aria-MIDI | CC BY-NC-SA (NC: keep apart) | 1M piano MIDI transcribed from audio; its find-transcribe-filter pipeline → B4 |
| FMA (CC0 subset), MTG-Jamendo, Musopen, Citizen DJ, Great 78 | per track | Open audio to transcribe → B4. See `music-info.md` |
| imslp-midi-cc0 | CC0 | ~1,100 MIDI, mostly classical |
| Lakh MIDI | fan MIDI of copyrighted songs | Not for training (decision 7) |
| MidiTok | to check | MIDI ↔ tokens (REMI and others); keep tempo in the shared timeline, not per track → B1 |
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
