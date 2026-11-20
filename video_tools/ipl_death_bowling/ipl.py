"""IPL 2026 death-overs bowling top-5 reel. 1080x1920 @30fps. Pillow frames -> ffmpeg."""
import json, math, random, subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

D = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(D, "..", "fonts")
OUT = sys.argv[1]
PREVIEW = [float(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else None
W, H, FPS, DUR = 1080, 1920, 30, 55.33
font = lambda n, s: ImageFont.truetype(os.path.join(FONTS, n), s)
ANTON = lambda s: font("Anton.ttf", s)
MB = lambda s: font("Montserrat-Black.ttf", s)
MX = lambda s: font("Montserrat-ExtraBold.ttf", s)
MS = lambda s: font("Montserrat-SemiBold.ttf", s)
WHITE = (255, 255, 255); GOLD = (255, 196, 40)
timing = json.load(open(os.path.join(D, "timing.json")))

def wt(phrase_idx, word):
    for w in timing[phrase_idx]["words"]:
        if word.lower() in w["w"].lower(): return w["s"]
    raise KeyError(word)

TEAMS = {
 "RR":  dict(name="RAJASTHAN ROYALS", short="RR", c1=(234, 26, 133), c2=(60, 100, 220), eco=9.95, wk=26),
 "DC":  dict(name="DELHI CAPITALS", short="DC", c1=(30, 90, 200), c2=(239, 27, 35), eco=9.91, wk=24),
 "RCB": dict(name="ROYAL CHALLENGERS\nBENGALURU", short="RCB", c1=(213, 32, 39), c2=(212, 175, 55), eco=9.70, wk=34),
 "KKR": dict(name="KOLKATA KNIGHT RIDERS", short="KKR", c1=(120, 70, 200), c2=(212, 175, 55), eco=9.53, wk=34),
 "SRH": dict(name="SUNRISERS HYDERABAD", short="SRH", c1=(242, 101, 34), c2=(255, 200, 0), eco=9.49, wk=32),
}
LOGO = {k: Image.open(os.path.join(D, "logos", k + ".png")).convert("RGBA") for k in TEAMS}

# rank sections: (team, rank, t_number, t_name, t_eco, t_wk, t_end)
RANKS = [("RR", 5, 9.41, 10.46, 11.84, 13.67, 15.20),
         ("DC", 4, 15.20, 16.09, 17.34, 19.04, 20.40),
         ("RCB", 3, 20.40, 21.29, 23.04, 24.93, 26.31),
         ("KKR", 2, 26.31, 27.24, 28.69, 30.45, 31.73),
         ("SRH", 1, 31.73, 33.76, 35.53, 37.63, 38.90)]
T_BOARD, T_POLL, T_FOLLOW = 38.90, 45.40, 51.45

# ------------------------------------------------------------------ easing
clamp = lambda x, a=0.0, b=1.0: max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in_out(x): x = clamp(x); return x * x * (3 - 2 * x)
def back(x):
    x = clamp(x); c1 = 1.9; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def prog(t, s, d): return clamp((t - s) / d)

# ------------------------------------------------------------------ background
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
BASE = np.zeros((H, W, 3), np.float32)
BASE[...] = np.array([8, 10, 22], np.float32)
BASE += (yy / H)[..., None] * np.array([6, 6, 14], np.float32)
def radial(cx, cy, rx, ry):
    return np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)).astype(np.float32)
