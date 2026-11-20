"""IPL 2026 powerplay kings: top 5 batters. 1080x1920 @30fps."""
import math, os, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

D = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(D, "..", "fonts")
OUT = sys.argv[1]
PREVIEW = [float(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else None
W, H, FPS, DUR = 1080, 1920, 30, 94.59
WHITE = (255, 255, 255); GOLD = (255, 196, 40); MUTED = (200, 200, 215)
_F = {}
def F(n, s):
    if (n, s) not in _F:
        _F[(n, s)] = ImageFont.truetype(os.path.join(FONTS, {"anton": "Anton.ttf", "mb": "Montserrat-Black.ttf", "mx": "Montserrat-ExtraBold.ttf", "ms": "Montserrat-SemiBold.ttf"}[n]), s)
    return _F[(n, s)]
clamp = lambda x, a=0.0, b=1.0: max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return x * x * (3 - 2 * x)
def back(x):
    x = clamp(x); c1 = 1.7; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def pr(t, s, d): return clamp((t - s) / d)
def fade(t, a, b, d=0.3): return eo(pr(t, a, d)) * (1 - eio(pr(t, b - d, d)))

P = [  # rank, key, name, team, logo, c1, c2, img, kind, t_rank, t_name, t_end, stats[(label, value, fmt, t)], tags[(text, t0, t1)]
 dict(rank=5, name="TRAVIS HEAD", team="SUNRISERS HYDERABAD", logo="SRH", c1=(242, 101, 34), c2=(255, 170, 60), img="HEAD.jpg", kind="photo", focus=(0.5, 0.25),
      tr=10.16, tn=10.90, te=29.76, stats=[("RUNS", 337, "{:.0f}", 20.77), ("STRIKE RATE", 170.2, "{:.1f}", 17.60), ("SIXES", 17, "{:.0f}", 22.19)],
      tags=[("BAD SEASON?  STILL TOP 5", 23.83, 29.5)]),
 dict(rank=4, name="SAI SUDHARSAN", team="GUJARAT TITANS", logo=None, c1=(40, 70, 150), c2=(212, 175, 55), img="SAI.jpg", kind="photo", focus=(0.42, 0.2),
      tr=29.76, tn=30.55, te=41.76, stats=[("RUNS", 347, "{:.0f}", 36.40), ("FOURS", 50, "{:.0f}", 39.80)],
      tags=[("MOST FOURS IN THE POWERPLAY", 40.3, 41.5)]),
 dict(rank=3, name="VIRAT KOHLI", team="ROYAL CHALLENGERS BENGALURU", logo="RCB", c1=(213, 32, 39), c2=(212, 175, 55), img="KOHLI.png", kind="cutout", ch=820,
      tr=41.76, tn=42.55, te=55.94, stats=[("RUNS", 360, "{:.0f}", 53.00), ("STRIKE RATE", 174.8, "{:.1f}", 50.21), ("AVERAGE", 51.4, "{:.1f}", 47.70)],
      tags=[]),
 dict(rank=2, name="ABHISHEK SHARMA", team="SUNRISERS HYDERABAD", logo="SRH", c1=(242, 101, 34), c2=(255, 200, 0), img="ABHI.jpg", kind="photo", focus=(0.5, 0.2),
      tr=55.94, tn=56.70, te=69.25, stats=[("RUNS", 369, "{:.0f}", 64.46), ("STRIKE RATE", 214.5, "{:.1f}", 61.02), ("SIXES", 29, "{:.0f}", 66.90)],
      tags=[]),
 dict(rank=1, name="VAIBHAV SOORYAVANSHI", team="RAJASTHAN ROYALS", logo="RR", c1=(234, 26, 133), c2=(60, 100, 230), img="VAIBHAV.png", kind="cutout", ch=1060,
      tr=69.25, tn=73.40, te=88.01, stats=[("RUNS", 521, "{:.0f}", 80.68), ("STRIKE RATE", 233.6, "{:.1f}", 76.40), ("SIXES", 46, "{:.0f}", 82.96)],
      tags=[("15 YEARS OLD", 70.77, 75.3)]),
]
T_BOARD = 88.01

# ------------------------------------------------------------------ background
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
BASE = np.zeros((H, W, 3), np.float32) + np.array([7, 9, 18], np.float32)
GLOW = np.exp(-(((xx - W * 0.5) / 650) ** 2 + ((yy - H * 0.32) / 720) ** 2))[..., None].astype(np.float32)
GLOW2 = np.exp(-(((xx - W * 0.5) / 900) ** 2 + ((yy - H * 1.05) / 450) ** 2))[..., None].astype(np.float32)
VIG = np.clip(1 - 0.5 * (((xx - W / 2) / (W * 0.8)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2), 0.35, 1)[..., None].astype(np.float32)
rng = np.random.default_rng(3)
GR = [np.asarray(Image.fromarray(rng.normal(0, 3.5, (H // 2, W // 2)).astype(np.float32)).resize((W, H)))[..., None] for _ in range(4)]

def who(t):
    for p in P:
        if p["tr"] <= t < p["te"]: return p
    return None
def cols(t):
    p = who(t)
    if p is None: return (255, 120, 30), (60, 90, 220)
    k = eio(pr(t, p["tr"], 0.4)); i = P.index(p)
    prev = (P[i - 1]["c1"], P[i - 1]["c2"]) if i > 0 else ((255, 120, 30), (60, 90, 220))
    mx = lambda a, b: tuple(a[j] * (1 - k) + b[j] * k for j in range(3))
    return mx(prev[0], p["c1"]), mx(prev[1], p["c2"])

def background(t):
    c1, c2 = cols(t)
    a = BASE + GLOW * np.array(c1, np.float32) * (0.50 + 0.06 * math.sin(t * 2)) + GLOW2 * np.array(c2, np.float32) * 0.28
    a = a * VIG + GR[int(t * FPS) % 4]
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(4):
        off = ((t * 120 + i * 650) % 2700) - 700
        d.polygon([(off, 0), (off + 80, 0), (off - 900, H), (off - 980, H)], fill=(*[int(v) for v in c1], 14))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(22)))
    return img

# ------------------------------------------------------------------ text helpers
_tc = {}
def timg(txt, f, fill=WHITE, spacing=0, stroke=0, stroke_fill=(0, 0, 0), glow=None, shadow=True):
    k = (txt, id(f), fill, spacing, stroke, stroke_fill, glow, shadow)
    if k in _tc: return _tc[k]
    chars = list(txt)
    if spacing:
        ws = [(f.getbbox(c)[2] - f.getbbox(c)[0]) if c != " " else f.getbbox("n")[2] for c in chars]
        tw = sum(ws) + spacing * (len(chars) - 1)
    else:
        bb = f.getbbox(txt, stroke_width=stroke); tw = bb[2] - bb[0]
    asc, desc = f.getmetrics(); th = asc + desc + stroke * 2
    pad = 50; im = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    def draw(dd, dy, col, sw=0, sf=None):
        if spacing:
            x = pad
            for c, w_ in zip(chars, ws):
                dd.text((x - (f.getbbox(c)[0] if c != " " else 0), pad + dy), c, font=f, fill=col, stroke_width=sw, stroke_fill=sf); x += w_ + spacing
        else:
            dd.text((pad - f.getbbox(txt, stroke_width=stroke)[0], pad + dy + stroke), txt, font=f, fill=col, stroke_width=sw, stroke_fill=sf)
    if glow:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0)); draw(ImageDraw.Draw(g), 0, glow, stroke + 8, glow)
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(20)))
    if shadow:
        s = Image.new("RGBA", im.size, (0, 0, 0, 0)); draw(ImageDraw.Draw(s), 6, (0, 0, 0, 150), stroke, (0, 0, 0, 150))
        im.alpha_composite(s.filter(ImageFilter.GaussianBlur(9)))
    draw(ImageDraw.Draw(im), 0, fill, stroke, stroke_fill)
    _tc[k] = im
    return im

def put(img, im, cx, cy, alpha=1.0, scale=1.0):
    if alpha <= 0.01 or scale <= 0.01: return
    if abs(scale - 1) > 0.003: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 0.999: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def rrect(w, h, r, fill, outline=None, width=0):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=fill, outline=outline, width=width)
    return im

# ------------------------------------------------------------------ player images
_pc = {}
def player_img(p):
    if p["img"] in _pc: return _pc[p["img"]]
    src = Image.open(os.path.join(D, "img", p["img"]))
    if p["kind"] == "photo":
        im = src.convert("RGB"); im = ImageEnhance.Contrast(im).enhance(1.06); im = ImageEnhance.Color(im).enhance(1.08)
        bw, bh = int(W * 1.1), int(1250 * 1.1)
        s = max(bw / im.width, bh / im.height); im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        fx, fy = p["focus"]; x = int((im.width - bw) * fx); y = int((im.height - bh) * fy)
        im = im.crop((x, y, x + bw, y + bh)).filter(ImageFilter.UnsharpMask(2, 70, 2)).convert("RGBA")
        m = np.ones((bh, bw), np.float32)
        ys = np.arange(bh)[:, None] / bh
        m *= np.clip((1 - ys) / 0.40, 0, 1) ** 1.3          # fade bottom 40%
        m *= np.clip(ys / 0.06, 0, 1)                        # soft top
        im.putalpha(Image.fromarray((m * 255).astype(np.uint8)))
    else:
        im = src.convert("RGBA"); s = p["ch"] / im.height
        im = im.resize((int(im.width * s), p["ch"]), Image.LANCZOS)
        im = im.filter(ImageFilter.UnsharpMask(2, 80, 2))
        a = np.asarray(im.getchannel("A")).astype(np.float32) / 255
        ys = np.arange(im.height)[:, None] / im.height
        a *= np.clip((1 - ys) / 0.22, 0, 1)
        im.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    _pc[p["img"]] = im
    return im

_lg = {}
def logo(k, h):
    if (k, h) not in _lg:
        lg = Image.open(os.path.join(D, "img", k + ".png")).convert("RGBA"); s = h / lg.height
        _lg[(k, h)] = lg.resize((int(lg.width * s), h), Image.LANCZOS)
    return _lg[(k, h)]

# ------------------------------------------------------------------ sections
def intro(img, t):
    if t >= P[0]["tr"] + 0.3: return
    out = 1 - pr(t, P[0]["tr"] - 0.2, 0.4)
    k = pr(t, 0.05, 0.35)
    put(img, rrect(330, 74, 37, (230, 40, 40, 255)), W / 2, 450, k * out, back(k))
    put(img, timg("IPL 2026", F("mb", 40), WHITE, spacing=3, shadow=False), W / 2, 450, k * out, back(k))
    k1 = eo(pr(t, 0.3, 0.45)); k2 = eo(pr(t, 0.55, 0.45))
    put(img, timg("POWERPLAY", F("anton", 210), WHITE), W / 2 - (1 - k1) * 900, 640, k1 * out)
    put(img, timg("KINGS", F("anton", 260), (0, 0, 0, 0), stroke=6, stroke_fill=GOLD, glow=(255, 140, 0, 120), shadow=False), W / 2 + (1 - k2) * 900, 880, k2 * out)
    k3 = eo(pr(t, 2.0, 0.4))
    put(img, timg("TOP 5 BATTERS", F("mb", 70), WHITE, spacing=4), W / 2, 1090 + (1 - k3) * 40, k3 * out)
    # overs 1-6 meter, lighting as "overs 1 to 6" is spoken
    label_k = eo(pr(t, 4.9, 0.35))
    put(img, timg("OVERS", F("mx", 30), MUTED, spacing=6), W / 2, 1250, label_k * out)
    for i in range(6):
        on = eo(pr(t, 5.0 + i * 0.22, 0.25))
        cx = W / 2 + (i - 2.5) * 140; cy = 1360
        ring = Image.new("RGBA", (120, 120), (0, 0, 0, 0)); rd = ImageDraw.Draw(ring)
        rd.ellipse((6, 6, 113, 113), fill=(255, 196, 40, int(255 * on)) if on > 0.5 else (255, 255, 255, 24), outline=(255, 196, 40, 255), width=4)
        put(img, ring, cx, cy, label_k * out, 0.85 + 0.15 * back(on))
        put(img, timg(str(i + 1), F("anton", 64), (20, 14, 0) if on > 0.5 else WHITE, shadow=False), cx, cy - 2, label_k * out)

def player(img, t, p):
    if not (p["tr"] - 0.05 <= t < p["te"] + 0.35): return
    out = 1 - pr(t, p["te"] - 0.1, 0.35)
    is1 = p["rank"] == 1
    c1 = p["c1"]
    # big faint numeral
    kn = pr(t, p["tr"], 0.35)
    slam = 1 + 0.6 * (1 - eo(kn))
    put(img, timg(str(p["rank"]), F("anton", 980), (*c1, 70) if not is1 else (255, 196, 40, 80), shadow=False), W / 2 + 230, 560, min(1, kn * 2) * out, slam)
    # #1 suspense: before name reveal, a dark silhouette
    kp = pr(t, p["tn"] - 0.25, 0.5)
    if kp > 0:
        pim = player_img(p)
        drift = (t - p["tn"]) * 6
        if p["kind"] == "photo":
            put(img, pim, W / 2, 80 + pim.height / 2 - 20 - drift, eo(kp) * out, 1.04 - 0.04 * eo(kp))
        else:
            y = 1150 - pim.height / 2 - drift
            put(img, pim, W / 2, y, eo(kp) * out, 1.04 - 0.04 * eo(kp))
    # rank chip
    put(img, rrect(220, 70, 35, (*[int(v) for v in c1], 255) if not is1 else (255, 196, 40, 255)), W / 2, 185, min(1, kn * 2) * out, back(kn))
    put(img, timg(f"NO. {p['rank']}", F("mb", 36), WHITE if not is1 else (25, 15, 0), spacing=4, shadow=False), W / 2, 185, min(1, kn * 2) * out, back(kn))
    # name + team
    kname = eo(pr(t, p["tn"] + 0.05, 0.45))
    nsize = 118 if len(p["name"]) <= 15 else 96
    put(img, timg(p["name"], F("anton", nsize), WHITE), W / 2, 1210 + (1 - kname) * 40, kname * out)
    kt = eo(pr(t, p["tn"] + 0.25, 0.45))
    team_im = timg(p["team"], F("mx", 30), tuple(int(v) for v in (p["c2"] if p["rank"] in (3, 4) else c1)) if not is1 else GOLD, spacing=4)
    if p["logo"]:
        lg = logo(p["logo"], 58)
        tw = team_im.width - 100 + 20 + lg.width; x0 = W / 2 - tw / 2
        put(img, lg, x0 + lg.width / 2, 1300 + (1 - kt) * 30, kt * out)
        put(img, team_im, x0 + lg.width + 20 + (team_im.width - 100) / 2, 1300 + (1 - kt) * 30, kt * out)
    else:
        put(img, team_im, W / 2, 1300 + (1 - kt) * 30, kt * out)
    # stat cards (order on screen = list order; each appears when spoken)
    n = len(p["stats"]); cw = 300 if n == 3 else 420; gap = 30
    x0 = W / 2 - (n * cw + (n - 1) * gap) / 2 + cw / 2
    for i, (lab, val, fmt, ts) in enumerate(p["stats"]):
        kc = pr(t, ts - 0.05, 0.35)
        if kc <= 0: continue
        cx = x0 + i * (cw + gap); cy = 1510 + (1 - eo(kc)) * 60
        main = i == 0
        acc = GOLD if is1 else tuple(int(v) for v in (p['c2'] if p['rank'] == 4 else c1))
        card = Image.new("RGBA", (cw, 230), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((0, 0, cw - 1, 229), 26, fill=(12, 14, 28, 215), outline=(*acc, 255) if main else (255, 255, 255, 50), width=4 if main else 2)
        put(img, card, cx, cy, min(1, kc * 1.6) * out)
        v = val * eo(pr(t, ts, 0.75))
        s = fmt.format(v)
        put(img, timg(s, F("anton", 112), acc if main else WHITE), cx, cy + 20, min(1, kc * 1.6) * out)
        put(img, timg(lab, F("mx", 24), MUTED, spacing=3, shadow=False), cx, cy - 72, min(1, kc * 1.6) * out)
    # tags
    for txt, a, b in p["tags"]:
        k = fade(t, a, b)
        if k <= 0: continue
        tim = timg(txt, F("mb", 32), (20, 14, 0) if is1 else WHITE, spacing=3, shadow=False)
        pill = rrect(tim.width - 100 + 70, 70, 35, (255, 196, 40, 255) if is1 else (*[int(v) for v in c1], 255))
        y = 1735 if not is1 else 1210
        put(img, pill, W / 2, y, k, 0.9 + 0.1 * back(pr(t, a, 0.35)))
        put(img, tim, W / 2, y, k, 0.9 + 0.1 * back(pr(t, a, 0.35)))
    if is1:
        kr = fade(t, 84.72, 87.9)
        if kr > 0:
            sc = 0.85 + 0.15 * back(pr(t, 84.72, 0.4))
            badge = Image.new("RGBA", (900, 130), (0, 0, 0, 0)); bd = ImageDraw.Draw(badge)
            bd.rounded_rectangle((0, 0, 899, 129), 65, fill=(255, 196, 40, 255))
            put(img, badge, W / 2, 1745, kr, sc)
            put(img, timg("IPL RECORD", F("anton", 54), (25, 15, 0), shadow=False), W / 2, 1722, kr, sc)
            put(img, timg("BROKE DAVID WARNER'S 10-YEAR RECORD", F("mx", 24), (60, 40, 0), spacing=2, shadow=False), W / 2, 1774, kr, sc)
        confetti(img, t - 80.68)

random.seed(5)
CONF = [dict(x=random.uniform(-100, W + 100), vx=random.uniform(-160, 160), vy=random.uniform(-1500, -700), rot=random.uniform(0, 360), vr=random.uniform(-400, 400),
             c=random.choice([(234, 26, 133), (255, 196, 40), (255, 255, 255), (60, 100, 230)]), w=random.uniform(12, 24), h=random.uniform(6, 12)) for _ in range(140)]
def confetti(img, dt):
    if dt < 0 or dt > 3.6: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for c in CONF:
        x = c["x"] + c["vx"] * dt; y = H + 40 + c["vy"] * dt + 900 * dt * dt
        if -60 < y < H + 60:
            lay.alpha_composite(Image.new("RGBA", (int(c["w"]), int(c["h"])), (*c["c"], 230)).rotate(c["rot"] + c["vr"] * dt, expand=True), (int(x), int(y)))
    al = clamp((3.6 - dt) / 0.8)
    if al < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * al)))
    img.alpha_composite(lay)

