#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定位 Square Home 应用抽屉（app drawer）列表视图的实现类。"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"E:\B1807\Documents\DSH\douqiu-os\tools")
from dex_inspect_compat import Dex
import zipfile

APK = r"E:\B1807\Documents\DSH\squarehome-mod\squarehome-orig.apk"
z = zipfile.ZipFile(APK)
names = sorted([n for n in z.namelist() if re.match(r"classes\d*\.dex$", n)],
               key=lambda s: (len(s), s))

dexes = [(n, Dex(z.read(n))) for n in names]
for n, d in dexes:
    allc = [desc for desc, off in d.classes()]
    print(f"=== {n}: {len(allc)} classes ===")

# 目标 1：com/ss/ 下的视图与 adapter
KEY = re.compile(r"(drawer|Drawer|Adapter|List)", re.I)
for n, d in dexes:
    hits = [desc for desc, off in d.classes() if desc.startswith("Lcom/ss/")]
    sel = [h for h in hits if KEY.search(h)]
    print(f"--- {n}: {len(hits)} com/ss classes, {len(sel)} matching ---")
    for h in sorted(sel):
        print("   ", h)

# 目标 2：哪些类的字符串常量里出现 item_appdrawer_list / layout_appdrawer
WANT = ("item_appdrawer_list", "layout_appdrawer")
for n, d in dexes:
    for desc, off in d.classes():
        if not desc.startswith("Lcom/ss/"):
            continue
        try:
            ints, strs = d.class_consts(desc)
        except Exception:
            continue
        for w in WANT:
            if any(s == w for s in strs):
                print(f"[REFLECT] {n} {desc} -> {w}")
