# -*- coding: utf-8 -*-
r"""받은 번역 대조: 번호·JP 일치, 빈칸, 줄 수(／), 일본어 잔존, 용어 집계"""
import os, re, sys, glob, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
jp = {}
for l in open(os.path.join(ROOT, 'work', 'text', 'jp.tsv'), encoding='utf-8').read().split('\n')[1:]:
    if l: c = l.split('\t'); jp[c[0]] = c
ko = {}; bad = []
for p in sorted(glob.glob(os.path.join(ROOT, 'my files', '번역', '*.tsv'))):
    for n, l in enumerate(open(p, encoding='utf-8-sig').read().split('\n')[1:], 2):
        if not l: continue
        c = l.split('\t')
        if len(c) != 5 or c[0] not in jp or jp[c[0]][3] != c[3]: bad.append((os.path.basename(p), n, l[:90])); continue
        ko[c[0]] = c[4]
print('원문', len(jp), '번역', len(ko), '불량', len(bad), bad[:6])
print('빈', [n for n in jp if not ko.get(n, '').strip()][:20])
print('줄 수 다름', len(d := [n for n in ko if ko[n].count('／') != jp[n][3].count('／')]))
for n in d[:30]: print(n, jp[n][3][:40], '|', ko[n][:40])
print('일본어 잔존', [(n, ko[n][:30]) for n in ko if re.search('[ぁ-ヺ一-龥]', ko[n])][:20])
print('글자', collections.Counter(c for k in ko.values() for c in k if not ('가' <= c <= '힣') and not c.isalnum() and c not in ' ').most_common(30))