def board(img, t):
    if t < T_BOARD - 0.1: return
    k0 = eo(pr(t, T_BOARD, 0.4))
    put(img, timg("POWERPLAY KINGS", F("anton", 96), WHITE), W / 2, 300 + (1 - k0) * -40, k0)
    put(img, timg("IPL 2026  •  OVERS 1–6  •  RUNS", F("mx", 28), MUTED, spacing=3, shadow=False), W / 2, 385, k0)
    rows = sorted(P, key=lambda p: p["rank"])
    mx = 521
    for i, p in enumerate(rows):
        ts = T_BOARD + 0.25 + (4 - i) * 0.18
        kr = eo(pr(t, ts, 0.45))
        if kr <= 0: continue
        y = 540 + i * 190; xoff = (1 - kr) * 700; hl = p["rank"] == 1
        row = rrect(980, 160, 30, (255, 255, 255, 24) if not hl else (255, 160, 30, 55), (255, 196, 40, 255) if hl else (255, 255, 255, 40), 5 if hl else 2)
        put(img, row, W / 2 + xoff, y, kr)
        put(img, timg(str(p["rank"]), F("anton", 84), GOLD if hl else WHITE), 105 + xoff, y, kr)
        put(img, timg(p["name"], F("mx", 30), WHITE, spacing=2, shadow=False), 175 + xoff + (timg(p["name"], F("mx", 30), WHITE, spacing=2, shadow=False).width - 100) / 2, y - 40, kr)
        runs = next(s for s in p["stats"] if s[0] == "RUNS")[1]
        kb = eo(pr(t, ts + 0.2, 0.7)); bw = int(600 * runs / mx * kb)
        if bw > 10:
            bar = rrect(bw, 38, 19, (*[int(v) for v in (p["c1"] if not hl else GOLD)], 255))
            img.alpha_composite(bar, (int(175 + xoff), int(y + 8)))
        put(img, timg(str(runs), F("anton", 70), GOLD if hl else WHITE), 900 + xoff, y + 5, kb)
    kc = eo(pr(t, 91.66, 0.4))
    if kc > 0:
        put(img, timg("COMMENT YOUR FAVOURITE", F("mx", 34), WHITE, spacing=3), W / 2, 1530, kc)
        pill = rrect(440, 112, 56, (230, 40, 40, 255)); sc = 0.9 + 0.1 * back(pr(t, 91.66, 0.4)) + 0.03 * math.sin(t * 6)
        put(img, pill, W / 2, 1670, kc, sc)
        put(img, timg("+  FOLLOW", F("anton", 66), WHITE, shadow=False), W / 2, 1667, kc, sc)

