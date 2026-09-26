#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列出 app 用到、但 zh-rTW / zh-rCN 缺失的字符串（完整英文原文），供翻译用。"""
import io, os, re, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
W = r"E:\B1807\Documents\DSH\squarehome-mod\decoded"


def load(path):
    out = {}
    name = None
    if not os.path.exists(path):
        return out
    for line in io.open(path, encoding="utf-8"):
        m = re.search(r'<string name="([^"]+)"', line)
        if m:
            name = m.group(1)
        m2 = re.search(r"<string name=\"[^\"]+\"[^>]*>(.*)</string>", line)
        if m2 and name:
            out[name] = m2.group(1)
    return out


en = load(os.path.join(W, "res", "values", "strings.xml"))
tw = load(os.path.join(W, "res", "values-zh-rTW", "strings.xml"))
cn = load(os.path.join(W, "res", "values-zh-rCN", "strings.xml"))

ids = {}
for line in io.open(os.path.join(W, "res", "values", "public.xml"), encoding="utf-8"):
    m = re.search(r'<public type="(\w+)" name="([^"]+)" id="(0x[0-9a-f]+)"', line)
    if m:
        ids[m.group(3).lower()] = (m.group(1), m.group(2))
used = set()
for line in io.open(os.path.join(W, "smali_classes4", "com", "ss", "squarehome2", "mc.smali"), encoding="utf-8"):
    m = re.match(r"\.field public static ([A-Za-z0-9_$]+):I = (0x[0-9a-f]+)", line.strip())
    if m:
        t, n = ids.get(m.group(2).lower(), ("?", "?"))
        if t == "string":
            used.add(n)

missing = sorted(n for n in used if n in en and n not in tw)
print(f"共 {len(missing)} 条（app 用到 / zh-rTW 缺失）\n")
for i, n in enumerate(missing, 1):
    print(f"{i:>3}. {n}\n     EN: {en[n]}")
