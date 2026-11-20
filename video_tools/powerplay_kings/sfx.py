import json, os, wave
import numpy as np
from earshot.forge import bank
D = os.path.dirname(os.path.abspath(__file__)); SR = 48000; N = int(SR * 95.0)
mix = np.zeros((N, 2), np.float32); log = []
def place(sid, t, anchor="onset", off_ms=0, db=0.0, **kw):
    y, m = bank.render(sid, **kw)
    if y.ndim == 1: y = np.stack([y, y], 1)
    a = m["peak_s"] if anchor == "peak" else m["onset_s"]
    i = int(round((t + off_ms / 1000 - a) * SR))
    if i < 0: y = y[-i:]; i = 0
    n = min(len(y), N - i); mix[i:i + n] += y[:n] * 10 ** (db / 20)
    log.append((sid, kw.get("seed"), m["checks"]["summary"]))
def ticks(ts):
    for j in range(10): place("pro_hover_tick/soft", ts + j * 0.07, db=-16 - j * 0.6, seed=j + 1)
# intro
place("ui_pop/soft", 0.05, db=-8)
place("whoosh_fast/crisp", 0.50, "peak", 37, db=-10, dur=0.7, apex=0.30)
place("whoosh_fast/tight", 0.75, "peak", 37, db=-10, dur=0.6, apex=0.25)
place("cut_hit/punch", 0.95, db=-6)
place("swish/bright", 2.10, "peak", 0, db=-12)
for i in range(6): place("pro_pop_in/round", 5.0 + i * 0.22, db=-11, seed=10 + i)
P = [(10.16, 10.90, [20.77, 17.60, 22.19]), (29.76, 30.55, [36.40, 39.80]), (41.76, 42.55, [53.00, 50.21, 47.70]), (55.94, 56.70, [64.46, 61.02, 66.90])]
for k, (tr, tn, st) in enumerate(P):
    place("riser/dark", tr, "peak", 0, db=-13, dur=1.0)
    place("whoosh_big/thump", tr, "peak", 37, db=-8, seed=k + 1)
    place("cut_hit/kick", tr, db=-5)
    place("pro_impact/short", tn, db=-7, seed=k + 1)
    place("reverse_swell/short", tn, "peak", 42, db=-14)
    for ts in st: place("pro_pop_in/deep", ts - 0.05, db=-10); ticks(ts)
for a in (23.83, 40.30): place("ui_pop/wide", a, db=-10)
# number 1
place("riser/tension", 69.25, "peak", 0, db=-12, dur=1.6)
place("whoosh_big/thump_deep", 69.25, "peak", 37, db=-8)
place("impact/punch", 69.25, db=-6)
place("ui_pop/wide", 70.77, db=-10, seed=3)
place("riser/build", 73.40, "peak", 0, db=-14)
place("impact/deep", 73.40, db=-4)
place("logo_sting/spark", 73.45, db=-11)
for ts in (76.40, 80.68, 82.96): place("pro_pop_in/deep", ts - 0.05, db=-10); ticks(ts)
place("cut_hit/sub", 80.68, db=-5); place("pro_shimmer/m4", 80.9, db=-15)
place("notify/mid_tine", 84.72, db=-10); place("mallet/up4", 84.75, db=-14)
# board + outro
place("whoosh_big/swell", 88.01, "peak", 42, db=-9); place("cut_hit/sub", 88.01, db=-6)
for i in range(5): place("pro_pop_in/knock", 88.26 + (4 - i) * 0.18, db=-11, seed=20 + i)
place("pro_notify/ding_2045", 91.66, db=-10); place("pro_click/mouse", 91.9, db=-9)
place("logo_sting/soft_bloom", 92.8, db=-13)
pk = np.abs(mix).max(); mix *= 0.95 / pk
with wave.open(os.path.join(D, "sfx.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
bad = [l for l in log if not l[2].split(":", 1)[1].strip().startswith("clean")]
print(len(log), "placements;", len(bad), "flagged"); [print(" ", b) for b in bad]
