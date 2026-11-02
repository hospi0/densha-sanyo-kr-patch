# -*- coding: utf-8 -*-
r"""work/tex → work/ocr/<번호>.png(어두운 바탕 합성 → 뒤집기 → 3배), 목록 work/ocr/list.tsv"""
import os, sys
from PIL import Image, ImageOps
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(ROOT, 'work', 'tex'); O = os.path.join(ROOT, 'work', 'ocr'); os.makedirs(O, exist_ok=True)
L = []
for dp, _, fs in os.walk(T):
    for f in sorted(fs):
        if not f.endswith('.png'): continue
        p = os.path.join(dp, f); im = Image.open(p).convert('RGBA')
        if im.width < 16 or im.height < 10: continue
        if im.width * im.height > 700000: pass
        bg = Image.new('RGBA', im.size, (20, 24, 50, 255)); bg.alpha_composite(im)
        g = ImageOps.autocontrast(bg.convert('L')); s = 3 if max(im.size) * 3 < 9000 else 1
        g = g.resize((im.width * s, im.height * s), Image.LANCZOS)
        k = '%05d' % len(L); ImageOps.invert(g).save(os.path.join(O, k + '.png')); L.append((k, os.path.relpath(p, T).replace(os.sep, '/')))
open(os.path.join(O, 'list.tsv'), 'w', encoding='utf-8', newline='\n').write('\n'.join('%s\t%s' % x for x in L))
print(len(L))
