# SPDX-License-Identifier: GPL-3.0-or-later
"""Reference tag parsing and descriptive audio features (no learned models).

Spectral features use 24 kHz PCM: air means 6–12 kHz, not full-band air.
Loudness/true peak come from FFmpeg ebur128 on the original sample rate.
"""
import json
import re
import numpy as np

BANDS = {'sub': (0, 60), 'bass': (60, 250), 'low_mid': (250, 500),
         'mid': (500, 2000), 'presence': (2000, 6000), 'air': (6000, 12001)}


def parse_tags(text):
    def field(name):
        m = re.search(r'^' + re.escape(name) + r':[ \t]*([^\n]*)', text, re.M)
        return m.group(1).strip() if m else None
    raw = {}
    if '--- Raw API Response ---' in text:
        try:
            raw = json.loads(text.split('--- Raw API Response ---', 1)[1].strip())
        except (ValueError, TypeError):
            pass
    if not isinstance(raw, dict):
        raw = {}
    meta = raw.get('metadata', {})
    if not isinstance(meta, dict):
        meta = {}
    prompt = field('Prompt') or meta.get('tags') or ''
    if not isinstance(prompt, str):
        prompt = ''
    return dict(title=field('Title') or raw.get('title'), prompt=prompt,
                tags=sorted(set(t.strip().lower() for t in prompt.split(',') if t.strip())),
                model=raw.get('major_model_version') or raw.get('model_name'),
                api_duration=meta.get('duration'), api_valid=bool(raw))


def parse_ebur128(stderr):
    # Last summary only, never intermediate 100 ms readouts.
    summary = stderr.rsplit('Summary:', 1)[-1]
    result = {}
    for key, pattern in {
        'lufs': r'I:\s*([-\d.]+) LUFS',
        'lra_lu': r'LRA:\s*([-\d.]+) LU',
        'true_peak_dbfs': r'Peak:\s*([-\d.]+) dBFS',
    }.items():
        m = re.search(pattern, summary)
        result[key] = float(m.group(1)) if m else None
    return result


def audio_features(pcm, sr=24000):
    """Energy-weighted FFT features, whole-track RMS and 1-second envelopes.

    Tempo is the strongest onset-envelope autocorrelation peak in 60–180 BPM;
    it is an estimate with octave ambiguity, not an annotated musical tempo.
    Width is side power / mid power (unitless); stereo correlation is signed.
    """
    x = np.asarray(pcm, dtype=np.float32)
    # The 1-second envelope needs at least one full second.
    if x.ndim != 2 or x.shape[1] != 2 or len(x) < max(4096, sr):
        raise ValueError('At least one second of stereo samples required')
    eps = 1e-20
    mid = (x[:, 0] + x[:, 1]) * .5
    side = (x[:, 0] - x[:, 1]) * .5
    power = float(np.mean(x.astype(np.float64)**2))
    peak = float(np.max(np.abs(x)))
    result = {'rms_dbfs': 10 * np.log10(max(power, eps)),
              'crest_db': 20 * np.log10(max(peak, 1e-10)) - 10*np.log10(max(power, eps)),
              'side_mid': float(np.mean(side**2) / max(float(np.mean(mid**2)), eps)),
              'lr_correlation': float(np.mean(x[:,0]*x[:,1]) / max(float(np.sqrt(np.mean(x[:,0]**2)*np.mean(x[:,1]**2))), eps))}
    n = 2048
    count = len(x)//n
    frames = x[:count*n].reshape(count, n, 2)
    spec = np.fft.rfft(frames * np.hanning(n)[None,:,None], axis=1)
    # Sum channel power, preserving anti-phase signals.
    energy = np.mean(np.abs(spec)**2, axis=(0,2))
    freqs = np.fft.rfftfreq(n, 1/sr)
    total = max(float(energy.sum()), eps)
    result['centroid_hz'] = float(np.dot(freqs, energy)/total)
    result['rolloff85_hz'] = float(freqs[min(np.searchsorted(np.cumsum(energy), .85*total), len(freqs)-1)])
    for name,(lo,hi) in BANDS.items():
        result['energy_'+name] = float(energy[(freqs>=lo)&(freqs<hi)].sum()/total)
    for name,lo,hi in [('low',0,150),('body',150,2000),('high',2000,sr/2+1)]:
        z = spec[:,(freqs>=lo)&(freqs<hi),:]
        l,r = z[:,:,0], z[:,:,1]
        mp,sp = float(np.sum(np.abs((l+r)/2)**2)), float(np.sum(np.abs((l-r)/2)**2))
        result['side_mid_'+name] = sp/max(mp,eps)
        result['correlation_'+name] = float(np.real(np.sum(l*np.conj(r)))/max(float(np.sqrt(np.sum(abs(l)**2)*np.sum(abs(r)**2))),eps))
    onset_n = 512
    onset_frames = x[:len(x)//onset_n*onset_n].reshape(-1,onset_n,2)
    onset_spec = np.fft.rfft(onset_frames*np.hanning(onset_n)[None,:,None],axis=1)
    magnitude = np.sqrt(np.mean(abs(onset_spec)**2,axis=2))
    flux = np.maximum(np.diff(magnitude,axis=0),0).sum(axis=1)
    hop_seconds=onset_n/sr
    threshold = np.median(flux)+1.5*np.median(abs(flux-np.median(flux)))
    peaks = np.flatnonzero((flux[1:-1]>flux[:-2])&(flux[1:-1]>=flux[2:])&(flux[1:-1]>threshold))+1
    # Refractory interval 170 ms prevents counting adjacent FFT bins as attacks.
    accepted=[]
    for i in peaks:
        if not accepted or (i-accepted[-1])*hop_seconds>=.17: accepted.append(i)
    result['onsets_per_second']=len(accepted)/(len(x)/sr)
    env=flux-float(np.mean(flux))
    lags=np.arange(int(np.ceil(60/180/hop_seconds)),int(np.floor(60/60/hop_seconds))+1)
    ac=np.array([np.dot(env[:-lag],env[lag:]) for lag in lags])
    best=int(np.argmax(ac))
    result['tempo_bpm']=float(60/(lags[best]*hop_seconds)) if np.max(ac)>0 else None
    result['tempo_ac_strength']=float(ac[best]/max(float(np.dot(env,env)),eps))
    seconds=len(x)//sr
    envelope=np.mean(x[:seconds*sr].reshape(seconds,sr,2).astype(np.float64)**2,axis=(1,2))
    db=10*np.log10(np.maximum(envelope,eps))
    edge=max(1,min(15,seconds//10))
    result.update(intro_rms_dbfs=float(np.mean(db[:edge])),outro_rms_dbfs=float(np.mean(db[-edge:])),
                  peak_second_rms_dbfs=float(np.max(db)), envelope_p90_p10_db=float(np.diff(np.percentile(db,[10,90]))[0]))
    # Non-overlapping 5s windows: adjacent changes >=6dB; excludes silence < -60dB.
    windows=len(envelope)//5
    block=10*np.log10(np.maximum(envelope[:windows*5].reshape(windows,5).mean(axis=1),eps))
    delta=np.diff(block); active=(block[1:]>-60)&(block[:-1]>-60)
    result['big_builds_6db']=int(np.sum((delta>=6)&active))
    result['big_drops_6db']=int(np.sum((delta<=-6)&active))
    result['envelope_5s_dbfs']=block.tolist()
    return result
