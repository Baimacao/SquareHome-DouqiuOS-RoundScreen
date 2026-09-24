#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接打印每行的列平均亮度剖面，用眼睛定位图标方块（背景是平滑模糊的，图标是突变块）。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from PIL import Image

P = r"C:\Users\B1807\.dsh\attachments\v1\objects\25\250b1d1e8c9507406e554f85ffc54edfe67e62a84e64e7c6407132c96bb939b7"
im = Image.open(P).convert("L")
px = im.load()

# 行中心来自标签文字带；图标带 = 中心 ±28
centers = [77, 155, 232, 307, 384]
for c in centers:
    y0, y1 = c - 26, c + 26
    vals = []
    for x in range(0, 336, 4):
        vals.append(int(sum(px[x + dx, y] for dx in range(4) for y in range(y0, y1 + 1)) / (4.0 * (y1 - y0 + 1))))
    line = " ".join(f"{x:>3}:{v:>3}" for x, v in zip(range(0, 336, 4), vals))
    print(f"row center y={c}")
    print("   ", line)
    print()
