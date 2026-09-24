#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""量一下截图里列表行的实际位置/尺寸，用于推算圆屏几何参数。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from PIL import Image

SRC = r"C:\Users\B1807\.dsh\attachments\v1\objects\bc\bce3094515fbc7996cae293a60f8641a54b74d471fcca672830e6e83eff8941c"
im = Image.open(SRC).convert("RGB")
W, H = im.size
print("screenshot:", W, "x", H)
px = im.load()

# 图标列的暗色像素统计（图标是深色圆角方块，背景是浅色模糊图）
def dark_rows(x0, x1, thr=90):
    rows = []
    for y in range(H):
        n = 0
        for x in range(x0, x1):
            r, g, b = px[x, y]
            if (r + g + b) / 3 < thr:
                n += 1
        rows.append(n)
    return rows

rows = dark_rows(20, 90)
# 找出连续的“有图标”区间
bands = []
cur = None
for y, n in enumerate(rows):
    if n > 10:
        if cur is None:
            cur = [y, y]
        else:
            cur[1] = y
    else:
        if cur is not None and cur[1] - cur[0] > 8:
            bands.append(tuple(cur))
        cur = None
if cur is not None:
    bands.append(tuple(cur))
print("dark bands in x=20..90:", bands)

# 每个 band 的水平范围（在该 band 的中间行扫描）
for (y0, y1) in bands:
    ym = (y0 + y1) // 2
    xs = [x for x in range(0, W) if sum(px[x, ym]) / 3 < 90]
    if xs:
        print(f"band y={y0}..{y1} (h={y1-y0+1}) mid-y={ym}: x={min(xs)}..{max(xs)} width={max(xs)-min(xs)+1}")

# 底部栏：扫 y=420..480 的行，找亮度变化
for y in range(H - 60, H, 10):
    row = [sum(px[x, y]) / 3 for x in range(0, W, 40)]
    print("y=%d  mean=%s" % (y, [int(v) for v in row]))
