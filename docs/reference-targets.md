# Reference mix targets (R.4)

Offline reference measurement: 2,345 distinct file hashes, 83.5 hours. Median [10th–90th percentile]: -14.2 [-15.5, -13.3] LUFS, 2.7 [1.7, 4.4] LU loudness range, 12.6 [11.6, 13.9] dB crest. Low-band side/mid power 0.015 [0.003, 0.046]; high-band 0.207 [0.102, 0.401].

These describe full mixes, including short cues and unfinished takes. Cohorts overlap; tags and measurements are associations, not causal controls or ratings. Individual sources, prompts and audio remain private; nothing is training data. No sound verdict is inferred.

Provisional targets for a fixed full-band fixture when auditioning one kit at a time:

1. Mix gain and impact: use -15.5–-13.3 LUFS integrated and 11.6–13.9 dB crest as reference bounds for a full-band fixture. An output ceiling of −1 dBTP is a design choice from the production workflow.
2. Low end: side/mid power below 150 Hz 0.003–0.046; keep the bass near the centre while allowing wider upper layers. Do not turn stereo reference power percentages into oscillator gain settings.
3. Synth / supersaw: for future-bass/supersaw full mixes (n=914), high-band side/mid 0.123–0.412 and centroid 498–1016 Hz. Use these to audition detune, chorus and pad width together.
4. Dark / industrial: for matching full mixes (n=761), presence-band power 7.4–14.1% and crest 11.6–13.4 dB.
5. Chill / ambient: matching full mixes (n=507) have LRA 2.0–5.3 LU and 1-second envelope p90−p10 2.8–6.9 dB. Preserve slow changes when auditioning pads and textures.
6. Bright / pop / chip: matching full mixes (n=537) put 4.6–12.5% of measured power at 2–6 kHz, with 85% rolloff 750–2203 Hz. Compare bell/lead colour at matched loudness.
7. Trap / hip-hop: matching full mixes (n=192) have sub power 21.2–54.9%, low-band side/mid 0.001–0.029 and crest 11.0–13.3 dB. Treat these as full-mix checks while auditioning sub glide and drum accents, not as solo-drum targets.

Width is side power / mid power, measured below 150 Hz and above 2 kHz (up to 12 kHz). Spectral shares use 24 kHz PCM and bands <60, 60–250, 250–500, 500–2,000, 2,000–6,000 and 6,000–12,000 Hz. Crest and FFT features are descriptive; integrated loudness and true peak use FFmpeg ebur128 at the native sample rate. [FFmpeg filter documentation](https://ffmpeg.org/ffmpeg-filters.html#ebur128-1).

Preserve dynamics; compare brightness and width at matched loudness. Finished mixes do not establish isolated oscillator or drum settings, and no acid-specific target is established. The next step is DadCraft’s review, followed by one kit audition at a time.
