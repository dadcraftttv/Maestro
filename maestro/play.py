# SPDX-License-Identifier: GPL-3.0-or-later
"""The clip player: renders MIDI clips to WAV with FluidSynth on this PC and plays them, saying first what to listen
for (the clip's JSON). Everything runs offline. FluidSynth (LGPL-2.1) is used as the system library through ctypes,
so Maestro needs no extra Python package; the sounds come from a General MIDI soundfont, FluidR3 GM (MIT) in
`sounds/` (`tools/get_sounds.sh`), else TimGM6mb from the system. A member whose sound is one of Maestro's own
(`synth.py`: trap's 808 and its kit) is left out of FluidSynth's part and mixed in from `synth.py`. Only DadCraft
judges sound.

    python -m maestro.play clips/baseline            # every clip in the folder, in order
    python -m maestro.play clip.mid --wav-only       # render only (the WAV lands beside the MIDI)"""
import argparse, ctypes, ctypes.util, json, os, shutil, subprocess, sys, tempfile, wave

import mido
import numpy as np

from . import synth

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUNDFONTS = (os.environ.get("MAESTRO_SF2", ""), os.path.join(HERE, "sounds", "FluidR3_GM.sf2"),
              "/usr/share/sounds/sf2/FluidR3_GM.sf2", "/usr/share/sounds/sf2/TimGM6mb.sf2")
RATE, TAIL_S = 44100, 2.0       # sample rate; time left for the last notes and the reverb to ring out
GAIN = 0.6                      # FluidSynth's master gain (its default 0.2 leaves the clips about 15 dB down)
PERIOD = 64                     # frames a rendered block (FluidSynth's default period size)


def soundfont():
    for p in SOUNDFONTS:
        if p and os.path.isfile(p):
            return p
    sys.exit("no soundfont: run tools/get_sounds.sh (or set MAESTRO_SF2)")


def _lib():
    name = ctypes.util.find_library("fluidsynth") or "libfluidsynth.so.3"
    try:
        lib = ctypes.CDLL(name)
    except OSError:
        sys.exit("FluidSynth not found: install libfluidsynth3")
    for f in ("new_fluid_settings", "new_fluid_synth", "new_fluid_player", "new_fluid_file_renderer"):
        getattr(lib, f).restype = ctypes.c_void_p
    for f in ("new_fluid_synth", "new_fluid_player", "new_fluid_file_renderer", "fluid_player_play",
              "fluid_file_renderer_process_block", "delete_fluid_file_renderer",
              "delete_fluid_player", "delete_fluid_synth", "delete_fluid_settings"):
        getattr(lib, f).argtypes = [ctypes.c_void_p]
    lib.fluid_settings_setstr.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
    lib.fluid_settings_setnum.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_double]
    lib.fluid_settings_setint.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    lib.fluid_synth_sfload.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    lib.fluid_player_add.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    lib.fluid_set_log_function.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
    for level in (2, 3, 4):   # FluidSynth's warnings, info and debug: quiet (errors still print)
        lib.fluid_set_log_function(level, None, None)
    return lib


def _own(mid):
    """{track name: (Maestro's own sound, how deep it ducks under the kick, 0-1)} from the clip's JSON."""
    info = mid[:-4] + ".json"
    if not os.path.exists(info):
        return {}
    members = json.load(open(info)).get("members", {})
    return {n: (m["sound"], m.get("pump", 0) / 100) for n, m in members.items() if m.get("sound") in synth.SYNTHS}


OWN = {"supersaw": synth.supersaw, "saw bass": synth.saw_bass, "pluck": synth.pluck, "saw lead": synth.saw_lead}


def _synth_tracks(midi, own, length):
    """Maestro's own sounds for the tracks named in `own`, mixed, stereo, `length` samples: each with its echo and
    reverb (`synth.MIX`), ducking under the kit's kicks as deep as its `pump`."""
    sec = 60 / mido.tempo2bpm(next((m.tempo for m in midi.tracks[0] if m.type == "set_tempo"), 500000))
    out, kicks, parts = np.zeros((length, 2)), [], []
    for tr in midi.tracks:
        if tr.name not in own:
            continue
        sound, depth = own[tr.name]
        now, held, notes, hits, bends = 0, {}, [], [], []
        for m in tr:
            now += m.time
            t = now / midi.ticks_per_beat * sec
            if m.type == "note_on" and m.velocity:
                held[m.note] = (t, m.velocity)
                hits.append([t, None, m.note, m.velocity])   # every hit, even one a quick roll overlaps
            elif m.type in ("note_on", "note_off") and m.note in held:
                on, v = held.pop(m.note)
                notes.append((on, t, m.note, v))
                last = next(h for h in reversed(hits) if h[2] == m.note)
                last[1] = last[1] or t
            elif m.type == "pitchwheel":
                bends.append((t, m.pitch / 8192 * 12))
        if sound == "808":
            x = synth.bass_808(notes, bends, length)[:, None].repeat(2, 1)
        elif sound == "808 kit":
            x = synth.kit_808([(a, b or a + 0.1, n, v) for a, b, n, v in hits], length)[:, None].repeat(2, 1)
        elif sound == "linn kit":
            x = synth.linn_kit([(a, b or a + 0.1, n, v) for a, b, n, v in hits], length)
        else:
            x = OWN[sound](notes, length)
        if sound.endswith("kit"):
            kicks += [h[0] for h in hits if h[2] == 36]
        wet_echo, feedback, wet_room, room = synth.MIX.get(sound, (0, 0, 0, 0))
        if wet_echo:
            x = synth.echo(x, sec, wet_echo, feedback)
        if wet_room:
            x = synth.reverb(x, room, wet_room)
        parts.append((x, depth))
    for x, depth in parts:
        out += x * synth.pump(length, kicks, depth)[:, None] if depth and kicks else x
    return out


