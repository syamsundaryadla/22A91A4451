"""Music bed (pad + earshot celesta melody) and earshot SFX for the Travishek reel."""
import numpy as np, wave, os
from earshot.forge import bank
D = os.path.dirname(os.path.abspath(__file__)); SR = 48000; DUR = 67.2; N = int(SR * DUR)
rng = np.random.default_rng(2)
def tt(d): return np.arange(int(SR * d)) / SR
def wav(name, x):
    x = x / max(1e-9, np.abs(x).max()) * 0.92
    with wave.open(os.path.join(D, name), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())
def add(buf, y, t, db=0.0):
    if y.ndim == 1: y = np.stack([y, y], 1)
    i = int(round(t * SR))
    if i < 0: y = y[-i:]; i = 0
    n = min(len(y), N - i)
    if n > 0: buf[i:i + n] += y[:n] * 10 ** (db / 20)

# ---------------- music: warm pad, sub pulse in the stats section, celesta melody (earshot mallet)
music = np.zeros((N, 2), np.float32)
note = lambda m: 440 * 2 ** ((m - 69) / 12)
CH = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [55, 60, 64]), (55, [55, 59, 62])]   # Am F C G
BAR = 3.4
def pad(ms, d):
    t = tt(d); s = np.zeros_like(t)
    for m in ms:
        for det in (-0.004, 0.0, 0.004):
            ph = 2 * np.pi * note(m) * (1 + det) * t
            s += sum(np.sin(ph * h) / h ** 1.6 for h in range(1, 6))
    env = np.minimum(1, t / 0.9) * np.minimum(1, (d - t) / 0.9)
    return s * env
k = 0; t0 = 0.0
while t0 < 66.2:
    root, ms = CH[k % 4]
    p = pad(ms, BAR + 0.9); add(music, np.stack([p, np.roll(p, 300)], 1), t0, -2)
    b = pad([root - 12], BAR + 0.9); add(music, b, t0, -4)
    k += 1; t0 += BAR
# sub pulse during the numbers (22.3 - 56.8), a soft heartbeat on each beat
for x in np.arange(22.35, 56.8, BAR / 4):
    t = tt(0.5); f = 50 + 40 * np.exp(-t * 20)
    add(music, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7), x, 4)
# melody: celesta notes from the earshot bank, tuned
_cache = {}
def cel(name):
    if name not in _cache: _cache[name] = bank.render("mallet/celesta", pitch=name)[0]
    return _cache[name]
MEL = ["E5", "C5", "A4", "B4", "C5", "A4", "F4", "G4", "G4", "E4", "C5", "B4", "D5", "B4", "G4", "A4"]
step = BAR / 4
t0 = 3.2; i = 0
while t0 < 64.5:
    if not (22.0 < t0 < 49.0):          # melody rests under the stats, so numbers stay clear
        add(music, cel(MEL[i % len(MEL)]), t0, -5)
    i += 1; t0 += step
env = np.minimum(1, np.arange(N) / (SR * 1.5)) * np.minimum(1, (N - np.arange(N)) / (SR * 2.0))
music *= env[:, None]
wav("music.wav", np.tanh(music * 0.5))

# ---------------- sfx from earshot, aimed at onset / peak
sfx = np.zeros((N, 2), np.float32); log = []
def place(sid, t, anchor="onset", off_ms=0, db=0.0, **kw):
    y, m = bank.render(sid, **kw)
    a = m["peak_s"] if anchor == "peak" else m["onset_s"]
    add(sfx, y, t + off_ms / 1000 - a, db); log.append((sid, t, m["checks"]["summary"]))
place("pro_sub_drop/soft", 0.05, db=-6)
place("reverse_swell/dark", 1.35, "peak", 42, db=-12)
CUTS = [3.15, 7.00, 11.65, 18.95, 22.35, 27.40, 34.72, 37.50, 49.10, 56.85, 58.62, 59.62, 62.30]
for i, c in enumerate(CUTS):
    place("swipe/velvet", c, "peak", 37, db=-17, seed=[1,2,4,5,6,7,9,10,11,12,13,1,2][i])
place("cut_hit/sub", 13.20, db=-6)
place("reverse_swell/short", 13.20, "peak", 42, db=-16)
for ts in (23.57, 28.20, 49.72, 53.44):
    for j in range(10):
        place("pro_hover_tick/soft", ts + j * 0.09, db=-22 - j * 0.5, seed=j + 1)
place("knock/wood" if False else "ui_pop/soft", 34.82, db=-12); place("ui_pop/soft", 36.12, db=-12, seed=2)
place("cut_hit/punch", 37.56, db=-8)
place("pro_pop_in/round", 40.29, db=-12); place("pro_pop_in/round", 44.67, db=-12, seed=2)
place("whoosh_big/thump", 49.10, "peak", 37, db=-11)
place("notify/mid_tine", 56.93, db=-14)
place("cut_hit/sub", 58.70, db=-7)
place("mallet/celesta", 60.73, db=-12, pitch="E5")
place("pro_click/soft", 63.81, db=-12)
place("logo_sting/soft_bloom", 64.3, db=-15)
wav("sfx.wav", sfx)
print(len(log), "sfx;", sum("clean" not in l[2] for l in log), "with audit warnings")
