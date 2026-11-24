"""15s Hanuman reel: 'Who said I'm alone?'  1080x1920 @30fps."""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

D = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(D, "..", "fonts")
OUT = sys.argv[1]
PREVIEW = [float(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else None
W, H, FPS, DUR = 1080, 1920, 30, 15.0
GOLD = (255, 200, 90); WHITE = (255, 255, 255); SOFT = (225, 222, 215)
_F = {}
def F(n, s):
    if (n, s) not in _F:
        _F[(n, s)] = ImageFont.truetype(os.path.join(FONTS, {"cb": "Cinzel-Black.ttf", "cz": "Cinzel-Bold.ttf", "ms": "Montserrat-SemiBold.ttf", "mx": "Montserrat-ExtraBold.ttf"}[n]), s)
    return _F[(n, s)]
clamp = lambda x, a=0.0, b=1.0: max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return x * x * (3 - 2 * x)
def pr(t, s, d): return clamp((t - s) / d)
def fade(t, a, b, d=0.3): return eo(pr(t, a, d)) * (1 - eio(pr(t, b - d, d)))
DROP = 3.0

# scenes: (img, start, end, zoom0, zoom1, focus_y, pan_y)
S = [("FEET", 2.05, 3.0, 1.00, 1.06, 0.6, 0.0),
     ("STORM", 3.0, 4.8, 1.18, 1.04, 0.45, 0.0),
     ("FACE", 4.8, 6.4, 1.00, 1.16, 0.30, 0.0),
     ("FLY", 6.4, 8.6, 1.05, 1.15, 0.40, -0.3),
     ("CLIFF", 8.6, 15.0, 1.00, 1.14, 0.45, 0.0)]
SS = 1.18
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1 - 0.55 * (((xx - W / 2) / (W * 0.8)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2), 0.3, 1)[..., None]
rng = np.random.default_rng(3)
GRAIN = [np.asarray(Image.fromarray(rng.normal(0, 4.5, (H // 2, W // 2)).astype(np.float32)).resize((W, H)))[..., None] for _ in range(5)]
BOT = (1 - np.clip((yy / H - 0.58) / 0.42, 0, 1) ** 1.4 * 0.65)[..., None]
_b = {}
def base(name):
    if name not in _b:
        im = Image.open(os.path.join(D, "img", name + ".jpg")).convert("RGB")
        im = ImageEnhance.Contrast(im).enhance(1.08); im = ImageEnhance.Color(im).enhance(1.1)
        bw, bh = int(W * SS), int(H * SS)
        im = im.resize((bw, bh), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
        a = np.asarray(im).astype(np.float32); a[..., 0] *= 1.05; a[..., 2] *= 0.94   # warm grade
        _b[name] = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return _b[name]
def shot(i, t):
    name, s, e, z0, z1, fy, py = S[i]
    b = base(name); p = clamp((t - s) / (e - s)); p = 0.5 * p + 0.5 * eio(p)
    z = z0 + (z1 - z0) * p
    cw, ch = b.width / z, b.height / z
    cx = b.width / 2; cy = b.height * fy + (b.height / 2 - b.height * fy) * 0 + py * p * (b.height - ch) / 2
    cy = min(max(cy, ch / 2), b.height - ch / 2)
    # shake on the drop
    if i == 1 and t - DROP < 0.45:
        k = 1 - (t - DROP) / 0.45; cx += math.sin(t * 95) * 18 * k; cy += math.cos(t * 80) * 14 * k
    fr = b.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
    return np.asarray(fr).astype(np.float32)

def background(t):
    if t < S[0][1]: return np.zeros((H, W, 3), np.float32)
    idx = max(i for i in range(len(S)) if S[i][1] <= t)
    a = shot(idx, t)
    if idx == 0: a *= eio(pr(t, S[0][1], 0.6)) * 0.55          # feet: dim, emerging from black
    if idx > 1 and t - S[idx][1] < 0.25:                         # quick dissolve between shots after drop
        k = eio((t - S[idx][1]) / 0.25); a = shot(idx - 1, t) * (1 - k) + a * k
    if idx >= 4: a *= 1 - 0.25 * eio(pr(t, 9.0, 1.0))           # cliff darkens a bit under text
    return a

# embers
rs = np.random.default_rng(9)
EMB = [(rs.uniform(0, W), rs.uniform(0, H), rs.uniform(30, 110), rs.uniform(1.5, 4), rs.uniform(0, 6.3)) for _ in range(70)]
def embers(img, t):
    if t < DROP: return
    k = eo(pr(t, DROP, 0.6))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for x0, y0, v, r, ph in EMB:
        y = (y0 - v * t) % H; x = x0 + math.sin(t + ph) * 25
        a = int((110 + 90 * math.sin(t * 3 + ph)) * k)
        d.ellipse((x - r * 2.4, y - r * 2.4, x + r * 2.4, y + r * 2.4), fill=(255, 140, 30, a // 5))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 205, 110, a))
    img.alpha_composite(lay)

_tc = {}
def timg(txt, f, fill=WHITE, spacing=0, glow=None):
    k = (txt, id(f), fill, spacing, glow)
    if k in _tc: return _tc[k]
    chars = list(txt)
    ws = [(f.getbbox(c)[2] - f.getbbox(c)[0]) if c != " " else f.getbbox("n")[2] * 0.9 for c in chars]
    tw = int(sum(ws) + spacing * (len(chars) - 1)); asc, desc = f.getmetrics(); th = asc + desc
    pad = 50; im = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    def draw(dd, dy, col, sw=0):
        x = pad
        for c, w_ in zip(chars, ws):
            if c != " ": dd.text((x - f.getbbox(c)[0], pad + dy), c, font=f, fill=col, stroke_width=sw, stroke_fill=col)
            x += w_ + spacing
    if glow:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0)); draw(ImageDraw.Draw(g), 0, glow, 6); im.alpha_composite(g.filter(ImageFilter.GaussianBlur(16)))
    s = Image.new("RGBA", im.size, (0, 0, 0, 0)); draw(ImageDraw.Draw(s), 4, (0, 0, 0, 170)); im.alpha_composite(s.filter(ImageFilter.GaussianBlur(8)))
    draw(ImageDraw.Draw(im), 0, fill)
    _tc[k] = im
    return im
def put(img, im, cx, cy, alpha=1.0, scale=1.0):
    if alpha <= 0.01: return
    if abs(scale - 1) > 0.003: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 0.999: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def typed(img, t, lines, a, b, y, size, col, cps=26, font="ms", sp=2):
    k = 1 - eio(pr(t, b - 0.25, 0.25))
    if t < a or k <= 0: return
    total = sum(len(l) for l in lines); n = int((t - a) * cps)
    used = 0
    for li, l in enumerate(lines):
        shown = l[:max(0, min(len(l), n - used))]; used += len(l)
        if not shown: continue
        full = timg(l, F(font, size), col, sp); part = timg(shown, F(font, size), col, sp)
        put(img, part, W / 2 - (full.width - part.width) / 2, y + li * (size * 1.45), k)
        if n < total and len(shown) < len(l) and int(t * 3) % 2 == 0 and shown:
            cur = Image.new("RGBA", (4, int(size * 1.1)), (*col, 230))
            img.alpha_composite(cur, (int(W / 2 - full.width / 2 + part.width - 50 + 6), int(y + li * size * 1.45 - size * 0.55)))

def frame(t):
    a = background(t) * VIG * BOT + GRAIN[int(t * FPS) % 5]
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    embers(img, t)
    # hook
    typed(img, t, ["Aren't you scared of", "facing everything alone?"], 0.15, 1.9, 890, 62, SOFT, cps=30, font="mx")
    k = fade(t, 1.95, 2.95, 0.25)
    if k > 0:
        put(img, timg("Who said I'm alone?", F("mx", 64), WHITE, 2), W / 2, 960, k, 0.96 + 0.04 * eo(pr(t, 1.95, 0.5)))
    # flash on the drop (lightning)
    if 0 <= t - DROP < 0.35:
        fk = 1 - (t - DROP) / 0.35
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 245, 225, int(235 * fk ** 1.5))))
    if 3.55 <= t < 3.75:   # second lightning flicker
        img.alpha_composite(Image.new("RGBA", (W, H), (220, 230, 255, 90)))
    # Chalisa line, word by word
    words1 = ["Sankat", "kate", "mite", "sab", "peera"]; words2 = ["Jo", "sumire", "Hanumat", "balbeera"]
    for wi, (line, y0, t0) in enumerate(((words1, 1180, 9.0), (words2, 1275, 10.1))):
        if not (t0 - 0.1 <= t < 13.0): continue
        ims = [timg(w, F("cz", 54), GOLD, 1, glow=(255, 140, 20, 110)) for w in line]
        gap = 26; tot = sum(i.width - 100 for i in ims) + gap * (len(ims) - 1); x = W / 2 - tot / 2
        for j, im in enumerate(ims):
            ts = t0 + j * 0.2; kk = eo(pr(t, ts, 0.4)) * (1 - eio(pr(t, 12.6, 0.4)))
            ww = im.width - 100; put(img, im, x + ww / 2, y0 + (1 - eo(pr(t, ts, 0.4))) * 14, kk); x += ww + gap
    kc = fade(t, 11.2, 13.0)
    if kc > 0:
        put(img, timg("Every trouble vanishes for the one who remembers Hanuman", F("ms", 27), SOFT, 0), W / 2, 1385, kc)
    # end card
    ke = eo(pr(t, 13.0, 0.5)) * min(1, (DUR - t) / 0.3)
    if ke > 0:
        put(img, timg("JAI HANUMAN", F("cb", 100), GOLD, 4, glow=(255, 130, 10, 150)), W / 2, 1220, ke, 0.9 + 0.1 * eo(pr(t, 13.0, 0.6)))
    return img.convert("RGB")

if PREVIEW:
    os.makedirs(os.path.join(D, "prev"), exist_ok=True)
    for t in PREVIEW: frame(t).save(os.path.join(D, "prev", f"p_{t:05.2f}.jpg"), quality=88)
    sys.exit()
n = int(DUR * FPS)
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
for i in range(n):
    ff.stdin.write(frame(i / FPS).tobytes())
ff.stdin.close(); ff.wait(); print("done")
