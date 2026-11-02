# -*- coding: utf-8 -*-
r"""한글 글자 그림(시험): 원본 그림의 잉크 범위·색을 재서 같은 칸에 다시 그림 — 글자 크기 → 장평 순으로 맞춤"""
import os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = r'C:\claude\utils\font\nanum-gothic\NanumGothicBold.ttf'; SS = 4


def probe(a):
    """RGBA → 잉크 가면(밝은 글자), 줄 범위, 글자색, 바깥 그림자색"""
    al = a[..., 3] > 40; lum = a[..., :3].mean(2)
    ink = al & (lum > 140); rows = np.nonzero(ink.sum(1))[0]
    return ink, rows


def text_img(t, size, sx):
    f = ImageFont.truetype(F, size * SS); w = int(f.getlength(t)) + 8 * SS; h = int(size * 1.6) * SS
    im = Image.new('L', (w, h)); ImageDraw.Draw(im).text((2 * SS, h // 2), t, font=f, fill=255, anchor='lm')
    a = np.asarray(im); xs = np.nonzero(a.any(0))[0]
    im = im.crop((xs.min(), 0, xs.max() + 1, h)); nw = max(1, int(im.width * sx / SS))
    return im.resize((nw, h // SS), Image.LANCZOS)


def fit(t, maxw, size, minsize=11, minsx=0.72):
    for s in range(size, minsize - 1, -1):
        g = text_img(t, s, 1.0)
        if g.width <= maxw: return g, s, 1.0
    s = minsize if False else size
    for s in (size, size - 1, size - 2):
        g = text_img(t, s, 1.0); sx = maxw / g.width
        if sx >= minsx: return text_img(t, s, sx), s, sx
    g = text_img(t, minsize, 1.0); sx = maxw / g.width
    return text_img(t, minsize, sx), minsize, sx


def bands(ink):
    r = ink.sum(1) > 0; out = []; y = 0; h = len(r)
    while y < h:
        if r[y]:
            e = y
            while e + 1 < h and r[e + 1]: e += 1
            if e - y >= 6: out.append((y, e + 1))
            y = e + 1
        else: y += 1
    return out


RED = ('자동 브레이크', '브레이크', '마스콘', 'ATC', '감점되지 않습니다', '감점됩니다', '없습니다')


def render(a, lines, shadow=(8, 10, 30, 255), center=False):
    """원본 줄 위치·왼쪽 시작·글자색을 재서 다시 그림. 판(불투명)이면 글자만 지우고 상자·아이콘을 남김, 글자 전용 띠면 통째로 지움"""
    h, w = a.shape[:2]; rgb = a[..., :3].astype(int); sat = rgb.max(2) - rgb.min(2); al = a[..., 3]; opq = al > 60
    _f = (al > 200); _nl = _f & (rgb.mean(2) < 170)
    solid = _f.mean() > 0.9 or (_f.mean() > 0.75 and _nl.any() and np.median(sat[_nl]) > 60); red = (rgb[..., 0] > 170) & (rgb[..., 1] < 110) & opq; yel = (rgb[..., 0] > 170) & (rgb[..., 1] > 130) & (rgb[..., 2] < 110) & opq
    ic = yel.copy() if solid else np.zeros(yel.shape, bool)
    if not solid:
        ink = opq.copy(); mono = len(rgb[opq]) and rgb[opq].std(0).max() < 12
        lit = opq & (rgb.mean(2) > 120); outline = lit.any() and (opq & (rgb.mean(2) < 70)).sum() > lit.sum() * 0.35
        if lit.any() and not mono: ink0 = lit
    else:
        ink = opq & (rgb.mean(2) > 120) & (sat < 60) | red; mono = False
    icx = int(np.nonzero(ic.any(0))[0].max()) + 3 if ic.sum() > 20 and np.nonzero(ic.any(0))[0].max() < 40 else 0
    if icx: ink[:, :icx] = False
    framed = solid and (rgb[1:-1, 1:3].mean(1) > 60).mean() > 0.6 and (rgb[1:-1, -3:-1].mean(1) > 60).mean() > 0.6   # 테두리 있는 상자만 가장자리 보호
    if framed: ink[:6] = ink[-6:] = False; ink[:, :6] = ink[:, -6:] = False
    B = bands(ink); pure = (locals().get('ink0', ink)) & ~red & ~yel
    col = tuple(int(x) for x in np.percentile(a[pure][:, :3], 90, axis=0)) if pure.any() else (255, 255, 255)
    hasred = int((ink & red).sum()) > 12 and pure.any(); hasyel = (not solid) and yel.sum() > 30 and pure.sum() > yel.sum() * 1.5
    bg = a.copy()
    if solid:
        m = ink.copy(); p = np.pad(m, 2)
        for dy in range(-2, 3):
            for dx in range(-2, 3): m = m | np.roll(np.roll(p, dy, 0), dx, 1)[2:-2, 2:-2]
        if icx: m[:, :icx] = False
        if framed: m[:3] = m[-3:] = False; m[:, :3] = m[:, -3:] = False
        rest = a[(al > 200) & ~m]; bg[m] = np.median(rest, axis=0).astype(np.uint8) if len(rest) else (0, 0, 0, 255)
    else: bg[:] = 0
    im = Image.fromarray(bg); n = len(lines); info = []
    if len(B) == n: ys = [(u + v) // 2 for u, v in B]
    elif B:
        c0, c1 = B[0][0], B[-1][1]; lh = max(15, min(23, (c1 - c0) / n if n > 1 else 20)); mid = (c0 + c1) / 2; ys = [int(mid + (i - (n - 1) / 2) * lh) for i in range(n)]
    else: ys = [h // 2]
    bh = min((v - u for u, v in B), default=16); size = max(11, min(bh + 2, 20))
    if n > 1 and not B: size = 12
    if n > 1: size = min(size, int(h / n) - 3)
    for i, t in enumerate(lines):
        bi = B[min(i, len(B) - 1)] if B else (0, h); row = ink[bi[0]:bi[1]]; cols = np.nonzero(row.any(0))[0]; L = int(cols.min()) if len(cols) else 2
        if not t.strip(): continue
        g, sz, sx = fit(t, w - L - 2, size); info.append((sz, round(sx, 2)))
        y = ys[i] - g.height // 2
        if center: L = (w - g.width) // 2                                        # 줄마다 그림 가운데(세이브 안내문, 하스피 2026-11-02)
        elif n == 1 and len(cols):                                                 # 한 줄 띠: 원문보다 짧으면 원문 범위 가운데(하스피 지시 2026-11-01)
            R_ = int(cols.max()) + 1
            if g.width < R_ - L: L = (L + R_ - g.width) // 2
        if not mono:
            sh = Image.new('RGBA', g.size, shadow)
            for ox, oy in (((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1)) if (not solid and locals().get('outline') and sz >= 14) else ((1, 1),)): im.paste(sh, (L + ox, y + oy), g)
        fl = Image.new('RGBA', g.size, col + (255,))
        if hasred or hasyel:
            f = ImageFont.truetype(F, sz); tot = f.getlength(t) or 1
            for tok in RED:
                k = t.find(tok)
                if k >= 0:
                    x0 = int(f.getlength(t[:k]) / tot * g.width); x1 = int(f.getlength(t[:k + len(tok)]) / tot * g.width)
                    c2 = (235, 40, 30, 255) if hasred else (250, 200, 60, 255); fl.paste(c2, (x0, 0, x1, g.height)); break
        im.paste(fl, (L, y), g)
    return np.asarray(im), info