CUTS = [p["tr"] for p in P] + [T_BOARD]
def wipe(img, t):
    for c in CUTS:
        dt = t - c
        if -0.18 <= dt < 0.18:
            k = (dt + 0.18) / 0.36; col = cols(c + 0.5)[0]
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); x = -900 + k * (W + 1800)
            d.polygon([(x - 300, 0), (x + 300, 0), (x - 100, H), (x - 700, H)], fill=(*[int(v) for v in col], 235))
            d.polygon([(x + 330, 0), (x + 380, 0), (x - 20, H), (x - 70, H)], fill=(255, 255, 255, 200))
            img.alpha_composite(lay)
def flash(img, t):
    for tt, s in [(p["tn"], 110) for p in P] + [(80.68, 150)]:
        dt = t - tt
        if 0 <= dt < 0.2: img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(s * (1 - dt / 0.2)))))

def frame(t):
    img = background(t)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    intro(lay, t)
    for p in P: player(lay, t, p)
    board(lay, t)
    dx = dy = 0
    for tt, amp in [(p["tr"], 8) for p in P] + [(80.68, 16)]:
        d_ = t - tt
        if 0 <= d_ < 0.3: dx = math.sin(d_ * 90) * amp * (1 - d_ / 0.3); dy = math.cos(d_ * 70) * amp * (1 - d_ / 0.3)
    img.alpha_composite(lay, (int(dx), int(dy)))
    flash(img, t); wipe(img, t)
    f = min(1, t / 0.3, (DUR - t) / 0.5)
    out = img.convert("RGB")
    if f < 1: out = Image.eval(out, lambda v: int(v * max(0, f)))
    return out

if PREVIEW:
    os.makedirs(os.path.join(D, "prev"), exist_ok=True)
    for t in PREVIEW: frame(t).save(os.path.join(D, "prev", f"p_{t:05.2f}.jpg"), quality=88)
    sys.exit()
n = int(DUR * FPS)
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
for i in range(n):
    ff.stdin.write(frame(i / FPS).tobytes())
    if i % 300 == 0: print("frame", i, "/", n, flush=True)
ff.stdin.close(); ff.wait(); print("done")
