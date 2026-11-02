# -*- coding: utf-8 -*-
r"""글자 그림 전체 다시 그리기 → work/build/files/<파일> (크기·팔레트 그대로 제자리)
  그림 ↔ 문구 = work/text/img_map.tsv · 번역 = work/text/ko.tsv
  형식: C4·C8 = 원본 팔레트 가까운 색 · I4 · CMPR · RGBA8"""
import os, re, sys, struct, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import tpl, render_kr as R, title_kr as T, gfx_special as S2
from PIL import Image, ImageDraw, ImageFont
FILES = os.path.join(ROOT, 'work', 'disc', 'DATA', 'files'); OUT = os.path.join(ROOT, 'work', 'build', 'files'); TEX = os.path.join(ROOT, 'work', 'tex')


def enc_index(d, im, rgba):
    w, h, f, o, p = im; pal = tpl.clut(bytes(d), p).astype(int); a = rgba.astype(int)
    q = a.reshape(-1, 4); wt = np.array([1, 1, 1, 3]); u, inv = np.unique(q, axis=0, return_inverse=True)
    tr = int(pal[:, 3].argmin()); ui = ((((u[:, None, :] - pal[None, :, :]) * wt) ** 2).sum(2)).argmin(1); ui[u[:, 3] == 0] = tr
    idx = ui[inv.ravel()].reshape(h, w)
    bw, bh, bits = (8, 8, 4) if f == 8 else (8, 4, 8); bx, by = (w + bw - 1) // bw, (h + bh - 1) // bh
    g = np.zeros((by * bh, bx * bw), int); g[:h, :w] = idx
    blk = g.reshape(by, bh, bx, bw).transpose(0, 2, 1, 3).ravel().astype(np.uint8)
    b = ((blk[0::2] << 4) | blk[1::2]).tobytes() if bits == 4 else blk.tobytes()
    d[o:o + len(b)] = b


def enc_i4(d, im, rgba):
    w, h, f, o, p = im; v = (rgba[..., :3].mean(2) / 17 + 0.5).astype(int).clip(0, 15)
    bx, by = (w + 7) // 8, (h + 7) // 8; g = np.zeros((by * 8, bx * 8), int); g[:h, :w] = v
    blk = g.reshape(by, 8, bx, 8).transpose(0, 2, 1, 3).ravel().astype(np.uint8); b = ((blk[0::2] << 4) | blk[1::2]).tobytes(); d[o:o + len(b)] = b


