#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v8 最终核对：manifest 结构对比 / 新设置行 / 汉化字符串 / dex 钩子。"""
import io, os, re, subprocess, sys, zipfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
W = r"E:\B1807\Documents\DSH\squarehome-mod"
AAPT2 = r"E:\B1807\Documents\DSH\sdk\build-tools-r37\aapt2.exe"
ORIG = os.path.join(W, "squarehome-orig.apk")
NEW = os.path.join(W, "SquareHome_3.0.1-douqiuos-v8.apk")


def xmltree(apk, f):
    r = subprocess.run([AAPT2, "dump", "xmltree", "--file", f, apk],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return [l.rstrip() for l in r.stdout.splitlines()]


def res_dump(apk):
    r = subprocess.run([AAPT2, "dump", "resources", apk], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stdout.splitlines()


# 1) manifest
a = xmltree(ORIG, "AndroidManifest.xml")
b = xmltree(NEW, "AndroidManifest.xml")
na = [re.sub(r"\(line=\d+\)", "", x).strip() for x in a]
nb = [re.sub(r"\(line=\d+\)", "", x).strip() for x in b]
diff = [x for x in na if x not in set(nb)] + [x for x in nb if x not in set(na)]
print(f"1) manifest: orig={len(na)} new={len(nb)} lines | diff lines={len(diff)}")
for x in diff[:8]:
    print("     ", x[:120])

# 2) 新设置行
print("\n2) prefs_appdrawer 新设置行:")
for line in xmltree(NEW, "res/xml/prefs_appdrawer.xml"):
    if any(k in line for k in ("douqiu", "PreferenceCategory", "MyListPreference", "MyIntPreference",
                               "MySwitchPreference", "entryValues", "defaultValue", "dependency")):
        print("     ", line.strip()[:130])

# 3) 汉化 / 新字符串
print("\n3) 资源表里的新文案:")
d = res_dump(NEW)
for pat in ("douqiu_fit_mode_title", "douqiu_fade_scale_summary", "live_tile", "troubleshooting",
            "set_wallpaper_to", "work_apps"):
    hits = [x for x in d if pat in x]
    vals = [x for x in hits if re.search(r"[\u4e00-\u9fff]", x)]
    print(f"     {pat:<28} 条目 {len(hits)} | 含中文值 {len(vals)} | 例: {vals[0].strip()[:60] if vals else '-'}")

# 4) dex 钩子
print("\n4) dex 钩子:")
z = zipfile.ZipFile(NEW)
for dex, needles in (("classes.dex", [b"applyToGridView", b"scaleAnimation"]),
                     ("classes2.dex", [b"applyToGridView", b"scaleAnimation", b"RoundScreenInsets"]),
                     ("classes4.dex", [b"skipWallpaper", b"RoundScreenInsets"])):
    data = z.read(dex)
    print(f"     {dex}: " + ", ".join(f"{n.decode()}={n in data}" for n in needles))
print("\napk sha256:", __import__("hashlib").sha256(open(NEW, "rb").read()).hexdigest())
print("size:", os.path.getsize(NEW))
