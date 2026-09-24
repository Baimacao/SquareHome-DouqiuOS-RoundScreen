#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""量两张 OOBE 截图：卡片边界、内容块、底部按钮的位置。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from PIL import Image

IMGS = {
    "tile_effect (磚塊效果)": r"C:\Users\B1807\.dsh\attachments\v1\objects\52\529a68d71881fcabf9681f39e006850dc716dc5434afab869a49059b97770127",
    "advice (想自訂更多?)":  r"C:\Users\B1807\.dsh\attachments\v1\objects\50\50ca78f5097e71c5e0ae32287bf49ea4c924e3fa5cc8bcf1ece8aa2d8cff3fce",
}

for name, p in IMGS.items():
    im = Image.open(p).convert("RGB")
    px = im.load()
    W, H = im.size
    print("=====", name, W, "x", H)
    row = (W // 2, None)
    # 1) 沿中轴找“卡片”的上下边界（白底 -> 灰卡片）
    def lum(x, y):
        r, g, b = px[x, y]
        return (r + g + b) / 3.0
    mid = W // 2
    col = [round(lum(mid, y)) for y in range(H)]
    print("  中轴亮度(每10px):", " ".join(f"{y}:{col[y]}" for y in range(0, H, 10)))
    # 2) 每行找“非白”像素范围（卡片/内容）
    for y in range(0, H, 30):
        xs = [x for x in range(W) if lum(x, y) < 245]
        if xs:
            print(f"  y={y:>3}  非白 x={min(xs):>3}..{max(xs):<3}")
    # 3) 底部按钮区
    print("  底部 20 行非白统计:")
    for y in range(H - 60, H, 10):
        xs = [x for x in range(W) if lum(x, y) < 200]
        seg = []
        if xs:
            s = xs[0]; pr = xs[0]
            for x in xs[1:]:
                if x - pr > 6:
                    seg.append((s, pr)); s = x
                pr = x
            seg.append((s, pr))
        print(f"    y={y:>3} 深色段: {seg}")
