#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在每个行带里用竖直边缘检测找图标左右边缘（图标是清晰的圆角方块，背景是模糊壁纸）。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from PIL import Image

PATCHED = r"C:\Users\B1807\.dsh\attachments\v1\objects\25\250b1d1e8c9507406e554f85ffc54edfe67e62a84e64e7c6407132c96bb939b7"
ORIG = r"C:\Users\B1807\.dsh\attachments\v1\objects\bc\bce3094515fbc7996cae293a60f8641a54b74d471fcca672830e6e83eff8941c"

# 行带（y0,y1）由上一轮白色文字测量得到
BANDS_PATCHED = [(66, 89), (142, 169), (223, 241), (284, 331), (361, 408)]
BANDS_ORIG = [(149, 168), (225, 246), (303, 322), (376, 401)]


def icon_edges(path, bands, xlim=340):
    im = Image.open(path).convert("L")
    px = im.load()
    print("=====", path.split("\\")[-1][:16])
    for (y0, y1) in bands:
        prof = []
        for x in range(3, xlim):
            s = 0
            for y in range(y0, y1 + 1):
                s += abs(px[x + 3, y] - px[x - 3, y])
            prof.append((s, x))
        prof.sort(reverse=True)
        peaks = []
        for s, x in prof:
            if all(abs(x - p[1]) > 12 for p in peaks):
                peaks.append((s, x))
            if len(peaks) == 4:
                break
        peaks.sort(key=lambda t: t[1])
        print(f"  y={y0:>3}..{y1:<3} 边缘峰: " + ", ".join(f"x={x}({s})" for s, x in peaks))


icon_edges(ORIG, BANDS_ORIG)
icon_edges(PATCHED, BANDS_PATCHED)
