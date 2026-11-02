# -*- coding: utf-8 -*-
r"""빌드 결과를 다시 풀어 원본과 나란히 → work/gfxprev/<묶음>_NN.png"""
import os, re, sys, glob, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tpl, numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); O = os.path.join(ROOT, 'work', 'gfxprev'); os.makedirs(O, exist_ok=True)
M = [l.split('\t') for l in open(os.path.join(ROOT, 'work', 'text', 'img_map.tsv'), encoding='utf-8').read().split('\n') if l]
cache = {}
def dec(root, rel, off, j):
    p = os.path.join(root, rel)
    if not os.path.exists(p): return None
    d = cache.setdefault(p, open(p, 'rb').read()); return tpl.decode_all(d, tpl.images(d, off)[j])
def pair(p):
    m = re.match(r'(.+)/([0-9A-F]+)_(\d+)_', p); rel, off, j = m[1], int(m[2], 16), int(m[3])
    a = np.asarray(Image.open(os.path.join(ROOT, 'work', 'tex', p)).convert('RGBA')); b = dec(os.path.join(ROOT, 'work', 'build', 'files'), rel, off, j)
    return a, b
def sheet(tag, ps, W=1050, H=1380):
    n = 0; cv = Image.new('RGB', (W, H), (70, 0, 70)); x = y = rh = 0
    def flush():
        nonlocal n, cv, x, y, rh
        cv.crop((0, 0, W, min(H, y + rh + 4))).save(os.path.join(O, '%s_%02d.png' % (tag, n))); n += 1; cv = Image.new('RGB', (W, H), (70, 0, 70)); x = y = rh = 0
    for p in ps:
        a, b = pair(p)
        if b is None: continue
        s = np.concatenate([a, np.full((a.shape[0], 3, 4), 255, np.uint8), b], 1)
        i = Image.fromarray(s); bg = Image.new('RGBA', i.size, (30, 60, 110, 255)); bg.alpha_composite(i); i = bg.convert('RGB')
        if i.width > W: i = i.crop((0, 0, W, i.height))
        if x + i.width > W: x = 0; y += rh + 4; rh = 0
        if y + i.height > H: flush()
        cv.paste(i, (x, y)); x += i.width + 8; rh = max(rh, i.height)
    flush(); return n
if __name__ == '__main__':
    for f in glob.glob(os.path.join(O, '*.png')): os.remove(f)
    al = [p for p, s in M if 'staff' not in p]
    print(sheet('all', al), len(al))