def enc_cmpr(d, im, rgba, best=False):
    w, h, f, o, p = im; bx, by = (w + 7) // 8, (h + 7) // 8; q = o
    g = np.zeros((by * 8, bx * 8, 4), np.uint8); g[:h, :w] = rgba
    r5 = lambda v: (int(v[0]) >> 3) << 11 | (int(v[1]) >> 2) << 5 | int(v[2]) >> 3
    for yy in range(by):
        for xx in range(bx):
            for sy in (0, 4):
                for sx in (0, 4):
                    t = g[yy * 8 + sy:yy * 8 + sy + 4, xx * 8 + sx:xx * 8 + sx + 4].astype(int); op = t[..., 3] > 128
                    if not op.any():
                        d[q:q + 8] = struct.pack('>HH', 0, 0xFFFF) + bytes((255, 255, 255, 255)); q += 8; continue
                    c = t[op][:, :3]; lum = c.sum(1); hi, lo = c[lum.argmax()], c[lum.argmin()]
                    if best and op.all(): hi, lo = best_pair(c)
                    a_, b_ = r5(hi), r5(lo); trans = not op.all()
                    if trans:
                        if a_ > b_: a_, b_ = b_, a_; hi, lo = lo, hi
                        pal = [hi, lo, (hi + lo) // 2]
                    else:
                        if a_ < b_: a_, b_ = b_, a_; hi, lo = lo, hi
                        if a_ == b_: a_ = min(0xFFFF, a_ + 1)
                        pal = [hi, lo, (2 * hi + lo) // 3, (hi + 2 * lo) // 3]
                    for y in range(4):
                        v = 0
                        for x in range(4):
                            k = 3 if not op[y, x] else int(np.argmin([((t[y, x, :3] - pc) ** 2).sum() for pc in pal]))
                            v = v << 2 | k
                        d[q + 4 + y] = v
                    d[q:q + 4] = struct.pack('>HH', a_, b_); q += 8


def best_pair(c):
    """불투명 4×4 블록: 끝점 두 색을 블록 색 쌍 전수로 골라 오차 최소(흰 글자+그림자+바탕 3색 블록 노이즈 방지)"""
    q = lambda v: np.array([(int(v[0]) >> 3) * 255 // 31, (int(v[1]) >> 2) * 255 // 63, (int(v[2]) >> 3) * 255 // 31])
    u = np.unique(c, axis=0); bestv = None
    for i in range(len(u)):
        for j in range(i, len(u)):
            a_, b_ = q(u[i]), q(u[j]); pal = np.array([a_, b_, (2 * a_ + b_) // 3, (a_ + 2 * b_) // 3])
            e = ((c[:, None, :] - pal[None]) ** 2).sum(2).min(1).sum()
            if bestv is None or e < bestv[0]: bestv = (e, u[i], u[j])
    return bestv[1], bestv[2]


def enc_rgba8(d, im, rgba):
    w, h, f, o, p = im; bx, by = (w + 3) // 4, (h + 3) // 4; g = np.zeros((by * 4, bx * 4, 4), np.uint8); g[:h, :w] = rgba; q = o
    for yy in range(by):
        for xx in range(bx):
            t = g[yy * 4:yy * 4 + 4, xx * 4:xx * 4 + 4].reshape(-1, 4)
            d[q:q + 32] = bytes(np.stack([t[:, 3], t[:, 0]], 1).ravel()); d[q + 32:q + 64] = bytes(t[:, 1:3].ravel()); q += 64


def cell(a, box, t):
    """판 일부(box)만 다시 그림"""
    x0, y0, x1, y1 = box; n, _ = R.render(a[y0:y1, x0:x1].copy(), [t]); out = a.copy(); out[y0:y1, x0:x1] = n; return out


def special(a, s, k):
    h, w = a.shape[:2]
    if (w, h) == (50, 46):
        return cell(a, (0, 0, 50, 22), re.sub(r'[0-9B]+$', '', k)), '아이콘'
    if (w, h) == (46, 50):
        p = cell(cell(a, (0, 0, 46, 18), '정시'), (0, 18, 46, 36), '정속'); return p, '아이콘'
    if '分' in s and '秒' in s:
        ls = k.split('／'); n, _ = R.render(a, [' '] + ls[1:]) if len(ls) > 1 else R.render(a, [' ']); im = Image.fromarray(n.copy()); H = 26
        for t, x, c in (('분', 36, (235, 40, 30)), ('초', 83, (235, 40, 30)), ('늦어지고 있습니다.', 106, (255, 255, 255))):
            g = R.text_img(t, 17, 1.0); y = 16 - g.height // 2
            if len(ls) == 1: y = 24 - g.height // 2
            im.paste(Image.new('RGBA', g.size, (8, 10, 30, 255)), (x + 1, y + 1), g); im.paste(Image.new('RGBA', g.size, c + (255,)), (x, y), g)
        return np.asarray(im), '시간 문구'
    if s in ('100系', '300系', '500系', '700系'):
        out = a.copy(); xs = np.nonzero((a[..., 3] > 60).any(0))[0]; R0 = int(xs.max()) + 1; cut = R0 - 42; out[:, cut:] = 0; im = Image.fromarray(out)
        m = T.fit('계', 40, 28, T.JUA); T.draw(im, m, cut + 4, (h - m.height) // 2, [(235, 240, 250), (150, 170, 205)], (30, 44, 90), 1, None); return np.asarray(im), '계열 표시'
    if s in ('通過駅', '停車駅'):
        rgb = a[..., :3].astype(int); ink = (a[..., 3] > 60) & (rgb.mean(2) > 150); out = a.copy()
        ys, xs = np.nonzero(ink)
        if len(ys):
            box = (int(xs.min()) - 2, int(ys.min()) - 1, int(xs.max()) + 3, int(ys.max()) + 2); bar = np.median(a[(a[..., 3] > 200) & ~ink], axis=0).astype(np.uint8)
            out[box[1]:box[3], box[0]:box[2]] = bar; im = Image.fromarray(out); g = R.text_img(k.replace(' ', '　'), max(11, box[3] - box[1]), 1.0)
            x = (w - g.width) // 2; y = (h - g.height) // 2; im.paste(Image.new('RGBA', g.size, (250, 250, 250, 255)), (x, y), g); return np.asarray(im), '역 띠'
    if s == '戸じめ' and h == 80:                                                 # 버튼 그림 유지, 아래 남색 칸 글자만
        out = a.copy(); rgb = a[..., :3].astype(int); box = (5, 57, 49, 76); sub = a[box[1]:box[3], box[0]:box[2]]; lit = sub[..., :3].mean(2) > 130
        bg = np.median(sub[~lit], axis=0).astype(np.uint8); out[box[1]:box[3], box[0]:box[2]] = bg; im = Image.fromarray(out)
        g = R.text_img(k, 13, 1.0); g = g.resize((min(g.width, 42), g.height)) ; im.paste(Image.new('RGBA', g.size, (250, 250, 250, 255)), (27 - g.width // 2, 66 - g.height // 2), g); return np.asarray(im), '알림등'
    if s == '戸じめ' and h >= 60:                                                 # 알림등: 캡슐 안 글자만 지우고 같은 중심축에 세로로
        out = a.copy(); rgb = a[..., :3].astype(int); op = a[..., 3] > 128; xs = np.nonzero(op.any(0))[0]; cx = (int(xs.min()) + int(xs.max()) + 1) / 2
        prof = a[20:47].astype(int); prof = prof[prof[..., :3].sum(2).argmax(0), np.arange(a.shape[1])].astype(np.uint8)   # 열마다 가장 밝은 값 = 글자 없는 무늬
        ink = op & (rgb[..., 0] < 0xF0); ink[:9] = False; ink[53:] = False; ink[:, :8] = False; ink[:, 32:] = False
        for y, x in zip(*np.nonzero(ink)): out[y, x] = prof[x]
        for y in range(9, 53):                                                   # 글자 번짐(그림자)까지: 가운데 열은 무늬로 통일
            for x in range(12, 28):
                if op[y, x] and rgb[y, x, 2] < 0xC0 and 11 <= y <= 50: out[y, x] = prof[x]
        im = Image.fromarray(out); f = ImageFont.truetype(R.F, 11 * 4); ys = (19, 31, 43)
        for ch, yc in zip(k, ys):
            t = Image.new('L', (22 * 4, 16 * 4)); ImageDraw.Draw(t).text((11 * 4, 8 * 4), ch, font=f, fill=255, anchor='mm'); t = t.resize((22, 16), Image.LANCZOS)
            im.paste(Image.new('RGBA', t.size, (0x73, 0x31, 0x10, 255)), (int(cx - 11), yc - 8), t)
        return np.asarray(im), '알림등'
    if w == 306 and h == 52:
        ws = k.split('／'); out = a.copy()
        for r in range(2):
            for c_, t in enumerate(ws): out = cell(out, (c_ * 102, r * 26, (c_ + 1) * 102, (r + 1) * 26), t)
        return out, '탭'
    if w == 288 and h == 48:
        ws = k.split('／'); out = a.copy()
        for b_, t in zip(((8, 0, 62, 16), (62, 0, 118, 16), (118, 0, 205, 16), (205, 0, 285, 16)), ws): out = cell(out, b_, t)
        return out, '정보 판'
    if w == 420 and h == 56:
        out = a.copy(); ls = k.split('／'); im = None; n = len(ls); cw = w / n
        rgb = a[..., :3].astype(int); lm = rgb.mean(2); ink = (a[..., 3] > 60) & (lm > np.median(lm[a[..., 3] > 60]) + 22); base = np.median(a[(a[..., 3] > 200) & ~ink], axis=0).astype(np.uint8)
        col = tuple(int(v) for v in np.percentile(a[ink][:, :3], 90, axis=0)); p = np.pad(ink, 1)
        m = ink | p[2:, 1:-1] | p[:-2, 1:-1] | p[1:-1, 2:] | p[1:-1, :-2]; out[m] = base; im = Image.fromarray(out)
        for i, t in enumerate(ls): S2.vtext(im, t, (int(cw * i) + 1, 2, int(cw * (i + 1)) - 1, h - 2), col)
        return np.asarray(im), '역 이름 시트'
    return None, None


def draw_one(a, s, k, rel):
    h, w = a.shape[:2]; ls = k.split('／')
    n, how = S2.special(a, s, k)
    if n is not None: return n, how
    if how == '메뉴 항목':                                                         # 일반 경로로 그린 뒤 왼쪽 맞춤
        n, how2 = draw_one(a, s + '#', k, rel)
        return (S2.left_align(n) if n is not None else None), '메뉴 항목'
    n, how = special(a, s, k)
    if n is not None: return n, how
    if w == 224 and h >= 230 and ('Mode' in s or 'Setting' in s or 'Train ' in s):      # 메뉴 버튼 시트
        K = []; E = []
        for x, y in zip(s.split('／'), ls):
            e = re.search(r'[A-Za-z].*$', x); K.append(re.sub(r'\s+[A-Za-z].*$', '', y)); E.append(e[0] if e else '')
        return T.menu_sheet(a, K, E), '메뉴 시트'
    if len(ls) == 1 and 30 <= h <= 44 and (a[..., 3] > 200).mean() < 0.9:
        n = T.title(a, k, 'light'); return (S2.left_align(n, 4) if s == 'ポーズメニュー' else n), '큰 제목'   # 포즈 제목은 원본처럼 왼쪽
    if len(ls) >= 8: return None, '시트 보류'
    if len(ls) == 1 and h <= 30 and (a[..., 3] > 200).mean() < 0.75:
        op = a[..., 3] > 60; c = a[op][:, :3].astype(int) if op.any() else None
        if c is not None and (c.max(1) - c.min(1)).mean() > 60 and c.mean(0)[0] > c.mean(0)[2] + 40:
            return T.title(a, k, 'yellow'), '노란 제목'
    try:
        n, i = R.render(a, ls); return n, '일반'
    except Exception as e:
        print('실패', s, repr(e)[:60]); return None, '실패'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    M = [l.split('\t') for l in open(os.path.join(ROOT, 'work', 'text', 'img_map.tsv'), encoding='utf-8').read().split('\n') if l]
    ko = {}
    for l in open(os.path.join(ROOT, 'work', 'text', 'ko.tsv'), encoding='utf-8').read().split('\n'):
        if l: c = l.split('\t'); ko[c[3]] = c[4]
    dup = collections.defaultdict(list)
    for l in open(os.path.join(TEX, 'index.tsv'), encoding='utf-8').read().split('\n'):
        c = l.split('\t')
        if len(c) > 6 and c[6]: dup[c[6]].append((c[0], int(c[1], 16), int(c[2])))
    bufs = {}; c = collections.Counter(); log = []
    def buf(rel):
        if rel not in bufs: bufs[rel] = bytearray(open(os.path.join(FILES, rel), 'rb').read())
        return bufs[rel]
    M.sort(key=lambda r: 0 if 'Driving Mode' in r[1] else 1)
    for p, s in M:
        if 'staff_tex' in p: c['스태프 제외'] += 1; continue
        if s not in ko: c['번역 없음'] += 1; log.append((p, s, '')); continue
        m = re.match(r'(.+)/([0-9A-F]+)_(\d+)_(\d+)x(\d+)_f(\d+)\.png$', p); rel = m[1]; off = int(m[2], 16); j = int(m[3]); f = int(m[6])
        a = np.asarray(Image.open(os.path.join(TEX, p)).convert('RGBA')).copy(); k = ko[s].replace('[　]', '　　')
        new, how = draw_one(a, s, k, rel); c[how] += 1
        if new is None: log.append((p, s, k)); continue
        for r_, o_, j_ in [(rel, off, j)] + dup.get(p, []):
            d = buf(r_); im = tpl.images(bytes(d), o_)[j_]
            if how == '강조줄': S2.hilite_pal(d, im)
            if f in (8, 9): enc_index(d, im, new)
            elif f == 0: enc_i4(d, im, new)
            elif f == 14: enc_cmpr(d, im, new, best=s in ('通過', '停車'))
            elif f == 6: enc_rgba8(d, im, new)
            else: c['형식 미지원 f%d' % f] += 1
    import json, gfx_extra as X
    RP = json.load(open(os.path.join(ROOT, 'work', 'text', 'rest_paths.json')))
    for i, e in X.TBL.items():
        p = RP[i]; m = re.match(r'(.+)/([0-9A-F]+)_(\d+)_(\d+)x(\d+)_f(\d+)\.png$', p); rel = m[1]; off = int(m[2], 16); j = int(m[3]); f = int(m[6])
        a = np.asarray(Image.open(os.path.join(TEX, p)).convert('RGBA')).copy()
        try: new = X.draw(a, e); c['보충'] += 1
        except Exception as ex: print('보충 실패', i, e, repr(ex)[:70]); continue
        for r_, o_, j_ in [(rel, off, j)] + dup.get(p, []):
            d = buf(r_); im = tpl.images(bytes(d), o_)[j_]
            if f in (8, 9): enc_index(d, im, new)
            elif f == 14: enc_cmpr(d, im, new)
            elif f == 0: enc_i4(d, im, new)
    base = 0; REL = 'menu/nTplCommon.dat'
    print('이름 음절', len(X.SYL))
    for o_ in (0x4C32A0, 0x4C8600):
        p = '%s/%07X_0_312x132_f8.png' % (REL, o_); a = np.asarray(Image.open(os.path.join(TEX, p)).convert('RGBA')).copy()
        new, n_ = X.kana_sheet(a, X.SYL[base:]); base += n_; d = buf(REL); enc_index(d, tpl.images(bytes(d), o_)[0], new); print('입력판', hex(o_), n_)
    a = np.asarray(Image.open(os.path.join(TEX, REL, '04CD960_0_312x88_f8.png')).convert('RGBA')).copy(); d = buf(REL); enc_index(d, tpl.images(bytes(d), 0x4CD960)[0], X.alnum_sheet(a))
    for p, box in X.CLOCK.items():
        m = re.match(r'(.+)/([0-9A-F]+)_(\d+)_(\d+)x(\d+)_f(\d+)\.png$', p); rel = m[1]; off = int(m[2], 16); f = int(m[6])
        a = np.asarray(Image.open(os.path.join(TEX, p)).convert('RGBA')).copy(); new = X.clock(a, box)
        for r_, o_, j_ in [(rel, off, 0)] + dup.get(p, []):
            d = buf(r_); im = tpl.images(bytes(d), o_)[j_]
            if f in (8, 9): enc_index(d, im, new); continue
            t_ = bytearray(d); enc_cmpr(t_, im, new); x0, x1, y0, y1 = box                     # 글자 닿는 8×8 칸만 교체 — 나머지 압축 블록은 원본 그대로
            for ty in range((y0 - 3) // 8, (y1 + 3) // 8 + 1):
                for tx in range((x0 - 3) // 8, (x1 + 3) // 8 + 1):
                    q_ = im[3] + (ty * (im[0] // 8) + tx) * 32; d[q_:q_ + 32] = t_[q_:q_ + 32]
        print('시계판', p)
    for o_, t in ((0x54BA60, '약'), (0x54C9C0, '중'), (0x54D920, '강')):              # 진동 설정 弱中強(2026-11-02)
        p = 'menu/nTplCommon.dat/%07X_0_100x32_f9.png' % o_; a = np.asarray(Image.open(os.path.join(TEX, p)).convert('RGBA')).copy()
        for r_, oo, j_ in [('menu/nTplCommon.dat', o_, 0)] + dup.get(p, []):
            d = buf(r_); enc_index(d, tpl.images(bytes(d), oo)[j_], S2.vib_button(a, t))
    HS = 'menu/nTplCommon.dat/02EC560_0_116x52_f8.png'                          # 정보 화면 하이스코어 칸의 点(img_map 누락, 2026-11-02)
    a = np.asarray(Image.open(os.path.join(TEX, HS)).convert('RGBA')).copy(); S2.mark(a.copy(), (78, 17, 102, 42), 62, '점', 17, S2.bright(a, (80, 19, 100, 40)), (90, 30))
    for r_, o_, j_ in [('menu/nTplCommon.dat', 0x2EC560, 0)] + dup.get(HS, []):
        d = buf(r_); enc_index(d, tpl.images(bytes(d), o_)[j_], S2.LAST[0])
    print('하이스코어 칸 점', 1 + len(dup.get(HS, [])))
    for rel, b in bufs.items():
        q = os.path.join(OUT, rel); os.makedirs(os.path.dirname(q), exist_ok=True); open(q, 'wb').write(b)
    print(dict(c), '파일', len(bufs))
    open(os.path.join(ROOT, 'work', 'gfx_skip.tsv'), 'w', encoding='utf-8', newline=chr(10)).write(chr(10).join(chr(9).join(x) for x in log))


if __name__ == '__main__':
    main()
