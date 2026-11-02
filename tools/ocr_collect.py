# -*- coding: utf-8 -*-
r"""OCR 결과 모으기 → work/ocr_all.tsv(그림·크기·형식·판독문)"""
import os, re, sys, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); O = os.path.join(ROOT, 'work', 'ocr')
L = [l.split('\t') for l in open(os.path.join(O, 'list.tsv'), encoding='utf-8').read().split('\n') if l]
rows = []
for k, p in L:
    t = os.path.join(O, 'img_%s.txt' % k)
    s = open(t, encoding='utf-8-sig').read().split('\n') if os.path.exists(t) else []
    s = [re.sub(r'(?<=[^ -~]) (?=[^ -~])', '', x).strip() for x in s if x.strip()]
    rows.append((k, p, '／'.join(s)))
open(os.path.join(ROOT, 'work', 'ocr_all.tsv'), 'w', encoding='utf-8', newline='\n').write('\n'.join('\t'.join(r) for r in rows))
J = re.compile('[ぁ-ヺ一-龥]')
has = [r for r in rows if len(J.findall(r[2])) >= 2]
print(len(rows), '일본어 2자 이상', len(has), '글자', sum(len(J.findall(r[2])) for r in has))
c = collections.Counter(r[1].split('/')[0] + '/' + r[1].split('/')[1] for r in has); print(c.most_common(30))
c = collections.Counter(r[1].split('/')[0] + '/' + r[1].split('/')[1] for r in rows); print(c.most_common(30))
