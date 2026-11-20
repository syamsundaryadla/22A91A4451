"""Sandpapergate 2018-2026: documentary reel, 1080x1920 @30fps."""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

D = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(D, "..", "fonts")
OUT = sys.argv[1]
PREVIEW = [float(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else None
W, H, FPS, DUR = 1080, 1920, 30, 112.27
RED = (230, 57, 70); WHITE = (255, 255, 255); MUTED = (190, 192, 200); PAPER = (236, 226, 204)
_F = {}
def F(n, s):
    if (n, s) not in _F:
        _F[(n, s)] = ImageFont.truetype(os.path.join(FONTS, {"anton": "Anton.ttf", "mb": "Montserrat-Black.ttf", "mx": "Montserrat-ExtraBold.ttf", "ms": "Montserrat-SemiBold.ttf"}[n]), s)
    return _F[(n, s)]
clamp = lambda x, a=0.0, b=1.0: max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return x * x * (3 - 2 * x)
def pr(t, s, d): return clamp((t - s) / d)
def fade(t, a, b, d=0.35): return eo(pr(t, a, d)) * (1 - eio(pr(t, b - d, d)))

# ------------------------------------------------------------------ scenes (img, start, end, mode, opts)
S = [
 ("A1", 0.00, 10.23, "framed", dict(zoom=(1.0, 1.12), fy=0.42, sat=0.0)),
 ("A2", 10.23, 18.92, "fill", dict(focus=(0.5, 0.3), zoom=(1.04, 1.12), dark=0.15)),
 ("A3", 18.92, 25.49, "framed", dict(zoom=(1.0, 1.10), fy=0.42)),
 ("A4", 25.49, 27.35, "fill", dict(focus=(0.5, 0.35), zoom=(1.0, 1.06))),
 ("BALL", 27.35, 29.59, "rub", {}),
 ("A4", 29.59, 35.04, "fill", dict(focus=(0.5, 0.35), zoom=(1.06, 1.18))),
 ("A5", 35.04, 42.35, "fill", dict(focus=(0.5, 0.35), zoom=(1.0, 1.10), dark=0.2)),
 ("BAN21", 42.35, 47.07, "framed", dict(zoom=(1.0, 1.08), fy=0.42)),
 ("BOWLERS", 47.07, 55.16, "framed", dict(zoom=(1.0, 1.08), fy=0.42)),
 ("SABR", 55.16, 69.05, "framed", dict(zoom=(1.0, 1.10), fy=0.36)),
 ("CUMMINS", 69.05, 78.12, "fill", dict(focus=(0.5, 0.2), zoom=(1.0, 1.12), dark=0.1)),
 ("WARNER26", 78.12, 84.21, "framed", dict(zoom=(1.0, 1.10), fy=0.40)),
 ("BAN26", 84.21, 93.57, "framed", dict(zoom=(1.0, 1.12), fy=0.40)),
 ("WARNER", 93.57, 96.76, "framed", dict(zoom=(1.05, 1.12), fy=0.40, sat=0.0)),
 ("BAN26", 96.76, 100.39, "framed", dict(zoom=(1.12, 1.2), fy=0.40)),
 ("BALL", 100.39, 103.20, "swing", {}),
 ("BOWLERS", 103.20, 106.44, "framed", dict(zoom=(1.08, 1.0), fy=0.42, sat=0.0)),
 ("SMITH", 106.44, 112.27, "framed", dict(zoom=(1.0, 1.10), fy=0.40)),
]
SS = 1.12
def load(name):
    im = Image.open(os.path.join(D, "img", name + ".jpg")).convert("RGB")
    return ImageEnhance.Contrast(im).enhance(1.1)
def cover(im, w, h, fx=0.5, fy=0.5):
    s = max(w / im.width, h / im.height)
    im = im.resize((max(w, round(im.width * s)), max(h, round(im.height * s))), Image.LANCZOS)
    x = int((im.width - w) * fx); y = int((im.height - h) * fy)
    return im.crop((x, y, x + w, y + h))
def build(sc):
    name, s, e, mode, o = sc
    bw, bh = int(W * SS), int(H * SS)
    src = load(name)
    if mode == "fill":
        base = cover(src, bw, bh, *o.get("focus", (0.5, 0.5)))
    else:
        bg = cover(src, bw // 8, bh // 8).filter(ImageFilter.GaussianBlur(4)).resize((bw, bh), Image.BICUBIC)
        bg = ImageEnhance.Brightness(bg).enhance(0.32)
        fw = bw; fh = int(src.height * fw / src.width)
        fg = src.resize((fw, fh), Image.LANCZOS)
        y = int(bh * o.get("fy", 0.42) - fh / 2)
        m = Image.new("L", (fw, fh), 255); md = ImageDraw.Draw(m)
        for i in range(70):
            a = int(255 * i / 70); md.line((0, i, fw, i), fill=a); md.line((0, fh - 1 - i, fw, fh - 1 - i), fill=a)
        bg.paste(fg, (0, y), m); base = bg
    base = base.filter(ImageFilter.UnsharpMask(2, 60, 2))
    return base

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1 - 0.55 * (((xx - W / 2) / (W * 0.8)) ** 2 + ((yy - H / 2) / (H * 0.72)) ** 2), 0.25, 1)
GRAD = 1 - np.clip((yy / H - 0.55) / 0.45, 0, 1) ** 1.3 * 0.78 - np.clip((0.14 - yy / H) / 0.14, 0, 1) * 0.55
SHADE = (VIG * GRAD)[..., None].astype(np.float32)
rng = np.random.default_rng(8)
GRAIN = [np.asarray(Image.fromarray(rng.normal(0, 6, (H // 2, W // 2)).astype(np.float32)).resize((W, H), Image.BILINEAR))[..., None] for _ in range(6)]
TINT = np.array([1.02, 1.0, 0.96], np.float32)   # slightly warm, documentary

# ------------------------------------------------------------------ procedural cricket ball
BCX, BCY, BR = W / 2, 760, 300
_dx = (xx - BCX) / BR; _dy = (yy - BCY) / BR
_r2 = _dx ** 2 + _dy ** 2
BMASK = np.clip((1 - np.sqrt(_r2)) * BR / 1.5, 0, 1)[..., None]
_nz = np.sqrt(np.clip(1 - _r2, 0, 1))
_rng = np.random.default_rng(11)
_leather = np.asarray(Image.fromarray((_rng.normal(0, 1, (H // 2, W // 2)) * 40 + 128).clip(0, 255).astype(np.uint8)).resize((W, H)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 128 - 1
_scr = _rng.random((H // 2, W // 2)).astype(np.float32)
_scr = np.asarray(Image.fromarray((_scr * 255).astype(np.uint8)).resize((W, H)).filter(ImageFilter.BoxBlur(1)), np.float32) / 255
_scr = np.asarray(Image.fromarray((_scr * 255).astype(np.uint8)).resize((W // 6, H)).resize((W, H)), np.float32) / 255   # horizontal streaks
SCUFF_TEX = np.clip((_scr - 0.55) * 4, 0, 1)
def ball_frame(t, mode, t0, t1):
    p = clamp((t - t0) / (t1 - t0))
    tilt = math.radians(14)
    sx, sy = math.cos(tilt), math.sin(tilt)            # seam plane normal ~ x axis, tilted
    d_seam = _dx * sx + _dy * sy * 0.3                # signed distance to seam (in sphere units)
    side_left = d_seam < 0
    Lx, Ly, Lz = -0.45, -0.55, 0.70
    diff = np.clip(_dx * Lx + _dy * Ly + _nz * Lz, 0, 1)
    base = np.array([150, 18, 24], np.float32)
    col = base[None, None, :] * (0.25 + 0.85 * diff[..., None]) * (1 + np.where(side_left, 0.10, 0.04)[..., None] * _leather[..., None])
    # specular: shiny side strong, rough side weak
    hx, hy, hz = Lx, Ly, Lz + 1; hn = math.sqrt(hx * hx + hy * hy + hz * hz)
    spec = np.clip((_dx * hx + _dy * hy + _nz * hz) / hn, 0, 1) ** 60
    if mode == "rub": scuff = eio(pr(t, t0 + 0.2, 1.8))
    else: scuff = 1.0
    shine_r = 1.0 if mode == "swing" else 0.7
    spec_amt = np.where(side_left, 0.15 * (1 - scuff) + 0.05, shine_r)
    col = col + (spec * spec_amt * 255)[..., None]
    if mode == "swing":   # extra soft sheen on shiny side
        sheen = np.clip(1 - ((_dx - 0.35) ** 2 + (_dy + 0.35) ** 2) / 0.25, 0, 1) ** 2
        col = col + (sheen * (~side_left) * 70)[..., None]
    # scuffs on the left side: lighter, dull, streaky
    sc = (SCUFF_TEX * side_left * scuff * np.clip(-d_seam * 4, 0, 1))[..., None]
    col = col * (1 - sc * 0.7) + np.array([215, 150, 128], np.float32) * sc * 0.7
    # seam + stitches
    w = 0.035
    ad = np.abs(d_seam)
    seam = np.clip(1 - ad / w, 0, 1)[..., None]
    col = col * (1 - seam * 0.5)
    ang = _dy * 40
    st = ((ad > w * 1.1) & (ad < w * 2.4) & (np.sin(ang * 3.0) > 0.35))[..., None].astype(np.float32)
    col = col * (1 - st) + np.array([228, 214, 188], np.float32) * (0.35 + 0.7 * diff[..., None]) * st
    # background: dark with soft spot light
    bg = np.zeros((H, W, 3), np.float32) + 10
    glow = np.exp(-(((xx - BCX) / 520) ** 2 + ((yy - BCY) / 520) ** 2))[..., None]
    bg = bg + glow * np.array([70, 40, 34], np.float32)
    # contact shadow
    shadow = np.exp(-(((xx - BCX) / 260) ** 2 + ((yy - (BCY + BR + 25)) / 26) ** 2))[..., None]
    bg = bg * (1 - shadow * 0.8)
    a = bg * (1 - BMASK) + np.clip(col, 0, 255) * BMASK
    # gentle push-in
    return a

bases = {}
def idx(t):
    for i, sc in enumerate(S):
        if sc[1] <= t < sc[2]: return i
    return len(S) - 1
def scene(i, t):
    sc = S[i]; name, s, e, mode, o = sc
    if mode in ("rub", "swing"):
        return ball_frame(t, mode, s, e)
    if i not in bases:
        bases[i] = build(sc)
        for j in list(bases):
            if j < i - 1: del bases[j]
    b = bases[i]
    p = clamp((t - s) / (e - s)); p = 0.5 * p + 0.5 * eio(p)
    z0, z1 = o.get("zoom", (1.0, 1.08)); z = z0 + (z1 - z0) * p
    cw, ch = b.width / z, b.height / z
    fr = b.resize((W, H), Image.BILINEAR, box=(b.width / 2 - cw / 2, b.height / 2 - ch / 2, b.width / 2 + cw / 2, b.height / 2 + ch / 2))
    a = np.asarray(fr).astype(np.float32)
    sat = o.get("sat", 0.45)
    l = a.mean(-1, keepdims=True); a = l + (a - l) * sat
    a *= TINT * (1 - o.get("dark", 0.0))
    return a
def background(t):
    i = idx(t); a = scene(i, t)
    if i > 0 and t - S[i][1] < 0.4:
        k = eio((t - S[i][1]) / 0.4); a = scene(i - 1, t) * (1 - k) + a * k
    a = a * SHADE + GRAIN[int(t * FPS) % 6]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")

# ------------------------------------------------------------------ typography
_tc = {}
def timg(txt, f, fill=WHITE, spacing=0, shadow=True):
    k = (txt, id(f), fill, spacing, shadow)
    if k in _tc: return _tc[k]
    chars = list(txt)
    if spacing:
        ws = [(f.getbbox(c)[2] - f.getbbox(c)[0]) if c != " " else f.getbbox("n")[2] for c in chars]
        tw = sum(ws) + spacing * (len(chars) - 1)
    else:
        bb = f.getbbox(txt); tw = bb[2] - bb[0]
    asc, desc = f.getmetrics(); th = asc + desc
    pad = 36; im = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    def draw(dd, dy, col):
        if spacing:
            x = pad
            for c, w_ in zip(chars, ws):
                dd.text((x - (f.getbbox(c)[0] if c != " " else 0), pad + dy), c, font=f, fill=col); x += w_ + spacing
        else:
            dd.text((pad - f.getbbox(txt)[0], pad + dy), txt, font=f, fill=col)
    if shadow:
        s = Image.new("RGBA", im.size, (0, 0, 0, 0)); draw(ImageDraw.Draw(s), 4, (0, 0, 0, 170))
        im.alpha_composite(s.filter(ImageFilter.GaussianBlur(10)))
    draw(ImageDraw.Draw(im), 0, fill)
    _tc[k] = im
    return im
def put(img, im, cx, cy, alpha=1.0, scale=1.0):
    if alpha <= 0.01: return
    if abs(scale - 1) > 0.003: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 0.999: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
def box(img, x0, y0, x1, y1, col, a):
    if a <= 0.01 or x1 - x0 < 1: return
    img.alpha_composite(Image.new("RGBA", (int(x1 - x0), int(y1 - y0)), (*col, int(255 * a))), (int(x0), int(y0)))

def label(img, txt, cx, cy, t, a, b, size=34, col=WHITE, sp=5, font="mx"):
    k = fade(t, a, b); put(img, timg(txt, F(font, size), col, spacing=sp), cx, cy + (1 - eo(pr(t, a, 0.45))) * 16, k)

def big(img, txt, cx, cy, t, a, b, size=150, col=WHITE):
    k = fade(t, a, b); put(img, timg(txt, F("anton", size), col), cx, cy + (1 - eo(pr(t, a, 0.45))) * 24, k, 0.95 + 0.05 * eo(pr(t, a, 0.45)))

def date_card(img, t, txt, sub, a, b, y=1330):
    """typewriter date + red underline + subtitle"""
    k = fade(t, a, b)
    if k <= 0: return
    n = int(len(txt) * eo(pr(t, a, 0.55))) or 1
    full = timg(txt, F("anton", 150), WHITE)
    part = timg(txt[:n], F("anton", 150), WHITE)
    put(img, part, W / 2 - (full.width - part.width) / 2, y, k)
    ww = 220 * eo(pr(t, a + 0.3, 0.5))
    box(img, W / 2 - ww / 2, y + 95, W / 2 + ww / 2, y + 101, RED, k)
    if sub: label(img, sub, W / 2, y + 160, t, a + 0.6, b, 32, MUTED)

def quote(img, t, txt, who, a, b, y=1380, size=120):
    k = fade(t, a, b)
    if k <= 0: return
    put(img, timg("“", F("anton", 200), RED, shadow=False), W / 2, y - 125, k)
    big(img, txt, W / 2, y, t, a, b, size)
    if who: label(img, who, W / 2, y + 120, t, a + 0.3, b, 30, MUTED)

def ban_cards(img, t, a, b):
    items = [("STEVE SMITH", "12", "MONTHS"), ("DAVID WARNER", "12", "MONTHS"), ("CAMERON BANCROFT", "9", "MONTHS")]
    for i, (nm, n, u) in enumerate(items):
        ts = a + i * 0.9; k = fade(t, ts, b)
        if k <= 0: continue
        y = 1180 + i * 175; dx = (1 - eo(pr(t, ts, 0.45))) * -80
        card = Image.new("RGBA", (900, 150), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((0, 0, 899, 149), 22, fill=(10, 10, 12, 200), outline=(255, 255, 255, 40), width=2)
        cd.rectangle((0, 25, 8, 125), fill=(*RED, 255))
        put(img, card, W / 2 + dx, y, k)
        put(img, timg(nm, F("mx", 36), WHITE, spacing=3, shadow=False), 130 + dx + (timg(nm, F("mx", 36), WHITE, spacing=3, shadow=False).width - 72) / 2, y, k)
        put(img, timg(n, F("anton", 100), RED, shadow=False), 800 + dx, y - 5, k)
        put(img, timg(u, F("mx", 22), MUTED, spacing=3, shadow=False), 900 + dx, y + 28, k)

def steps(img, t):
    """1ST TEST -> 2ND TEST -> 3RD TEST progression (18.9 - 35.0)"""
    a, b = 14.11, 34.9
    if not (a <= t < b): return
    k = fade(t, a, b)
    labels = [("1ST TEST", "SUSPICION", 14.11), ("2ND TEST", "CAMERA ON BALL", 18.92), ("3RD TEST", "CAUGHT", 25.49)]
    y = 1640
    for i, (l1, l2, ts) in enumerate(labels):
        cx = W / 2 + (i - 1) * 330
        on = eo(pr(t, ts, 0.4))
        col = RED if (i == 2 and t >= 25.49) else WHITE
        d = Image.new("RGBA", (40, 40), (0, 0, 0, 0)); ImageDraw.Draw(d).ellipse((4, 4, 35, 35), fill=(*col, int(255 * (0.25 + 0.75 * on))))
        put(img, d, cx, y, k)
        put(img, timg(l1, F("mx", 26), WHITE if on > 0.5 else MUTED, spacing=3, shadow=False), cx, y + 50, k * (0.4 + 0.6 * on))
        put(img, timg(l2, F("ms", 22), col if on > 0.5 else MUTED, spacing=2, shadow=False), cx, y + 85, k * on)
        if i < 2:
            nxt = eo(pr(t, labels[i + 1][2], 0.6))
            box(img, cx + 30, y - 2, cx + 30 + 270 * nxt, y + 2, WHITE, k * 0.6)

# timeline bar at top: 2018 . 2021 . 2026
ERAS = [("2018", 10.23), ("2021", 42.35), ("2026", 55.16)]
def timeline(img, t):
    k = fade(t, 10.0, 106.3, 0.5)
    if k <= 0: return
    x0, x1, y = 140, 940, 150
    box(img, x0, y - 2, x1, y + 2, WHITE, 0.25 * k)
    xs = [x0, (x0 + x1) / 2, x1]
    # progress
    if t < 42.35: px = x0 + (xs[1] - x0) * 0.35 * eio(pr(t, 10.23, 32))
    elif t < 55.16: px = xs[0] + (xs[1] - xs[0]) * eio(pr(t, 42.35, 0.9))
    else: px = xs[1] + (xs[2] - xs[1]) * eio(pr(t, 55.16, 1.1))
    box(img, x0, y - 2, px, y + 2, RED, k)
    for (yr, ts), x in zip(ERAS, xs):
        active = t >= ts
        d = Image.new("RGBA", (44, 44), (0, 0, 0, 0)); ImageDraw.Draw(d).ellipse((6, 6, 37, 37), fill=(*(RED if active else (90, 90, 96)), 255), outline=(255, 255, 255, 200), width=3)
        put(img, d, x, y, k, 1 + 0.25 * (1 - eo(pr(t, ts, 0.4))) * active)
        put(img, timg(yr, F("mx", 26), WHITE if active else MUTED, spacing=3, shadow=False), x, y + 48, k)


def ball_overlay(img, t):
    if 27.35 <= t < 29.59 + 0.2:
        k = fade(t, 27.35, 29.59, 0.25)
        # sandpaper sheet rubbing over the left half
        osc = math.sin((t - 27.35) * 2 * math.pi * 2.4)
        cx = BCX - 150 + osc * 95; cy = BCY + 10 + math.cos((t - 27.35) * 2 * math.pi * 2.4) * 18
        sp = Image.new("RGBA", (300, 190), (0, 0, 0, 0)); sd = ImageDraw.Draw(sp)
        sd.rounded_rectangle((0, 0, 299, 189), 8, fill=(196, 164, 112, 255))
        g = np.random.default_rng(int(t * 10) % 3).integers(0, 60, (190, 300)).astype(np.uint8)
        grit = Image.fromarray(g, "L")
        tex = Image.new("RGBA", (300, 190), (60, 45, 25, 0)); tex.putalpha(grit)
        sp.alpha_composite(tex)
        m = Image.new("L", sp.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 299, 189), 8, fill=255)
        sp.putalpha(m)
        sp = sp.rotate(-18 + osc * 4, Image.BICUBIC, expand=True)
        sh = Image.new("RGBA", sp.size, (0, 0, 0, 0)); sh.putalpha(sp.getchannel("A").point(lambda v: int(v * 0.5)))
        put(img, sh.filter(ImageFilter.GaussianBlur(14)), cx + 18, cy + 26, k)
        put(img, sp, cx, cy, k)
        label(img, "SANDPAPER", W / 2, 1180, t, 27.5, 29.5, 34, PAPER, 8)
    if 100.39 <= t < 103.2 + 0.2:
        label(img, "REVERSE SWING", W / 2, 330, t, 100.45, 103.1, 40, WHITE, 8)
        label(img, "ROUGH SIDE", BCX - 230, 1135, t, 100.8, 103.1, 28, PAPER, 4)
        label(img, "SHINY SIDE", BCX + 230, 1135, t, 101.2, 103.1, 28, PAPER, 4)
        k = fade(t, 101.2, 103.1)
        for side, x in ((-1, BCX - 230), (1, BCX + 230)):
            box(img, x - 1, 1075, x + 1, 1105, WHITE, 0.5 * k)

def overlay(img, t):
    timeline(img, t)
    ball_overlay(img, t)
    # hook
    big(img, "SANDPAPERGATE", W / 2, 1360, t, 0.3, 10.1, 150)
    box(img, W / 2 - 110 * eo(pr(t, 0.7, 0.5)), 1450, W / 2 + 110 * eo(pr(t, 0.7, 0.5)), 1456, RED, fade(t, 0.7, 10.1))
    label(img, "8 YEARS LATER, IT'S BACK", W / 2, 1515, t, 1.2, 5.1, 32, MUTED)
    label(img, "THE FULL TIMELINE", W / 2, 1515, t, 5.23, 10.1, 32, MUTED)
    # March 2018
    date_card(img, t, "MARCH 2018", "AUSTRALIA TOUR OF SOUTH AFRICA", 10.23, 14.0)
    label(img, "FAF DU PLESSIS", W / 2, 1300, t, 14.11, 18.8, 44, WHITE)
    label(img, "SA CAPTAIN, 2018", W / 2, 1360, t, 14.4, 18.8, 28, MUTED)
    label(img, "2ND TEST  •  PORT ELIZABETH", W / 2, 1300, t, 18.92, 25.4, 38, WHITE)
    label(img, "“KEEP THE CAMERA ON THE BALL”", W / 2, 1375, t, 21.0, 25.4, 30, PAPER)
    label(img, "3RD TEST  •  CAPE TOWN", W / 2, 1300, t, 25.49, 34.9, 38, WHITE)
    big(img, "CAUGHT ON CAMERA", W / 2, 1420, t, 29.59, 34.9, 110, RED)
    steps(img, t)
    # bans
    label(img, "BANNED", W / 2, 1040, t, 35.04, 42.2, 40, RED, 10)
    ban_cards(img, t, 37.93, 42.2)
    # May 2021
    date_card(img, t, "MAY 2021", "BANCROFT HINTS: BOWLERS KNEW?", 42.35, 47.0)
    label(img, "CUMMINS  •  STARC  •  HAZLEWOOD  •  LYON", W / 2, 1300, t, 47.07, 55.0, 30, WHITE, 3)
    big(img, "“WE DIDN'T KNOW”", W / 2, 1420, t, 52.18, 55.0, 110)
    label(img, "JOINT STATEMENT", W / 2, 1520, t, 52.4, 55.0, 28, MUTED)
    # Nov 2026
    date_card(img, t, "NOVEMBER 2026", "THE STORY TURNS", 55.16, 58.6)
    label(img, "USMAN KHAWAJA'S AUTOBIOGRAPHY", W / 2, 1330, t, 58.74, 68.9, 30, MUTED)
    big(img, "SANDPAPER IN PORT ELIZABETH TOO", W / 2, 1430, t, 62.56, 68.9, 72)
    big(img, "THE WHOLE TEAM KNEW", W / 2, 1530, t, 66.50, 68.9, 72, RED)
    # Cummins
    quote(img, t, "UTTER NONSENSE", "PAT CUMMINS", 69.05, 77.9)
    label(img, "70-MINUTE PRESS CONFERENCE", W / 2, 1640, t, 72.88, 77.9, 30, WHITE)
    # Warner
    label(img, "DAVID WARNER", W / 2, 1180, t, 78.12, 84.0, 44, WHITE)
    label(img, "BACKS KHAWAJA 100%", W / 2, 1245, t, 78.6, 84.0, 30, MUTED)
    quote(img, t, "A COVER-UP", "WARNER ON CUMMINS' RESPONSE", 81.50, 84.0, 1500, 110)
    # Bancroft
    big(img, "THE FINAL STRAW", W / 2, 1380, t, 84.21, 87.5, 120, RED)
    label(img, "NOV 18  •  CAMERON BANCROFT", W / 2, 1280, t, 87.77, 100.2, 34, WHITE)
    big(img, "4,000 WORDS", W / 2, 1400, t, 87.77, 93.3, 130)
    big(img, "IDEA: DAVID WARNER", W / 2, 1400, t, 93.57, 96.6, 100)
    big(img, "NOT JUST THREE PLAYERS", W / 2, 1400, t, 96.76, 100.2, 84, RED)
    label(img, "“I SPOKE TO THE BOWLERS", W / 2, 1360, t, 100.39, 106.2, 40, WHITE)
    label(img, "ABOUT REVERSE SWING”", W / 2, 1420, t, 100.39, 106.2, 40, WHITE)
    label(img, "INCLUDING PAT CUMMINS", W / 2, 1500, t, 101.77, 106.2, 30, RED)
    # outro
    big(img, "WAS STEVE SMITH WRONGED?", W / 2, 1380, t, 107.68, 112.2, 84)
    label(img, "WHO'S TELLING THE TRUTH?", W / 2, 1480, t, 109.63, 112.2, 36, RED)
    label(img, "COMMENT BELOW", W / 2, 1560, t, 111.29, 112.2, 30, MUTED)

def frame(t):
    img = background(t)
    overlay(img, t)
    f = min(1, t / 0.5, (DUR - t) / 0.7)
    out = img.convert("RGB")
    if f < 1: out = Image.eval(out, lambda v: int(v * max(0, f)))
    return out

if PREVIEW:
    os.makedirs(os.path.join(D, "prev"), exist_ok=True)
    for t in PREVIEW: frame(t).save(os.path.join(D, "prev", f"p_{t:06.2f}.jpg"), quality=88)
    sys.exit()
n = int(DUR * FPS)
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-tune", "grain", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
for i in range(n):
    ff.stdin.write(frame(i / FPS).tobytes())
    if i % 300 == 0: print("frame", i, "/", n, flush=True)
ff.stdin.close(); ff.wait(); print("done")
