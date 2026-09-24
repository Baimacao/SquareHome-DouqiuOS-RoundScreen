#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按亮度剖面找图标方块：图标明显比背景暗。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from PIL import Image

PATCHED = r"C:\Users\B1807\.dsh\attachments\v1\objects\25\250b1d1e8c9507406e554f85ffc54edfe67e62a84e64e7c6407132c96bb939b7"
ORIG = r"C:\Users\B1807\.dsh\attachments\v1\objects\bc\bce3094515fbc7996cae293a60f8641a54b74d471fcca672830e6e83eff8941c"

# 图标带（由行距 78、首行 top=48 推得）
BANDS_P = [(58, 115), (136, 193), (214, 271), (292, 349), (370, 427)]
BANDS_O = [(134, 181), (211, 258), (288, 335), (365, 412)]


def profile(path, bands, label):
    im = Image.open(path).convert("L")
    px = im.load()
    print("=====", label)
    for (y0, y1) in bands:
        lum = []
        for x in range(0, 320):
            s = sum(px[x, y] for y in range(y0, y1 + 1)) / float(y1 - y0 + 1)
            lum.append(s)
        # 找显著暗区（相对该行左半部分的中位数）
        base = sorted(lum[0:20])[len(lum[0:20]) // 2]
        dark = [x for x, v in enumerate(lum) if v < base - 12]
        runs = []
        if dark:
            s = dark[0]; p = dark[0]
            for x in dark[1:]:
                if x - p > 4:
                    if p - s >= 25:
                        runs.append((s, p))
                    s = x
                p = x
            if p - s >= 25:
                runs.append((s, p))
        print(f"  y={y0:>3}..{y1:<3} base_lum={base:>5.1f}  暗区: {runs}")


profile(ORIG, BANDS_O, "ORIGINAL (no patch)")
profile(PATCHED, BANDS_P, "PATCHED v2")
