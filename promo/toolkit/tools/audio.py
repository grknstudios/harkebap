"""Synthesise music bed + SFX for the promo and mix in the ElevenLabs voiceover.
usage: python3 audio.py <events.json> <vo_dir> <out.wav>
"""
import sys, json, os, subprocess
import numpy as np
from scipy.signal import butter, sosfilt

SR = 44100
DUR = 60.0
N = int(SR * DUR)
rs = np.random.RandomState(7)

def t_arr(d):
    return np.arange(int(SR * d)) / SR

def add(buf, sig, t0, gain=1.0):
    i0 = int(t0 * SR)
    if i0 >= len(buf):
        return
    if i0 < 0:
        sig = sig[-i0:]; i0 = 0
    n = min(len(sig), len(buf) - i0)
    if buf.ndim == 2:
        buf[i0:i0 + n] += sig[:n, None] * gain if sig.ndim == 1 else sig[:n] * gain
    else:
        buf[i0:i0 + n] += sig[:n] * gain

def lp(x, f, order=2):
    return sosfilt(butter(order, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, order=2):
    return sosfilt(butter(order, f, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], 'band', fs=SR, output='sos'), x)

def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)

# ---------------- music ----------------
BPM = 112
BEAT = 60 / BPM
BAR = BEAT * 4
# scene transpositions (semitones), applied from first bar starting at/after scene start
SCENE_STARTS = [(0, 0), (5.5, 0), (17.5, 2), (29.5, -3), (41.5, 3), (53.5, 0)]
def transpose_at(t):
    tr = 0
    for s, v in SCENE_STARTS:
        if t >= s - 0.01:
            tr = v
    return tr

PROG = [(60, 'maj'), (67, 'maj'), (69, 'min'), (65, 'maj')]  # C G Am F
def chord(root, q):
    return [root, root + (4 if q == 'maj' else 3), root + 7]

pad = np.zeros(N); arp = np.zeros(N); bass = np.zeros(N); drums = np.zeros(N)

def pluck(f, d, decay):
    tt = t_arr(d)
    s = np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2 * f * tt) + 0.15 * np.sin(2 * np.pi * 3 * f * tt)
    env = np.exp(-tt / decay) * np.minimum(1, tt / 0.004)
    return s * env

def padnote(f, d):
    tt = t_arr(d)
    s = np.zeros_like(tt)
    for h in range(1, 7):
        for det in (-0.12, 0.12):
            s += np.sin(2 * np.pi * f * h * (1 + det / 100 * h) * tt + h) / h
    env = np.minimum(1, tt / 0.35) * np.minimum(1, (d - tt) / 0.5).clip(0, 1)
    return s * env * 0.12

def kick():
    tt = t_arr(0.35)
    f = 45 + 95 * np.exp(-tt / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-tt / 0.16) * 0.9

def clap():
    tt = t_arr(0.22)
    n = bp(rs.randn(len(tt)), 900, 3500) * np.exp(-tt / 0.06)
    return n * 1.6

def hat():
    tt = t_arr(0.06)
    return hp(rs.randn(len(tt)), 7000) * np.exp(-tt / 0.018) * 0.5

KICK, CLAP, HAT = kick(), clap(), hat()
nbars = int(DUR / BAR) + 1
ARP_PAT = [0, 1, 2, 3, 2, 1, 2, 3]
for b in range(nbars):
    t0 = b * BAR
    tr = transpose_at(t0)
    root, q = PROG[b % 4]
    notes = [n + tr for n in chord(root, q)]
    full = 1.9 <= t0 < 58.5
    # pad
    for n in notes + [notes[0] + 12]:
        add(pad, padnote(mtof(n - 12), BAR + 0.3), t0)
    # arp (8ths)
    tones = notes + [notes[0] + 12]
    for k in range(8):
        n = tones[ARP_PAT[k]] + 12
        add(arp, pluck(mtof(n), 0.4, 0.13 if k % 2 else 0.18), t0 + k * BEAT / 2, 0.22 if k % 2 else 0.3)
    if not full:
        continue
    # bass: root on 8ths with octave jumps
    for k in range(8):
        n = notes[0] - 24 + (12 if k in (3, 7) else 0)
        tt = t_arr(BEAT / 2)
        s = np.tanh(2.2 * np.sin(2 * np.pi * mtof(n) * tt)) * np.exp(-tt / 0.16)
        add(bass, s, t0 + k * BEAT / 2, 0.35)
    for k in range(4):
        add(drums, KICK, t0 + k * BEAT, 0.85)
        if k in (1, 3):
            add(drums, CLAP, t0 + k * BEAT, 0.35)
        add(drums, HAT, t0 + k * BEAT + BEAT / 2, 0.5)
        add(drums, HAT, t0 + k * BEAT, 0.18)

pad = lp(pad, 2200)
arp = lp(arp, 6000)
# sidechain pump from kick grid (only in full section)
tt = np.arange(N) / SR
since = (tt % BEAT)
pump = 1 - 0.45 * np.exp(-since / 0.11) * ((tt >= 1.9) & (tt < 58.5))
music = (pad * 0.9 + bass) * pump + arp * 0.9 + drums * 0.55