GLOW_TOP = radial(W * 0.5, H * 0.33, 700, 760)[..., None]
GLOW_BOT = radial(W * 0.5, H * 1.05, 900, 500)[..., None]
VIG = np.clip(1 - 0.55 * (((xx - W / 2) / (W * 0.8)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2), 0.35, 1)[..., None]
# grid + diagonal stripes overlay (static texture)
tex = Image.new("L", (W, H), 0); td = ImageDraw.Draw(tex)
for x in range(0, W, 60): td.line((x, 0, x, H), fill=14)
for y in range(0, H, 60): td.line((0, y, W, y), fill=14)
TEX = np.asarray(tex, np.float32)[..., None] / 255.0
rng = np.random.default_rng(1)
NOISE = (rng.normal(0, 3.0, (H // 2, W // 2)).astype(np.float32))
NOISE = np.asarray(Image.fromarray(NOISE).resize((W, H)), np.float32)[..., None]

def team_at(t):
    if t < RANKS[0][2]: return None
    for r in RANKS:
        if r[2] <= t < r[6]: return r[0]
    if t < T_POLL: return "SRH"
    return None

def mix(a, b, k): return tuple(a[i] * (1 - k) + b[i] * k for i in range(3))
NEUTRAL1, NEUTRAL2 = (255, 120, 30), (40, 90, 255)
def colors_at(t):
    """smoothly blended accent colours"""
    def raw(tt):
        k = team_at(tt)
        if k is None: return NEUTRAL1, NEUTRAL2
        return TEAMS[k]["c1"], TEAMS[k]["c2"]
    a1, a2 = raw(t); b1, b2 = raw(t - 0.35)
    # blend across changes over 0.35s
    if (a1, a2) == (b1, b2): return a1, a2
    for back_t in np.linspace(0, 0.35, 15):
        if raw(t - back_t) != (a1, a2):
            k = back_t / 0.35; return mix(b1, a1, k), mix(b2, a2, k)
    return a1, a2

def background(t):
    c1, c2 = colors_at(t)
    pulse = 0.85 + 0.15 * math.sin(t * 2 * math.pi * 0.5)
    a = BASE + GLOW_TOP * (np.array(c1, np.float32) * 0.42 * pulse) + GLOW_BOT * (np.array(c2, np.float32) * 0.30)
    a = a + TEX * 60 * 0.6 + NOISE
    a *= VIG
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    # moving light streaks
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(5):
        off = ((t * 140 + i * 520) % 2600) - 700
        d.polygon([(off, 0), (off + 90, 0), (off - 900, H), (off - 990, H)], fill=(*[int(v) for v in c1], 16))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(24)))
    return img

# ------------------------------------------------------------------ text helpers
_tc = {}
def text_img(txt, fnt, fill=WHITE, stroke=0, stroke_fill=(0, 0, 0), glow=None, shadow=True, key=None):
    k = key or (txt, id(fnt), fill, stroke, stroke_fill, glow, shadow)
    if k in _tc: return _tc[k]
    bb = fnt.getbbox(txt, stroke_width=stroke); pad = 50
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); org = (pad - bb[0], pad - bb[1])
    if glow:
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g).text(org, txt, font=fnt, fill=glow, stroke_width=stroke + 8, stroke_fill=glow)
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(20)))
    if shadow:
        s = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(s).text((org[0], org[1] + 8), txt, font=fnt, fill=(0, 0, 0, 160), stroke_width=stroke, stroke_fill=(0, 0, 0, 160))
        im.alpha_composite(s.filter(ImageFilter.GaussianBlur(9)))
    ImageDraw.Draw(im).text(org, txt, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    _tc[k] = im
    return im

FONT_CACHE = {}
def F(kind, s):
    k = (kind, s)
    if k not in FONT_CACHE: FONT_CACHE[k] = {"anton": ANTON, "mb": MB, "mx": MX, "ms": MS}[kind](s)
    return FONT_CACHE[k]

def put(img, im, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.01 or scale <= 0.01: return
    if abs(scale - 1) > 0.003:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if rot: im = im.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 0.999:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def text(img, txt, kind, size, cx, cy, fill=WHITE, scale=1, alpha=1, stroke=0, stroke_fill=(0, 0, 0), glow=None, rot=0):
    put(img, text_img(txt, F(kind, size), tuple(int(v) for v in fill), stroke, stroke_fill, glow), cx, cy, scale, alpha, rot)

def rrect(size, r, fill, outline=None, width=0):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), r, fill=fill, outline=outline, width=width)
    return im

