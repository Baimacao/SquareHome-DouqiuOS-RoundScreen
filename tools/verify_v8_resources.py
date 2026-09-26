#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v8 资源核对（按 ID/名称/配置/值比较，忽略文件路径行与 PUBLIC 标记）。"""
import io, re, collections, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
W = r"E:\B1807\Documents\DSH\squarehome-mod"

a = [l.rstrip() for l in io.open(W + r"\work3\v8_res_orig.txt", encoding="utf-8")]
b = [l.rstrip() for l in io.open(W + r"\work3\v8_res_new.txt", encoding="utf-8")]
norm = lambda L: [re.sub(r"\s+PUBLIC$", "", x) for x in L]
na = [x for x in norm(a) if "(file) res/" not in x]
nb = [x for x in norm(b) if "(file) res/" not in x]
sa, sb = set(na), set(nb)
d1 = [x for x in na if x not in sb]
d2 = [x for x in nb if x not in sa]
print("ID/name/config-level lines: orig=%d new=%d" % (len(na), len(nb)))
print("only-orig=%d only-new=%d\n" % (len(d1), len(d2)))

DOLLAR = "$"


def kind(x):
    if DOLLAR + "avd" in x or "/" + DOLLAR in x or DOLLAR + "mtrl" in x:
        return "renamed $ resource"
    if "douqiu" in x:
        return "douqiu new"
    if re.search(r"[\u4e00-\u9fff]", x):
        return "new zh translation"
    return "OTHER"


for tag, d in (("only-orig", d1), ("only-new", d2)):
    c = collections.Counter(kind(x) for x in d)
    print("---", tag, "---")
    for k, v in c.most_common():
        print("   %-24s %d" % (k, v))
print("\n--- OTHER samples ---")
for x in [y for y in d1 + d2 if kind(y) == "OTHER"][:16]:
    print("   ", x.strip()[:112])
