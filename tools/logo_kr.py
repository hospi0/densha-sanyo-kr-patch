# -*- coding: utf-8 -*-
r"""제목 로고(menu/nTplCommon.dat 067AFC0, 560×166 C8) 한글화 — 2026-11-02 하스피 «타이틀 작업, PS2 버전 참고»
  PS2 전차로 파이널·여정편 tools/logo_kr.py 방식: 블랙한산스·4배로 그려 줄임·오른쪽 기울임 0.15.
  電車→전차(빨강 줄 색) · で→로(청록) · 新幹線→신칸센(파랑) · 山陽新幹線編→산요 신칸센편(검정). GO!·EX·열차 그림·®은 그대로.
  원본 층(화소 실측): 채움 · 안쪽 흰 2px · 검정 3px · 바깥 흰 2px.
  python tools/logo_kr.py → work/gfxprev/logo.png(원본|한글, 2배)"""
import os, sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
FONT = r'C:\claude\utils\font\logo\BlackHanSans.ttf'
SS = 4; W, H = 560, 166; SHEAR = 0.15
# (글, 채움 상자 x0,y0,x1,y1, 층 (안쪽 흰, 검정, 바깥 흰) px)
BIG = ('전차', (78, 7, 210, 72), (2, 3, 2))
SMALL = ('로', (207, 40, 232, 69), (1.5, 2, 1.5))
SHIN = ('신칸센', (127, 86, 264, 126), (1.5, 2.5, 2))
SUB = ('산요 신칸센편', (118, 132, 253, 159), (1.5, 2.5, 2))
ERASE = [((60, 0, 236, 85), 'top'), ((124, 85, 266, 131), 'mid'), ((110, 126, 262, 166), 'low')]


def mask_text(text, box, shear=SHEAR, stretch=False):
    x0, y0, x1, y1 = box; HH = (y1 - y0) * SS; f = ImageFont.truetype(FONT, HH * 2); gl = []; sp = []
    for ch in text:
        if ch == ' ': sp.append(len(gl)); continue
        l, t, r, b = f.getbbox(ch); im = Image.new('L', (r - l + 8, b - t + 8)); ImageDraw.Draw(im).text((4 - l, 4 - t), ch, font=f, fill=255)
        a = np.array(im); ys = np.nonzero(a.max(1))[0]; xs = np.nonzero(a.max(0))[0]; a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        gl.append(np.array(Image.fromarray(a).resize((max(1, int(round(a.shape[1] * HH / a.shape[0]))), HH), Image.LANCZOS)))
    gap = 1 * SS; spw = HH // 4
    Wd = sum(g.shape[1] for g in gl) + gap * (len(gl) - 1) + spw * len(sp) + int(shear * HH)
    sx = (x1 - x0) * SS / Wd if stretch else min(1.0, (x1 - x0) * SS / Wd); out = np.zeros((H * SS, W * SS), np.uint8)
    x = x0 * SS + int(round(((x1 - x0) * SS - Wd * sx) / 2)); Y0 = y0 * SS
    for i, g in enumerate(gl):
        if i in sp: x += int(round(spw * sx))
        w = max(1, int(round(g.shape[1] * sx))); g = np.array(Image.fromarray(g).resize((w, HH), Image.LANCZOS))
        for yy in range(HH):
            dx = int(round(shear * sx * (HH - 1 - yy))); out[Y0 + yy, x + dx:x + dx + w] = np.maximum(out[Y0 + yy, x + dx:x + dx + w], g[yy])
        x += w + int(round(gap * sx))
    return out >= 128


def rows(a, box, sel):
    """채움 줄 색: 상자 안 sel 화소의 줄마다 최빈 색(없는 줄은 가까운 줄)"""
    x0, y0, x1, y1 = box; out = {}
    for y in range(y0, y1):
        r = a[y, x0:x1][sel[y, x0:x1]][:, :3]
        if len(r) >= 3:
            u, n = np.unique(r, axis=0, return_counts=True); out[y] = u[n.argmax()].astype(float)
    ks = sorted(out); return np.array([out[min(ks, key=lambda k: abs(k - y))] for y in range(H)])


def ring(m, r):
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(2 * r * SS) + 1, int(2 * r * SS) + 1)); return cv2.dilate(m.astype(np.uint8), k).astype(bool)


