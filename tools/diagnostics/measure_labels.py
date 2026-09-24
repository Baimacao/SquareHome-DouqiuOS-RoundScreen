#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用白色标签文字定位每行，量出标签左边缘 → 反推图标位置与偏移。
同时对“未打补丁的截图”做同样测量以校准（基线偏移=0）。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from PIL import Image

IMGS = {
    "ORIGINAL(no patch)": r"C:\Users\B1807\.dsh\attachments\v1\objects\bc\bce3094515fbc7996cae293a60f8641a54b74d471fcca672830e6e83eff8941c",
    "PATCHED(v2)":        r"C:\Users\B1807\.dsh\attachments\v1\objects\25\250b1d1e8c9507406e554f85ffc54edfe67e62a84e64e7c6407132c96bb939b7",
}


def bands_of_white(path, xmax=420, ymax=428, thr=205, minpix=6):
    im = Image.open(path).convert("RGB")
    px = im.load()
    W, H = im.size
    ys = []
    for y in range(0, ymax):
        n = 0
        for x in range(0, xmax):
            r, g, b = px[x, y]
            if r > thr and g > thr and b > thr:
                n += 1
        ys.append(n)
    out, cur = [], None
    for y, n in enumerate(ys):
        if n >= minpix:
            cur = [y, y] if cur is None else [cur[0], y]
        else:
            if cur and cur[1] - cur[0] >= 12:
                out.append(tuple(cur))
            cur = None
    if cur and cur[1] - cur[0] >= 12:
        out.append(tuple(cur))
    res = []
    for (y0, y1) in out:
        xs = [x for x in range(0, xmax) for y in range(y0, y1 + 1)
              if all(c > thr for c in px[x, y])]
        if xs:
            res.append((y0, y1, min(xs), max(xs)))
    return res


for name, p in IMGS.items():
    print("=====", name)
    for (y0, y1, x0, x1) in bands_of_white(p):
        print(f"  label y={y0:>3}..{y1:<3}  x={x0:>3}..{x1:<3}   (label left={x0})")