# ---------------- SFX ----------------
sfx = np.zeros(N)
def s_pop(pitch=1.0):
    tt = t_arr(0.12)
    f = (950 * pitch) * np.exp(-tt / 0.05) + 260
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-tt / 0.045) * 0.55 + hp(rs.randn(len(tt)), 3000) * np.exp(-tt / 0.004) * 0.15
def s_lift():
    tt = t_arr(0.08)
    f = 380 + 500 * tt / 0.08
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / 0.08) * 0.12
def bell(f, d=0.9):
    tt = t_arr(d)
    return (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * 2.76 * f * tt) * np.exp(-tt / 0.08)) * np.exp(-tt / 0.28)
def s_chime():
    out = np.zeros(int(SR * 1.2))
    for i, m in enumerate([88, 91, 96]):
        b = bell(mtof(m)); i0 = int(i * 0.07 * SR); out[i0:i0 + len(b)] += b[:len(out) - i0]
    return out * 0.22
def s_fanfare():
    out = np.zeros(int(SR * 1.6))
    for i, m in enumerate([72, 76, 79, 84]):
        b = pluck(mtof(m), 0.9, 0.25); i0 = int(i * 0.085 * SR); out[i0:i0 + len(b)] += b[:len(out) - i0]
    for m in [72, 76, 79, 84, 88]:
        b = bell(mtof(m), 1.2); i0 = int(0.34 * SR); out[i0:i0 + len(b)] += b[:len(out) - i0] * 0.5
    return out * 0.28
def s_whoosh(d=0.7, gain=0.5):
    tt = t_arr(d)
    n = rs.randn(len(tt))
    env = np.sin(np.pi * (tt / d) ** 0.7) ** 2
    lo = bp(n, 300, 1200) * np.clip(1 - tt / d * 1.4, 0, 1)
    hi = bp(n, 1500, 6000) * np.clip(tt / d * 1.4, 0, 1)
    return (lo + hi) * env * gain
def s_tick():
    tt = t_arr(0.07)
    return (np.sin(2 * np.pi * 1700 * tt) * 0.6 + np.sin(2 * np.pi * 850 * tt)) * np.exp(-tt / 0.018) * 0.22
def s_horn():
    tt = t_arr(0.36)
    f = np.where(tt < 0.17, 392, 494)
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR))
    return lp(s, 1400) * np.minimum(1, tt / 0.01) * np.exp(-tt / 0.3) * 0.08
def s_boom():
    tt = t_arr(1.6)
    f = 32 + 45 * np.exp(-tt / 0.25)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.6)
    return s * 0.9 + lp(rs.randn(len(tt)), 400) * np.exp(-tt / 0.15) * 0.5
def s_riser():
    d = 1.6; tt = t_arr(d)
    f = 200 * (6 ** (tt / d))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.15 + hp(rs.randn(len(tt)), 2000) * 0.12
    return s * (tt / d) ** 2 * 0.8
def s_sparkle():
    out = np.zeros(int(SR * 0.9))
    for i in range(9):
        f = 2000 + rs.rand() * 3500; tt = t_arr(0.25)
        b = np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.06); i0 = int(i * 0.05 * SR); out[i0:i0 + len(b)] += b
    return out * 0.09
def s_boing():
    tt = t_arr(0.45)
    f = 260 + 220 * (tt / 0.45) + 60 * np.sin(2 * np.pi * 16 * tt)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.18) * 0.35

events = json.load(open(sys.argv[1]))
CACHE = {'chime': s_chime(), 'fanfare': s_fanfare(), 'whoosh': s_whoosh(0.75, 0.55), 'whooshS': s_whoosh(0.5, 0.22),
         'swoosh': s_whoosh(0.45, 0.3), 'tick': s_tick(), 'horn': s_horn(), 'boom': s_boom(), 'riser': s_riser(),
         'sparkle': s_sparkle(), 'boing': s_boing(), 'lift': s_lift()}
last = {}
for e in events:
    t, ty = e['t'], e['type']
    if t < 0 or t >= DUR:
        continue
    # avoid machine-gun stacking of identical sfx
    if ty in last and t - last[ty] < 0.05:
        continue
    last[ty] = t
    if ty == 'pop':
        add(sfx, s_pop(0.8 + rs.rand() * 0.5), t, 0.8)
    elif ty in CACHE:
        add(sfx, CACHE[ty], t - (1.6 if ty == 'riser' else 0), 1.0)

# ---------------- voiceover ----------------
VO = [('1_intro.mp3', 0.6), ('2_feather.mp3', 6.0), ('3_park.mp3', 18.0), ('4_nut.mp3', 30.0),
      ('5_terminal.mp3', 42.0), ('6_outro.mp3', 54.0)]
vo = np.zeros(N); duck = np.ones(N); have_vo = []
for fn, t0 in VO:
    p = os.path.join(sys.argv[2], fn)
    if not os.path.exists(p):
        continue
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.9
    add(vo, x, t0)
    have_vo.append(fn)
    i0, i1 = int(t0 * SR), int((t0 + len(x) / SR) * SR)
    duck[max(0, i0 - int(.25 * SR)):min(N, i1 + int(.3 * SR))] = 0.38
# smooth duck curve
k = int(0.25 * SR)
duck = np.convolve(duck, np.ones(k) / k, mode='same')

fade = np.ones(N); fi = int(58.3 * SR); fade[fi:] = np.linspace(1, 0, N - fi)
music = music / (np.max(np.abs(music)) + 1e-9) * 0.42
mix = music * duck * fade + sfx * 0.55 * np.maximum(duck, 0.6) + vo * 1.0
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
out = (mix * 32767 * 0.95).astype(np.int16)
import wave
with wave.open(sys.argv[3], 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
print('wrote', sys.argv[3], 'vo files:', have_vo)
