# SPDX-License-Identifier: GPL-3.0-or-later
"""Real music to notes (decision 19's proof; later task 4.3), all on this PC. Demucs (MIT) splits a recording into
stems: htdemucs_ft, the fine-tuned model, from Ultimate Vocal Remover's model folder when it's there. Then, on one
beat grid fitted to the drum stem (the recording's tempo held steady):
- the bass and the lead (the "other" stem's leading line) as single lines, from pYIN's pitch track (librosa, ISC),
  a note a 16th or longer, a new one where the pitch moves or the stem strikes again;
- the pad as chords, a half bar each, from the "other" stem's pitch classes, voiced the shortest way;
- every note on the grid's 16ths, its velocity from the stem's loudness there.
The notes become a Maestro clip (MIDI and its JSON) the clip player renders through Maestro's own sounds, or through
a plain GM piano with `--piano`. The drum stem stays audio; nothing here writes drums.

Runs in its own environment, `private/transcribe` (torch, demucs, librosa; gitignored):

    private/transcribe/bin/python tools/transcribe.py inbox/song.mp3 --out private/refs/song
    private/transcribe/bin/python tools/transcribe.py --score private/refs/song/notes.mid --stems private/refs/song

then `.venv/bin/python -m maestro.play private/refs/song/notes.mid --wav-only`. A copyrighted recording stays in
`inbox/` or `private/` (decision 7: ideas only, never committed or sent out)."""
import argparse, glob, json, os, subprocess, sys

import librosa
import mido
import numpy as np

SR, HOP = 22050, 256               # the analysis rate; a frame is about 12 ms
BEAT = 960                          # ticks a beat
UVR = os.path.expanduser("~/ultimatevocalremovergui/models/Demucs_Models/v3_v4_repo")
SOUNDS = {"melody": "saw lead", "pad": "supersaw", "bass": "saw bass"}
PIANO = {"melody": 0, "pad": 0, "bass": 0}      # GM programs for --piano: a plain grand on every line


def stems(audio, out):
    """{stem: its WAV} (drums, bass, other, vocals), split on the GPU when there is one."""
    import torch
    model = ["-n", "htdemucs_ft", "--repo", UVR] if os.path.isdir(UVR) else ["-n", "htdemucs"]
    if not glob.glob(os.path.join(out, model[1], "*")):        # split once
        subprocess.run([sys.executable, "-m", "demucs", *model, "-o", out, "-d",
                        "cuda" if torch.cuda.is_available() else "cpu", audio], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    folder = glob.glob(os.path.join(out, model[1], "*"))[0]
    return {s: os.path.join(folder, s + ".wav") for s in ("drums", "bass", "other", "vocals")}


def grid(drums, bpm=None):
    """(first beat s, beat s): a straight line through the drum stem's beats (found on 23 ms frames: finer ones
    lock onto the wrong pulse), at `bpm` when it's known."""
    y, _ = librosa.load(drums, sr=SR)
    _, beats = librosa.beat.beat_track(y=y, sr=SR, hop_length=512, units="time", **({"bpm": bpm} if bpm else {}))
    k = np.arange(len(beats))
    beat, first = np.polyfit(k, beats, 1)
    if bpm:                                             # the known tempo, the fit's phase
        beat = 60 / bpm
        first = np.median(beats - beat * k)
    return first % beat, beat


def phase(beat, wavs):
    """Where the 16ths fall, s: the offset (5 ms steps) whose 16ths meet the most of the pitched stems' strikes. The
    beat tracker's own phase can sit tens of ms off, or on the off-beat."""
    strike = sum(librosa.onset.onset_strength(y=librosa.load(w, sr=SR)[0], sr=SR, hop_length=HOP) for w in wavs)
    t = librosa.frames_to_time(np.arange(len(strike)), sr=SR, hop_length=HOP)
    best, first = -1.0, 0.0
    for off in np.arange(0, beat, 0.005):
        at = librosa.time_to_frames(np.arange(off, t[-1], beat / 4), sr=SR, hop_length=HOP)
        got = strike[at].mean()
        if got > best:
            best, first = got, off
    return first


def _slots(n_frames, first, beat):
    """The frame each 16th starts on, from the grid's first 16th to the end."""
    times = np.arange(first, n_frames * HOP / SR, beat / 4)
    return librosa.time_to_frames(times, sr=SR, hop_length=HOP)


def line(wav, first, beat, low, high):
    """[(start 16th, length in 16ths, pitch, velocity)]: the stem's leading line, one note at a time."""
    y, _ = librosa.load(wav, sr=SR)
    f0, voiced, prob = librosa.pyin(y, fmin=low, fmax=high, sr=SR, hop_length=HOP, frame_length=2048)
    pitch = np.where(voiced, np.round(librosa.hz_to_midi(np.nan_to_num(f0, nan=1.0))), -1)
    strike = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP)
    loud = librosa.feature.rms(y=y, hop_length=HOP)[0]
    slots = _slots(len(pitch), first, beat)
    hit = np.percentile(strike, 85)
    top = np.percentile(loud, 98) or 1.0
    notes, now = [], None
    for i, (a, b) in enumerate(zip(slots, slots[1:])):
        ps = pitch[a:b][pitch[a:b] > 0]
        if len(ps) < (b - a) / 2:                       # silent or unpitched for most of the 16th: a rest
            now = None
            continue
        p = int(np.median(ps))
        struck = strike[max(0, a - 1):a + 2].max() > hit
        if now and now[2] == p and not struck:
            now[1] += 1
            continue
        v = int(np.clip(50 + 70 * loud[a:b].mean() / top, 1, 127))
        now = [i, 1, p, v]
        notes.append(now)
    return [tuple(n) for n in notes]


