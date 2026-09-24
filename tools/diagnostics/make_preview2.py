#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2 几何示意：把「紧贴圆边」画出来，并对比 v1（有内切方平台段）与 v2（纯圆弧）。"""
import sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from PIL import Image, ImageDraw

W = H = 480
R = 240
CY = 240
ROW_H = 77
ICON_H = 57
ICON_OFF = 10          # icon top inside the row (10dp @ density 1.0)
ICON_LEFT = 10         # icon left edge inside the row
MARGIN = 2             # same EDGE_MARGIN as the helper
MIN_CONTENT_V1 = 80    # v1 clamp (removed in v2)


def gap_at(ym):
    """圆盘在距圆心 ym 处相对屏幕边缘的收进量"""
    if ym >= R:
        return R
    return math.ceil(R - math.sqrt(R * R - ym * ym))


def offset_v2(row_top):
    band_top = row_top + ICON_OFF
    band_bottom = band_top + ICON_H
    ym = max(abs(band_top - CY), abs(band_bottom - CY))
    return max(0, gap_at(ym) + MARGIN - ICON_LEFT)


def offset_v1(row_top):
    """旧版：整行 + 双侧 padding + MIN_CONTENT 平台段（会被截到 160）"""
    d1 = abs(row_top - CY)
    d2 = abs(row_top + ROW_H - CY)
    ym = max(d1, d2)
    return min(max(0, R - MIN_CONTENT_V1), gap_at(ym))


print("== 实测截图那一屏（未滚动）==")
print(f"{'行':>3} {'y':>11} {'v1 内缩':>8} {'v2 偏移':>8} {'图标左边缘':>10}")
for i in range(4):
    top = 124 + i * ROW_H
    print(f"{i+1:>3} {top:>5}..{top+ROW_H:<5} {offset_v1(top):>8} {offset_v2(top):>8} {ICON_LEFT+offset_v2(top):>10}")

# ---------------------------------------------------------------- 画图
PAD = 24
img = Image.new("RGB", (W * 3 + PAD * 4, H + PAD * 2 + 44), (24, 24, 28))
d = ImageDraw.Draw(img)


def circle(x0, y0):
    for a in range(0, 360, 4):
        a2 = a + 2
        d.line([x0 + W / 2 + R * math.cos(math.radians(a)), y0 + H / 2 + R * math.sin(math.radians(a)),
                x0 + W / 2 + R * math.cos(math.radians(a2)), y0 + H / 2 + R * math.sin(math.radians(a2))],
               fill=(255, 70, 70), width=2)


def chrome(x0, y0):
    d.rectangle([x0 + 170, y0 + 48, x0 + 310, y0 + 74], fill=(150, 148, 160))
    d.rounded_rectangle([x0 + 20, y0 + 428, x0 + 460, y0 + 474], 24, fill=(120, 118, 132))


def rows_panel(x0, title, tops, fn):
    y0 = PAD + 40
    d.rectangle([x0, y0, x0 + W, y0 + H], fill=(60, 58, 74))
    circle(x0, y0)
    chrome(x0, y0)
    for t in tops:
        off = fn(t)
        d.rectangle([x0 + off, y0 + t, x0 + W - off, y0 + t + ROW_H - 2], outline=(205, 205, 215))
        d.rounded_rectangle([x0 + off + ICON_LEFT, y0 + t + ICON_OFF,
                             x0 + off + ICON_LEFT + ICON_H, y0 + t + ICON_OFF + ICON_H], 8, fill=(238, 238, 248))
        lx = x0 + off + ICON_LEFT + ICON_H + 10
        d.rectangle([lx, y0 + t + 24, lx + 120, y0 + t + 46], fill=(240, 240, 250))
    d.text((x0 + 12, PAD + 8), title, fill=(255, 255, 255))


rows_panel(PAD, "BEFORE  straight rows (cut by the bezel)", [124 + i * ROW_H for i in range(4)], lambda t: 0)
rows_panel(PAD * 2 + W, "AFTER v1  clamped: flat 'inscribed' tail", [124 + i * ROW_H for i in range(4)], offset_v1)
rows_panel(PAD * 3 + W * 2, "AFTER v2  icon hugs the arc", [124 + i * ROW_H for i in range(4)], offset_v2)

# 第四个面板：图标左边缘随滚动位置变化的曲线（v1 vs v2）
x0 = PAD
y0 = PAD
img2 = Image.new("RGB", (W + PAD * 2, H + PAD * 2 + 40), (24, 24, 28))
d2 = ImageDraw.Draw(img2)
plot_y0, plot_h = PAD + 40, H
d2.rectangle([x0, plot_y0, x0 + W, plot_y0 + plot_h], fill=(30, 34, 40))


def to_px(row_top, off):
    return x0 + ICON_LEFT + off


for t in range(-40, 500, 4):
    d2.point((to_px(t, offset_v1(t)), plot_y0 + t), fill=(255, 170, 60))
    d2.point((to_px(t, offset_v2(t)), plot_y0 + t), fill=(90, 220, 140))
    d2.point((x0 + W / 2 - math.sqrt(max(0.0, R * R - min(R, abs(t + ICON_OFF + ICON_H / 2 - CY)) ** 2)), plot_y0 + t),
             fill=(255, 70, 70))
d2.text((x0 + 12, PAD + 8), "icon left edge vs scroll position: red=bezel, orange=v1, green=v2", fill=(255, 255, 255))
out = r"E:\B1807\Documents\DSH\squarehome-mod\ref\preview_round_inset_v2.png"
img.save(out)
img2.save(r"E:\B1807\Documents\DSH\squarehome-mod\ref\preview_arc_path_v2.png")
print("\n->", out)
print("-> ref\\preview_arc_path_v2.png")