def layer(m, fill, lay):
    """4배 RGBA(0~1): 바깥 흰 → 검정 → 안쪽 흰 → 채움(줄 색 또는 한 색)"""
    w1, w2, w3 = lay; img = np.zeros(m.shape + (4,))
    i1 = ring(m, w1); i2 = ring(i1, w2); i3 = ring(i2, w3)
    img[i3] = (1, 1, 1, 1); img[i2] = (0, 0, 0, 1); img[i1] = (1, 1, 1, 1)
    f = np.repeat(fill, SS, 0)[:, None, :] / 255.0 if fill.ndim == 2 else np.array(fill)[None, None] / 255.0
    col = np.broadcast_to(f, m.shape + (3,)); img[m, :3] = col[m]; img[m, 3] = 1
    return img


def down(img):
    a = img.reshape(H, SS, W, SS, 4); al = a[..., 3]; A = al.mean((1, 3))
    C = (a[..., :3] * al[..., None]).sum((1, 3)) / np.maximum(al.sum((1, 3)), 1e-6)[..., None]
    return np.concatenate([C, A[..., None]], -1)


def over(base, top):
    ta = top[..., 3:4]; ba = base[..., 3:4]; oa = ta + ba * (1 - ta)
    oc = (top[..., :3] * ta + base[..., :3] * ba * (1 - ta)) / np.maximum(oa, 1e-6); return np.concatenate([oc, oa], -1)


def make(a):
    a = a.copy(); rgb = a[..., :3].astype(int); r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]; op = a[..., 3] > 0
    red = op & (r > 120) & (g < 90) & (b < 90); green = op & (g > r + 30) & (g > b + 10)
    teal = op & (b > r + 40) & (g > r + 30) & (g >= 50); blue = op & (b > r + 60) & (b > g + 50)
    X = np.arange(W)[None, :]; Y = np.arange(H)[:, None]
    fills = {'big': rows(a, BIG[1], red), 'small': rows(a, (200, 35, 236, 72), teal), 'shin': rows(a, SHIN[1], blue)}
    # 지우기: 상자 안 글자(흰 아닌 화소)를 3px 넓혀서(바깥 흰 테 포함) 투명. 위 상자는 G(초록 7px 안) 보존
    dG = cv2.distanceTransform((~green).astype(np.uint8), cv2.DIST_L2, 3)
    er = np.zeros((H, W), bool)
    for (x0, y0, x1, y1), tag in ERASE:
        box = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)
        ink = box & op & (rgb.min(2) < 200) & ~((rgb.max(2) - rgb.min(2) < 20) & (rgb.min(2) > 120))   # 회색 열차 선은 글자 아님
        if tag == 'top': ink &= ~(dG <= 7)
        e = ring(ink, 0) if False else cv2.dilate(ink.astype(np.uint8), np.ones((7 if tag == 'top' else 3, 7 if tag == 'top' else 3), np.uint8)).astype(bool) & box
        if tag == 'top': e &= ~((dG <= 7) & (X >= 228))
        er |= e
    base = a.astype(float) / 255.0
    # 아래 두 줄(열차 그림과 붙은 곳)은 원본 글자 자리를 흰색으로 — 투명으로 지우면 열차 몸통이 뚫린다. 위 줄만 투명.
    top = ((Y < 85) | ((Y < 89) & (X >= 140))) & (X < 236);   # 電車 아래 바깥 흰 테가 신칸센 위로 남던 줄
    base[er & top] = 0; base[er & ~top & op] = (1, 1, 1, 1); base[er & ~top & ~op] = 0
    for t, box, lay, key in ((SHIN[0], SHIN[1], SHIN[2], 'shin'), (SUB[0], SUB[1], SUB[2], None), (BIG[0], BIG[1], BIG[2], 'big'), (SMALL[0], SMALL[1], SMALL[2], 'small')):
        m = mask_text(t, box, stretch=(t == SHIN[0]));   # 신칸센은 상자 폭까지 늘림 — 원래 한자 자리 흰 메움 가리기(하스피 2026-11-02)
        fill = fills[key] if key else np.array([8.0, 8.0, 8.0])
        base = over(base, down(layer(m, fill, lay)))
    return (base * 255).round().clip(0, 255).astype(np.uint8)


if __name__ == '__main__':
    p = os.path.join(ROOT, 'work', 'tex', 'menu', 'nTplCommon.dat', '067AFC0_0_560x166_f9.png')
    a = np.asarray(Image.open(p).convert('RGBA')); n = make(a)
    s = np.concatenate([a, np.full((6, W, 4), 255, np.uint8), n], 0)
    im = Image.fromarray(s); bg = Image.new('RGBA', im.size, (40, 44, 70, 255)); bg.alpha_composite(im)
    q = os.path.join(ROOT, 'work', 'gfxprev', 'title_logo.png'); bg.resize((im.width * 2, im.height * 2), Image.NEAREST).save(q); print(q)
