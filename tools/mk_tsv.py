# -*- coding: utf-8 -*-
r"""OCR 초안 → work/text/jp.tsv + my files/tsv/sanyo_NNN.tsv(18KB 단위, 번호·그림·크기·JP·KO) — 판독은 Windows OCR 초안 + 잦은 오독 치환, 눈 검토 전"""
import os, re, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); LIMIT = 18 * 1024
FIX = [('ひなり', 'ひかり'), ('運転主', '運転士'), ('ー連', '一連'), ('プレーキ', 'ブレーキ'), ('嗚', '鳴'), ('コント一ラ', 'コントローラ'), ('サウ冫ド', 'サウンド'), ('マスつン', 'マスコン'), ('こ:だま', 'こだま'), ('ましよう', 'ましょう')]
J = re.compile('[ぁ-ヺ一-龥]')
rows = [l.split('\t') for l in open(os.path.join(ROOT, 'work', 'ocr_all.tsv'), encoding='utf-8').read().split('\n')]
JF = {}
fp = os.path.join(ROOT, 'work', 'text', 'jp_fix.tsv')
if os.path.exists(fp):
    for l in open(fp, encoding='utf-8').read().split(chr(10)):
        if l: x, y = l.split(chr(9)); JF[x] = y
pre = []; ps = {}
for k, p, s in rows:
    if len(J.findall(s)) < 2: continue
    for a, b in FIX: s = s.replace(a, b)
    s = re.sub(r'(?<=\d) (?=[系号両])|(?<=[系号]) (?=\d)', '', s)
    if s in ps: continue
    ps[s] = 1; pre.append(s)
RE = {s: JF.get('%05d' % (i + 1), s) for i, s in enumerate(pre)}


def norm(t):
    t = re.sub(r'(?<=\d) (?=\d)', '', t).replace('ひがり', 'ひかり').replace('ヒカリ', 'ひかり').replace('ひガり', 'ひかり').replace('ひガリ', 'ひかり').replace('小自', '小倉').replace('新自敷', '新倉敷').replace('新数', '新倉敷')
    t = re.sub('あ(?=[客疲願待急見])', 'お', t); t = re.sub(r'ますな ?[?？]', 'ますか？', t); t = re.sub(r'(?<=[ぁ-ん一-龥]) +(?=[!！?？])', '', t)
    m = re.match(r'(車内車掌放送|駅構内放送) *\( *(\S+) *\) *[:・]? *(.*)', t)
    if m: t = '%s(%s):%s' % (m[1], m[2], m[3])
    m = re.match(r'運転士一連の確認 *[:・]? *(.*)', t)
    if m: t = '運転士一連の確認:' + m[1].replace(' ', '')
    m = re.match(r'(運転士|CTC) *:? *「(.*)', t)
    if m: t = m[1] + (':' if m[1] == '運転士' else '') + '「' + m[2].replace(' ', '')
    return t


out = []; seen = {}; staff = []; imap = []
for k, p, s in rows:
    if len(J.findall(s)) < 2: continue
    for a, b in FIX: s = s.replace(a, b)
    s = re.sub(r'(?<=\d) (?=[系号両])|(?<=[系号]) (?=\d)', '', s)
    s = RE.get(s, s)
    if s == 'DROP': continue
    if s == 'STAFF': staff.append(p); continue
    s = norm(s)
    imap.append((p, s))
    if s in seen: seen[s][4] += 1; continue
    m = re.search(r'(\d+)x(\d+)_f(\d+)', p)
    r = ['%05d' % (len(out) + 1), p, m[1] + 'x' + m[2], s, 1]; seen[s] = r; out.append(r)
os.makedirs(os.path.join(ROOT, 'work', 'text'), exist_ok=True); os.makedirs(os.path.join(ROOT, 'my files', 'tsv'), exist_ok=True)
head = '번호\t그림\t크기\tJP\tKO\n'; rw = ['%s\t%s(×%d)\t%s\t%s\t' % (r[0], r[1], r[4], r[2], r[3]) for r in out]
open(os.path.join(ROOT, 'work', 'text', 'jp.tsv'), 'w', encoding='utf-8', newline='\n').write(head + '\n'.join(rw) + '\n')
ch = []; cur = []; sz = len(head.encode())
for r in rw:
    b = len((r + '\n').encode())
    if cur and sz + b > LIMIT: ch.append(cur); cur = []; sz = len(head.encode())
    cur.append(r); sz += b
if cur: ch.append(cur)
if len(ch) > 1 and sum(len((r + '\n').encode()) for r in ch[-1]) < LIMIT // 4: last = ch.pop(); ch[-1] += last
for f in glob.glob(os.path.join(ROOT, 'my files', 'tsv', 'sanyo_*.tsv')): os.remove(f)
for i, c in enumerate(ch): open(os.path.join(ROOT, 'my files', 'tsv', 'sanyo_%03d.tsv' % (i + 1)), 'w', encoding='utf-8', newline='\n').write(head + '\n'.join(c) + '\n')
nums = [int(r.split('\t')[0]) for c in ch for r in c]; assert nums == list(range(1, len(rw) + 1))
open(os.path.join(ROOT, 'work', 'text', 'img_map.tsv'), 'w', encoding='utf-8', newline=chr(10)).write(chr(10).join('%s	%s' % x for x in imap))
print('스태프 제외', len(staff)); print('고유 문구', len(out), '글자', sum(len(J.findall(r[3])) for r in out), 'TSV', len(ch))
