# -*- coding: utf-8 -*-
r"""main.dol 기본 기록표(0x17CCE0~0x17CEC0)의 열차 이름 → 한글 칸 번호 (2026-11-02 하스피 «운전사명에 규송마»)
  이름은 이름 입력판 첫 장의 칸 번호(0~79)로 저장 — こだま=09 41 1E 가 한글판에서 «규송마»로 찍혔다.
  → work/build/main.dol (build_iso 가 넣음)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import gfx_extra as X
SRC = os.path.join(ROOT, 'work', 'disc', 'DATA', 'sys', 'main.dol'); DST = os.path.join(ROOT, 'work', 'build', 'main.dol')
LO, HI = 0x17CCE0, 0x17CEC0
NAMES = {'こだま': (bytes.fromhex('09411E'), '코다마'), 'ひかり': (bytes.fromhex('1A0527'), '히카리'), 'のぞみ': (bytes.fromhex('18401F'), '노조미')}


def main():
    d = bytearray(open(SRC, 'rb').read()); n = 0
    for jp, (old, ko) in NAMES.items():
        new = bytes(X.SYL.index(c) for c in ko); assert max(new) < 80, (ko, new)
        i = d.find(old, LO)
        while 0 <= i < HI:
            d[i:i + 3] = new; n += 1; i = d.find(old, i + 3)
        assert d.find(old) < 0 or d.find(old) >= HI
    os.makedirs(os.path.dirname(DST), exist_ok=True); open(DST, 'wb').write(d)
    print('바꾼 이름', n, '→', DST)


if __name__ == '__main__':
    main()
