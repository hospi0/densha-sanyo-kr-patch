# -*- coding: utf-8 -*-
r"""DAT('DAT\0' [개수][오프셋·크기]) · TPL 읽기(C4·C8·I8·CMPR, CLUT RGB5A3/IA8/RGB565) → numpy RGBA"""
import struct
import numpy as np


def dat(d):
    if d[:4] != b'DAT\0': return [(0, len(d))]
    n = struct.unpack_from('>I', d, 4)[0]
    return [struct.unpack_from('>II', d, 8 + i * 8) for i in range(n)]


def images(d, o):
    if d[o:o + 4] != bytes.fromhex('0020AF30'): return []
    n, t = struct.unpack_from('>II', d, o + 4); out = []
    for i in range(n):
        im, pal = struct.unpack_from('>II', d, o + t + i * 8)
        h, w, fmt, data = struct.unpack_from('>HHII', d, o + im)
        p = None
        if pal: pn, _, pf, pd = struct.unpack_from('>HHII', d, o + pal); p = (pn, pf, o + pd)
        out.append((w, h, fmt, o + data, p))
    return out


def clut(d, p):
    n, f, o = p; a = np.frombuffer(d, '>u2', n, o).astype(int); r = np.zeros((n, 4), np.uint8)
    if f == 0: r[..., 0] = a & 255; r[..., 1] = r[..., 2] = r[..., 0]; r[..., 0] = r[..., 1] = r[..., 2] = a & 255; r[..., 3] = a >> 8
    elif f == 1:
        r[..., 0] = (a >> 11 & 31) * 255 // 31; r[..., 1] = (a >> 5 & 63) * 255 // 63; r[..., 2] = (a & 31) * 255 // 31; r[..., 3] = 255
    else:
        op = a >> 15 == 1
        r[..., 0] = np.where(op, (a >> 10 & 31) * 255 // 31, (a >> 8 & 15) * 17); r[..., 1] = np.where(op, (a >> 5 & 31) * 255 // 31, (a >> 4 & 15) * 17)
        r[..., 2] = np.where(op, (a & 31) * 255 // 31, (a & 15) * 17); r[..., 3] = np.where(op, 255, (a >> 12 & 7) * 36)
    return r


def decode(d, im):
    w, h, f, o, p = im; bw, bh, bits = {8: (8, 8, 4), 9: (8, 4, 8), 1: (8, 4, 8), 0: (8, 8, 4)}.get(f, (0, 0, 0))
    if not bw: return None
    bx, by = (w + bw - 1) // bw, (h + bh - 1) // bh
    a = np.frombuffer(d, np.uint8, bx * by * bw * bh * bits // 8, o)
    if bits == 4: a = np.stack([a >> 4, a & 15], 1).ravel()
    a = a.reshape(by, bx, bh, bw).transpose(0, 2, 1, 3).reshape(by * bh, bx * bw)[:h, :w]
    if p: return clut(d, p)[a]
    v = a * 17 if bits == 4 else a
    return np.stack([v, v, v, np.full_like(v, 255)], -1).astype(np.uint8)


def _block(blk):
    c0, c1 = struct.unpack('>HH', blk[:4]); P = np.zeros((4, 4), np.uint8)
    def c(v): return ((v >> 11 & 31) * 255 // 31, (v >> 5 & 63) * 255 // 63, (v & 31) * 255 // 31, 255)
    a, b = c(c0), c(c1)
    if c0 > c1: pal = [a, b, tuple((2 * x + y) // 3 for x, y in zip(a, b)), tuple((x + 2 * y) // 3 for x, y in zip(a, b))]
    else: pal = [a, b, tuple((x + y) // 2 for x, y in zip(a, b)), (0, 0, 0, 0)]
    idx = [(blk[4 + y] >> (6 - 2 * x)) & 3 for y in range(4) for x in range(4)]
    return np.array([pal[i] for i in idx], np.uint8).reshape(4, 4, 4)


def decode_all(d, im):
    w, h, f, o, p = im
    if f in (0, 1, 2, 8, 9) and f != 2:
        if f == 0:                                                               # I4
            bx, by = (w + 7) // 8, (h + 7) // 8; a = np.frombuffer(d, np.uint8, bx * by * 32, o); a = np.stack([a >> 4, a & 15], 1).ravel()
            a = a.reshape(by, bx, 8, 8).transpose(0, 2, 1, 3).reshape(by * 8, bx * 8)[:h, :w] * 17
            return np.stack([a, a, a, np.full_like(a, 255)], -1).astype(np.uint8)
        return decode(d, im)
    if f == 14:
        bx, by = (w + 7) // 8, (h + 7) // 8; out = np.zeros((by * 8, bx * 8, 4), np.uint8); q = o
        for yy in range(by):
            for xx in range(bx):
                for sy in (0, 4):
                    for sx in (0, 4):
                        out[yy * 8 + sy:yy * 8 + sy + 4, xx * 8 + sx:xx * 8 + sx + 4] = _block(d[q:q + 8]); q += 8
        return out[:h, :w]
    if f in (3, 4, 5, 6, 2):
        bw, bh = {2: (8, 4), 3: (4, 4), 4: (4, 4), 5: (4, 4), 6: (4, 4)}[f]
        bx, by = (w + bw - 1) // bw, (h + bh - 1) // bh; out = np.zeros((by * bh, bx * bw, 4), np.uint8)
        if f == 6:
            q = o
            for yy in range(by):
                for xx in range(bx):
                    ar = np.frombuffer(d, np.uint8, 32, q); gb = np.frombuffer(d, np.uint8, 32, q + 32); q += 64
                    out[yy * 4:yy * 4 + 4, xx * 4:xx * 4 + 4] = np.stack([ar[1::2].reshape(4, 4), gb[0::2].reshape(4, 4), gb[1::2].reshape(4, 4), ar[0::2].reshape(4, 4)], -1)
            return out[:h, :w]
        if f == 2:
            a = np.frombuffer(d, np.uint8, bx * by * 32, o).reshape(by, bx, 4, 8).transpose(0, 2, 1, 3).reshape(by * 4, bx * 8)
            v = (a & 15) * 17; al = (a >> 4) * 17; return np.stack([v, v, v, al], -1).astype(np.uint8)[:h, :w]
        a = np.frombuffer(d, '>u2', bx * by * 16, o).reshape(by, bx, 4, 4).transpose(0, 2, 1, 3).reshape(by * 4, bx * 4).astype(int)
        P = np.arange(0)
        if f == 3: v = a & 255; al = a >> 8; return np.stack([v, v, v, al], -1).astype(np.uint8)[:h, :w]
        r = clut(a.tobytes() if False else struct.pack('>%dH' % a.size, *a.ravel().tolist()), (a.size, 1 if f == 4 else 2, 0))
        return r.reshape(a.shape[0], a.shape[1], 4)[:h, :w]
    return None
