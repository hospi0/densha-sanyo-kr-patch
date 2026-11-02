# -*- coding: utf-8 -*-
r"""OCR 이 놓친 글자 그림(번호 = work/text/rest_paths.json) → 한글. 스타일: t 일반 띠 · b 큰 글자(원본 색·기울임) · p 판 위 글자 · v 세로 · g 버튼 · c 작은 칸"""
import numpy as np
from PIL import Image
import render_kr as R, title_kr as T, gfx_special as S
ST = '신오사카 신코베 니시아카시 히메지 아이오이 오카야마 신쿠라시키 후쿠야마 신오노미치 미하라 히가시히로시마 히로시마 신이와쿠니 토쿠야마 신야마구치 아사 신시모노세키 코쿠라 하카타 하카타미나미 하카타종합차량소'.split()
TBL = {36: ('g', '운전 스타트'), 37: ('g', '운전 스타트'), 117: ('g', '프리런 스타트'), 118: ('g', '프리런 스타트'),
       41: ('t', '히메지'), 42: ('t', '미하라'), 43: ('t', '히가시히로시마'), 45: ('t', 'P편성'), 46: ('t', 'NH편성'), 47: ('t', 'WR편성'), 48: ('t', 'Sk편성'), 49: ('t', '입문 다이아'),
       64: ('t', '새벽'), 65: ('t', '아침'), 66: ('t', '낮'), 67: ('t', '신오사카'), 68: ('t', '미하라'), 69: ('t', '히가시히로시마'), 70: ('t', '히로시마'), 71: ('t', '코쿠라'),
       77: ('t', '결정'), 78: ('t', '노선'), 112: ('t', '총주행거리'), 119: ('t', '새벽'), 120: ('t', '아침'), 121: ('t', '낮'), 122: ('t', '저녁'), 123: ('b', '0계'), 127: ('t', '맑음'), 128: ('t', '흐림'), 129: ('t', '비'), 130: ('t', '눈'),
       176: ('t', 'GREAT!정차'), 179: ('t', '0계 SK편성'), 180: ('t', '100계 G편성'), 181: ('t', '100계 V편성'), 182: ('t', '100계 P편성'), 183: ('t', '300계 F편성'), 184: ('t', '700계 B편성'), 185: ('t', '오프닝'),
       187: ('t', '0계'), 188: ('t', '0계'), 189: ('t', '100계'), 190: ('t', '100계'), 191: ('t', '100계'), 192: ('t', '300계'), 193: ('t', '500계'), 194: ('t', '700계'),
       197: ('t', '설명 지움'), 198: ('t', '축소'), 199: ('t', '종료'), 200: ('t', '포인트'), 201: ('t', '타이틀'), 202: ('t', '합격'), 203: ('t', '불합격'), 207: ('t', '한 글자 지움'),
       231: ('t', 'ATC 확인'), 232: ('t', '브레이크↓'), 233: ('t', '경적'), 234: ('t', '시점 전환'), 235: ('t', '시선 이동'), 236: ('t', '시점 복귀'), 241: ('t', '투핸들 A'), 242: ('t', '투핸들 B'), 243: ('t', '원핸들'), 244: ('t', '전용 키 설정'),
       265: ('t', '조정 완료'), 272: ('b', '종합 평가'), 274: ('t', '히메지'), 275: ('t', '후쿠야마'), 276: ('t', '신오노미치'), 277: ('t', '미하라'), 278: ('t', '신이와쿠니'), 279: ('t', '아사'), 280: ('t', '코쿠라'), 282: ('t', '스킵'),
       283: ('t', '합격점: 점'), 335: ('i', '해제', (120, 235, 120)), 336: ('i', '내리막', (245, 245, 245)), 337: ('i', '접근', (245, 245, 245)),
       366: ('b', '출발!!'), 368: ('t', '발차지연'), 369: ('b', '출발 진행!'), 370: ('b', '정차'), 371: ('b', '통과'), 373: ('b', '전 구간 주파!'), 376: ('b', '운전 중지'), 382: ('b', '운전 평가'), 383: ('b', '불합격'), 384: ('b', '합격!!'),
       379: ('v', '문닫힘', (44, 8, 66, 54)), 380: ('p', '문닫힘', (8, 24, 46, 56)), 381: ('p', '문닫힘', (8, 24, 46, 56)), 407: ('s', '정차역'),
       408: ('b', '달성!'), 409: ('t', '를 찾아라!'), 416: ('t', '미스터 ESC'), 417: ('t', '기구'), 418: ('t', '비행선'), 419: ('t', '캐치 군'), 420: ('t', '버블룬'), 421: ('t', '봄'), 422: ('t', '철짱'), 423: ('t', '미스터 ESC'), 424: ('t', '기구'), 425: ('t', '캐치 군'),
       426: ('p', '목표', (3, 3, 58, 28)), 447: ('b', '달성!'), 448: ('t', '연속으로／가리켜라!'), 449: ('t', '정차 확인'), 486: ('t', '킵 버튼'), 490: ('t', '해제 버튼'), 496: ('b', '입문편'), 497: ('t', 'ATC／확인!'),
       502: ('b', 'B표'), 503: ('b', '운전 조작'), 504: ('b', '계기 보는 법'), 505: ('b', '출발'), 506: ('b', '가속'), 507: ('b', '감속'), 508: ('b', '통과'), 509: ('b', 'B표 설명'), 510: ('b', '정차'), 511: ('b', 'ATC 확인'),
       561: ('p', '음량', (20, 12, 100, 52)), 593: ('c', '착'), 594: ('c', '통'), 599: ('c', '현'), 600: ('c', '남음'), 602: ('c', '착'), 603: ('c', '통'), 608: ('c', '현'), 609: ('c', '남음'),
       621: ('c', '비'), 622: ('c', '상'), 623: ('c', '자'), 624: ('c', '동'), 635: ('c', '비'), 636: ('c', '상'), 637: ('c', '자'), 638: ('c', '동'), 658: ('t', '착'), 659: ('t', '통'), 662: ('t', '남음')}