_lc = {}
def logo_img(k, h, glow_col=None):
    key = (k, h, glow_col)
    if key in _lc: return _lc[key]
    lg = LOGO[k]; s = h / max(lg.height, lg.width * 0.95)
    lg = lg.resize((int(lg.width * s), int(lg.height * s)), Image.LANCZOS)
    pad = 80; im = Image.new("RGBA", (lg.width + pad * 2, lg.height + pad * 2), (0, 0, 0, 0))
    if glow_col:
        a = lg.getchannel("A"); g = Image.new("RGBA", lg.size, (*glow_col, 0)); g.putalpha(a.point(lambda v: int(v * 0.85)))
        gl = Image.new("RGBA", im.size, (0, 0, 0, 0)); gl.alpha_composite(g, (pad, pad))
        im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(28)))
    sh = Image.new("RGBA", lg.size, (0, 0, 0, 0)); sh.putalpha(lg.getchannel("A").point(lambda v: int(v * 0.5)))
    sl = Image.new("RGBA", im.size, (0, 0, 0, 0)); sl.alpha_composite(sh, (pad, pad + 14))
    im.alpha_composite(sl.filter(ImageFilter.GaussianBlur(12)))
    im.alpha_composite(lg, (pad, pad))
    _lc[key] = im
    return im

_mb = {}
def mystery_badge(n):
    if n in _mb: return _mb[n]
    w, h = 170, 200
    im = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    poly = [(30, 30), (30 + w, 30), (30 + w, 30 + h * 0.62), (30 + w / 2, 30 + h), (30, 30 + h * 0.62)]
    sd.polygon(poly, fill=(255, 140, 20, 140)); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(im)
    d.polygon(poly, fill=(18, 20, 40, 255), outline=(255, 196, 40, 255), width=4)
    q = text_img("?", ANTON(120), WHITE, shadow=False)
    im.alpha_composite(q, (int(30 + w / 2 - q.width / 2), int(30 + h * 0.43 - q.height / 2)))
    nb = text_img(f"#{n}", MB(30), GOLD, shadow=False)
    im.alpha_composite(nb, (int(30 + w / 2 - nb.width / 2), int(30 + h * 0.80 - nb.height / 2)))
    _mb[n] = im
    return im

# ------------------------------------------------------------------ particles
random.seed(4)
SPARKS = [dict(x=random.uniform(0, W), y=random.uniform(0, H), v=random.uniform(20, 70), r=random.uniform(1.2, 3.2), ph=random.uniform(0, 6.3)) for _ in range(55)]
def sparks(img, t, col):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for s in SPARKS:
        y = (s["y"] - s["v"] * t) % H; x = s["x"] + math.sin(t + s["ph"]) * 20
        a = int(90 + 70 * math.sin(t * 2.5 + s["ph"])); r = s["r"]
        d.ellipse((x - r, y - r, x + r, y + r), fill=(*[int(v) for v in col], a))
    img.alpha_composite(lay)

CONF = [dict(x=random.uniform(-100, W + 100), vx=random.uniform(-160, 160), vy=random.uniform(-1500, -700), rot=random.uniform(0, 360),
             vr=random.uniform(-400, 400), c=random.choice([(242, 101, 34), (255, 200, 0), (255, 255, 255), (255, 140, 0)]),
             w=random.uniform(12, 24), h=random.uniform(6, 12)) for _ in range(150)]
def confetti(img, dt):
    if dt < 0 or dt > 4.0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for c in CONF:
        x = c["x"] + c["vx"] * dt; y = H + 40 + c["vy"] * dt + 900 * dt * dt
        if y > H + 60 or y < -60: continue
        p = Image.new("RGBA", (int(c["w"]), int(c["h"])), (*c["c"], 235)).rotate(c["rot"] + c["vr"] * dt, expand=True)
        lay.alpha_composite(p, (int(x), int(y)))
    al = clamp((4.0 - dt) / 0.8)
    if al < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * al)))
    img.alpha_composite(lay)

