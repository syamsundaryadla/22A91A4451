"""Sound effects for the IPL reel from the earshot bank, each placed by its measured onset / peak."""
import json, os, wave
import numpy as np
from earshot.forge import bank

D = os.path.dirname(os.path.abspath(__file__))
SR = 48000; DUR = 55.5; N = int(SR * DUR)
mix = np.zeros((N, 2), np.float32)
log = []

def place(sid, t, anchor="onset", off_ms=0, db=0.0, **kw):
    y, m = bank.render(sid, **kw)
    if y.ndim == 1: y = np.stack([y, y], 1)
    a = m["peak_s"] if anchor == "peak" else m["onset_s"]
    start = t + off_ms / 1000 - a
    i = int(round(start * SR))
    if i < 0: y = y[-i:]; i = 0
    n = min(len(y), N - i)
    mix[i:i + n] += y[:n] * (10 ** (db / 20))
    log.append(dict(id=sid, cue=round(t, 3), anchor=anchor, start=round(start, 3), audit=m["checks"]["summary"]))

def run(times, gap_ms):          # earshot kit.space_run idea: keep a run at least gap apart
    out = []
    for x in times:
        if not out or (x - out[-1]) * 1000 >= gap_ms: out.append(x)
    return out

RANKS = [(5, 9.41, 10.46, 11.84, 13.67), (4, 15.20, 16.09, 17.34, 19.04), (3, 20.40, 21.29, 23.04, 24.93), (2, 26.31, 27.24, 28.69, 30.45)]

# ---- intro
place("ui_pop/soft", 0.10, db=-8)
place("whoosh_fast/crisp", 0.55, "peak", 37, db=-10, dur=0.7, apex=0.30)
place("whoosh_fast/tight", 0.80, "peak", 37, db=-10, dur=0.6, apex=0.25)
place("cut_hit/punch", 0.95, db=-6)
place("swish/bright", 2.50, "peak", 0, db=-12)
for i in range(5):
    place("pro_pop_in/round", 3.30 + i * 0.22, db=-10, seed=10 + i)
place("ui_pop/step", 6.37, db=-9); place("ui_pop/step", 7.70, db=-9, seed=3)

# ---- ranks 5..2
for rank, tn, tname, teco, twk in RANKS:
    place("riser/dark", tn, "peak", 0, db=-13, dur=1.0)
    place("whoosh_big/thump", tn, "peak", 37, db=-8, seed=rank)
    place("cut_hit/kick", tn, db=-5)
    place("pro_impact/short", tname, db=-7, seed=rank)
    place("reverse_swell/short", tname, "peak", 42, db=-14)
    for ts in (teco, twk):
        place("pro_pop_in/deep", ts - 0.05, db=-10)
        for k, x in enumerate(run([ts + j * 0.07 for j in range(10)], 66)):
            place("pro_hover_tick/soft", x, db=-15 - k * 0.6, seed=k + 1)

# ---- number 1
place("riser/tension", 32.85, "peak", 0, db=-12, dur=1.6)
place("impact/punch", 32.85, db=-6)
place("riser/build", 33.76, "peak", 0, db=-14)
place("whoosh_big/thump_deep", 33.76, "peak", 37, db=-7)
place("impact/deep", 33.76, db=-3)
place("logo_sting/spark", 33.80, db=-11)
place("pro_shimmer/m4", 34.0, db=-15)
for ts in (35.53, 37.63):
    place("pro_pop_in/deep", ts - 0.05, db=-10)
    for k, x in enumerate(run([ts + j * 0.07 for j in range(10)], 66)):
        place("pro_hover_tick/soft", x, db=-15 - k * 0.6, seed=k + 1)
place("mallet/up4", 35.53, db=-14)

# ---- leaderboard
place("whoosh_big/swell", 38.90, "peak", 42, db=-9)
place("cut_hit/sub", 38.90, db=-6)
for i in range(5):
    place("pro_pop_in/knock", 39.8 + i * 0.25, db=-11, seed=20 + i)
place("notify/mid_tine", 43.0, db=-11)

# ---- poll + comment
place("whoosh_fast/whip", 45.40, "peak", 37, db=-9)
for i, t in enumerate((47.88, 48.81, 49.70)):
    place("ui_pop/wide", t, db=-9, seed=30 + i)
place("pro_notify/ding_2045", 50.60, db=-10)

# ---- follow
place("whoosh_big/thump_airy", 51.45, "peak", 37, db=-8)
place("pro_click/mouse", 51.75, db=-8)
for i in range(5):
    place("drip/plink", 52.25 + i * 0.12, db=-15, seed=40 + i)
place("logo_sting/soft_bloom", 53.6, db=-12)

peak = np.abs(mix).max(); print("peak", peak)
if peak > 0.98: mix *= 0.98 / peak
with wave.open(os.path.join(D, "sfx.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
json.dump(log, open(os.path.join(D, "sfx_log.json"), "w"), indent=1)
bad = [l for l in log if "clean" not in l["audit"]]
print(len(log), "placements;", len(bad), "with audit warnings")
for b in bad: print(" ", b["id"], b["audit"])
