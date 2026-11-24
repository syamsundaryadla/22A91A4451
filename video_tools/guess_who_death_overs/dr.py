"""IPL all-time most death-overs runs: top 5 countdown, #1 hidden (guess). No VO. 1080x1920 @30fps."""
import math, os, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

D = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(D, "..", "fonts")
OUT = sys.argv[1]
PREVIEW = [float(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else None
W, H, FPS = 1080, 1920, 30
BEAT = 0.5                                   # 120 bpm grid: every player lands on a bar
T_HOOK, T_P = 0.0, [1.5, 3.5, 5.5, 7.5]      # #5..#2 start times
T_ONE, T_PIN, DUR = 9.5, 12.5, 14.0
WHITE = (255, 255, 255); GOLD = (255, 196, 40); MUTED = (200, 200, 215)
LABEL = "OVERS 16–20  •  TILL IPL 2025"
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

P = [  # rank, name, team, c1, c2, img, kind, runs, focus
 dict(rank=5, name="HARDIK PANDYA", team="MUMBAI INDIANS", c1=(0, 90, 190), c2=(212, 175, 55), img="HARDIK.png", kind="cut", runs=1164),
 dict(rank=4, name="RAVINDRA JADEJA", team="CHENNAI SUPER KINGS", c1=(250, 200, 20), c2=(30, 60, 150), img="JADEJA.jpg", kind="photo", runs=1532, focus=(0.5, 0.2)),
 dict(rank=3, name="DINESH KARTHIK", team="ROYAL CHALLENGERS BENGALURU", c1=(213, 32, 39), c2=(212, 175, 55), img="KARTHIK.jpg", kind="photo", runs=1565, focus=(0.6, 0.15)),
 dict(rank=2, name="KIERON POLLARD", team="MUMBAI INDIANS", c1=(0, 90, 190), c2=(212, 175, 55), img="POLLARD.jpg", kind="photo", runs=1708, focus=(0.4, 0.12)),
]
for p, t0 in zip(P, T_P): p["t0"] = t0; p["t1"] = t0 + 2.0

# ------------------------------------------------------------------ background
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
BASE = np.zeros((H, W, 3), np.float32) + np.array([7, 8, 16], np.float32)
GLOW = np.exp(-(((xx - W * 0.5) / 650) ** 2 + ((yy - H * 0.33) / 720) ** 2))[..., None].astype(np.float32)
GLOW2 = np.exp(-(((xx - W * 0.5) / 900) ** 2 + ((yy - H * 1.05) / 450) ** 2))[..., None].astype(np.float32)
VIG = np.clip(1 - 0.5 * (((xx - W / 2) / (W * 0.8)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2), 0.35, 1)[..., None].astype(np.float32)
rng = np.random.default_rng(3)
GR = [np.asarray(Image.fromarray(rng.normal(0, 3.5, (H // 2, W // 2)).astype(np.float32)).resize((W, H)))[..., None] for _ in range(4)]
def cur(t):
    for p in P:
        if p["t0"] <= t < p["t1"]: return p
    return None
def cols(t):
    p = cur(t)
    if p: return p["c1"], p["c2"]
    if t >= T_ONE: return (255, 170, 30), (60, 40, 10)
    return (255, 120, 30), (60, 90, 220)
def background(t):
    c1, c2 = cols(t)
    a = BASE + GLOW * np.array(c1, np.float32) * (0.48 + 0.06 * math.sin(t * 4)) + GLOW2 * np.array(c2, np.float32) * 0.26
    a = a * VIG + GR[int(t * FPS) % 4]
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(4):
        off = ((t * 160 + i * 650) % 2700) - 700
        d.polygon([(off, 0), (off + 80, 0), (off - 900, H), (off - 980, H)], fill=(*[int(v) for v in c1], 16))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(22)))
    return img

# ------------------------------------------------------------------ text
_tc = {}
def timg(txt, f, fill=WHITE, spacing=0, stroke=0, stroke_fill=(0, 0, 0), glow=None, shadow=True):
    k = (txt, id(f), fill, spacing, stroke, stroke_fill, glow, shadow)
    if k in _tc: return _tc[k]
    chars = list(txt)
    ws = [(f.getbbox(c, stroke_width=stroke)[2] - f.getbbox(c, stroke_width=stroke)[0]) if c != " " else f.getbbox("n")[2] for c in chars]
    tw = sum(ws) + spacing * (len(chars) - 1); asc, desc = f.getmetrics(); th = asc + desc + stroke * 2
    pad = 50; im = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    def draw(dd, dy, col, sw=0, sf=None):
        x = pad
        for c, w_ in zip(chars, ws):
            if c != " ": dd.text((x - f.getbbox(c, stroke_width=stroke)[0], pad + dy + stroke), c, font=f, fill=col, stroke_width=sw, stroke_fill=sf)
            x += w_ + spacing
    if glow:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0)); draw(ImageDraw.Draw(g), 0, glow, stroke + 8, glow); im.alpha_composite(g.filter(ImageFilter.GaussianBlur(20)))
    if shadow:
        s = Image.new("RGBA", im.size, (0, 0, 0, 0)); draw(ImageDraw.Draw(s), 6, (0, 0, 0, 150), stroke, (0, 0, 0, 150)); im.alpha_composite(s.filter(ImageFilter.GaussianBlur(9)))
    draw(ImageDraw.Draw(im), 0, fill, stroke, stroke_fill)
    _tc[k] = im
    return im
def put(img, im, cx, cy, alpha=1.0, scale=1.0):
    if alpha <= 0.01 or scale <= 0.01: return
    if abs(scale - 1) > 0.003: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 0.999: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
def rrect(w, h, r, fill, outline=None, width=0):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=fill, outline=outline, width=width); return im

_pc = {}
def player_img(p):
    if p["img"] in _pc: return _pc[p["img"]]
    src = Image.open(os.path.join(D, "img", p["img"]))
    if p["kind"] == "photo":
        im = ImageEnhance.Color(src.convert("RGB")).enhance(1.08)
        bw, bh = int(W * 1.08), int(1250 * 1.08)
        s = max(bw / im.width, bh / im.height); im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        fx, fy = p["focus"]; x = int((im.width - bw) * fx); y = int((im.height - bh) * fy)
        im = im.crop((x, y, x + bw, y + bh)).filter(ImageFilter.UnsharpMask(2, 70, 2)).convert("RGBA")
        ys = np.arange(bh)[:, None] / bh
        m = np.clip((1 - ys) / 0.40, 0, 1) ** 1.3 * np.clip(ys / 0.05, 0, 1) * np.ones((1, bw))
        im.putalpha(Image.fromarray((m * 255).astype(np.uint8)))
    else:
        im = src.convert("RGBA"); s = 1000 / im.height
        im = im.resize((int(im.width * s), 1000), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 80, 2))
        a = np.asarray(im.getchannel("A")).astype(np.float32) / 255
        a *= np.clip((1 - np.arange(im.height)[:, None] / im.height) / 0.22, 0, 1)
        im.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    _pc[p["img"]] = im
    return im

# mystery silhouette for #1 (cut-out DHONI.png if present, else a generic batter shape)
def silhouette():
    if "sil" in _pc: return _pc["sil"]
    path = os.path.join(D, "img", "DHONI.png")
    if os.path.exists(path):
        src = Image.open(path).convert("RGBA"); s = 860 / src.height
        src = src.resize((int(src.width * s), 860), Image.LANCZOS); a = src.getchannel("A")
        aa = np.asarray(a).astype(np.float32) * np.clip((1 - np.arange(a.height)[:, None] / a.height) / 0.06, 0, 1)
        a = Image.fromarray(aa.astype(np.uint8))
    else:
        a = Image.new("L", (620, 1050), 0); d = ImageDraw.Draw(a)
        d.ellipse((240, 60, 380, 210), fill=255)                                   # head + helmet
        d.rounded_rectangle((200, 200, 420, 560), 60, fill=255)                    # torso
        d.rounded_rectangle((215, 540, 305, 1000), 40, fill=255); d.rounded_rectangle((315, 540, 405, 1000), 40, fill=255)
        d.polygon([(390, 250), (560, 80), (590, 105), (420, 290)], fill=255)        # raised bat arm
        d.polygon([(540, 60), (600, 0), (620, 20), (565, 85)], fill=255)
        a = a.filter(ImageFilter.GaussianBlur(2))
    sil = Image.new("RGBA", a.size, (6, 6, 10, 255)); sil.putalpha(a)
    pad = 90; out = Image.new("RGBA", (a.width + pad * 2, a.height + pad * 2), (0, 0, 0, 0))
    rim = Image.new("RGBA", a.size, (255, 170, 30, 255)); rim.putalpha(a)
    rl = Image.new("RGBA", out.size, (0, 0, 0, 0)); rl.alpha_composite(rim, (pad, pad))
    out.alpha_composite(rl.filter(ImageFilter.GaussianBlur(26))); out.alpha_composite(rl.filter(ImageFilter.GaussianBlur(6)))
    out.alpha_composite(sil, (pad, pad))
    _pc["sil"] = out
    return out


def mosaic():
    if "mos" in _pc: return _pc["mos"]
    src = Image.open(os.path.join(D, "img", "DHONI_FULL.jpg")).convert("RGB")
    # portrait crop around the player
    cw = int(src.height * 0.78); x0 = max(0, min(src.width - cw, 330 - cw // 2))
    crop = src.crop((x0, 0, x0 + cw, src.height))
    bw, bh = 860, int(860 * crop.height / crop.width)
    small = crop.resize((14, int(14 * crop.height / crop.width)), Image.BILINEAR)
    big = small.resize((bw, bh), Image.NEAREST)
    big = ImageEnhance.Brightness(big).enhance(0.75)
    im = big.convert("RGBA")
    # thin grid lines between blocks for a clean "censored" look
    d = ImageDraw.Draw(im); step = bw / 14
    for i in range(1, 14): d.line((int(i * step), 0, int(i * step), bh), fill=(0, 0, 0, 60), width=2)
    for j in range(1, int(bh / step) + 1): d.line((0, int(j * step), bw, int(j * step)), fill=(0, 0, 0, 60), width=2)
    m = Image.new("L", (bw, bh), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, bw - 1, bh - 1), 40, fill=255)
    im.putalpha(m)
    out = Image.new("RGBA", (bw + 120, bh + 120), (0, 0, 0, 0))
    g = Image.new("RGBA", out.size, (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle((60, 60, 60 + bw, 60 + bh), 40, fill=(255, 170, 30, 200))
    out.alpha_composite(g.filter(ImageFilter.GaussianBlur(28)))
    out.alpha_composite(im, (60, 60))
    ImageDraw.Draw(out).rounded_rectangle((60, 60, 60 + bw, 60 + bh), 40, outline=(255, 196, 40, 255), width=5)
    _pc["mos"] = out
    return out

# ------------------------------------------------------------------ sections
def hook(img, t):
    if t >= T_P[0] + 0.25: return
    out = 1 - pr(t, T_P[0] - 0.15, 0.3)
    k1 = eo(pr(t, 0.0, 0.3)); k2 = eo(pr(t, 0.25, 0.3)); k3 = eo(pr(t, 0.55, 0.3))
    put(img, timg("MOST RUNS IN", F("anton", 120), WHITE), W / 2, 760, k1 * out, 1.4 - 0.4 * back(pr(t, 0.0, 0.3)))
    put(img, timg("DEATH OVERS", F("anton", 150), (0, 0, 0, 0), stroke=6, stroke_fill=GOLD, glow=(255, 140, 0, 130), shadow=False), W / 2, 920, k2 * out, 1.4 - 0.4 * back(pr(t, 0.25, 0.3)))
    put(img, timg("IPL HISTORY", F("mb", 66), WHITE, spacing=10), W / 2, 1075, k3 * out)
    put(img, timg(LABEL, F("mx", 26), MUTED, spacing=4, shadow=False), W / 2, 1150, k3 * out)

def player(img, t, p):
    if not (p["t0"] - 0.05 <= t < p["t1"] + 0.25): return
    out = 1 - pr(t, p["t1"] - 0.08, 0.25)
    c1 = p["c1"]; acc = p["c2"] if p["rank"] == 4 else c1          # CSK: navy number on yellow is hard -> keep yellow glow, number white
    kn = pr(t, p["t0"], 0.28)
    put(img, timg(str(p["rank"]), F("anton", 980), (*c1, 70), shadow=False), W / 2 + 230, 560, min(1, kn * 2) * out, 1 + 0.6 * (1 - eo(kn)))
    pim = player_img(p); kp = eo(pr(t, p["t0"] + 0.05, 0.35)); drift = (t - p["t0"]) * 10
    if p["kind"] == "photo": put(img, pim, W / 2, 80 + pim.height / 2 - 20 - drift, kp * out, 1.05 - 0.05 * kp)
    else: put(img, pim, W / 2, 1150 - pim.height / 2 - drift, kp * out, 1.05 - 0.05 * kp)
    put(img, rrect(220, 70, 35, (*[int(v) for v in c1], 255)), W / 2, 185, min(1, kn * 2) * out, back(kn))
    put(img, timg(f"NO. {p['rank']}", F("mb", 36), (20, 20, 30) if p["rank"] == 4 else WHITE, spacing=4, shadow=False), W / 2, 185, min(1, kn * 2) * out, back(kn))
    kname = eo(pr(t, p["t0"] + 0.15, 0.35))
    put(img, timg(p["name"], F("anton", 104 if len(p["name"]) < 15 else 92), WHITE), W / 2, 1210 + (1 - kname) * 40, kname * out)
    put(img, timg(p["team"], F("mx", 28), tuple(int(v) for v in (c1 if p["rank"] != 4 else (250, 200, 20))), spacing=4), W / 2, 1295, kname * out)
    kc = eo(pr(t, p["t0"] + 0.3, 0.35))
    if kc > 0:
        card = rrect(560, 250, 30, (12, 14, 28, 220), (*[int(v) for v in c1], 255), 4)
        put(img, card, W / 2, 1530 + (1 - kc) * 60, kc * out)
        v = int(round(p["runs"] * eo(pr(t, p["t0"] + 0.35, 0.9))))
        put(img, timg(f"{v:,}", F("anton", 140), WHITE), W / 2, 1550 + (1 - kc) * 60, kc * out)
        put(img, timg("DEATH-OVERS RUNS", F("mx", 24), MUTED, spacing=4, shadow=False), W / 2, 1450 + (1 - kc) * 60, kc * out)

def number_one(img, t):
    if t < T_ONE - 0.05: return
    k = eo(pr(t, T_ONE, 0.4))
    put(img, timg("1", F("anton", 980), (255, 196, 40, 60), shadow=False), W / 2 + 230, 560, k, 1 + 0.6 * (1 - k))
    mo = mosaic(); pulse = 1 + 0.01 * math.sin(t * 8)
    put(img, mo, W / 2, 650, eo(pr(t, T_ONE + 0.05, 0.5)), (1.06 - 0.06 * eo(pr(t, T_ONE, 0.6))) * pulse * 0.86)
    put(img, rrect(220, 70, 35, (255, 196, 40, 255)), W / 2, 185, k, back(pr(t, T_ONE, 0.35)))
    put(img, timg("NO. 1", F("mb", 36), (25, 15, 0), spacing=4, shadow=False), W / 2, 185, k, back(pr(t, T_ONE, 0.35)))
    kq = pr(t, T_ONE + 0.5, 0.35)
    put(img, timg("?", F("anton", 420), GOLD, glow=(0, 0, 0, 230)), W / 2, 660, kq, (0.6 + 0.4 * back(kq)) * (1 + 0.04 * math.sin(t * 6)))
    kg = eo(pr(t, T_ONE + 0.9, 0.4))
    put(img, timg("GUESS WHO?", F("anton", 130), WHITE), W / 2, 1230 + (1 - kg) * 40, kg)
    kc = eo(pr(t, T_ONE + 1.2, 0.35))
    if kc > 0:
        put(img, rrect(560, 250, 30, (12, 14, 28, 220), (255, 196, 40, 255), 4), W / 2, 1530 + (1 - kc) * 60, kc)
        put(img, timg("DEATH-OVERS RUNS", F("mx", 24), MUTED, spacing=4, shadow=False), W / 2, 1450 + (1 - kc) * 60, kc)
        sc = "".join(random.Random(int(t * 12)).choice("0123456789") for _ in range(4)) if t < T_PIN - 0.8 else "????"
        put(img, timg(sc if t < T_PIN - 0.8 else "?,???", F("anton", 140), GOLD), W / 2, 1550 + (1 - kc) * 60, kc)
    # pinned comment card
    kp = eo(pr(t, T_PIN, 0.35))
    if kp > 0:
        dim = Image.new("RGBA", (W, H), (0, 0, 0, int(150 * kp))); img.alpha_composite(dim)
        card = rrect(880, 300, 40, (255, 255, 255, 245)); y = 960 + (1 - kp) * 80
        put(img, card, W / 2, y, kp, 0.9 + 0.1 * back(pr(t, T_PIN, 0.35)))
        # pin icon
        pin = Image.new("RGBA", (120, 120), (0, 0, 0, 0)); pd = ImageDraw.Draw(pin)
        pd.ellipse((30, 8, 90, 68), fill=(230, 40, 40, 255)); pd.polygon([(50, 60), (70, 60), (60, 112)], fill=(120, 120, 130, 255))
        put(img, pin, W / 2, y - 80, kp, 0.9 + 0.1 * back(pr(t, T_PIN, 0.35)))
        put(img, timg("ANSWER IN THE", F("mb", 46), (20, 20, 30), spacing=3, shadow=False), W / 2, y + 10, kp)
        put(img, timg("PINNED COMMENT", F("anton", 80), (230, 40, 40), shadow=False), W / 2, y + 80, kp)

CUTS = T_P + [T_ONE]
def wipe(img, t):
    for c in CUTS:
        dt = t - c
        if -0.15 <= dt < 0.15:
            k = (dt + 0.15) / 0.3; col = cols(c + 0.3)[0]
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); x = -900 + k * (W + 1800)
            d.polygon([(x - 300, 0), (x + 300, 0), (x - 100, H), (x - 700, H)], fill=(*[int(v) for v in col], 235))
            d.polygon([(x + 330, 0), (x + 380, 0), (x - 20, H), (x - 70, H)], fill=(255, 255, 255, 200))
            img.alpha_composite(lay)
def flash(img, t):
    for tt, s in [(T_ONE + 0.5, 170)] + [(c + 0.05, 90) for c in T_P]:
        dt = t - tt
        if 0 <= dt < 0.18: img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(s * (1 - dt / 0.18)))))

def frame(t):
    img = background(t); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hook(lay, t)
    for p in P: player(lay, t, p)
    number_one(lay, t)
    dx = dy = 0
    for tt, amp in [(c, 10) for c in T_P] + [(T_ONE + 0.5, 18)]:
        d_ = t - tt
        if 0 <= d_ < 0.25: dx = math.sin(d_ * 90) * amp * (1 - d_ / 0.25); dy = math.cos(d_ * 70) * amp * (1 - d_ / 0.25)
    img.alpha_composite(lay, (int(dx), int(dy)))
    flash(img, t); wipe(img, t)
    out = img.convert("RGB")
    f = min(1, (DUR - t) / 0.3)
    if f < 1: out = Image.eval(out, lambda v: int(v * max(0, f)))
    return out

if PREVIEW:
    os.makedirs(os.path.join(D, "prev"), exist_ok=True)
    for t in PREVIEW: frame(t).save(os.path.join(D, "prev", f"p_{t:05.2f}.jpg"), quality=88)
    sys.exit()
n = int(DUR * FPS)
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
for i in range(n): ff.stdin.write(frame(i / FPS).tobytes())
ff.stdin.close(); ff.wait(); print("done")
