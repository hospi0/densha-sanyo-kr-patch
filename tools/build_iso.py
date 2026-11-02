# -*- coding: utf-8 -*-
r"""work/build/files → dist/build/RG4JC0_KR.iso (원본 ISO 제자리 패치, isopatch) — 먼저 재굽기 검산"""
import os, sys, struct, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import wiiiso, isopatch
SRC = os.path.join(ROOT, 'work', 'game.iso'); DST = os.path.join(ROOT, 'dist', 'build', 'RG4JC0_KR.iso'); FILES = os.path.join(ROOT, 'work', 'build', 'files')
f = open(SRC, 'rb'); f.seek(0x40000); cnt, tb = struct.unpack('>II', f.read(8)); f.seek(tb << 2)
pt = [struct.unpack('>II', f.read(8)) for _ in range(cnt)]; print('파티션', [(hex(o << 2), t) for o, t in pt])
off = [o << 2 for o, t in pt if t == 0][0]; assert off == 0xF800000, hex(off)
p = wiiiso.Partition(f, off); fs = p.load_fst()
repl = []
for dp, _, n in os.walk(FILES):
    for x in n:
        q = os.path.join(dp, x); repl.append(('/' + os.path.relpath(q, FILES).replace(os.sep, '/'), q)); assert repl[-1][0] in fs, repl[-1]
DOL = os.path.join(ROOT, 'work', 'build', 'main.dol')                          # 기본 기록표 열차 이름(tools/dol_kr.py)
if os.path.exists(DOL): repl.append(('/main.dol', DOL))
print(len(repl), [r[0] for r in repl])
os.makedirs(os.path.dirname(DST), exist_ok=True); f.close()
isopatch.main(SRC, DST, repl)
print('끝', os.path.getsize(DST))
