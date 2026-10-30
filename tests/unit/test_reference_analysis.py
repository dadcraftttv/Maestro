# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic checks only; no private references or prompt material."""
import shutil
import subprocess
import numpy as np
import pytest
from maestro.analysis.reference import parse_tags, parse_ebur128, audio_features


def tone(hz=1000, seconds=4, sr=24000, amplitude=.1):
    t=np.arange(seconds*sr)/sr
    y=amplitude*np.sin(2*np.pi*hz*t)
    return np.column_stack([y,y]).astype('float32')


def test_tag_parser_and_fallback():
    s='Title: Synthetic take\nPrompt: Bright, Wide, bright\n--- Raw API Response ---\n{"major_model_version":"v-test","metadata":{"duration":4}}'
    r=parse_tags(s)
    assert r['tags']==['bright','wide'] and r['model']=='v-test'
    assert r['api_duration']==4 and r['title']=='Synthetic take'
    assert parse_tags('--- Raw API Response ---\n{"metadata":{"tags":"Soft, slow"}}')['tags']==['slow','soft']
    assert parse_tags('Prompt: dry\n--- Raw API Response ---\ninvalid')['tags']==['dry']
    assert parse_tags('--- Raw API Response ---\n[]')['tags']==[]
    assert parse_tags('Prompt:\nCover Art URL: synthetic')['tags']==[]
    assert parse_tags('--- Raw API Response ---\n{"metadata":{"tags":[]}}')['tags']==[]


def test_tone_level_spectrum_and_mono():
    r=audio_features(tone())
    assert r['rms_dbfs']==pytest.approx(-23.0103,abs=.001)
    assert r['crest_db']==pytest.approx(3.0103,abs=.001)
    assert r['centroid_hz']==pytest.approx(1000,abs=2)
    assert r['rolloff85_hz']==pytest.approx(1000,abs=15)
    assert r['side_mid']<1e-12 and r['lr_correlation']==pytest.approx(1,abs=1e-6)
    assert r['energy_mid']>.999
    assert sum(r['energy_'+b] for b in ['sub','bass','low_mid','mid','presence','air'])==pytest.approx(1)


def test_known_width_and_bands():
    x=tone(100)
    x[:,1]*=.5
    r=audio_features(x)
    assert r['side_mid']==pytest.approx(1/9,rel=1e-5)
    assert r['side_mid_low']==pytest.approx(1/9,rel=1e-5)
    assert r['correlation_low']==pytest.approx(1,abs=1e-6)
    x=tone();x[:,1]*=-1
    r=audio_features(x)
    assert r['lr_correlation']==pytest.approx(-1,abs=1e-6)
    assert r['centroid_hz']==pytest.approx(1000,abs=2)  # no anti-phase cancellation


def test_energy_changes():
    x=tone(seconds=30)
    x[:10*24000]*=.1;x[20*24000:]*=.1
    r=audio_features(x)
    assert r['big_builds_6db']==1 and r['big_drops_6db']==1
    assert r['envelope_p90_p10_db']==pytest.approx(20,abs=.01)


@pytest.mark.skipif(not shutil.which('ffmpeg'),reason='FFmpeg not installed')
def test_bs1770_known_stereo_sine():
    # Stereo 1 kHz, each channel -20 dBFS sample peak: approximately -20 LUFS.
    sr=48000;t=np.arange(sr*6)/sr;y=.1*np.sin(2*np.pi*1000*t)
    x=np.column_stack([y,y]).astype('<f4')
    p=subprocess.run(['ffmpeg','-hide_banner','-nostats','-f','f32le','-ar',str(sr),'-ac','2','-i','pipe:0','-af','ebur128=peak=true:framelog=verbose','-f','null','-'],input=x.tobytes(),capture_output=True,check=True)
    r=parse_ebur128(p.stderr.decode())
    assert r['lufs']==pytest.approx(-20,abs=.15)
    assert r['true_peak_dbfs']==pytest.approx(-20,abs=.15)
    assert r['lra_lu']<.2


def test_click_tempo_and_density():
    sr=24000
    x=np.zeros((sr*12,2),dtype=np.float32)
    burst=tone(seconds=1)[:480]
    for i in range(0,len(x),sr//2):x[i:i+len(burst)]=burst
    r=audio_features(x)
    # Autocorrelation can choose half tempo, so assert the known 120 BPM pulse
    # or its documented octave ambiguity, never claim annotated musical tempo.
    assert min(abs(r['tempo_bpm']-120),abs(r['tempo_bpm']-60))<4
    assert r['onsets_per_second']==pytest.approx(2,abs=.2)


@pytest.mark.skipif(not shutil.which('ffmpeg'),reason='FFmpeg not installed')
def test_true_peak_detects_intersample_overs():
    sr=48000;t=np.arange(sr*4)/sr
    y=.1*np.sin(2*np.pi*12000*t+np.pi/4)
    x=np.column_stack([y,y]).astype('<f4')
    p=subprocess.run(['ffmpeg','-hide_banner','-nostats','-f','f32le','-ar',str(sr),'-ac','2','-i','pipe:0','-af','ebur128=peak=true:framelog=verbose','-f','null','-'],input=x.tobytes(),capture_output=True,check=True)
    r=parse_ebur128(p.stderr.decode())
    assert r['true_peak_dbfs']>20*np.log10(np.max(abs(x)))+2
