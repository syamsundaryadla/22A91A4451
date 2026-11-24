import numpy as np, wave, os
from earshot.forge import bank
D = os.path.dirname(os.path.abspath(__file__)); SR = 48000; DUR = 15.2; N = int(SR * DUR)
rng = np.random.default_rng(2)
def tt(d): return np.arange(int(SR * d)) / SR
def add(buf, y, t, db=0.0):
    if y.ndim == 1: y = np.stack([y, y], 1)
    i = int(round(t * SR)); n = min(len(y), N - i)
    if n > 0: buf[i:i + n] += y[:n] * 10 ** (db / 20)
def place(buf, sid, tc, anchor="onset", off=0.0, db=0.0, **kw):
    y, m = bank.render(sid, **kw)
    a = m["peak_s"] if anchor == "peak" else m["onset_s"]
    add(buf, y, tc + off - a, db); return m["checks"]["summary"]
def wav(name, x, peak=0.9):
    x = x / max(1e-9, np.abs(x).max()) * peak
    with wave.open(os.path.join(D, name), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())
def heartbeat():
    t = tt(0.35); f = 45 + 35 * np.exp(-t * 25); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 10)
def thunder(d=3.0):
    t = tt(d); n = rng.normal(0, 1, len(t)); y = np.zeros_like(n); acc = 0.0
    a = 0.02 + 0.3 * np.exp(-t * 6)
    for i in range(len(n)): acc += a[i] * (n[i] - acc); y[i] = acc
    crack = rng.normal(0, 1, len(t)) * np.exp(-t * 18) * 0.6
    return (y * 3 + crack) * (np.exp(-t * 1.3))
sfx = np.zeros((N, 2), np.float32); log = []
for x in (0.35, 0.62, 1.35, 1.62): add(sfx, heartbeat(), x, -4)
log.append(place(sfx, "reverse_swell/dark", 3.0, "peak", 0, -10))
log.append(place(sfx, "cut_hit/sub", 2.15, db=-6))                  # footstep thud as feet appear
log.append(place(sfx, "impact/deep", 3.0, db=0))                    # THE DROP
add(sfx, thunder(), 2.98, -2); add(sfx, thunder(1.5) * 0.6, 3.55, -6)
for i, c in enumerate((4.8, 6.4, 8.6)): log.append(place(sfx, "swipe/velvet", c, "peak", 0.037, -12, seed=[1, 2, 4][i]))
log.append(place(sfx, "fit/bell/small_bell", 13.0, db=-8))
log.append(place(sfx, "logo_sting/soft_bloom", 12.95, db=-12))
print(len(log), "earshot sfx;", sum(not l.split(":", 1)[1].strip().startswith("clean") for l in log), "flagged")
wav("sfx.wav", sfx)
# --- backup BGM: devotional drone + taiko-style drop beat from 3.0 s
music = np.zeros((N, 2), np.float32); t = tt(DUR)
note = lambda m: 440 * 2 ** ((m - 69) / 12)
drone = sum(np.sin(2 * np.pi * note(m) * h * t + h) / h ** 1.4 for m in (38, 45) for h in range(1, 7))
env = np.clip((t - 2.9) / 0.1, 0, 1) * np.clip((DUR - t) / 1.2, 0, 1) + 0.25 * np.clip(t / 1.0, 0, 1) * (t < 2.95)
music[:, 0] += drone * env * 0.5; music[:, 1] += np.roll(drone, 500) * env * 0.5
def taiko():
    tt_ = tt(0.6); f = 70 + 60 * np.exp(-tt_ * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt_ * 6) + rng.normal(0, 1, len(tt_)) * np.exp(-tt_ * 60) * 0.2
beat = 60 / 90
for k, x in enumerate(np.arange(3.0, 13.0, beat / 2)):
    if k % 4 in (0, 3): add(music, taiko(), x, -2 if k % 8 == 0 else -6)
wav("music.wav", np.tanh(music * 0.8), 0.8)