def chords(wav, first, beat, voices=4, low=52):
    """[(start 16th, 8, pitch, velocity)]: the stem's strongest pitch classes a half bar, each chord's voices moved
    the shortest way from the last."""
    y, _ = librosa.load(wav, sr=SR)
    chroma = librosa.feature.chroma_cqt(y=y, sr=SR, hop_length=HOP)
    loud = librosa.feature.rms(y=y, hop_length=HOP)[0]
    slots = _slots(chroma.shape[1], first, beat)[::8]
    top = np.percentile(loud, 98) or 1.0
    notes, last = [], [low + 5, low + 9, low + 12, low + 16]
    for i, (a, b) in enumerate(zip(slots, slots[1:])):
        if loud[a:b].mean() < 0.08 * top:
            continue
        c = chroma[:, a:b].mean(1)
        pcs = [int(q) for q in np.argsort(c)[::-1][:voices] if c[q] > 0.5 * c.max()]
        voiced = sorted(min((p for p in range(low, low + 24) if p % 12 == q), key=lambda p: min(abs(p - l) for l in last))
                        for q in pcs)
        v = int(np.clip(45 + 50 * loud[a:b].mean() / top, 1, 127))
        notes += [(i * 8, 8, p, v) for p in voiced]
        last = voiced
    return notes


