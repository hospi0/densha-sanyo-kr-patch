# -*- coding: utf-8 -*-
r"""파일 전체에서 TPL 머리를 훑어 PNG 로(같은 화소는 한 번만) → work/tex/<폴더>/<파일>/<오프셋>_<번호>_WxH_fN.png + work/tex/index.tsv"""
import os, sys, hashlib, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import tpl
from PIL import Image
R = os.path.join(ROOT, 'work', 'disc', 'DATA', 'files'); OUT = os.path.join(ROOT, 'work', 'tex'); M = bytes.fromhex('0020AF30')
SUB = sys.argv[1:] or ['menu', 'game2d', 'system', 'cockpit', 'kids', 'mapanim']
seen = {}; rows = []; c = collections.Counter()
for sub in SUB:
    for dp, _, fs in os.walk(os.path.join(R, sub)):
        for f in sorted(fs):
            p = os.path.join(dp, f); d = open(p, 'rb').read(); o = d.find(M); rel = os.path.relpath(p, R).replace(os.sep, '/')
            while o >= 0:
                if o % 4 == 0:
                    try: ims = tpl.images(d, o)
                    except Exception: ims = []
                    if ims and all(0 < w <= 2048 and 0 < h <= 2048 for w, h, *_ in ims):
                        for j, im in enumerate(ims):
                            c['그림'] += 1
                            try: a = tpl.decode_all(d, im)
                            except Exception: a = None
                            if a is None: c['못 풂 f%d' % im[2]] += 1; continue
                            k = hashlib.md5(a.tobytes()).hexdigest()
                            if k in seen: c['중복'] += 1; rows.append((rel, o, j, im[0], im[1], im[2], seen[k])); continue
                            q = os.path.join(OUT, rel, '%07X_%d_%dx%d_f%d.png' % (o, j, im[0], im[1], im[2])); os.makedirs(os.path.dirname(q), exist_ok=True)
                            Image.fromarray(a).save(q); seen[k] = os.path.relpath(q, OUT).replace(os.sep, '/'); rows.append((rel, o, j, im[0], im[1], im[2], '')); c['저장'] += 1
                o = d.find(M, o + 4)
with open(os.path.join(OUT, 'index.tsv'), 'a', encoding='utf-8', newline='\n') as f:
    for r in rows: f.write('%s\t%X\t%d\t%d\t%d\t%d\t%s\n' % r)
print(SUB, dict(c))
