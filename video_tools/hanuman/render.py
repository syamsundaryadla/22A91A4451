"""Render the Hanuman & Shani Dev reel: 1080x1920, 30fps, Pillow frames piped to ffmpeg."""
import json, math, random, subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = sys.argv[1]            # scratchpad dir
OUT = sys.argv[2]             # output mp4 (video only)
PREVIEW = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else None
W, H, FPS = 1080, 1920, 30
DUR = 56.19
F = lambda n: os.path.join(ROOT, "fonts", n)
font = lambda n, s: ImageFont.truetype(F(n), s)
SAFFRON = (255, 176, 0)
timing = json.load(open(os.path.join(ROOT, "timing.json")))
SCENES = json.load(open(os.path.join(ROOT, "scenes.json")))

# ---------------------------------------------------------------- backgrounds
def grade(im):
    im = ImageEnhance.Color(im).enhance(1.25)
    im = ImageEnhance.Contrast(im).enhance(1.12)
    a = np.asarray(im).astype(np.float32)
    a[..., 0] *= 1.06; a[..., 2] *= 0.92          # warm
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def cover(im, w, h, fx=0.5, fy=0.5):
    s = max(w / im.width, h / im.height)
    im = im.resize((max(w, round(im.width * s)), max(h, round(im.height * s))), Image.LANCZOS)
    x = int((im.width - w) * fx); y = int((im.height - h) * fy)
    return im.crop((x, y, x + w, y + h))

