"""Synthesize background score: tanpura-like drone + low pulses + booms/whooshes at cuts."""
import json, sys, os, wave
import numpy as np
ROOT = sys.argv[1]
SR = 44100; DUR = 56.4
t = np.arange(int(SR * DUR)) / SR
rng = np.random.default_rng(3)
mix = np.zeros((len(t), 2), np.float32)

def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR); n = min(len(sig), len(t) - i)
    if n <= 0: return
    mix[i:i+n, 0] += sig[:n] * gain * (1 - max(0, pan))
    mix[i:i+n, 1] += sig[:n] * gain * (1 + min(0, pan))

# drone in C# (tanpura-ish): root, fifth, octave with rich harmonics + slow swell
def tone(f, harm=8, det=0.0):
    s = np.zeros_like(t)
    for h in range(1, harm + 1):
        s += np.sin(2*np.pi*f*h*t*(1+det) + rng.uniform(0, 6)) / h**1.3 * (1 + 0.4*np.sin(2*np.pi*0.07*h*t + h))
    return s
root = 69.3
drone = tone(root) * 0.5 + tone(root*1.5, 6, 0.0007) * 0.3 + tone(root*2, 6, -0.0005) * 0.25
drone *= 0.55 + 0.45 * np.sin(2*np.pi*t/9.0)**2
env = np.clip(t / 2.5, 0, 1) * np.clip((DUR - t) / 2.0, 0, 1)
# tension rises during the crushing (34-43s), relief after
tension = 1 + 0.6 * np.exp(-((t - 40) / 4) ** 2)
drone = drone * env * tension
mix[:, 0] += drone * 0.11; mix[:, 1] += np.roll(drone, 400) * 0.11

# heartbeat-like low pulse, every 1.5s from 7.7 to 43
def boom(f0=70, f1=35, d=1.4, noise=0.15):
    n = int(SR*d); tt = np.arange(n)/SR
    f = f1 + (f0 - f1) * np.exp(-tt*6)
    s = np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-tt*3.2)
    s += rng.normal(0, 1, n) * np.exp(-tt*25) * noise
    return s
for k in np.arange(7.7, 43, 1.6):
    add(boom(55, 40, 0.5, 0.0), k, 0.28)

def whoosh(d=0.6):
    n = int(SR*d); tt = np.arange(n)/SR
    x = rng.normal(0, 1, n)
    # moving low-pass via cumulative smoothing with varying alpha
    y = np.zeros(n); a = 0.02 + 0.25 * np.sin(np.pi * tt / d)**2; acc = 0
    for i in range(n): acc += a[i] * (x[i] - acc); y[i] = acc
    return y * np.sin(np.pi * tt / d) ** 2 * 2.2

def bell(f=554, d=3.5):
    n = int(SR*d); tt = np.arange(n)/SR
    s = sum(np.sin(2*np.pi*f*r*tt) * np.exp(-tt*k) * g for r, k, g in [(1, 1.2, 1), (2.76, 2.5, .4), (5.4, 4, .2), (8.9, 6, .1)])
    return s

scenes = json.load(open(os.path.join(ROOT, "scenes.json")))
W = whoosh()
for sc in scenes[1:]:
    add(W, sc["s"] - 0.35, 0.10, rng.uniform(-.4, .4))
for kw in json.load(open(os.path.join(ROOT, "keywords.json"))):
    if kw.get("boom"): add(boom(), kw["s"], 0.55 * kw["boom"])
add(bell(), 0.05, 0.10); add(bell(), 49.2, 0.08); add(bell(831), 53.35, 0.07)

mix = np.tanh(mix * 1.2)
pcm = (mix / max(1e-6, np.abs(mix).max()) * 0.9 * 32767).astype(np.int16)
with wave.open(os.path.join(ROOT, "music.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("ok")
