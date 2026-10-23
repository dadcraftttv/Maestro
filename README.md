# Maestro

The composer of the Orchestra: the music brain that will drive Ouralia's generative music.

Status: idea stage. Nothing built yet.

## The idea

Maestro learns what makes music music: theory (scales, harmony, voice leading, rhythm, form) and what sets genres
apart (EDM, future bass, synthwave, chillwave, ambient, afrobeat, salsa, rock, hip hop, trap, ...). It can be big on
the computer, and a small version distilled from it runs on the phone.

## Direction (from the first planning talk, 2026-10-23)

- **Decisions, not audio.** Ouralia already makes its sound with Pd. Maestro decides *what* to play: the next chord,
  a rhythm for the style, where the melody goes, when to build or drop. That's symbolic music (MIDI-level), so a
  phone-sized model can be a few MB and cheap on battery (ONNX Runtime or TFLite). Audio models such as ACE-Step,
  MusicGen or Suno make finished sound, are billions of parameters, and can't respond live, so we study them for ideas
  but don't ship them.
- **Layers:**
  1. A rule-based theory engine: keys, chord function, voice leading, style templates. Works on day one.
  2. A small style model trained on this PC (RTX 2070, 8 GB) from openly licensed MIDI data.
  3. Research into open models (ACE-Step, Magenta RealTime and others) for how they handle style and structure.
- **Data must be clean.** The repos are public, so train only on openly licensed or public-domain material.

A proper Maestro plan comes in its own phase.