def render(mid, wav, sf2=None):
    """Renders a MIDI file to a 16-bit WAV, faster than real time; Maestro's own sounds mixed in."""
    own = _own(mid)
    if not own:
        return _fluid(mid, wav, sf2)
    midi = mido.MidiFile(mid)
    with tempfile.TemporaryDirectory() as tmp:
        rest = mido.MidiFile(type=1, ticks_per_beat=midi.ticks_per_beat)
        rest.tracks = [t for t in midi.tracks if t.name not in own]
        part = os.path.join(tmp, "gm.mid")
        rest.save(part)
        _fluid(part, os.path.join(tmp, "gm.wav"), sf2, midi.length)
        with wave.open(os.path.join(tmp, "gm.wav")) as w:
            ch, frames = w.getnchannels(), w.readframes(w.getnframes())
    gm = np.frombuffer(frames, dtype="<i2").reshape(-1, ch).astype(float) / 32768
    own_mix = _synth_tracks(midi, own, len(gm))
    mix = gm + (own_mix if gm.shape[1] == 2 else own_mix.mean(1, keepdims=True))
    peak = np.max(np.abs(mix))
    if peak > 0:                         # its peak at about -1 dB
        mix *= 0.89 / peak
    with wave.open(wav, "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((mix * 32767).astype("<i2").tobytes())
    return wav


def _fluid(mid, wav, sf2=None, length=None):
    """FluidSynth's render of a MIDI file to a 16-bit WAV. `length` (s): the clip's own, when `mid` holds only some
    of its tracks."""
    lib, sf2 = _lib(), sf2 or soundfont()
    s = lib.new_fluid_settings()
    lib.fluid_settings_setstr(s, b"audio.file.name", wav.encode())
    lib.fluid_settings_setstr(s, b"audio.file.type", b"wav")
    lib.fluid_settings_setstr(s, b"player.timing-source", b"sample")
    lib.fluid_settings_setnum(s, b"synth.sample-rate", RATE)
    lib.fluid_settings_setint(s, b"synth.lock-memory", 0)
    lib.fluid_settings_setnum(s, b"synth.gain", GAIN)
    synth = lib.new_fluid_synth(s)
    player = renderer = None
    try:
        if lib.fluid_synth_sfload(synth, sf2.encode(), 1) < 0:
            raise RuntimeError(f"can't load {sf2}")
        player = lib.new_fluid_player(synth)
        if lib.fluid_player_add(player, mid.encode()) != 0:
            raise RuntimeError(f"can't read {mid}")
        renderer = lib.new_fluid_file_renderer(synth)
        if not renderer:
            raise RuntimeError("FluidSynth can't write WAV files here")
        lib.fluid_player_play(player)
        # the clip's own length and a tail (the player's status stays "playing" for seconds after the last note)
        for _ in range(int(((length or mido.MidiFile(mid).length) + TAIL_S) * RATE / PERIOD)):
            if lib.fluid_file_renderer_process_block(renderer) != 0:
                break
    finally:
        if renderer:
            lib.delete_fluid_file_renderer(renderer)
        if player:
            lib.delete_fluid_player(player)
        lib.delete_fluid_synth(synth)
        lib.delete_fluid_settings(s)
    return wav


def play_wav(wav):
    for tool in ("pw-play", "paplay", "aplay"):
        if shutil.which(tool):
            return subprocess.run([tool, wav]).returncode
    sys.exit("no audio player found (pw-play, paplay or aplay)")


def clips(target):
    if os.path.isdir(target):
        return sorted(os.path.join(target, f) for f in os.listdir(target) if f.endswith(".mid"))
    return [target]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("target", help="a .mid clip or a folder of them")
    ap.add_argument("--wav-only", action="store_true", help="render, don't play")
    ap.add_argument("--sf2", help="another soundfont")
    a = ap.parse_args(argv)
    sf2 = a.sf2 or soundfont()
    if "TimGM6mb" in sf2:
        print("(TimGM6mb: thin sounds; tools/get_sounds.sh fetches FluidR3 GM)")
    found = clips(a.target)
    if not found:
        sys.exit(f"no clips in {a.target}")
    for i, mid in enumerate(found):
        wav = mid[:-4] + ".wav"
        if not os.path.exists(wav) or os.path.getmtime(wav) < os.path.getmtime(mid):
            render(mid, wav, sf2)
        info = mid[:-4] + ".json"
        listen = json.load(open(info)).get("listen", "") if os.path.exists(info) else ""
        print(f"\n[{i + 1}/{len(found)}] {os.path.basename(mid)}" + (f"\n  {listen}" if listen else ""))
        if a.wav_only:
            print(f"  {wav}")
        elif play_wav(wav):
            break   # (Ctrl+C in the player stops the run)


if __name__ == "__main__":
    main()
