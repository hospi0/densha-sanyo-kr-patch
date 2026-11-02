# -*- coding: utf-8 -*-
r"""칸으로 잘라 쓰는 그림·판 그림 개별 처리(눈금으로 잰 좌표, 2026-11-02)"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import render_kr as R, title_kr as T


def wipe(o, box, clear=False):
    """상자 안을 줄마다 좌우 가장자리 사이 보간으로 지움 — 판 무늬 유지"""
    x0, y0, x1, y1 = box; x0 = max(1, x0); x1 = min(o.shape[1] - 1, x1)
    if clear: o[y0:y1, x0:x1] = 0; return                                        # 글자 전용 띠는 투명으로
    for y in range(y0, y1):
        l, r = o[y, x0 - 1].astype(float), o[y, x1].astype(float); n = x1 - x0
        for i in range(n): o[y, x0 + i] = (l + (r - l) * (i + 1) / (n + 1)).astype(np.uint8)


def put(im, g, x, y, col, sh=(8, 10, 30), ring=False):
    if sh:
        S = Image.new('RGBA', g.size, tuple(sh) + (255,))
        for ox, oy in (((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1)) if ring else ((1, 1),)): im.paste(S, (x + ox, y + oy), g)
    im.paste(Image.new('RGBA', g.size, tuple(col) + (255,)), (x, y), g)


GAL = r'C:\claude\utils\font\Galmuri-v2.40.3' + chr(92)


def pix(c, name, size):
    f = ImageFont.truetype(GAL + name, size); i = Image.new('L', (size + 6, size + 6)); d = ImageDraw.Draw(i); d.fontmode = '1'; d.text((2, 2), c, font=f, fill=255); return i.crop(i.getbbox())


def ptext(t, name, size, gap=1):
    gs = [pix(c, name, size) for c in t]; h = max(g.height for g in gs); i = Image.new('L', (sum(g.width + gap for g in gs), h)); x = 0
    for g in gs: i.paste(g, (x, h - g.height)); x += g.width + gap
    return i


def cond(t):
    """긴 탭 글자: 좁은 글꼴을 1px 겹쳐 굵게"""
    gs = [pix(c, 'Galmuri11-Condensed.ttf', 12) for c in t]; h = max(g.height for g in gs); i = Image.new('L', (sum(g.width + 3 for g in gs), h)); x = 0
    for g in gs:
        for dx in (0, 1): i.paste(255, (x + dx, h - g.height), g)
        x += g.width + 3
    return i.crop(i.getbbox())


def vtext(im, t, box, col, sh=None):
    """세로 글: 칸 높이가 모자라면 두 줄로 — 작은 글자는 비트맵 글꼴(갈무리)"""
    x0, y0, x1, y1 = box; W, H = x1 - x0, y1 - y0; n = len(t); st = H / n
    if st >= 12:
        for i, c in enumerate(t):
            g = R.text_img(c, min(14, W - 1), 1.0); g = g.crop(g.getbbox()); put(im, g, x0 + (W - g.width) // 2, int(y0 + st * (i + .5) - g.height / 2), col, sh)
        return
    if st >= 10:
        for i, c in enumerate(t):
            g = pix(c, 'Galmuri9.ttf', 10); put(im, g, x0 + (W - g.width) // 2, int(y0 + st * (i + .5) - g.height / 2), col, sh)
        return
    rows = (n + 1) // 2; st = H / rows; name, sz = ('Galmuri9.ttf', 10) if W >= 20 and st >= 10 else ('Galmuri7.ttf', 8)
    for i, c in enumerate(t):
        col_ = i // rows; g = pix(c, name, sz); put(im, g, x0 + (W // 2 if col_ else 0) + (W // 2 - g.width) // 2, int(y0 + st * (i % rows + .5) - g.height / 2), col, None)


def rowfill(o, box):
    """글자 칸을 줄마다 가장 흔한 색으로 — 탭 줄무늬 유지, 칸 경계 사선은 상자 밖에 둘 것"""
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        u, n = np.unique(o[y, x0:x1].reshape(-1, 4), axis=0, return_counts=True); o[y, x0:x1] = u[n.argmax()]


LAST = [None]


def mark(o, box, ref, t, size, col, c):
    """상자 안 글자를 같은 줄 ref 열 색으로 지우고 중심 c 에 씀 → LAST[0]"""
    x0, y0, x1, y1 = box
    for y in range(y0, y1): o[y, x0:x1] = o[y, ref]
    im = Image.fromarray(o); g = R.text_img(t, size, 1.0); g = g.crop(g.getbbox()); put(im, g, c[0] - g.width // 2, c[1] - g.height // 2, col, (8, 10, 30)); LAST[0] = np.asarray(im).copy()


def bright(a, box, q=92):
    x0, y0, x1, y1 = box; r = a[y0:y1, x0:x1]; r = r[r[..., 3] > 100][:, :3]
    return tuple(int(v) for v in np.percentile(r, q, axis=0)) if len(r) else (255, 255, 255)


def labels(a, items, col=None, sh=(8, 10, 30), ring=False, size=None, clear=False):
    """[(상자, 글)] — 상자 지우고 가운데에 맞춰 씀(색은 상자별 원본에서)"""
    out = a.copy(); cols = [col or bright(a, b) for b, t in items]
    for b, t in items: wipe(out, b, clear)
    im = Image.fromarray(out)
    for (b, t), c in zip(items, cols):
        bw, bh = b[2] - b[0], b[3] - b[1]
        for z in range(size or min(bh + 1, 20), 7, -1):
            g = R.text_img(t, z, 1.0); bb = g.getbbox()
            if g.width <= bw - 1 and (bb[3] - bb[1]) <= bh: break
        g = g.crop((0, bb[1], g.width, bb[3]))
        put(im, g, b[0] + (bw - g.width) // 2, b[1] + (bh - g.height) // 2, c, sh, ring)
    return np.asarray(im)


CELLS = {'162x20': [((1, 0, 101, 20), 'Wii 리모컨'), ((103, 0, 161, 20), 'TV')],   # 소리 출력 선택지: 게임이 원문 낱말 범위로 잘라 씀(2026-11-02)
         '398x22': [((223, 0, 258, 22), '도착'), ((265, 0, 300, 22), '현재'), ((307, 0, 342, 22), '통과'), ((350, 0, 384, 22), '시각')],   # 원문 한자 흰 획 범위 안쪽 — 게임이 잘라 쓰는 칸에 옆 글자 획이 끼던 것(2026-11-02)
         '798x24': [((588, 0, 626, 24), '끔'), ((630, 0, 672, 24), '비상'), ((672, 0, 714, 24), '해제')],
         '106x22': [((0, 0, 44, 22), '예'), ((44, 0, 105, 22), '아니요')],
         '150x20': [((0, 0, 39, 20), '정속'), ((39, 0, 78, 20), '정시'), ((78, 0, 150, 20), '포인트')],
         '108x28': [((0, 0, 27, 28), '빠름'), ((27, 0, 54, 28), '정시'), ((54, 0, 81, 28), '늦음'), ((81, 0, 108, 28), '통과')],
         '132x24': [((0, 0, 22, 24), '역'), ((22, 0, 66, 24), '출발'), ((66, 0, 131, 24), '량 편성')],
         '96x22': [((0, 0, 44, 22), '도착'), ((48, 0, 92, 22), '정차')],
         '244x20': [((148, 0, 228, 20), '성공 조건')], '246x24': [((189, 0, 227, 24), '남은'), ((228, 0, 245, 24), '체')],
         '372x20': [((150, 0, 224, 20), '정차역 수'), ((224, 0, 332, 20), '컨티뉴'), ((332, 0, 371, 20), '횟수')]}
JP_CELL = {'162x20': 'Wii', '398x22': '到着', '798x24': '切', '106x22': 'はい', '150x20': '定速', '108x28': '早定遅通', '132x24': '駅出発', '96x22': '到着', '244x20': '成功', '246x24': 'あと', '372x20': '停車駅数'}
SPLIT = {'運転中、どこかの景色': (266, '운전 중 어딘가의 풍경에 나타나는 것을', '체 찾아보자!'), '指示されたキャラクター': (187, '지시된 캐릭터를', '체 찾자!목표 캐릭터를 찾을 때마다 다음 목표가 바뀌어 가.'),
         '運転中に現れるを': (205, '운전 중 나타나는 것을 연속으로', '체 골라 보자!1체라도 놓치면 연속 기록이 끊겨서 처음 수로 돌아가 버려.')}
RD = (235, 40, 30); WH = (255, 255, 255)
LOOK = {'マスコンを に': [('마스콘', RD, 60), ('을', WH, None), ('에', WH, 178)], 'ブレーキを に': [('브레이크', RD, 60), ('를', WH, None), ('에', WH, 178)], '運転速度の目安は': None}


DESC = {'運転を中止して': (144, '운전을 중지하고'), '運転を始めた駅': (185, '운전을 시작한 역부터'), '画面に表示される': (266, '화면에 표시되는 계기 표시를'),   # 자르는 x = 원문 줄바꿈 글자 틈(실측). 일시정지·역간 세이브 설명은 한 줄(스샷 확인 2026-11-02)
        '運転中に流れる': (144, '운전 중에 흐르는'), '運転中に再生される': (350, '운전 중에 재생되는 사운드 설정을'), 'ボーナス獲得条件': (185, '보너스 획득 조건을')}
MENU = {'運転再開', '運転中止', '開始駅に戻る', 'メーター表示', 'セーブ', 'セープ', 'サウンド設定', 'ボーナス条件'}
MENU_SZ = {(104, 24), (102, 24), (144, 24), (138, 24), (68, 24), (88, 22), (86, 22), (122, 22), (116, 22), (58, 22)}


def left_align(n, x0=2):
    """포즈 메뉴 항목: 원본처럼 왼쪽 맞춤 — 선택/비선택 그림 위치가 원본과 같게"""
    xs = np.nonzero((n[..., 3] > 60).any(0))[0]
    if not len(xs) or xs.min() == x0: return n
    o = np.zeros_like(n); d = int(xs.min()) - x0; w = n.shape[1]
    o[:, :w - d] = n[:, d:] if d > 0 else o[:, :w - d]
    if d < 0: o[:, -d:] = n[:, :w + d]
    return o



def vib_button(a, t):
    """진동 설정 버튼(100×32, 밝은/어두운 버튼 둘): 남색 한자만 지우고(줄마다 버튼 바탕색) 같은 남색으로 한글(2026-11-02 하스피 «약중강»)"""
    o = a.copy(); rgb = a[..., :3].astype(int); lm = rgb.mean(2); op = a[..., 3] > 200
    navy = op & (lm < 110) & (rgb[..., 2] >= rgb[..., 0] + 45)                 # 글자 남색 b−r≥45 · 어두운 버튼 바탕은 b−r≈33
    im = None; cols = []
    for x0, x1 in ((10, 38), (58, 88)):
        ink = np.zeros_like(navy); ink[5:27, x0:x1] = navy[5:27, x0:x1]
        for y in range(3, 28):                                                   # 글자 둘레 밝은 테(줄 바탕보다 25↑ 밝은 화소)도 지울 것 — 강 위 찌꺼기(2026-11-02)
            rr = lm[y, x0:x1][op[y, x0:x1] & ~navy[y, x0:x1]]
            if len(rr):
                hl = op[y, x0:x1] & (lm[y, x0:x1] > np.median(rr) + 25)
                if hl.sum() <= 8: ink[y, x0:x1] |= hl
        ys, xs = np.nonzero(ink)
        if not len(ys): continue
        cols.append(np.median(a[ink][:, :3], axis=0)); bx = (int(xs.min()) - 3, int(ys.min()) - 2, int(xs.max()) + 4, int(ys.max()) + 3)   # 번짐까지
        import cv2
        near = cv2.dilate((navy | ink).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
        for y in range(bx[1], bx[3]):                                            # 줄마다 버튼 안 «글자에서 2px 이상 떨어진» 바탕 중앙값
            r_ = a[y, x0:x1][op[y, x0:x1] & ~near[y, x0:x1]]
            if not len(r_): r_ = a[y, bx[0] - 1:bx[0]]                              # 버튼 윗단(줄이 짧음): 상자 바로 왼쪽 화소
            if len(r_): o[y, bx[0]:bx[2]] = np.median(r_, axis=0).astype(np.uint8)
        cols[-1] = (cols[-1], ((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2), bx[3] - bx[1])
    im = Image.fromarray(o)
    for c, (cx, cy), hh in cols:
        m = T.fit(t, 22, min(17, hh), T.JUA); T.draw(im, m, int(cx - m.width / 2), int(cy - m.height / 2), (22, 28, 84), None, 0, None)   # 원본 남색(밝은·어두운 버튼 같은 색)
    return np.asarray(im)



def stn_name(a, t, size=15):
    """다이아 선택 «역 ～ 역» 이름: 게임은 원문 글자 폭에 맞춘 역별 위치로 놓는다 → 원문 잉크 범위 [L,R] 안에만.
    짧으면 그 범위 가운데(자간 안 벌림), 길면 장평(2026-11-02 하스피 — 그림 폭 꽉 채우기·자간 벌림은 ～ 에 붙어 틀렸음)"""
    h, w = a.shape[:2]; xs = np.nonzero((a[..., 3] > 60).any(0))[0]; L = int(xs.min()); W = int(xs.max()) + 1 - L
    for z in (size, size - 1, size - 2):
        g = R.text_img(t, z, 1.0)
        if g.width <= W: break
    if g.width > W: g = R.text_img(t, z, W / g.width)
    Lm = Image.new('L', (w, h)); Lm.paste(g, (L + (W - g.width) // 2, (h - g.height) // 2 + 1))
    out = np.zeros((h, w, 4), np.uint8); out[..., 0], out[..., 1], out[..., 2] = 24, 32, 90; out[..., 3] = np.asarray(Lm)
    return out



TITLE_SPLIT = {'ノーマルモード入門': [('노멀 모드', 3, 183), ('입문', 192, 246)],     # 일반 다이아에선 게임이 «入門» 앞(그림 x≈190, 스샷 실측)에서 잘라 씀 — 경계 양쪽에만(2026-11-02)
               'リアルモード入門': [('리얼 모드', 3, 155), ('입문', 164, 218)]}       # 원문 경계 157(노멀 185)에 같은 +5


def title_split(a, parts):
    """큰 제목을 낱말마다 정해진 범위에 — 모든 글자 같은 크기·장평 그대로(하스피 «전부 같은 크기»).
    크기 = 모든 낱말이 자기 범위에 들어가는 최대. 앞 낱말은 범위 오른쪽 끝에 붙여 낱말 사이가 보통 띄어쓰기처럼"""
    h, w = a.shape[:2]; S = T.STY['light']; sw = S.get('sw', 1); H = h - 4 - 2 * sw; font = S.get('font', T.EB); sh = S.get('shear', 0)
    for z in range(int(H * 1.2), 7, -1):
        ms = [T.mask(t, z, font, sh) for t, _, _ in parts]
        if all(m.height <= H and m.width <= x1 - x0 - 2 * sw for m, (_, x0, x1) in zip(ms, parts)): break
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for k, (m, (t, x0, x1)) in enumerate(zip(ms, parts)):
        x = x1 - sw - m.width if k < len(parts) - 1 else x0 + sw
        T.draw(im, m, x, (h - m.height) // 2, S['fill'], S.get('stroke'), sw, S.get('shadow'))
    return np.asarray(im)


HILITE = {'・ATCの予告': '없습니다', '・ATCブレーキが作動しても': '감점되지 않습니다', '・ATCブレーキが作動すると': '감점됩니다'}


def hilite(a, k, tok):
    """옵션 설명 작은 줄: 흰 글자 + 강조 낱말만 노랑(픽셀 글꼴, 줄 칸 16px)"""
    h, w = a.shape[:2]; im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ls = k.replace('・', '·').split('／')
    for n_, z in (('Galmuri11-Bold.ttf', 12), ('Galmuri11.ttf', 12), ('Galmuri9.ttf', 10)):
        f = ImageFont.truetype(GAL + n_, z)
        if max(f.getlength(t) for t in ls) + 2 <= w: break
    for i, t in enumerate(ls):
        m = Image.new('L', (w, 16)); d = ImageDraw.Draw(m); d.fontmode = '1'; x = 0 if i == 0 else 6; d.text((x, 1), t, font=f, fill=255)
        c = Image.new('RGBA', (w, 16), (255, 255, 255, 255)); j = t.find(tok)
        if j >= 0: c.paste((255, 231, 0, 255), (x + int(f.getlength(t[:j])), 0, x + int(f.getlength(t[:j + len(tok)])) + 1, 16))
        y = i * 16                                                               # 팔레트에 어두운 색이 없다 — 그림자 넣으면 노랗게 뭉침
        im.paste(c, (0, y), m)
    return np.asarray(im)


def hilite_pal(d, im):
    """원본 팔레트는 연한 색뿐 — 불투명 칸을 진짜 흰색·노란색으로(RGB5A3)"""
    n, f, o = im[4]
    for i in range(n):
        v = int.from_bytes(d[o + i * 2:o + i * 2 + 2], 'big')
        if v >> 15: d[o + i * 2:o + i * 2 + 2] = (0xFFFF if (v & 31) > 20 else 0xFF80).to_bytes(2, 'big')


def special(a, s, k):
    h, w = a.shape[:2]; sz = '%dx%d' % (w, h)
    for key, tok in HILITE.items():
        if s.startswith(key): return hilite(a, k, tok), '강조줄'
    if sz == '398x22' and JP_CELL[sz] in s:                                      # 한자 넷 자리 통째로 비우고 칸 안쪽에만
        o = a.copy(); o[:, 219:388] = 0; return labels(o, CELLS[sz], bright(a, (222, 0, 385, 22)), clear=True), '칸 그림'
    if s in TITLE_SPLIT: return title_split(a, TITLE_SPLIT[s]), '큰 제목'
    for key, (cut, first) in DESC.items():                                       # 포즈 메뉴 설명: 게임이 그림을 원문 줄바꿈 x 에서 잘라 두 줄로(2026-11-02)
        if s.startswith(key) and k.startswith(first):
            t2 = k[len(first):].strip(); out = np.zeros_like(a)
            _, i1 = R.render(a[:, :cut - 3].copy(), [first]); _, i2 = R.render(a[:, cut + 3:].copy(), [t2]); z = min(i1[0][0], i2[0][0])   # 두 줄 같은 크기
            n1, _ = R.render(a[:, :cut - 3].copy(), [first], fsize=z); out[:, :cut - 3] = n1
            n2, _ = R.render(a[:, cut + 3:].copy(), [t2], fsize=z); out[:, cut + 3:] = n2
            return out, '설명 두 줄'
    if s in MENU and (w, h) in MENU_SZ:
        return left_align(T.title(a, k, 'gray' if h == 22 else 'yellow')), '메뉴 항목'   # 선택(노랑)·비선택(회색) 모두 원본처럼 같은 기울인 굵은 글꼴, 왼쪽 맞춤
    if s == 'リアルモード「 」':                                                  # 「 」 사이는 게임이 ON/OFF 를 찍는 자리 — 괄호는 원본 그대로, 앞 낱말만(2026-11-02)
        out = a.copy(); n, _ = R.render(a[:, :110].copy(), ['리얼 모드']); out[:, :110] = n; return out, '판'
    if sz == '76x120':                                                           # 정보 화면 라벨: 원본처럼 남색 글자 + 연한 테 — 4배로 그려 줄임(하스피 «고해상도로», 2026-11-02), 줄마다 원문 폭 안
        from PIL import ImageFilter
        Q = 4; out = np.zeros((h, w, 4), np.uint8); f = ImageFont.truetype(R.F, 15 * Q)
        for r_, t in enumerate(k.split('／')):
            b = a[r_ * 20:(r_ + 1) * 20]; W_ = int(np.nonzero((b[..., 3] > 60).any(0))[0].max()) + 1
            g = Image.new('L', (int(f.getlength(t)) + 16 * Q, 20 * Q)); ImageDraw.Draw(g).text((8 * Q, 10 * Q), t, font=f, fill=255, anchor='lm'); g = g.crop(g.getbbox())
            maxw = (W_ - 5) * Q
            if g.width > maxw: g = g.resize((maxw, g.height), Image.LANCZOS)
            G_ = Image.new('L', (w * Q, 20 * Q)); G_.paste(g, (int(2.5 * Q), (20 * Q - g.height) // 2))
            G_ = G_.filter(ImageFilter.MaxFilter(3))                              # 획 0.5px 굵게(원본 획 2px)
            H_ = G_.filter(ImageFilter.MaxFilter(2 * Q + 1)).filter(ImageFilter.MaxFilter(2 * Q + 1))   # 테 2px
            gc = np.asarray(G_.resize((w, 20), Image.BOX)) / 255.0; hc = np.asarray(H_.resize((w, 20), Image.BOX)) / 255.0
            ga = gc; ha = hc * (216 / 255) * (1 - gc); al = ga + ha
            rgb = (ga[..., None] * np.array([24, 32, 90]) + ha[..., None] * np.array([204, 204, 221])) / np.maximum(al, 1e-6)[..., None]
            o = out[r_ * 20:(r_ + 1) * 20]; o[..., :3] = rgb.clip(0, 255); o[..., 3] = (al * 255).clip(0, 255)
        return out, '라벨'
    if sz == '404x46':
        n, _ = R.render(a, k.split('／'), center=True); return n, '가운데'
    if sz == '162x20' and JP_CELL[sz] in s:
        return labels(np.zeros_like(a), CELLS[sz], bright(a, (0, 0, w, h)), clear=True, size=17, ring=True), '칸 그림'
    if sz in JP_CELL and JP_CELL[sz] in s: return labels(a, CELLS[sz], clear=(a[..., 3] > 200).mean() < 0.9), '칸 그림'
    if s.startswith('電車でGO!新幹線EX'):                                         # 제목 로고(2026-11-02 하스피 «타이틀 작업»)
        import logo_kr; return logo_kr.make(a), '로고'
    if s == 'GOOD! BAD' or s == '中': return a, '원본 유지'
    if s.startswith('合格範囲'):
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        for t, x0, x1 in (('합격범위!!', 0, 100), ('오버런!!', 100, 166)):
            m = T.fit(t, x1 - x0 - 4, h - 4, T.EB, 0.2); T.draw(im, m, x0 + (x1 - x0 - m.width) // 2, (h - m.height) // 2, (255, 255, 255), (20, 20, 40), 1, None)
        return np.asarray(im), '칸 그림'
    for key, (gx, l_, r_) in SPLIT.items():
        if s.startswith(key):
            im = Image.fromarray(np.zeros_like(a)); c = bright(a, (0, 0, w, h), 85)
            for t, mw, right in ((l_, gx - 2, True), (r_, w - gx - 6, False)):
                for z in range(18, 9, -1):
                    g = R.text_img(t, z, 1.0)
                    if g.width <= mw: break
                put(im, g, gx - 2 - g.width if right else gx + 6, (h - g.height) // 2, c, (10, 10, 20), True)
            return np.asarray(im), '틈 맞춤'
    for key, parts in LOOK.items():
        if s.startswith(key):
            ls = k.split('／'); n, _ = R.render(a, [' ', ls[1]] if parts else [ls[0], ' ']); im = Image.fromarray(n.copy()); yl = 22 if h == 72 else 17
            if parts:
                x = 60
                for t, c, px in parts:
                    x = px if px else x; g = R.text_img(t, 17, 1.0); put(im, g, x, yl - g.height // 2, c); x += g.width + 2
            else:
                for t, x in (('시속', 10), ('km입니다', 96)):
                    g = R.text_img(t, 17, 1.0); put(im, g, x, 44 - g.height // 2, WH)
            return np.asarray(im), '틈 맞춤'
    if sz == '172x80' and 'はやい' in s:
        o = a.copy()
        for b in ((12, 21, 64, 47), (108, 21, 161, 47)): wipe(o, b)
        im = Image.fromarray(o)
        for t, x, c in (('빠름', 16, (120, 225, 255)), ('느림', 116, (255, 110, 90))):
            g = R.text_img(t, 17, 1.0); put(im, g, x, 33 - g.height // 2, c, (10, 14, 50), True)
        return np.asarray(im), '판'
    if sz in ('166x56', '304x60'):
        o = a.copy(); ytab, ref, xend, xl = (10, 92, 90, 19) if w == 166 else (14, 104, 100, 20)        # 탭 위로 솟은 제목: 탭 무늬는 글자 없는 열에서, 탭 위는 투명
        for y in range(0, ytab + 8): o[y, (16 if y < ytab else xl):xend] = a[y, ref]
        im = Image.fromarray(o); m = T.fit(k.split('／')[0], xend - 20, 15, T.EB); T.draw(im, m, 19, 1, (14, 20, 80), (240, 244, 252), 1, None); out = np.asarray(im).copy()
        if w == 166:
            mark(out, (126, 26, 149, 46), 110, '점', 17, (205, 215, 235), (137, 36)); out = LAST[0]
        return out, '판'
    if sz == '354x40':
        return labels(a, [((164, 8, 226, 31), '합계'), ((312, 8, 336, 31), '점')], (200, 205, 205), (10, 14, 40)), '판'
    if sz == '288x48':
        dk = tuple(int(v) for v in a[8, 15, :3]) if a[8, 15, :3].mean() < 90 else (24, 32, 90); ts = k.split('／'); o = a.copy()
        for (x0, x1, tx), t in zip(((11, 60, 12), (66, 112, 67), (119, 205, 120), (214, 270, 214)), ts):
            o[3:15, x0:x1] = a[3:15, 190:191]; g = ptext(t, 'Galmuri11-Bold.ttf', 12) if len(t) < 5 else cond(t); im = Image.fromarray(o); put(im, g, tx, 9 - g.height // 2, dk, None); o = np.asarray(im).copy()
        if '休日' in s:
            mark(o, (95, 18, 190, 40), 60, ts[4], 18, (240, 240, 240), (144, 29)); o = LAST[0]
        elif ts[4] == '점':
            mark(o, (251, 19, 269, 40), 226, '점', 15, bright(a, (252, 22, 269, 38)), (260, 30)); o = LAST[0]
        return o, '판'
    if s == 'フリーランスタート':
        o = labels(a, [((16, 7, 196, 30), '프리런 스타트')], (130, 165, 215), (12, 30, 80), True, size=16)
        return labels(o, [((16, 43, 196, 66), '프리런 스타트')], (250, 250, 250), (10, 50, 20), True, size=16), '판'
    if sz == '306x52':
        o = a.copy(); ws = k.split('／')
        for yy, c, xs in ((3, (20, 26, 80), ((12, 92), (113, 196), (215, 298))), (29, (30, 36, 92), ((12, 90), (113, 192), (215, 294)))):
            for (x0, x1), t in zip(xs, ws):
                for y in range(yy, yy + 19): o[y, x0:x1] = a[y, x0 - 1]
                bw = x1 - x0; im = Image.fromarray(o)
                for z in range(17, 7, -1):
                    g = R.text_img(t, z, 1.0)
                    if g.width <= bw - 2: break
                g = g.crop(g.getbbox()); put(im, g, x0 + (bw - g.width) // 2, yy + (18 - g.height) // 2, c, None); o = np.asarray(im).copy()
        return o, '판'
    if sz == '420x232':
        ls = k.split('／'); ts = ls[0].replace('☆', ''); o = a.copy(); o[14:56, 48:372] = a[14:56, 8:9]; wipe(o, (36, 66, 330, 222)); im = Image.fromarray(o)
        m = T.fit(ts, 310, 26, T.JUA); T.draw(im, m, 210 - m.width // 2, 35 - m.height // 2, [(255, 250, 120), (250, 200, 40)], (70, 40, 10), 1, None)
        for t, y in zip(ls[1:], (86, 110, 150, 174, 198)):
            g = R.text_img(t, 15, 1.0); put(im, g, 42, y - g.height // 2, (250, 250, 255))
        return np.asarray(im), '판'
    if sz == '410x254':
        ls = k.split('／'); o = a.copy(); wipe(o, (112, 10, 298, 52)); o[190:244, 60:350] = a[190:244, 30:31]; im = Image.fromarray(o)
        m = T.fit(ls[0], 170, 32, T.JUA); T.draw(im, m, 205 - m.width // 2, 31 - m.height // 2, (70, 80, 140), (190, 200, 225), 1, None)
        for t, y in zip(ls[1:], (206, 229)):
            g = R.text_img(t, 15, 1.0); put(im, g, 205 - g.width // 2, y - g.height // 2, (250, 250, 255))
        return np.asarray(im), '판'
    if sz == '438x204':
        o = labels(a, [((30, 14, 294, 50), '캐릭터 보너스')], (40, 240, 240), (5, 10, 60)); o = o.copy(); o[18:50, 372:404] = a[34, 300]; _i = Image.fromarray(o); _g = R.text_img('점', 20, 1.0); put(_i, _g, 376, 34 - _g.height // 2, (40, 240, 240), (5, 10, 60)); o = np.asarray(_i).copy()
        o = o.copy()
        for y in range(70, 132):
            for r_ in ((30, 165), (205, 242)): o[y, r_[0]:r_[1]] = a[y, 190]
        _i = Image.fromarray(o)
        for t, yc, xr in (('실패 횟수', 87, 154), ('감점', 114, 154), ('회', 87, 234), ('점', 114, 234)):
            _g = R.text_img(t, 16, 1.0); _g = _g.crop(_g.getbbox()); put(_i, _g, xr - _g.width, yc - _g.height // 2, (240, 240, 245), (5, 10, 60))
        o = np.asarray(_i)
        o = labels(o, [((60, 150, 270, 184), '합계 보너스 점수')], (250, 225, 60), (5, 10, 60)).copy(); mark(o, (386, 150, 424, 192), 370, '점', 16, (250, 225, 60), (405, 174)); return LAST[0], '판'
    if s == 'キープ中':
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); m = R.text_img('킵 중', 13, 1.0); put(im, m, (w - m.width) // 2, (h - m.height) // 2, (255, 240, 60), (20, 20, 20), True); return np.asarray(im), '판'
    if s in ('通過', '停車') and w <= 44:
        o = a.copy(); rgb = a[..., :3].astype(int); lm = rgb.mean(2); op = a[..., 3] > 200; bgm = op & (lm > 60) & (lm < 150) & (rgb.max(2) - rgb.min(2) > 60)   # 판 바탕(글자 흰 획·검은 테두리 제외)
        gm = np.median(a[bgm], axis=0).astype(np.uint8)                          # 가장자리 보간은 원문 테두리를 끌어와 검은 줄이 생겼다(2026-11-02)
        for y in range(1, h - 1):
            o[y, 1:w - 1][op[y, 1:w - 1]] = gm                                # 판은 한 색(가장자리 줄마다 재면 원문 그림자 줄이 남음)
        im = Image.fromarray(o); g = R.text_img(k, 15, 1.0); put(im, g, (w - g.width) // 2, (h - g.height) // 2, (250, 250, 250)); return np.asarray(im), '판'
    if s in ('通過駅', '停車駅'):
        o = a.copy()
        for y in range(3, h - 3): o[y, 4:w - 4] = a[y, 5]
        o[6:h - 6, 6:w - 6] = a[h // 2, 5]                                       # 안쪽 어두운 줄까지 바탕 한 색 — CMPR 블록에 글자+여러 바탕색이 섞이면 네모 얼룩(2026-11-02)
        im = Image.fromarray(o); g = R.text_img(k, min(h - 8, 14), 1.0); put(im, g, (w - g.width) // 2, (h - g.height) // 2, (250, 250, 250), None); return np.asarray(im), '역 띠'   # CMPR: 그림자 넣으면 4×4 블록이 검게 뭉개짐(2026-11-02)
    return None, None