SS = 1.18  # oversample for ken burns
def build_base(sc):
    src = Image.open(os.path.join(ROOT, "img", sc["img"] + ".jpg")).convert("RGB")
    if "crop" in sc:                                    # crop box in fractions
        l, t, r, b = sc["crop"]; src = src.crop((int(l*src.width), int(t*src.height), int(r*src.width), int(b*src.height)))
    if sc.get("flip"): src = src.transpose(Image.FLIP_LEFT_RIGHT)
    src = grade(src)
    bw, bh = int(W * SS), int(H * SS)
    if sc.get("mode", "fill") == "fill":
        base = cover(src, bw, bh, *sc.get("focus", (0.5, 0.5)))
        base = base.filter(ImageFilter.UnsharpMask(2, 60, 2))
    else:                                              # framed: blurred bg + full image
        bg = cover(src, bw // 6, bh // 6).filter(ImageFilter.GaussianBlur(6)).resize((bw, bh), Image.BICUBIC)
        bg = ImageEnhance.Brightness(bg).enhance(0.45)
        fw = int(bw * sc.get("fw", 1.0)); fh = int(src.height * fw / src.width)
        if fh > bh * 0.62: fh = int(bh * 0.62); fw = int(src.width * fh / src.height)
        fg = src.resize((fw, fh), Image.LANCZOS)
        y = int(bh * sc.get("fy", 0.40) - fh / 2)
        sh = Image.new("L", (bw, bh), 0); ImageDraw.Draw(sh).rectangle(((bw-fw)//2, y+18, (bw+fw)//2, y+fh+18), fill=200)
        bg.paste(Image.new("RGB", (bw, bh), 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(30)))
        bg.paste(fg, ((bw - fw) // 2, y))
        base = bg
    return base

# vignette + gradients overlay
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
d = np.sqrt(((xx - W/2) / (W*0.75))**2 + ((yy - H/2) / (H*0.70))**2)
vig = np.clip((d - 0.55) * 1.3, 0, 0.75)
grad_b = np.clip((yy / H - 0.55) / 0.45, 0, 1) ** 1.3 * 0.80
grad_t = np.clip((0.16 - yy / H) / 0.16, 0, 1) * 0.55
DARK = 1 - np.clip(vig + grad_b + grad_t, 0, 0.88)
DARK = DARK[..., None]

# ---------------------------------------------------------------- particles (embers)
random.seed(7)
EMB = [dict(x=random.uniform(0, W), y=random.uniform(0, H), v=random.uniform(25, 90), r=random.uniform(1.5, 4.5),
            ph=random.uniform(0, 6.28), sw=random.uniform(10, 40)) for _ in range(70)]

def draw_embers(img, t):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
    for e in EMB:
        y = (e["y"] - e["v"] * t) % (H + 40) - 20
        x = e["x"] + math.sin(t * 0.8 + e["ph"]) * e["sw"]
        a = int(120 + 100 * math.sin(t * 3 + e["ph"]))
        r = e["r"]
        dr.ellipse((x-r*2.2, y-r*2.2, x+r*2.2, y+r*2.2), fill=(255, 140, 20, a // 5))
        dr.ellipse((x-r, y-r, x+r, y+r), fill=(255, 200, 90, a))
    img.alpha_composite(lay)

# ---------------------------------------------------------------- text helpers
def text_img(txt, fnt, fill, stroke=0, stroke_fill=(0, 0, 0), glow=None, shadow=True):
    bb = fnt.getbbox(txt, stroke_width=stroke)
    pad = 40
    w, h = bb[2] - bb[0] + pad*2, bb[3] - bb[1] + pad*2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    org = (pad - bb[0], pad - bb[1])
    if glow:
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g).text(org, txt, font=fnt, fill=glow, stroke_width=stroke + 6, stroke_fill=glow)
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(18)))
    if shadow:
        s = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(s).text((org[0], org[1] + 8), txt, font=fnt, fill=(0, 0, 0, 170), stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
        im.alpha_composite(s.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(im).text(org, txt, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return im

def paste_center(img, t_im, cx, cy, scale=1.0, alpha=1.0, rot=0):
    if scale != 1.0:
        t_im = t_im.resize((max(1, int(t_im.width*scale)), max(1, int(t_im.height*scale))), Image.BICUBIC)
    if rot: t_im = t_im.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 1.0:
        a = t_im.getchannel("A").point(lambda v: int(v * alpha)); t_im = t_im.copy(); t_im.putalpha(a)
    img.alpha_composite(t_im, (int(cx - t_im.width/2), int(cy - t_im.height/2)))

def ease_out_back(x):
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1)**3 + c1 * (x - 1)**2

# ---------------------------------------------------------------- captions
CAP_F = font("Montserrat-Black.ttf", 66)
CAP_Y = 1395
cache = {}
def word_img(w, hl):
    k = (w, hl)
    if k not in cache:
        cache[k] = text_img(w.upper(), CAP_F, SAFFRON if hl else (255, 255, 255), stroke=7, stroke_fill=(0, 0, 0))
    return cache[k]

def pages(seg):
    ws = seg["words"]; out = []; cur = []
    for w in ws:
        cur.append(w)
        n = sum(len(x["w"]) for x in cur)
        if len(cur) >= 4 or n > 17 or w["w"][-1] in ",.!?\"":
            out.append(cur); cur = []
    if cur: out.append(cur)
    # merge single trailing word page into previous if short
    return out

PAGES = []
for seg in timing:
    for p in pages(seg):
        PAGES.append(dict(words=p, s=p[0]["s"], e=p[-1]["e"]))
for i, p in enumerate(PAGES):  # extend display until next page (max 0.6s gap)
    nxt = PAGES[i+1]["s"] if i + 1 < len(PAGES) else DUR
    p["e2"] = min(nxt, p["e"] + 0.6)

def layout(words, maxw=930):
    lines = [[]]; lw = 0; sp = 4
    for w in words:
        im = word_img(w["w"], False)
        ww = im.width - 80
        if lines[-1] and lw + ww + 22 > maxw:
            lines.append([]); lw = 0
        lines[-1].append(w); lw += ww + 22
    return lines

def draw_captions(img, t):
    for p in PAGES:
        if p["s"] - 0.05 <= t < p["e2"]:
            lines = layout(p["words"])
            lh = 92
            y0 = CAP_Y - (len(lines) - 1) * lh / 2
            for li, ln in enumerate(lines):
                ims = [word_img(w["w"].replace('"', ''), w["s"] <= t < w["e"] + 0.02) for w in ln]
                tot = sum(im.width - 80 for im in ims) + 22 * (len(ims) - 1)
                x = W/2 - tot/2
                for w, im in zip(ln, ims):
                    ww = im.width - 80
                    dt = t - w["s"]
                    if dt >= -0.04:
                        k = min(1, max(0, (dt + 0.04) / 0.14))
                        sc = 0.85 + 0.15 * ease_out_back(k)
                        if w["s"] <= t < w["e"]: sc *= 1.06
                        paste_center(img, im, x + ww/2, y0 + li*lh, sc, 0.5 + 0.5 * min(1, k*1.6))
                    else:
                        paste_center(img, im, x + ww/2, y0 + li*lh, 0.85, 0.5 * min(1, (t - p["s"] + 0.05) / 0.12))
                    x += ww + 22
            return

# ---------------------------------------------------------------- big keywords
KW = json.load(open(os.path.join(ROOT, "keywords.json")))
KW_F = {"anton": lambda s: font("Anton.ttf", s), "cinzel": lambda s: font("Cinzel-Black.ttf", s)}
kwcache = {}
def draw_keywords(img, t):
    for k in KW:
        s, e = k["s"], k["e"]
        if s <= t < e:
            key = (k["text"], k.get("size", 190), k.get("font", "anton"))
            if key not in kwcache:
                col = tuple(k.get("color", SAFFRON))
                fn = KW_F[k.get("font", "anton")](k.get("size", 190))
                imgs = [text_img(line, fn, col, stroke=4, stroke_fill=(40, 10, 0), glow=tuple(k.get("glow",(255, 90, 0, 150)))) for line in k["text"].split("\n")]
                kwcache[key] = imgs
            imgs = kwcache[key]
            x = min(1, (t - s) / 0.28)
            sc = 1.6 - 0.6 * ease_out_back(x) if x < 1 else 1 + (t - s - 0.28) * 0.03
            al = min(1, x * 2) * min(1, (e - t) / 0.2)
            cy = k.get("y", 560)
            hsum = sum(i.height - 80 for i in imgs)
            yy_ = cy - hsum / 2
            for im in imgs:
                ih = im.height - 80
                paste_center(img, im, W/2, yy_ + ih/2, sc, al, k.get("rot", 0))
                yy_ += ih * 0.98

# ---------------------------------------------------------------- header
HDR = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
dh = ImageDraw.Draw(HDR)
dh.rectangle((60, 92, 68, 150), fill=(230, 40, 30))
dh.text((86, 88), "UNTOLD STORIES", font=font("Montserrat-ExtraBold.ttf", 30), fill=(255, 255, 255))
dh.text((86, 122), "of Hanuman", font=font("Cinzel-Bold.ttf", 26), fill=SAFFRON)

# ---------------------------------------------------------------- main loop
bases = {}
def scene_at(t):
    for i, sc in enumerate(SCENES):
        if sc["s"] <= t < sc["e"]: return i, sc
    return len(SCENES) - 1, SCENES[-1]

def frame(t):
    i, sc = scene_at(t)
    if i not in bases:
        bases[i] = build_base(sc)
        for j in list(bases):
            if j < i - 1: del bases[j]
    base = bases[i]
    p = (t - sc["s"]) / (sc["e"] - sc["s"])
    p = p * p * (3 - 2 * p) * 0.6 + p * 0.4
    z0, z1 = sc.get("zoom", (1.0, 1.12))
    z = z0 + (z1 - z0) * p
    # punch-in at cut
    dtc = t - sc["s"]
    if i > 0 and dtc < 0.3: z *= 1 + 0.08 * (1 - dtc / 0.3) ** 2
    cw, ch = W * SS / z / SS * SS / SS, 0
    cw = base.width / z; ch = base.height / z
    px, py = sc.get("pan", (0, 0))
    cx = base.width / 2 + px * p * (base.width - cw) / 2
    cy = base.height / 2 + py * p * (base.height - ch) / 2
    sh = sc.get("shake", 0)
    for (a, b, amp) in sc.get("shakes", []):
        if a <= t < b: sh = max(sh, amp * (1 - (t - a) / (b - a)))
    if sh:
        cx += math.sin(t * 91) * sh * 1.2; cy += math.cos(t * 77) * sh
    box = (cx - cw/2, cy - ch/2, cx + cw/2, cy + ch/2)
    fr = base.resize((W, H), Image.BILINEAR, box=box)
    a = np.asarray(fr).astype(np.float32) * DARK
    if sc.get("tint"):
        r, g, b, k = sc["tint"]; a = a * (1 - k) + np.array([r, g, b], np.float32) * (a.mean(-1, keepdims=True) / 255) * k
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    draw_embers(img, t)
    img.alpha_composite(HDR)
    draw_keywords(img, t)
    draw_captions(img, t)
    # flash at cuts
    if i > 0 and dtc < 0.18 and sc.get("flash", True):
        fl = Image.new("RGBA", (W, H), (255, 240, 210, int(170 * (1 - dtc / 0.18))))
        img.alpha_composite(fl)
    # fade in / out
    fade = min(1, t / 0.35, (DUR - t) / 0.5)
    out = img.convert("RGB")
    if fade < 1: out = Image.eval(out, lambda v: int(v * max(0, fade)))
    # progress bar
    dr = ImageDraw.Draw(out); dr.rectangle((0, H - 10, int(W * t / DUR), H), fill=SAFFRON)
    return out

if PREVIEW:
    for t in PREVIEW:
        frame(t).save(os.path.join(ROOT, "prev", f"p_{t:05.2f}.jpg"), quality=88)
    sys.exit()

n = int(DUR * FPS)
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
for f in range(n):
    ff.stdin.write(frame(f / FPS).tobytes())
    if f % 150 == 0: print("frame", f, "/", n, flush=True)
ff.stdin.close(); ff.wait()
print("done")
