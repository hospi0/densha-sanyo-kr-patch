# -*- coding: utf-8 -*-
r"""my files/번역 → work/text/ko.tsv: 용어 통일·말줄임표·부호 뒤 공백(2026-11-01)"""
import os, re, glob, sys, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
# 전차로 GO 시리즈 용어(파이널·프로·여정편·EX 표 대조) + 거센소리 규칙
TERMS = [('기관사', '운전사'), ('다이어', '다이아'), ('운행표', '다이아'), ('철덕', '철짱'), ('고다마', '코다마'), ('고쿠라', '코쿠라'), ('신고베', '신코베'), ('신구라시키', '신쿠라시키'), ('도쿠야마', '토쿠야마'), ('도쿄', '토쿄'),
         ('조기 도착', '조착'), ('지연 도착', '연착'), ('조기 출발', '조발'), ('지연 출발', '연발'), ('문닫힘등', '알림등'), ('정통 포인트', '정시 포인트'), ('시작 역', '시발역'), ('시작역', '시발역'), ('스키드음', '스킬음'), ('하이 스코어', '하이스코어'),
         ('출발 전 브레이크', '발차 전 브레이크'), ('출발 전 경적', '발차 전 경적'), ('출발 직후', '발차 직후'), ('平担', '평지')]
# 그림 낱말(판정·평가 라벨)은 붙여 씀 — 파이널/EX 규칙
TIGHT = '남은 거리|ATC 비상 브레이크|비상 브레이크|선행 열차 따라잡음|ATC 미확인 정차|ATC 브레이크 작동|브레이크 취급 주의|발차 전 브레이크 해제|발차 직후 브레이크|가속 중 브레이크|알림등 확인 실수|제한 속도 초과|예정 외 정차|경적 과다|발차 전 경적|확인 실패|정차역 통과|정지 위치|표지·신호 준수|안전성 배려|적정 속도 유지|다이아 정확도'
ONE = {'00014': '정시／정속', '00003': '끔 비상 해제 －－ N', '00012': '평지', '00015': '정속 정시 포인트', '00023': '선행열차가까움', '00148': '남은 [　]체', '00762': '가 추가되었습니다', '00778': '합계 점수 점', '00478': '전 구간 주파!'}
jp = {}
for l in open(os.path.join(ROOT, 'work', 'text', 'jp.tsv'), encoding='utf-8').read().split(chr(10))[1:]:
    if l: c = l.split(chr(9)); jp[c[0]] = c
ko = {}
for p in glob.glob(os.path.join(ROOT, 'my files', '번역', '*.tsv')):
    for l in open(p, encoding='utf-8-sig').read().split(chr(10))[1:]:
        if l: c = l.split(chr(9)); ko[c[0]] = c[4]
ch = 0
for n in ko:
    k = o = ko[n]
    for a, b in TERMS: k = k.replace(a, b)
    k = k.replace('......', '…').replace('...', '…').replace('・・・', '…'); k = re.sub('…{2,}', '…', k)
    k = re.sub(r'([.,!?！？…])[ 　]+(?=\S)', r'\1', k)
    if '／' not in k and len(k) <= 16:
        for m in TIGHT.split('|'):
            if k == m: k = k.replace(' ', '')
    k = ONE.get(n, k)
    ko[n] = k; ch += k != o
with open(os.path.join(ROOT, 'work', 'text', 'ko.tsv'), 'w', encoding='utf-8', newline=chr(10)) as f:
    for n, c in jp.items():
        if c[3].startswith('0123456789'): continue
        f.write('%s\t%s\t%s\t%s\t%s\n' % (n, c[1], c[2], c[3], ko[n]))
print('바뀐 줄', ch, '· 쓴 줄', len(jp))
