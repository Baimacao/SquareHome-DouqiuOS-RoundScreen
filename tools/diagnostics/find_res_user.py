#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给定资源 ID，找出 R 类字段名 + 所有使用点（smali 里 sget 该字段的方法）。"""
import sys, io, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DEC = r"E:\B1807\Documents\DSH\squarehome-mod\decoded"
targets = sys.argv[1:] or ["0x7f11001b"]

field_re = re.compile(r"^\.field public static ([A-Za-z0-9_$]+):I = (0x[0-9a-f]{8})$")

# 1) 找 R 类字段定义
found = {}
for root, dirs, files in os.walk(DEC):
    if not re.search(r"[\\/]smali", root):
        continue
    for fn in files:
        if not fn.endswith(".smali"):
            continue
        p = os.path.join(root, fn)
        cls = None
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                for line in f:
                    if line.startswith(".class"):
                        m = re.search(r"L([\w/$]+);", line)
                        cls = m.group(1) if m else None
                    m = field_re.match(line.strip())
                    if m:
                        fid = m.group(2)
                        for t in targets:
                            if fid.lower() == t.lower():
                                found.setdefault(t, []).append((cls, m.group(1)))
        except OSError:
            pass

for t in targets:
    print(f"### {t}")
    for cls, field in found.get(t, []):
        print(f"  R field: Lcom/{cls};->{field}:I")
        # 2) 找使用点
        pat = re.compile(r"L" + re.escape(cls) + r";->" + re.escape(field) + r":I")
        for root, dirs, files in os.walk(DEC):
            if not re.search(r"[\\/]smali", root):
                continue
            for fn in files:
                if not fn.endswith(".smali"):
                    continue
                p = os.path.join(root, fn)
                try:
                    with open(p, encoding="utf-8", errors="replace") as f:
                        cur = None
                        for i, line in enumerate(f, 1):
                            if line.startswith(".method"):
                                cur = line.strip()
                            if pat.search(line):
                                rel = os.path.relpath(p, DEC)
                                print(f"    {rel}:{i}  {cur}   |  {line.strip()}")
                except OSError:
                    pass