# ------------------------------------------------------------------ captions
CAP_Y = 1665
CF = MB(54)
_wc = {}
def word_img(w, col):
    k = (w, col)
    if k not in _wc: _wc[k] = text_img(w.upper(), CF, col, stroke=6, stroke_fill=(0, 0, 0), shadow=True, key=("cap",) + k)
    return _wc[k]
PAGES = []
for seg in timing:
    cur = []
    for w in seg["words"]:
        cur.append(w)
        if len(cur) >= 4 or sum(len(x["w"]) for x in cur) > 18 or w["w"][-1] in ".,!?":
            PAGES.append(cur); cur = []
    if cur: PAGES.append(cur)
PAGES = [dict(words=p, s=p[0]["s"], e=p[-1]["e"]) for p in PAGES]
for i, p in enumerate(PAGES):
    p["e2"] = min(PAGES[i + 1]["s"] if i + 1 < len(PAGES) else DUR, p["e"] + 0.5)

def captions(img, t, hl):
    for p in PAGES:
        if p["s"] - 0.05 <= t < p["e2"]:
            ims = []
            for w in p["words"]:
                active = w["s"] <= t < w["e"] + 0.02
                spoken = t >= w["s"]
                ims.append((w, word_img(w["w"], hl if active else WHITE), spoken, active))
            # line wrap
            lines = [[]]; lw = 0
            for it in ims:
                ww = it[1].width - 100
                if lines[-1] and lw + ww + 18 > 940: lines.append([]); lw = 0
                lines[-1].append(it); lw += ww + 18
            y0 = CAP_Y - (len(lines) - 1) * 40
            for li, ln in enumerate(lines):
                tot = sum(it[1].width - 100 for it in ln) + 18 * (len(ln) - 1); x = W / 2 - tot / 2
                for w, im, spoken, active in ln:
                    ww = im.width - 100
                    k = prog(t, w["s"] - 0.04, 0.14)
                    sc = (0.9 + 0.1 * back(k)) * (1.07 if active else 1)
                    put(img, im, x + ww / 2, y0 + li * 80, sc if spoken else 0.9, 1.0 if spoken else 0.45 * prog(t, p["s"] - 0.05, 0.12))
                    x += ww + 18
            return

# ------------------------------------------------------------------ header / chrome
HDR = Image.new("RGBA", (W, 190), (0, 0, 0, 0)); hd = ImageDraw.Draw(HDR)
hd.rectangle((56, 86, 64, 140), fill=(230, 40, 40))
hd.text((80, 82), "IPL 2026", font=MB(30), fill=WHITE)
hd.text((80, 116), "DEATH OVERS • BOWLING", font=MS(22), fill=(200, 200, 215))

def chrome(img, t, col):
    img.alpha_composite(HDR)
    d = ImageDraw.Draw(img)
    d.rectangle((0, H - 12, W, H), fill=(255, 255, 255, 30))
    d.rectangle((0, H - 12, int(W * t / DUR), H), fill=tuple(int(v) for v in col) + (255,))

