import numpy as np, wave, os
from earshot.forge import bank
D = os.path.dirname(os.path.abspath(__file__)); SR = 48000; N = int(SR * 18.3)
mix = np.zeros((N, 2), np.float32); log = []
def place(sid, t, anchor="onset", off=0.0, db=0.0, **kw):
    y, m = bank.render(sid, **kw); a = m["peak_s"] if anchor == "peak" else m["onset_s"]
    i = int(round((t + off - a) * SR)); n = min(len(y), N - i)
    if i < 0: y = y[-i:]; n = min(len(y), N); i = 0
    mix[i:i + n] += y[:n] * 10 ** (db / 20); log.append(m["checks"]["summary"])
place("cut_hit/punch", 0.0, db=-5); place("whoosh_fast/crisp", 0.4, "peak", 0.037, -10, dur=0.6, apex=0.25)
for k, t0 in enumerate([2.0, 4.6, 7.2, 9.8]):
    place("whoosh_big/thump", t0, "peak", 0.037, -8, seed=k + 1); place("cut_hit/kick", t0, db=-6)
    for j in range(12): place("pro_hover_tick/soft", t0 + 0.45 + j * 0.1, db=-17 - j * 0.5, seed=j + 1)
place("riser/tension", 12.4, "peak", 0, -11, dur=1.4)
place("whoosh_big/thump_deep", 12.4, "peak", 0.037, -7); place("impact/deep", 13.1, db=-3)
for j in range(20): place("glitch/mid", 10.7 + j * 0.06, db=-24, seed=j % 9 + 1) if False else None
place("pro_glitch/data", 14.0, db=-16)
place("pro_notify/ding_2045", 15.9, db=-8); place("pro_pop_in/round", 15.9, db=-10)
pk = np.abs(mix).max(); mix *= 0.95 / pk
with wave.open(os.path.join(D, "sfx.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print(len(log), "sfx;", sum(not l.split(":", 1)[1].strip().startswith("clean") for l in log), "flagged")
