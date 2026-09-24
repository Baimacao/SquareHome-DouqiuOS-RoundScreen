#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在编译后的 AXML 里按原始字节找字符串，定位哪些 layout 用了哪些自定义 View。"""
import sys, io, zipfile, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

APK = r"E:\B1807\Documents\DSH\squarehome-mod\squarehome-orig.apk"
z = zipfile.ZipFile(APK)

NEEDLES = [b"AnimateListView", b"AnimateGridView", b"com.ss.view", b"RecyclerView",
           b"FloatingButton", b"ListView", b"GridView", b"ViewPager"]

for e in sorted(z.namelist()):
    if not e.startswith("res/layout"):
        continue
    data = z.read(e)
    hits = []
    for n in NEEDLES:
        if n in data or n.decode().encode("utf-16-le") in data:
            hits.append(n.decode())
    if hits:
        print(f"{e}: {', '.join(hits)}")