def write(parts, first, beat, out, piano=False):
    """The clip: 16ths on the grid, the recording's tempo, its first 16th at the recording's time."""
    midi = mido.MidiFile(type=1, ticks_per_beat=BEAT)
    midi.tracks.append(mido.MidiTrack([mido.MetaMessage("set_tempo", tempo=round(beat * 1e6), time=0)]))
    offset = round(first / beat * BEAT)
    for ch, (name, ns) in enumerate(parts.items()):
        tr = mido.MidiTrack([mido.MetaMessage("track_name", name=name, time=0)])
        if piano:
            tr.append(mido.Message("program_change", channel=ch, program=PIANO[name], time=0))
        events = sorted([(offset + s * BEAT // 4, 1, p, v) for s, n, p, v in ns] +
                        [(offset + (s + n) * BEAT // 4 - 1, 0, p, 0) for s, n, p, v in ns])
        now = 0
        for t, on, p, v in events:
            tr.append(mido.Message("note_on" if on else "note_off", channel=ch, note=p, velocity=v, time=t - now))
            now = t
        midi.tracks.append(tr)
    path = os.path.join(out, "piano.mid" if piano else "notes.mid")
    midi.save(path)
    members = {n: {"role": n, "sound": PIANO[n] if piano else SOUNDS[n]} for n in parts}
    json.dump({"source": {"style": "synthwave", "from": "tools/transcribe.py"}, "members": members},
              open(path[:-4] + ".json", "w"), indent=1)
    return path


def score(mid, folder):
    """How well a clip's notes match its stems: the pitch classes sounding each 16th against the bass and other
    stems' (cosine, 1 is the same), and how many of the other stem's strikes a note starts within 40 ms of."""
    m = mido.MidiFile(mid)
    stem = lambda s: sorted(glob.glob(os.path.join(folder, "htdemucs*", "*", s + ".wav")))[-1]   # _ft when there
    y = librosa.load(stem("other"), sr=SR)[0] + librosa.load(stem("bass"), sr=SR)[0]
    heard = librosa.feature.chroma_cqt(y=y, sr=SR, hop_length=HOP)
    roll, onsets, now = np.zeros_like(heard), [], 0.0
    held = {}
    for msg in m:                                       # mido's play order: times in seconds
        now += msg.time
        if msg.type == "note_on" and msg.velocity:
            held[(msg.channel, msg.note)] = now
            onsets.append(now)
        elif msg.type in ("note_on", "note_off") and (msg.channel, msg.note) in held:
            a, b = (librosa.time_to_frames(t, sr=SR, hop_length=HOP) for t in (held.pop((msg.channel, msg.note)), now))
            roll[msg.note % 12, a:b + 1] += 1
    n = min(heard.shape[1], roll.shape[1])
    h, r = heard[:, :n], roll[:, :n]
    on = r.sum(0) > 0
    cos = (h * r).sum(0)[on] / (np.linalg.norm(h, axis=0)[on] * np.linalg.norm(r, axis=0)[on] + 1e-9)
    strikes = librosa.onset.onset_detect(y=librosa.load(stem("other"), sr=SR)[0], sr=SR, hop_length=HOP, units="time")
    onsets = np.array(sorted(onsets))
    found = np.mean([np.min(np.abs(onsets - s)) < 0.04 for s in strikes]) if len(onsets) else 0
    return float(np.mean(cos)), float(found), len(onsets) / max(1, len(strikes))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("audio", nargs="?")
    ap.add_argument("--out", help="a folder under private/")
    ap.add_argument("--score", help="a clip to score against --stems")
    ap.add_argument("--stems", help="the folder holding its stems")
    ap.add_argument("--bpm", type=float, help="the recording's tempo, when it's known")
    a = ap.parse_args(argv)
    if a.score:
        c, f, ratio = score(a.score, a.stems)
        print(f"{a.score}: pitch match {c:.2f}, strikes met {f:.0%}, notes per strike {ratio:.1f}")
        return
    os.makedirs(a.out, exist_ok=True)
    wavs = stems(a.audio, a.out)
    _, beat = grid(wavs["drums"], a.bpm)
    first = phase(beat, [wavs["other"], wavs["bass"]])
    parts = {"melody": line(wavs["other"], first, beat, 130, 2100),
             "pad": chords(wavs["other"], first, beat),
             "bass": line(wavs["bass"], first, beat, 30, 330)}
    for piano in (False, True):
        path = write(parts, first, beat, a.out, piano)
    print(f"{a.out}: {60 / beat:.1f} BPM, first 16th at {first:.3f} s; "
          + ", ".join(f"{n} {len(ns)}" for n, ns in parts.items()) + " notes")


if __name__ == "__main__":
    main()
