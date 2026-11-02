# -*- coding: utf-8 -*-
r"""교정 시트: 그림(1배) + 번호·판독문 → work/review/NN.png"""
import os, re, glob
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); T = os.path.join(ROOT, 'work', 'tex'); O = os.path.join(ROOT, 'work', 'review'); os.makedirs(O, exist_ok=True)
F = ImageFont.truetype(r'C:\Windows\Fonts\msgothic.ttc', 15)
L = [l.split('\t') for l in open(os.path.join(ROOT, 'work', 'text', 'jp.tsv'), encoding='utf-8').read().split('\n')[1:] if l]
W, H = 1040, 1400; cv = None; n = 0; y = 0
def flush():
    global cv, n
    if cv: cv.crop((0, 0, W, y + 2)).save(os.path.join(O, '%02d.png' % n)); n += 1
for f in glob.glob(os.path.join(O, '*.png')): os.remove(f)
for r in L:
    if int(r[0]) < 376: continue
    p = re.sub(r'\(×\d+\)$', '', r[1]); im = Image.open(os.path.join(T, p)).convert('RGBA')
    bg = Image.new('RGBA', im.size, (24, 30, 70, 255)); bg.alpha_composite(im); bg = bg.convert('RGB')
    if bg.height > 100: bg = bg.resize((bg.width // 2, bg.height // 2))
    if bg.width > W: bg = bg.crop((0, 0, W, bg.height))
    h = bg.height + 18
    if cv is None or y + h > H: flush(); cv = Image.new('RGB', (W, H), (0, 0, 0)); y = 0
    d = ImageDraw.Draw(cv); d.text((2, y + 1), r[0] + ' ' + r[3][:64], font=F, fill=(255, 240, 0)); cv.paste(bg, (0, y + 17)); y += h + 2
flush(); print(n)
