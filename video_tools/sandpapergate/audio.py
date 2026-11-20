"""Tense documentary score + earshot SFX for Sandpapergate."""
import numpy as np, wave, os
from earshot.forge import bank
D = os.path.dirname(os.path.abspath(__file__)); SR = 48000; DUR = 112.8; N = int(SR * DUR)
rng = np.random.default_rng(4)
def tt(d): return np.arange(int(SR * d)) / SR
def add(buf, y, t, db=0.0):
    if y.ndim == 1: y = np.stack([y, y], 1)
    i = int(round(t * SR))
    if i < 0: y = y[-i:]; i = 0
    n = min(len(y), N - i)
    if n > 0: buf[i:i + n] += y[:n] * 10 ** (db / 20)
def wav(name, x):
    x = x / max(1e-9, np.abs(x).max()) * 0.92
    with wave.open(os.path.join(D, name), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())
note = lambda m: 440 * 2 ** ((m - 69) / 12)
music = np.zeros((N, 2), np.float32); t = tt(DUR)
# low drone in D minor, slowly breathing; tension rises toward the Bancroft climax
def drone(m, det):
    return sum(np.sin(2 * np.pi * note(m) * h * (1 + det) * t + h) / h ** 1.5 for h in range(1, 7))
d = drone(38, 0) * 0.6 + drone(45, 0.0008) * 0.35 + drone(50, -0.0006) * 0.25
breath = 0.6 + 0.4 * np.sin(2 * np.pi * t / 8.0) ** 2
tension = 0.7 + 0.5 * np.clip((t - 55) / 45, 0, 1) - 0.4 * np.exp(-((t - 85.0) / 0.9) ** 2)   # dip on "final straw"
env = np.clip(t / 3, 0, 1) * np.clip((DUR - t) / 2.5, 0, 1)
music[:, 0] += d * breath * tension * env; music[:, 1] += np.roll(d, 600) * breath * tension * env
# ticking clock pulse (quiet), faster in the 2026 section
x = 10.2
while x < 106.3:
    y, _ = bank.render("pro_hover_tick/soft", seed=int(x * 10) % 50 + 1, checks=False)
    add(music, y, x, -6 if x < 55 else -3)
    x += 0.75 if x < 55 else 0.5
# low heartbeat under the 2026 section
for x in np.arange(55.2, 106.3, 1.0):
    tb = tt(0.4); f = 48 + 30 * np.exp(-tb * 25)
    hb = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tb * 9)
    add(music, hb, x, 6); add(music, hb * 0.6, x + 0.22, 6)
music *= 0.5
wav("music.wav", np.tanh(music))

sfx = np.zeros((N, 2), np.float32); log = []
def place(sid, tc, anchor="onset", off_ms=0, db=0.0, **kw):
    y, m = bank.render(sid, **kw)
    a = m["peak_s"] if anchor == "peak" else m["onset_s"]
    add(sfx, y, tc + off_ms / 1000 - a, db); log.append((sid, m["checks"]["summary"]))
place("impact/deep", 0.25, db=-4)
place("reverse_swell/dark", 0.3, "peak", 0, db=-14)
CUTS = [10.23, 18.92, 25.49, 35.04, 42.35, 47.07, 55.16, 69.05, 78.12, 84.21, 93.57, 96.76, 100.39, 106.44]
for i, c in enumerate(CUTS):
    place("swipe/velvet", c, "peak", 37, db=-16, seed=[1, 2, 4, 5, 6, 7, 9, 10, 11, 12, 13, 1, 2, 4][i])
for c in (10.23, 42.35, 55.16):                 # date cards: typewriter-ish ticks + low hit
    place("cut_hit/sub", c, db=-7)
    for j in range(6): place("pro_typing_key/tick", c + 0.04 + j * 0.09, db=-14, seed=j + 1)
place("shutter/snap", 25.49, db=-8)
for j, x in enumerate(np.arange(27.45, 29.45, 0.208)):          # sandpaper rubbing strokes
    place("swipe/paper", x, "peak", 0, db=-13, dur=0.26, apex=0.10, seed=[1, 2, 4, 5, 6, 7, 9, 10, 11, 12][j % 10])
place("cut_hit/punch", 29.59, db=-5)            # caught on camera
place("pro_impact/short", 35.04, db=-8)
for j in range(3): place("knock/desk", 37.93 + j * 0.9, db=-9, seed=j + 1)   # ban cards
place("pro_impact/air", 52.18, db=-10)
place("reverse_swell/ring", 58.74, "peak", 42, db=-13)
place("cut_hit/sub", 62.56, db=-7); place("cut_hit/sub", 66.50, db=-6)
place("impact/punch", 69.05, db=-6)             # utter nonsense
place("pro_impact/short", 81.50, db=-7)         # cover-up
place("riser/tension", 84.21, "peak", 0, db=-11, dur=2.0)
place("impact/deep", 84.21, db=-3)              # final straw
place("cut_hit/punch", 87.77, db=-7)
place("cut_hit/sub", 93.57, db=-6); place("cut_hit/sub", 96.76, db=-5)
place("riser/dark", 100.39, "peak", 0, db=-12, dur=1.0); place("impact/punch", 100.39, db=-5)
place("pro_shimmer/m1", 101.2, db=-12)
place("cut_hit/sub", 103.2, db=-8)
place("reverse_swell/cymbal", 106.44, "peak", 42, db=-12)
place("cut_hit/rumble", 107.68, db=-8)
place("logo_sting/soft_bloom", 110.6, db=-15)
wav("sfx.wav", sfx)
bad = [l for l in log if not l[1].split(":", 1)[1].strip().startswith("clean")]
print(len(log), "sfx;", len(bad), "flagged"); [print(" ", b) for b in bad]