# ------------------------------------------------------------------ sections
def intro(img, t):
    if t >= RANKS[0][2] + 0.3: return
    out = 1 - prog(t, RANKS[0][2] - 0.15, 0.35)
    # badge
    k = prog(t, 0.1, 0.35)
    badge = rrect((300, 74), 37, (230, 40, 40, 255))
    put(img, badge, W / 2, 420, back(k), k * out)
    text(img, "IPL 2026", "mb", 40, W / 2, 420, scale=back(k), alpha=k * out, shadow=False) if False else None
    put(img, text_img("IPL 2026", MB(40), WHITE, shadow=False), W / 2, 420, back(k), k * out)
    k1 = ease_out(prog(t, 0.35, 0.45)); k2 = ease_out(prog(t, 0.6, 0.45))
    text(img, "DEATH", "anton", 270, W / 2 - (1 - k1) * 900, 620, alpha=k1 * out)
    put(img, text_img("OVERS", ANTON(270), (0, 0, 0, 0), stroke=6, stroke_fill=GOLD, glow=(255, 140, 0, 120), shadow=False),
        W / 2 + (1 - k2) * 900, 880, 1, k2 * out)
    # sub title + underline wipe
    k3 = ease_out(prog(t, 2.39, 0.4))
    text(img, "TOP 5 BOWLING TEAMS", "mb", 74, W / 2, 1090 + (1 - k3) * 40, alpha=k3 * out)
    if k3 > 0:
        d = ImageDraw.Draw(img); ww = int(600 * ease_out(prog(t, 2.6, 0.5)))
        d.rounded_rectangle((W / 2 - ww / 2, 1150, W / 2 + ww / 2, 1160), 5, fill=(255, 196, 40, int(255 * out)))
    # mystery badges (no team revealed yet)
    for i in range(5):
        kk = prog(t, 3.3 + i * 0.22, 0.4)
        cx = 120 + i * 210; cy = 1300 + math.sin(t * 3 + i) * 6
        put(img, mystery_badge(5 - i), cx, cy, back(kk), kk * out)
    # chips
    for i, (lab, tt) in enumerate([("ECONOMY", wt(2, "Economy")), ("WICKETS", wt(2, "wickets"))]):
        kk = prog(t, tt, 0.35); cx = W / 2 + (-210 if i == 0 else 210)
        chip = rrect((370, 92), 46, (255, 255, 255, 235))
        put(img, chip, cx, 1475, back(kk), kk * out)
        put(img, text_img(lab, MB(40), (15, 15, 30), shadow=False), cx, 1475, back(kk), kk * out)

