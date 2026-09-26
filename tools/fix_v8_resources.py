#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v8 资源修修补补：
   1) aapt2 不接受 `$` 开头的资源名 -> 把 12 个 $avd_* 文件改名（去掉 $），
      并同步更新 4 个父 AVD 里的 @drawable/$avd_... 引用（除父 AVD 外无人引用它们）
   2) 修 today_24h / today_24h_m 的引号（需要写成 "\"'今天' HH:mm\""）"""
import io, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
W = r"E:\B1807\Documents\DSH\squarehome-mod\decoded"
DRAW = os.path.join(W, "res", "drawable")

# 1) rename $xxx -> xxx
renamed = []
for fn in os.listdir(DRAW):
    if fn.startswith("$"):
        new = fn[1:]
        os.replace(os.path.join(DRAW, fn), os.path.join(DRAW, new))
        renamed.append((fn, new))
print(f"1) renamed {len(renamed)} drawables (dropped leading $)")

# fix references in the 4 parent AVDs
fixed = 0
for fn in os.listdir(DRAW):
    if fn.endswith(".xml") and not fn.startswith("$"):
        p = os.path.join(DRAW, fn)
        t = io.open(p, encoding="utf-8").read()
        if "@drawable/$" in t:
            t2 = t.replace("@drawable/$", "@drawable/")
            io.open(p, "w", encoding="utf-8", newline="\n").write(t2)
            fixed += 1
            print(f"   refs fixed in {fn}")
print(f"   {fixed} files had references updated")

# 2) today_24h / today_24h_m quoting
pat = re.compile(r'(<string name="(?:today_24h|today_24h_m)">)(.*?)(</string>)')
tot = 0
for d in ("values", "values-zh-rTW", "values-zh-rCN"):
    p = os.path.join(W, "res", d, "strings.xml")
    if not os.path.exists(p):
        continue
    t = io.open(p, encoding="utf-8").read()

    def rep(m):
        global tot
        val = m.group(2)
        if val.startswith('"') and val.endswith('"'):
            return m.group(0)
        tot += 1
        return m.group(1) + '"' + val + '"' + m.group(3)

    t2 = pat.sub(rep, t)
    io.open(p, "w", encoding="utf-8", newline="\n").write(t2)
print(f"2) quoted {tot} today_24h* values")