for i, n in zip(range(134, 155), ST): TBL[i] = ('v', n, None)


def big(a, t):
    h, w = a.shape[:2]; op = a[..., 3] > 120; rgb = a[..., :3].astype(int); lm = rgb.mean(2)
    th = (np.percentile(lm[op], 5) + np.percentile(lm[op], 95)) / 2 if op.any() else 128; lit = op & (lm >= th); dk = op & (lm < th)
    ys = np.nonzero(lit.any(1))[0]; y0, y1 = int(ys.min()), int(ys.max()) + 1; m_ = (y0 + y1) // 2
    top = np.median(rgb[y0:m_][lit[y0:m_]], axis=0); bot = np.median(rgb[m_:y1][lit[m_:y1]], axis=0)
    sc = tuple(int(v) for v in np.median(rgb[dk], axis=0)) if dk.any() else (20, 20, 40)
    xs = np.nonzero(op.any(0))[0]; L, Rr = int(xs.min()), int(xs.max()) + 1
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); m = T.fit(t, Rr - L - 4, h - 4, T.JUA, 0.18 if h >= 36 else 0.0)
    T.draw(im, m, (L + Rr - m.width) // 2, (h - m.height) // 2, [tuple(int(v) for v in top), tuple(int(v) for v in bot)], sc, 1, None); return np.asarray(im)


def plate(a, t, box, corner=False):
    x0, y0, x1, y1 = box; o = a.copy(); r = a[y0:y1, x0:x1, :3].astype(int); vis = a[y0:y1, x0:x1, 3] > 128; u, n = np.unique(r[vis] // 16, axis=0, return_counts=True); med = u[n.argmax()] * 16 + 8
    if corner: med = a[y0 + 1, x0 + 1, :3].astype(int)
    d = np.abs(r - med).sum(2)
    ink = vis & (d > max(70, np.percentile(d[vis], 90))); col = tuple(int(v) for v in np.median(r[vis & (d >= np.percentile(d[vis], 97))], axis=0)) if ink.any() else (20, 20, 20)
    sub = o[y0:y1, x0:x1]; sub[vis] = np.append(med, 255).astype(np.uint8); im = Image.fromarray(o)
    for z in range(min(y1 - y0, 20), 6, -1):
        g = R.text_img(t, z, 1.0); bb = g.getbbox()
        if g.width <= x1 - x0 - 1 and bb[3] - bb[1] <= y1 - y0: break
    g = g.crop((0, bb[1], g.width, bb[3])); S.put(im, g, x0 + (x1 - x0 - g.width) // 2, y0 + (y1 - y0 - g.height) // 2, col, None); return np.asarray(im)


def vert(a, t, box):
    h, w = a.shape[:2]; solid = box is not None
    if solid:
        x0, y0, x1, y1 = box; o = a.copy(); r = a[y0:y1, x0:x1, :3].astype(int); med = np.median(r.reshape(-1, 3), axis=0); ink = np.abs(r - med).sum(2) > 70
        col = tuple(int(v) for v in np.median(r[ink], axis=0)); o[y0:y1, x0:x1, :3][ink] = med
    else:
        x0, y0, x1, y1 = 0, 0, w, h; col = tuple(int(v) for v in np.percentile(a[a[..., 3] > 100][:, :3], 90, axis=0)); o = np.zeros_like(a)
    im = Image.fromarray(o); S.vtext(im, t, (x0, y0, x1, y1), col, (8, 10, 30) if not solid else None); return np.asarray(im)


def vert_station(a, t):
    """운전 중 노선 지도 역 이름(폭 16): 3음절 이하는 한 줄 세로(갈무리9), 4음절 이상은 두 글자씩 가로로 묶어 위→아래(갈무리7)
    — 이름마다 같은 글꼴·같은 줄 간격·위쪽 맞춤(2026-11-02 하스피 «줄은 맞춰서»; 예전엔 세로 두 칸이라 오카야마가 «오야/카마»)"""
    h, w = a.shape[:2]; col = tuple(int(v) for v in np.percentile(a[a[..., 3] > 100][:, :3], 90, axis=0)); im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    n = len(t)
    if n <= 3 or n * 11 <= h:
        pitch = min(11, h // n)
        for i, c in enumerate(t):
            g = S.pix(c, 'Galmuri9.ttf', 10); S.put(im, g, (w - g.width) // 2, 1 + i * pitch + (pitch - 1 - g.height) // 2, col, (8, 10, 30))
    else:
        rows = [t[i:i + 2] for i in range(0, n, 2)]; pitch = min(9, h // len(rows))
        for r, pair in enumerate(rows):
            gs = [S.pix(c, 'Galmuri7.ttf', 8) for c in pair]; tw = sum(g.width for g in gs) + (len(gs) - 1); x = (w - tw) // 2
            for g in gs:
                S.put(im, g, x, 1 + r * pitch + (pitch - 1 - g.height) // 2, col, None); x += g.width + 1
    return np.asarray(im)


def button(a, t):
    h, w = a.shape[:2]; px = a[h // 2 - 6:h // 2 + 6, 20:w - 20, :3].astype(int).reshape(-1, 3)
    return S.labels(a, [((14, 5, w - 14, h - 6), t)], tuple(int(v) for v in np.percentile(px, 96, axis=0)), tuple(int(v) for v in np.percentile(px, 8, axis=0)), True, size=17)


def draw(a, e):
    k = e[0]; t = e[1]
    if k == 'b': return big(a, t)
    if k == 'p': return plate(a, t, e[2])
    if k == 'i':
        o = a.copy(); o[2:23, 2:48, :3] = np.median(a[23:26, 3:12, :3].reshape(-1, 3), axis=0).astype(np.uint8) if t != '해제' else (0, 0, 0); o[2:23, 2:48, 3] = 255; im = Image.fromarray(o); g = R.text_img(t, 15, 1.0); g = g.crop(g.getbbox()); g = g.resize((min(g.width, 42), g.height)); S.put(im, g, 25 - g.width // 2, 12 - g.height // 2, e[2], None); return np.asarray(im)
    if k == 'v': return vert_station(a, t) if e[2] is None else vert(a, t, e[2])
    if k == 'g': return button(a, t)
    if k == 'c': return plate(a, t, (2, 2, a.shape[1] - 2, a.shape[0] - 2), True)
    if k == 's': return S.special(a, '停車駅', t)[0]
    n, _ = R.render(a, t.split('／')); return n


# 이름 입력판: 22×22 칸 14열 6줄 — 가나 칸을 한글 음절로(쓴 이름도 같은 칸을 씀)
SYL = list(dict.fromkeys('''가 강 건 경 고 공 곽 구 권 규 금 기 길 김 나 남 노 다 대 도 동 두 라 란 래 레 로 류 리 린 마 만 맹 명 모 목 무 문 미 민 박 반 방 배 백 범 변 별 병 보 봉 부 비 빈 사 산 상 서 석 선 설 성 세 소 손 송 수 숙 순 슬 승 시 신 심 아 안 애 양 엄 여 연 영 예 오 옥 온 완 용 우 욱 운 원 월 위 유 윤 율 은 음 응 이 익 인 일 임 자 장 재 전 정 제 조 종 주 준 중 지 진 찬 창 채 천 철 초 최 추 춘 충 태 택 하 학 한 해 허 현 형 혜 호 홍 화 환 황 효 후 훈 휘 희 은 을 의 스 피 그 드 트 크 키 타 티 파 페 포 프 카 코 케'''.split()))
# 기본 기록표 열차 이름(main.dol, tools/dol_kr.py) 코다마·히카리·노조미는 «첫 장(번호 0~79)» 칸으로만 찍힌다 — 드문 곽·맹·엄·래 자리를 내줌(2026-11-02)
for _i, _c in ((6, '카'), (32, '코'), (24, '히'), (78, '조'), (111, '래')): SYL[_i] = _c


def kana_sheet(a, syl):
    o = np.zeros_like(a); out = []; k = 0
    im = Image.fromarray(o); f = T.JUA
    for r in range(6):
        for c in range(14):
            x, y = c * 22, r * 22; cell = a[y:y + 22, x:x + 22]
            if (cell[..., 3] > 60).sum() < 8: continue
            if r == 5 and c >= 10:
                o2 = np.asarray(im).copy(); o2[y:y + 22, x:x + 22] = cell; im = Image.fromarray(o2)
                if c == 12:
                    o2 = np.asarray(im).copy(); o2[y:y + 22, x:x + 22] = 0; im = Image.fromarray(o2); m = T.fit('끝', 19, 19, f); T.draw(im, m, x + (21 - m.width) // 2, y + (21 - m.height) // 2, (250, 250, 250), None, 0, None); S_shadow(im, m, x, y)
                continue
            m = T.fit(syl[k], 19, 19, f); k += 1; S_shadow(im, m, x, y)
    return np.asarray(im), k


def S_shadow(im, m, x, y):
    px, py = x + (21 - m.width) // 2, y + (21 - m.height) // 2
    S.put(im, m, px, py, (250, 250, 250), (10, 10, 20))


# 운전석 시계판의 작은 現 → 현 (글자 잉크 범위 x0, x1, y0, y1)
CLOCK = {'cockpit/co100.dat/0019D20_0_128x128_f14.png': (14, 28, 70, 82), 'cockpit/co300.dat/0020040_0_128x128_f14.png': (11, 25, 68, 82),
         'cockpit/co500.dat/001F8A0_0_128x128_f8.png': (14, 28, 70, 83), 'cockpit/co700.dat/0023560_0_128x128_f14.png': (15, 28, 70, 82)}


def clock(a, b):
    x0, x1, y0, y1 = b; o = a.copy(); r = a[y0:y1 + 1, x0:x1 + 1, :3].astype(int); col = tuple(int(v) for v in np.percentile(r.reshape(-1, 3), 97, axis=0))
    S.wipe(o, (x0 - 2, y0 - 2, x1 + 3, y1 + 3)); im = Image.fromarray(o); g = R.text_img('현', 15, 1.0); g = g.crop(g.getbbox()); S.put(im, g, (x0 + x1 + 1 - g.width) // 2, (y0 + y1 + 1 - g.height) // 2, col, None); return np.asarray(im)


def alnum_sheet(a):
    """영숫자 입력판 22×22: 系 → 계, 赤 → 적"""
    o = a.copy()
    for c, r in ((13, 2), (6, 3)): o[r * 22:r * 22 + 22, c * 22:c * 22 + 22] = 0
    im = Image.fromarray(o)
    for t, c, r in (('계', 13, 2), ('적', 6, 3)): S_shadow(im, T.fit(t, 17, 17, T.EB), c * 22, r * 22)
    return np.asarray(im)