def rank_section(img, t, r):
    k, rank, tn, tname, teco, twk, tend = r
    tm = TEAMS[k]; c1, c2 = tm["c1"], tm["c2"]
    if not (tn - 0.05 <= t < tend + 0.3): return
    out = 1 - prog(t, tend - 0.12, 0.3)
    sl = (1 - out) * -260  # slide up on exit
    is1 = rank == 1
    tnum = tn if not is1 else wt(19, "Number")
    # "AND FINALLY..." for #1
    if is1 and t < tname:
        kf = prog(t, tn, 0.4); fade = 1 - prog(t, tnum - 0.1, 0.25)
        shake = math.sin(t * 60) * 4 * kf
        text(img, "AND FINALLY...", "anton", 120, W / 2 + shake, 700, alpha=kf * fade, glow=(255, 160, 0, 90))
    # rank number
    kn = prog(t, tnum, 0.32)
    if kn > 0:
        slam = 1 + 1.4 * (1 - ease_out(kn))
        if is1:
            col = GOLD
            num_y = 470 if t >= tname else 760
            if t >= tname:
                kk = ease_in_out(prog(t, tname, 0.4)); num_y = 760 + (470 - 760) * kk
                sc_ = 1 - 0.45 * kk
            else:
                sc_ = 1
            text(img, "#1", "anton", 520, W / 2, num_y + sl, fill=GOLD, scale=slam * sc_, alpha=min(1, kn * 2) * out, glow=(255, 150, 0, 170))
        else:
            text(img, "NO.", "mb", 54, 330, 330 + sl, alpha=min(1, kn * 2) * out)
            put(img, text_img(str(rank), ANTON(330), (0, 0, 0, 0), stroke=7, stroke_fill=c1, glow=(*c1, 150), shadow=False),
                W / 2 + 40, 375 + sl, slam, min(1, kn * 2) * out)
    # logo
    kl = prog(t, tname, 0.45)
    if kl > 0:
        float_y = math.sin(t * 2.2) * 8
        lh = 430 if not is1 else 520
        ly = 880 if not is1 else 900
        put(img, logo_img(k, lh, c1), W / 2, ly + float_y + sl, 0.3 + 0.7 * back(kl), min(1, kl * 2) * out)
        # team name
        kname = ease_out(prog(t, tname + 0.1, 0.4))
        lines = tm["name"].split("\n")
        ny = 1180 if not is1 else 1215
        for li, ln in enumerate(lines):
            text(img, ln, "anton", 92 if len(lines) == 1 else 80, W / 2, ny + li * 90 - (len(lines) - 1) * 45 + sl + (1 - kname) * 40,
                 alpha=kname * out)
    # stat cards
    for i, (lab, val, ts, fmt) in enumerate([("ECONOMY", tm["eco"], teco, "{:.2f}"), ("WICKETS", tm["wk"], twk, "{:d}")]):
        kc = prog(t, ts - 0.05, 0.35)
        if kc <= 0: continue
        cx = W / 2 + (-235 if i == 0 else 235); cy = 1430 + sl + (1 - ease_out(kc)) * 80
        card = Image.new("RGBA", (440, 240), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((0, 0, 439, 239), 28, fill=(12, 14, 30, 215), outline=(*c1, 255), width=4)
        cd.rounded_rectangle((0, 0, 439, 16), 8, fill=(*c1, 255))
        put(img, card, cx, cy, 1, min(1, kc * 1.5) * out)
        cnt = ease_out(prog(t, ts, 0.7))
        v = val * cnt if isinstance(val, float) else int(round(val * cnt))
        if isinstance(val, float):
            # count from 0 is silly for economy: count down from 12.00 to value (lower = better)
            v = 12.0 + (val - 12.0) * cnt
        s = fmt.format(v)
        put(img, text_img(s, ANTON(140), WHITE if not is1 else GOLD, shadow=True, key=("num", s, is1)), cx, cy + 22, 1, min(1, kc * 1.5) * out)
        put(img, text_img(lab, MX(32), (200, 200, 220), shadow=False), cx, cy - 72, 1, min(1, kc * 1.5) * out)
        if is1 and i == 0:
            kj = prog(t, ts, 0.3)
            put(img, rrect((150, 54), 27, (255, 196, 40, 255)), cx - 120, cy - 135, back(kj), kj * out)
            put(img, text_img("JUST", MB(30), (20, 15, 0), shadow=False), cx - 120, cy - 135, back(kj), kj * out)
    if is1:
        confetti(img, t - tname)

def board(img, t):
    if not (T_BOARD - 0.1 <= t < T_POLL + 0.3): return
    out = 1 - prog(t, T_POLL - 0.1, 0.3)
    k0 = ease_out(prog(t, T_BOARD, 0.4))
    text(img, "YES!", "anton", 150, W / 2, 360 + (1 - k0) * -60, fill=GOLD, alpha=k0 * out * (1 - prog(t, 39.9, 0.3)), glow=(255, 150, 0, 140))
    kt = ease_out(prog(t, 39.6, 0.4))
    text(img, "DEATH OVERS LEADERBOARD", "anton", 84, W / 2, 330, alpha=kt * out)
    text(img, "Economy (lower is better)  •  Wickets", "ms", 32, W / 2, 400, fill=(190, 190, 210), alpha=kt * out, )
    order = ["SRH", "KKR", "RCB", "DC", "RR"]
    x0, x1 = 400, 860
    lo, hi = 9.0, 10.0
    for i, k in enumerate(order):
        tm = TEAMS[k]; ts = 39.8 + (4 - i) * 0.25   # rank 5 enters first
        kr = ease_out(prog(t, ts, 0.45))
        if kr <= 0: continue
        y = 560 + i * 205; xoff = (1 - kr) * 700
        hl = k == "SRH"
        row = Image.new("RGBA", (980, 178), (0, 0, 0, 0)); rd = ImageDraw.Draw(row)
        rd.rounded_rectangle((0, 0, 979, 177), 30, fill=(255, 255, 255, 26) if not hl else (255, 160, 30, 60),
                             outline=(255, 196, 40, 255) if hl else (255, 255, 255, 40), width=5 if hl else 2)
        put(img, row, W / 2 + xoff, y, 1, kr * out)
        text(img, str(i + 1), "anton", 90, 105 + xoff, y, fill=GOLD if hl else WHITE, alpha=kr * out)
        put(img, logo_img(k, 125), 225 + xoff, y, 1, kr * out)
        # bar
        kb = ease_out(prog(t, ts + 0.25, 0.7))
        full = (tm["eco"] - lo) / (hi - lo)
        bw = int((x1 - x0) * full * kb)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((x0 + xoff, y - 52, x0 + xoff + (x1 - x0), y - 8), 22, fill=(255, 255, 255, int(28 * kr * out)))
        if bw > 10:
            d.rounded_rectangle((x0 + xoff, y - 52, x0 + xoff + bw, y - 8), 22, fill=(*tm["c1"], int(255 * kr * out)))
        text(img, f"{tm['eco']:.2f}", "anton", 64, 960 + xoff, y - 30, fill=GOLD if hl else WHITE, alpha=kb * out)
        text(img, f"{tm['wk']} WICKETS", "mx", 34, x0 + 120 + xoff, y + 40, fill=(210, 210, 225), alpha=kb * out)
        text(img, tm["short"], "mb", 34, 320 + xoff, y + 40, fill=(170, 170, 190), alpha=kb * out) if False else None
    # axis note
    text(img, "Bar scale starts at 9.00 economy", "ms", 24, W / 2, 1585 - 110, fill=(150, 150, 170), alpha=ease_out(prog(t, 41.2, 0.4)) * out)
    # tag
    te = wt(24, "economical")
    kt2 = prog(t, te - 0.2, 0.35)
    if kt2 > 0:
        tag = rrect((420, 64), 32, (255, 196, 40, 255))
        put(img, tag, W / 2 + 230, 560 - 105, back(kt2), kt2 * out, -3)
        put(img, text_img("MOST ECONOMICAL", MB(32), (25, 15, 0), shadow=False), W / 2 + 230, 560 - 105, back(kt2), kt2 * out, -3)

def poll(img, t):
    if not (T_POLL - 0.1 <= t < T_FOLLOW + 0.3): return
    out = 1 - prog(t, T_FOLLOW - 0.1, 0.3)
    k0 = ease_out(prog(t, T_POLL, 0.4))
    text(img, "MEE FAVOURITE", "anton", 120, W / 2, 420 + (1 - k0) * 50, alpha=k0 * out)
    text(img, "DEATH-OVER BOWLING TEAM EDI?", "mb", 48, W / 2, 530 + (1 - k0) * 50, fill=GOLD, alpha=k0 * out)
    for i, (k, ts) in enumerate([("SRH", 47.88), ("KKR", 48.81), ("RCB", 49.70)]):
        kk = prog(t, ts - 0.05, 0.35)
        if kk <= 0: continue
        y = 760 + i * 250
        card = Image.new("RGBA", (860, 210), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
        active = ts <= t < ts + 0.75
        cd.rounded_rectangle((0, 0, 859, 209), 105, fill=(255, 255, 255, 30), outline=(*TEAMS[k]["c1"], 255), width=6 if active else 3)
        put(img, card, W / 2, y, back(kk) * (1.04 if active else 1), kk * out)
        put(img, logo_img(k, 170, TEAMS[k]["c1"] if active else None), W / 2 - 300, y, back(kk), kk * out)
        text(img, f"{TEAMS[k]['short']} aa?", "anton", 110, W / 2 + 90, y, alpha=kk * out)
    # comment cta
    kc = prog(t, 50.6, 0.35)
    if kc > 0:
        cy = 1490; bob = math.sin(t * 7) * 6
        bub = Image.new("RGBA", (760, 170), (0, 0, 0, 0)); bd = ImageDraw.Draw(bub)
        bd.rounded_rectangle((0, 0, 759, 140), 70, fill=(255, 255, 255, 250))
        bd.polygon([(120, 130), (190, 130), (110, 169)], fill=(255, 255, 255, 250))
        put(img, bub, W / 2, cy + bob, back(kc), kc * out)
        put(img, text_img("COMMENT CHEYYANDI!", MB(50), (230, 40, 40), shadow=False), W / 2, cy - 14 + bob, back(kc), kc * out)

def follow(img, t):
    if t < T_FOLLOW - 0.1: return
    k0 = prog(t, T_FOLLOW, 0.4)
    pulse = 1 + 0.04 * math.sin(t * 6)
    btn = rrect((560, 150), 75, (230, 40, 40, 255))
    put(img, btn, W / 2, 760, back(k0) * pulse, k0)
    put(img, text_img("+  FOLLOW", ANTON(92), WHITE, shadow=False), W / 2, 755, back(k0) * pulse, k0)
    k1 = ease_out(prog(t, T_FOLLOW + 0.4, 0.4))
    text(img, "for more exciting", "ms", 44, W / 2, 920 + (1 - k1) * 40, fill=(210, 210, 225), alpha=k1)
    text(img, "IPL STATISTICS", "anton", 120, W / 2, 1030 + (1 - k1) * 40, alpha=k1)
    text(img, "& CRICKET ANALYSIS", "anton", 90, W / 2, 1150 + (1 - k1) * 40, fill=GOLD, alpha=k1)
    for i, k in enumerate(["RR", "DC", "RCB", "KKR", "SRH"]):
        kk = prog(t, T_FOLLOW + 0.8 + i * 0.12, 0.35)
        put(img, logo_img(k, 120), 140 + i * 200, 1340 + math.sin(t * 3 + i) * 8, back(kk), kk)

# ------------------------------------------------------------------ transitions
CUTS = [r[2] for r in RANKS] + [T_BOARD, T_POLL, T_FOLLOW]
def wipe(img, t):
    for c in CUTS:
        dt = t - c
        if -0.18 <= dt < 0.18:
            k = (dt + 0.18) / 0.36
            col = colors_at(c + 0.4)[0]
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            x = -900 + k * (W + 1800)
            d.polygon([(x - 300, 0), (x + 300, 0), (x - 100, H), (x - 700, H)], fill=(*[int(v) for v in col], 230))
            d.polygon([(x + 330, 0), (x + 380, 0), (x - 20, H), (x - 70, H)], fill=(255, 255, 255, 200))
            img.alpha_composite(lay)

def flash(img, t):
    for tt, strength in [(r[3], 120) for r in RANKS] + [(RANKS[4][3], 220), (wt(19, "Number"), 140)]:
        dt = t - tt
        if 0 <= dt < 0.2:
            img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(strength * (1 - dt / 0.2)))))

