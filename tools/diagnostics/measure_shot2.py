#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""量新截图里每行的图标位置，反推补丁实际算出来的偏移，跟圆弧的“应有值”对比。"""
import sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from PIL import Image

SRC = r"C:\Users\B1807\.dsh\attachments\v1\objects\25\250b1d1e8c9507406e554f85ffc54edfe67e62a84e64e7c6407132c96bb939b7"
im = Image.open(SRC).convert("RGB")
W, H = im.size
px = im.load()
print("screenshot:", W, "x", H)

R, CY = 240, 240


def gap_at(ym):
    if ym >= R:
        return R
    return math.ceil(R - math.sqrt(R * R - ym * ym))


# 图标是深色圆角方块：找每行里“连续深色块”的水平范围
def dark(x, y, thr=95):
    r, g, b = px[x, y]
    return (r + g + b) / 3 < thr


rows = []
y = 0
while y < H:
    # 该行是否有深色像素（图标区）
    xs = [x for x in range(0, W) if dark(x, y)]
    if len(xs) > 8:
        # 找连通段
        segs = []
        s = xs[0]
        p = xs[0]
        for x in xs[1:]:
            if x - p > 3:
                segs.append((s, p))
                s = x
            p = x
        segs.append((s, p))
        # 只保留宽度 30..90 的段（图标），排除底栏等
        segs = [sg for sg in segs if 30 <= sg[1] - sg[0] <= 90]
        if segs:
            rows.append((y, segs))
    y += 1

# 合并相邻行 -> 图标带
bands = []
cur = None
for y, segs in rows:
    seg = min(segs, key=lambda s: s[0])
    if cur is None:
        cur = [y, y, seg[0], seg[1]]
    elif y - cur[1] <= 2:
        cur[1] = y
        cur[2] = min(cur[2], seg[0])
        cur[3] = max(cur[3], seg[1])
    else:
        bands.append(tuple(cur))
        cur = [y, y, seg[0], seg[1]]
if cur:
    bands.append(tuple(cur))

print(f"\n{'图标带 y':>14} {'高':>4} {'图标 x':>10} {'实测偏移':>9} {'圆弧gap':>8} {'应有偏移':>9} {'差':>6}")
for (y0, y1, x0, x1) in bands:
    if y1 - y0 < 25:
        continue
    ym = max(abs(y0 - CY), abs(y1 - CY))
    gap = gap_at(ym)
    want = max(0, gap + 2 - 10)      # 补丁公式：gap + EDGE_MARGIN - 图标行内左偏移(10)
    got = x0 - 10
    print(f"{y0:>6}..{y1:<6} {y1-y0+1:>4} {x0:>5}..{x1:<4} {got:>9} {gap:>8} {want:>9} {got-want:>6}")
