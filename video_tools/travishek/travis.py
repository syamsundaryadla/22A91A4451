"""End of the Travishek era: clean cinematic reel, 1080x1920 @30fps."""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

D = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(D, "..", "fonts")
OUT = sys.argv[1]
PREVIEW = [float(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else None
W, H, FPS, DUR = 1080, 1920, 30, 66.69
ORANGE = (255, 112, 30); WHITE = (255, 255, 255); MUTED = (205, 205, 212)
font = lambda n, s: ImageFont.truetype(os.path.join(FONTS, n), s)
_F = {}
def F(n, s):
    if (n, s) not in _F: _F[(n, s)] = font({"anton": "Anton.ttf", "mb": "Montserrat-Black.ttf", "mx": "Montserrat-ExtraBold.ttf", "ms": "Montserrat-SemiBold.ttf"}[n], s)
    return _F[(n, s)]

clamp = lambda x, a=0.0, b=1.0: max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return x * x * (3 - 2 * x)
def pr(t, s, d): return clamp((t - s) / d)

# ------------------------------------------------------------------ scenes
# (img, start, end, mode, options)
S = [
 ("IMG1", 0.00, 3.15, "fill", dict(focus=(0.5, 0.35), zoom=(1.12, 1.0), gray_at=1.35)),
 ("IMG2", 3.15, 7.00, "framed", dict(zoom=(1.0, 1.06), fy=0.40)),
 ("IMG3", 7.00, 11.65, "framed", dict(zoom=(1.0, 1.07), fy=0.40)),
 ("IMG7", 11.65, 18.95, "fill", dict(focus=(0.5, 0.3), zoom=(1.0, 1.10))),
 ("IMG4", 18.95, 22.35, "framed", dict(zoom=(1.0, 1.08), fy=0.40)),
 ("IMG5", 22.35, 27.40, "framed", dict(zoom=(1.0, 1.07), fy=0.36)),
 ("IMG8", 27.40, 34.72, "framed", dict(zoom=(1.0, 1.08), fy=0.36)),
 ("IMG10", 34.72, 37.50, "fill", dict(focus=(0.5, 0.25), zoom=(1.0, 1.08))),
 ("IMG6", 37.50, 49.10, "fill", dict(focus=(0.5, 0.5), zoom=(1.05, 1.18), dark=0.45)),
 ("SPLIT", 49.10, 56.85, "split", {}),
 ("IMG9", 56.85, 58.62, "fill", dict(focus=(0.5, 0.3), zoom=(1.0, 1.06))),
 ("IMG2", 58.62, 59.62, "framed", dict(zoom=(1.04, 1.08), fy=0.40, gray=True)),
 ("IMG1", 59.62, 62.30, "fill", dict(focus=(0.5, 0.35), zoom=(1.0, 1.08), fade_left_at=60.6)),
 ("IMG4", 62.30, 66.69, "framed", dict(zoom=(1.0, 1.06), fy=0.36, dark=0.35)),
]
SS = 1.12

def load(name):
    im = Image.open(os.path.join(D, "img", name + ".jpg")).convert("RGB")
    im = ImageEnhance.Contrast(im).enhance(1.08); im = ImageEnhance.Color(im).enhance(1.06)
    return im

def cover(im, w, h, fx=0.5, fy=0.5):
    s = max(w / im.width, h / im.height)
    im = im.resize((max(w, round(im.width * s)), max(h, round(im.height * s))), Image.LANCZOS)
    x = int((im.width - w) * fx); y = int((im.height - h) * fy)
    return im.crop((x, y, x + w, y + h))

def build(sc):
    name, s, e, mode, o = sc
    bw, bh = int(W * SS), int(H * SS)
    if mode == "split":
        top = cover(load("IMG8"), bw, bh // 2, 0.52, 0.0)
        bot = cover(load("IMG9"), bw, bh - bh // 2, 0.5, 0.62)
        base = Image.new("RGB", (bw, bh)); base.paste(top, (0, 0)); base.paste(bot, (0, bh // 2))
        return base.filter(ImageFilter.UnsharpMask(2, 50, 2))
    src = load(name)
    if mode == "fill":
        base = cover(src, bw, bh, *o.get("focus", (0.5, 0.5)))
    else:
        bg = cover(src, bw // 8, bh // 8).filter(ImageFilter.GaussianBlur(4)).resize((bw, bh), Image.BICUBIC)
        bg = ImageEnhance.Brightness(bg).enhance(0.38)
        fw = bw; fh = int(src.height * fw / src.width)
        fg = src.resize((fw, fh), Image.LANCZOS)
        y = int(bh * o.get("fy", 0.4) - fh / 2)
        # soft feathered edges top/bottom
        m = Image.new("L", (fw, fh), 255); md = ImageDraw.Draw(m)
        for i in range(60):
            a = int(255 * i / 60); md.line((0, i, fw, i), fill=a); md.line((0, fh - 1 - i, fw, fh - 1 - i), fill=a)
        bg.paste(fg, (0, y), m)
        base = bg
    return base.filter(ImageFilter.UnsharpMask(2, 60, 2))

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1 - 0.5 * (((xx - W / 2) / (W * 0.85)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2), 0.3, 1)
GRAD = 1 - np.clip((yy / H - 0.52) / 0.48, 0, 1) ** 1.4 * 0.72 - np.clip((0.12 - yy / H) / 0.12, 0, 1) * 0.35
SHADE = (VIG * GRAD)[..., None].astype(np.float32)
rng = np.random.default_rng(5)
GRAIN = [rng.normal(0, 5.5, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
GRAIN = [np.asarray(Image.fromarray(g).resize((W, H), Image.BILINEAR))[..., None] for g in GRAIN]

bases = {}
def scene_idx(t):
    for i, sc in enumerate(S):
        if sc[1] <= t < sc[2]: return i
    return len(S) - 1

def render_scene(i, t):
    sc = S[i]; name, s, e, mode, o = sc
    if i not in bases:
        bases[i] = build(sc)
        for j in list(bases):
            if j < i - 1: del bases[j]
    b = bases[i]
    p = clamp((t - s) / (e - s)); p = p * 0.5 + eio(p) * 0.5
    z0, z1 = o.get("zoom", (1.0, 1.08)); z = z0 + (z1 - z0) * p
    cw, ch = b.width / z, b.height / z
    box = (b.width / 2 - cw / 2, b.height / 2 - ch / 2, b.width / 2 + cw / 2, b.height / 2 + ch / 2)
    fr = b.resize((W, H), Image.BILINEAR, box=box)
    a = np.asarray(fr).astype(np.float32)
    g = None
    if o.get("gray"): g = 1.0
    if "gray_at" in o: g = eio(pr(t, o["gray_at"], 0.9)) * 0.92
    if g:
        l = a.mean(-1, keepdims=True); a = a * (1 - g) + l * g
    if "fade_left_at" in o:
        k = eio(pr(t, o["fade_left_at"], 0.8))
        mask = np.clip((W * 0.52 - xx) / 160, 0, 1)[..., None]   # Head stands on the left
        l = a.mean(-1, keepdims=True)
        a = a * (1 - mask * k) + (l * 0.25) * mask * k
    if o.get("dark"): a *= 1 - o["dark"]
    return a

def background(t):
    i = scene_idx(t)
    a = render_scene(i, t)
    # crossfade from previous scene over 0.35s
    if i > 0 and t - S[i][1] < 0.35:
        k = eio((t - S[i][1]) / 0.35)
        a = render_scene(i - 1, t) * (1 - k) + a * k
    a = a * SHADE + GRAIN[int(t * FPS) % 6]
    # dip for hook end -> s2 is handled by crossfade
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")

# ------------------------------------------------------------------ typography
_tc = {}
def timg(txt, f, fill=WHITE, spacing=0, shadow=True):
    k = (txt, id(f), fill, spacing, shadow)
    if k in _tc: return _tc[k]
    if spacing:
        widths = [f.getbbox(c)[2] - f.getbbox(c)[0] if c != " " else f.getbbox("n")[2] for c in txt]
        tw = sum(widths) + spacing * (len(txt) - 1)
    else:
        bb = f.getbbox(txt); tw = bb[2] - bb[0]
    asc, desc = f.getmetrics(); th = asc + desc
    pad = 30; im = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    def draw(dd, off, col):
        if spacing:
            x = pad + off[0]
            for c, w in zip(txt, widths):
                dd.text((x - (f.getbbox(c)[0] if c != " " else 0), pad + off[1]), c, font=f, fill=col); x += w + spacing
        else:
            dd.text((pad - f.getbbox(txt)[0] + off[0], pad + off[1]), txt, font=f, fill=col)
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); draw(ImageDraw.Draw(sh), (0, 4), (0, 0, 0, 150))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    draw(d, (0, 0), fill)
    _tc[k] = im
    return im

def put(img, im, cx, cy, alpha=1.0, scale=1.0, anchor="c"):
    if alpha <= 0.01: return
    if abs(scale - 1) > 0.003: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 0.999: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    x = cx - im.width / 2 if anchor == "c" else cx - 30
    img.alpha_composite(im, (int(x), int(cy - im.height / 2)))

def fade(t, a, b, d=0.35):
    return eo(pr(t, a, d)) * (1 - eio(pr(t, b - d, d)))

def label(img, txt, cx, cy, t, a, b, size=34, col=MUTED, rise=18):
    k = fade(t, a, b); put(img, timg(txt, F("mx", size), col, spacing=5), cx, cy + (1 - eo(pr(t, a, 0.4))) * rise, k)

def big(img, txt, cx, cy, t, a, b, size=210, col=WHITE):
    k = fade(t, a, b); put(img, timg(txt, F("anton", size), col), cx, cy + (1 - eo(pr(t, a, 0.45))) * 30, k, 0.94 + 0.06 * eo(pr(t, a, 0.45)))

def rule(img, cx, cy, t, a, b, w=120):
    k = fade(t, a, b); ww = int(w * eo(pr(t, a + 0.1, 0.5)))
    if k > 0.01 and ww > 2:
        bar = Image.new("RGBA", (ww, 6), (*ORANGE, int(255 * k)))
        img.alpha_composite(bar, (int(cx - ww / 2), int(cy - 3)))

def count(t, a, val, d=0.9, dec=0):
    v = val * eo(pr(t, a, d))
    return f"{v:,.{dec}f}"

_sh = np.zeros((H, W), np.float32)
for y0 in (H // 2 - 520, H - 520):
    band = np.clip((yy[:, 0] - y0) / 520, 0, 1) ** 1.2
    _sh = np.maximum(_sh, (band * ((yy[:, 0] < y0 + 520))).astype(np.float32)[:, None] * np.ones((1, W), np.float32))
SPLIT_SHADE = Image.fromarray((np.dstack([np.zeros((H, W, 3)), _sh[..., None] * 200])).astype(np.uint8), "RGBA")
_logo = {}
def logo(k, h):
    if (k, h) not in _logo:
        lg = Image.open(os.path.join(D, "img", k + ".png")).convert("RGBA"); s = h / lg.height
        _logo[(k, h)] = lg.resize((int(lg.width * s), h), Image.LANCZOS)
    return _logo[(k, h)]

def overlay(img, t):
    Y = 1430
    # hook
    big(img, "TRAVISHEK", W / 2, Y, t, 0.05, 3.05, 190)
    rule(img, W / 2, Y + 125, t, 0.3, 3.05)
    label(img, "2024  —  2026", W / 2, Y + 185, t, 0.4, 3.05)
    # opt out
    label(img, "TRAVIS HEAD", W / 2, 1260, t, 3.3, 6.9, 40, WHITE)
    label(img, "OPTS OUT OF IPL 2027", W / 2, 1325, t, 4.55, 6.9, 34, ORANGE)
    label(img, "TESTS  •  WORLD CUP", W / 2, 1290, t, 7.2, 11.5, 34, WHITE)
    # released
    big(img, "RELEASED", W / 2, 1330, t, 13.2, 18.85, 170)
    rule(img, W / 2, 1440, t, 13.4, 18.85)
    label(img, "14 CRORE FREED", W / 2, 1505, t, 14.99, 18.85, 40, WHITE)
    label(img, "MINI-AUCTION  •  DEC 16", W / 2, 1565, t, 16.80, 18.85, 32)
    # partnership runs
    if 23.5 <= t < 27.4:
        big(img, count(t, 23.57, 1892, 1.4), W / 2, 1300, t, 23.57, 27.3, 210)
    label(img, "PARTNERSHIP RUNS", W / 2, 1425, t, 23.7, 27.3, 34)
    label(img, "AVERAGE 46.14", W / 2, 1495, t, 25.96, 27.3, 34, ORANGE)
    # run rate
    if 28.1 <= t < 34.72:
        big(img, count(t, 28.2, 12.27, 1.2, 2), W / 2, 1300, t, 28.2, 34.62, 210)
    label(img, "RUNS PER OVER", W / 2, 1425, t, 28.4, 34.62, 34)
    label(img, "HIGHEST IN IPL HISTORY", W / 2, 1495, t, 33.69, 34.62, 34, ORANGE)
    label(img, "PAIRS WITH 1,000+ RUNS", W / 2, 1495, t, 30.29, 33.6, 28)
    # stands
    for cx, n, lab, ts in ((W / 2 - 220, "6", "100+ STANDS", 34.82), (W / 2 + 220, "9", "50+ STANDS", 36.12)):
        big(img, n, cx, 1330, t, ts, 37.4, 230)
        label(img, lab, cx, 1470, t, ts + 0.1, 37.4, 32)
    # powerplay
    big(img, "100+", W / 2, 640, t, 37.56, 49.0, 190, ORANGE)
    label(img, "POWERPLAY  ×3", W / 2, 765, t, 38.4, 49.0, 38, WHITE)
    for i, (sc, ov, vs, ts) in enumerate((("125/0", "6 OVERS", "vs DC", 40.29), ("167/0", "9.4 OVERS", "vs LSG", 44.67))):
        y = 1060 + i * 300
        k = fade(t, ts, 49.0)
        if k > 0:
            card = Image.new("RGBA", (880, 240), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
            cd.rounded_rectangle((0, 0, 879, 239), 34, fill=(10, 10, 14, 170), outline=(255, 255, 255, 40), width=2)
            cd.rectangle((0, 40, 7, 200), fill=(*ORANGE, 255))
            put(img, card, W / 2, y + (1 - eo(pr(t, ts, 0.4))) * 40, k)
            put(img, timg(sc, F("anton", 140), WHITE), W / 2 - 170, y + (1 - eo(pr(t, ts, 0.4))) * 40, k)
            put(img, timg(ov, F("mx", 36), WHITE, spacing=3), W / 2 + 225, y - 30 + (1 - eo(pr(t, ts, 0.4))) * 40, k)
            put(img, timg(vs.upper(), F("mx", 32), MUTED, spacing=4), W / 2 + 225, y + 30 + (1 - eo(pr(t, ts, 0.4))) * 40, k)
    label(img, "NO WICKET LOST", W / 2, 1520, t, 47.45, 49.0, 36, ORANGE)
    # head to head (split screen)
    if 49.1 <= t < 56.85:
        k = fade(t, 49.1, 56.85, 0.3)
        img.alpha_composite(SPLIT_SHADE)
        img.alpha_composite(Image.new("RGBA", (W, 6), (*ORANGE, int(255 * k))), (0, H // 2 - 3))
    for (nm, runs, sr, tn, tr, ts_, cy) in (("HEAD", 1351, "176.14", 49.22, 49.72, 51.04, 800), ("ABHISHEK", 1486, "201.08", 52.81, 53.44, 54.90, 1760)):
        label(img, nm, 250, cy - 120, t, tn, 56.75, 40, WHITE)
        if t >= tr - 0.05:
            big(img, count(t, tr, runs, 0.9), 250, cy, t, tr, 56.75, 140)
        label(img, "RUNS", 250, cy + 95, t, tr + 0.1, 56.75, 28)
        big(img, sr, 830, cy, t, ts_, 56.75, 140, ORANGE)
        label(img, "STRIKE RATE", 830, cy + 95, t, ts_ + 0.1, 56.75, 28)
    # retained / released
    big(img, "RETAINED", W / 2, 1420, t, 56.93, 58.55, 170, ORANGE)
    big(img, "RELEASED", W / 2, 1420, t, 58.70, 59.55, 170, WHITE)
    # who next
    label(img, "WHO'S NEXT?", W / 2, 1450, t, 60.73, 62.2, 52, WHITE)
    # outro
    label(img, "COMMENT YOUR PICK", W / 2, 1300, t, 62.41, 66.6, 40, WHITE)
    k = fade(t, 63.81, 66.6)
    if k > 0:
        pill = Image.new("RGBA", (420, 110), (0, 0, 0, 0)); ImageDraw.Draw(pill).rounded_rectangle((0, 0, 419, 109), 55, fill=(*ORANGE, 255))
        put(img, pill, W / 2, 1450, k, 0.9 + 0.1 * eo(pr(t, 63.81, 0.4)))
        put(img, timg("FOLLOW", F("mb", 48), WHITE, spacing=4, shadow=False), W / 2, 1450, k, 0.9 + 0.1 * eo(pr(t, 63.81, 0.4)))

def frame(t):
    img = background(t)
    overlay(img, t)
    f = min(1, t / 0.4, (DUR - t) / 0.6)
    out = img.convert("RGB")
    if f < 1: out = Image.eval(out, lambda v: int(v * max(0, f)))
    return out

if PREVIEW:
    os.makedirs(os.path.join(D, "prev"), exist_ok=True)
    for t in PREVIEW: frame(t).save(os.path.join(D, "prev", f"p_{t:05.2f}.jpg"), quality=88)
    sys.exit()
n = int(DUR * FPS)
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
for i in range(n):
    ff.stdin.write(frame(i / FPS).tobytes())
    if i % 300 == 0: print("frame", i, "/", n, flush=True)
ff.stdin.close(); ff.wait(); print("done")