def shake_offset(t):
    for tt, amp in [(r[2], 10) for r in RANKS[:4]] + [(wt(19, "Number"), 18), (RANKS[4][3], 22)]:
        dt = t - tt
        if 0 <= dt < 0.3: return math.sin(dt * 90) * amp * (1 - dt / 0.3), math.cos(dt * 70) * amp * (1 - dt / 0.3)
    return 0, 0

def frame(t):
    img = background(t)
    c1, c2 = colors_at(t)
    sparks(img, t, c2 if team_at(t) else (255, 200, 120))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    intro(layer, t)
    for r in RANKS: rank_section(layer, t, r)
    board(layer, t); poll(layer, t); follow(layer, t)
    dx, dy = shake_offset(t)
    img.alpha_composite(layer, (int(dx), int(dy))) if (dx or dy) else img.alpha_composite(layer)
    flash(img, t)
    hl = GOLD if team_at(t) in (None, "SRH", "KKR", "RCB") else tuple(int(v) for v in mix(c1, (255, 255, 255), 0.25))
    captions(img, t, hl)
    wipe(img, t)
    chrome(img, t, c1)
    fade = min(1, t / 0.3, (DUR - t) / 0.45)
    out = img.convert("RGB")
    if fade < 1: out = Image.eval(out, lambda v: int(v * max(0, fade)))
    return out

if PREVIEW:
    os.makedirs(os.path.join(D, "prev"), exist_ok=True)
    for t in PREVIEW: frame(t).save(os.path.join(D, "prev", f"p_{t:05.2f}.jpg"), quality=88)
    sys.exit()

n = int(DUR * FPS)
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
for f in range(n):
    ff.stdin.write(frame(f / FPS).tobytes())
    if f % 300 == 0: print("frame", f, "/", n, flush=True)
ff.stdin.close(); ff.wait(); print("done")
