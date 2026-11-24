"""Synth sports-stats beat + SFX for the IPL reel."""
import wave, os, sys
import numpy as np
D = os.path.dirname(os.path.abspath(__file__))
SR = 44100; DUR = 14.3; N = int(SR * DUR)
rng = np.random.default_rng(9)
L = np.zeros(N, np.float32); R = np.zeros(N, np.float32)
def add(sig, at, g=1.0, pan=0.0):
    i = int(at * SR)
    if i < 0: sig = sig[-i:]; i = 0
    n = min(len(sig), N - i)
    if n <= 0: return
    L[i:i+n] += sig[:n] * g * (1 - max(0, pan)); R[i:i+n] += sig[:n] * g * (1 + min(0, pan))
def tt(d): return np.arange(int(SR * d)) / SR

def kick():
    t = tt(0.45); f = 45 + 110 * np.exp(-t * 28)
    return np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t * 7) + rng.normal(0, 1, len(t)) * np.exp(-t * 200) * 0.3
def clap():
    t = tt(0.3); n = rng.normal(0, 1, len(t))
    env = np.exp(-t * 18) + 0.6 * np.exp(-np.maximum(t - 0.012, 0) * 30) * (t > 0.012)
    b = np.convolve(n, np.ones(6) / 6, "same") - np.convolve(n, np.ones(40) / 40, "same")
    return b * env * 0.9
def hat(open_=False):
    t = tt(0.25 if open_ else 0.06); n = rng.normal(0, 1, len(t))
    h = n - np.convolve(n, np.ones(4) / 4, "same")
    return h * np.exp(-t * (14 if open_ else 70)) * 0.5
def bass(f, d):
    t = tt(d); s = np.sign(np.sin(2*np.pi*f*t)) * 0.4 + np.sin(2*np.pi*f*t)
    s = np.convolve(s, np.ones(30) / 30, "same")
    return s * np.minimum(1, t * 80) * np.exp(-t * 2.5) * 0.5
def impact():
    t = tt(2.2); f = 30 + 70 * np.exp(-t * 9)
    s = np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t * 2.2)
    n = rng.normal(0, 1, len(t)); n = np.convolve(n, np.ones(20) / 20, "same")
    return s + n * np.exp(-t * 4) * 0.6
def riser(d=1.2):
    t = tt(d); n = rng.normal(0, 1, len(t))
    y = np.zeros_like(n); a = 0.02 + 0.5 * (t / d) ** 2; acc = 0.0
    for i in range(len(n)): acc += a[i] * (n[i] - acc); y[i] = acc
    tone = np.sin(2*np.pi*np.cumsum(200 + 900 * (t / d) ** 2)/SR) * 0.15
    return (y * 1.5 + tone) * (t / d) ** 2
def whoosh(d=0.5):
    t = tt(d); n = rng.normal(0, 1, len(t)); y = np.zeros_like(n); acc = 0.0
    a = 0.05 + 0.4 * np.sin(np.pi * t / d) ** 2
    for i in range(len(n)): acc += a[i] * (n[i] - acc); y[i] = acc
    return y * np.sin(np.pi * t / d) ** 2 * 1.6
def tick():
    t = tt(0.03); return np.sin(2*np.pi*2200*t) * np.exp(-t * 200) * 0.5
def snare():
    t = tt(0.15); return (rng.normal(0, 1, len(t)) * 0.7 + np.sin(2*np.pi*190*t)) * np.exp(-t * 25)
def chord(fs, d):
    t = tt(d); s = sum(np.sin(2*np.pi*f*t + 0.3*np.sin(2*np.pi*5*t)) + 0.5*np.sin(2*np.pi*f*2.005*t) for f in fs)
    return s * np.minimum(1, t * 6) * np.minimum(1, (d - t) * 6) * 0.08

BPM = 128; beat = 60 / BPM; bar = beat * 4
prog_ = [(55.0, [220.0, 261.6, 329.6]), (43.65, [174.6, 220.0, 261.6]), (65.4, [196.0, 261.6, 329.6]), (49.0, [196.0, 246.9, 293.7])]
DROP_OUT = [(9.5, 10.0)]   # breakdown for drumroll
def muted(x): return any(a <= x < b for a, b in DROP_OUT)
t0 = 0.0; b = 0
while t0 < 14.0:
    root, ch = prog_[b % 4]
    if not muted(t0): add(chord(ch, bar), t0, 0.9)
    for q in range(4):
        x = t0 + q * beat
        if x > 13.9 or muted(x): continue
        intro = x < 1.5
        if not intro: add(kick(), x, 0.9)
        if q in (1, 3) and not intro: add(clap(), x, 0.45, 0.1)
        add(hat(), x + beat / 2, 0.35, -0.3); add(hat(), x, 0.18, 0.3)
        if not intro: add(bass(root, beat * 0.9), x, 0.55)
    t0 += bar; b += 1

# drumroll into #1
x = 8.6
while x < 9.45:
    r = (x - 8.6) / 0.85; add(snare(), x, 0.25 + 0.5 * r, rng.uniform(-.2, .2)); x += 0.11 - 0.07 * r
mix = np.stack([L, R], 1)
env = np.minimum(1, np.arange(N) / (SR * 0.5)) * np.minimum(1, (N - np.arange(N)) / (SR * 1.2))
mix *= env[:, None]
mix = np.tanh(mix * 0.9)
mix = mix / np.abs(mix).max() * 0.92
with wave.open(os.path.join(D, "music.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok")
