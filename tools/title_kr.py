# -*- coding: utf-8 -*-
r"""큰 제목·메뉴 버튼 글자(시험) — 테두리·기울임·세로 그라데이션을 원본에서 재서 한글로"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
EB = r'C:\claude\utils\font\nanum-gothic\NanumGothicExtraBold.ttf'; B = r'C:\claude\utils\font\nanum-gothic\NanumGothicBold.ttf'; SS = 4


def mask(t, size, font=EB, shear=0.0, sp=0):
    f = ImageFont.truetype(font, size * SS); W = int(sum(f.getlength(c) + sp * SS for c in t)) + 16 * SS; H = int(size * 1.7) * SS
    im = Image.new('L', (W, H)); d = ImageDraw.Draw(im); x = 4 * SS
    for c in t: d.text((x, H // 2), c, font=f, fill=255, anchor='lm'); x += f.getlength(c) + sp * SS
    if shear: im = im.transform(im.size, Image.AFFINE, (1, shear, -shear * H / 2, 0, 1, 0), Image.BICUBIC)
    if ROUND:
        im = im.filter(ImageFilter.GaussianBlur(ROUND * SS)).point(lambda v: min(255, max(0, (v - 110) * 6)))
    bb = im.getbbox(); im = im.crop(bb)
    return im.resize((max(1, im.width // SS), max(1, im.height // SS)), Image.LANCZOS)


JUA = r'C:\claude\utils\font\jua\Jua-Regular.ttf'
ROUND = 0                                                                        # 획 끝 둥글리기(4배 그림에서 번짐 후 문턱)


def fit(t, w, h, font=EB, shear=0.0):
    for s in range(int(h * 1.2), 7, -1):
        m = mask(t, s, font, shear)
        if m.width <= w and m.height <= h: return m
    return m.resize((min(m.width, w), min(m.height, h)))


def grow(m, n):
    return m.filter(ImageFilter.MaxFilter(2 * n + 1)) if n else m


def grad(size, cols):
    h = size[1]; a = np.zeros((h, size[0], 3), np.uint8)
    for y in range(h):
        p = y / max(1, h - 1) * (len(cols) - 1); i = min(int(p), len(cols) - 2) if len(cols) > 1 else 0
        c = np.array(cols[i]) * (1 - (p - i)) + np.array(cols[min(i + 1, len(cols) - 1)]) * (p - i); a[y] = c
    return Image.fromarray(a).convert('RGBA')


def draw(canvas, m, x, y, fill, stroke=None, sw=1, shadow=None):
    pad = sw + 2; mm = Image.new('L', (m.width + pad * 2, m.height + pad * 2)); mm.paste(m, (pad, pad))
    if shadow: canvas.paste(Image.new('RGBA', mm.size, shadow + (255,)), (x - pad + 1, y - pad + 1), grow(mm, sw))
    if stroke: canvas.paste(Image.new('RGBA', mm.size, stroke + (255,)), (x - pad, y - pad), grow(mm, sw))
    f = grad(m.size, fill) if isinstance(fill, list) else Image.new('RGBA', m.size, fill + (255,))
    canvas.paste(f, (x, y), m)


def title(a, t, style):
    t = t.replace('·', ' ')
    h, w = a.shape[:2]; im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); S = STY[style]
    m = fit(t, w - 6, h - 4 - 2 * S.get('sw', 1), S.get('font', EB), S.get('shear', 0))
    xs = np.nonzero((a[..., 3] > 60).any(0))[0]; L, R = (int(xs.min()), int(xs.max()) + 1) if len(xs) else (3, w - 3)
    x = max(1, (L + R - m.width) // 2)                                           # 원문 범위 가운데
    draw(im, m, x, (h - m.height) // 2, S['fill'], S.get('stroke'), S.get('sw', 1), S.get('shadow')); return np.asarray(im)


STY = {'navy': dict(font=JUA, fill=(30, 44, 110), stroke=(225, 232, 245), sw=1, shadow=(8, 12, 40)), 'light': dict(font=JUA, fill=[(250, 252, 255), (150, 190, 235)], stroke=(16, 30, 80), sw=1, shadow=(6, 10, 40)),
       'yellow': dict(fill=[(255, 255, 170), (250, 205, 40)], stroke=(70, 40, 10), sw=1, shear=0.22), 'white': dict(fill=[(255, 255, 255), (200, 205, 215)], stroke=(40, 44, 60), sw=1, shear=0.22),
       'gray': dict(fill=[(178, 178, 182), (128, 128, 134)], stroke=(28, 30, 38), sw=1, shear=0.22)}   # 포즈 메뉴 비선택(원본 회색 기울임)


EFONT = EB
REF = {}
REFBAR = {}


def menu_sheet(a, labels, eng, font=JUA):
    """224×290 메뉴 판: 칸 58 줄, 막대 y 19~55 — 막대를 오른쪽 깨끗한 열로 다시 깔고 영어·한글을 얹음"""
    a0 = a.copy(); a = a.copy(); im = None; mode = eng[0] == 'Driving Mode'
    _o = a0[a0[..., 3] > 200][:, :3].astype(int); _o = _o[(_o.max(1) - _o.min(1)) > 50]; _m = np.median(_o, axis=0); sheet_hue = 'B' if _m[2] > _m[1] + 30 else ('L' if _m[0] > 90 else 'G')
    for i, (ko, en) in enumerate(zip(labels, eng)):
        y0 = 19 + 58 * i; y1 = 56 + 58 * i; top = 58 * i
        lo = np.nonzero(a[y1 - 2, :, 3] > 128)[0].min(); slope = 0.28
        a[top:y0] = 0
        for k, y in enumerate(range(y0, y1)):
            hue = sheet_hue
            if mode:
                seg = a0[y, 186:204]; op = seg[seg[:, 3] > 200]
                if not len(op): a[y, :206] = 0; continue
                c = np.median(op, axis=0).astype(np.uint8); REF[(hue, k)] = c
            else:
                c = REF.get((hue, k))
                if c is None: a[y, :206] = 0; continue
            lx = int(lo + (y1 - 2 - y) * slope); a[y, :lx] = 0
            for x in range(lx, 206):
                if x < 150: a[y, x] = c if (x < 110 or a[y, x, 3] > 128) else a[y, x]
                elif a0[y, x, 3] > 128 and (x < 192 or a0[y, x, :3].mean() > float(c[:3].mean()) + 18 or (k < 16 and x < 205) or not mode): a[y, x] = c   # 오른쪽 둥근 끝·테두리는 원본 유지, 영어 글자만 지움
        if mode and i == 0: REFBAR[sheet_hue] = a[19:56].copy()
        if not mode and sheet_hue in REFBAR: a[y0:y1] = REFBAR[sheet_hue]
    im = Image.fromarray(a)
    bar = (150, 185, 235)
    for i, (ko, en) in enumerate(zip(labels, eng)):
        y0 = 19 + 58 * i; f = ImageFont.truetype(EFONT, 19); d = ImageDraw.Draw(im); w = d.textlength(en, font=f)
        d.text((118 - w / 2, y0 + 21), en, font=f, fill=bar + (255,), anchor='lm')
        m = fit(ko, 150, 28, font, 0.05); draw(im, m, 4, 58 * i + 4, (28, 40, 110), (235, 240, 250), 1, (8, 12, 40))
    return np.asarray(im)
