#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v9 核对：出货 dex 里钩子落在哪个方法（崩溃修复的关键）+ 视频壁纸类 + 设置行 + 文案。"""
import io, os, re, subprocess, sys, zipfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
W = r"E:\B1807\Documents\DSH\squarehome-mod"
JAR = os.path.join(W, "_tools", "lib", "apktool-cli-3.0.3.jar")
AAPT2 = r"E:\B1807\Documents\DSH\sdk\build-tools-r37\aapt2.exe"
APK = os.path.join(W, "SquareHome_3.0.1-douqiuos-v9.apk")
TMP = os.path.join(W, "work3", "v9check")
os.makedirs(TMP, exist_ok=True)

z = zipfile.ZipFile(APK)
for dex in ("classes.dex", "classes2.dex", "classes4.dex"):
    open(os.path.join(TMP, dex), "wb").write(z.read(dex))
    d = os.path.join(TMP, dex + ".smali")
    if os.path.exists(d):
        import shutil
        shutil.rmtree(d)
    subprocess.run(["java", "-cp", JAR, "com.android.tools.smali.baksmali.Main", "d",
                    os.path.join(TMP, dex), "-o", d, "-a", "21"], capture_output=True)

print("1) 钩子落点（每个都必须在预期方法内）")
targets = {
    "classes.dex.smali/com/ss/view/AnimateGridView$a.smali": ("onScroll", "DouqiuOS hook"),
    "classes2.dex.smali/com/ss/view/AnimateGridView.smali": ("onLayout|t()", "DouqiuOS hook"),
    "classes4.dex.smali/com/ss/squarehome2/fk.smali": ("k(", "DouqiuOS hook"),
}
for rel, (expect, marker) in targets.items():
    p = os.path.join(TMP, rel.replace("/", os.sep))
    lines = io.open(p, encoding="utf-8", errors="replace").read().splitlines()
    hits = []
    for i, l in enumerate(lines):
        if marker in l:
            m = [x for x in lines[:i] if x.startswith(".method")]
            hits.append(m[-1].strip() if m else "?")
    print(f"   {os.path.basename(p)}: {len(hits)} hooks -> " + "; ".join(hits))

print("\n2) 视频壁纸类 / 跳过自绘壁纸")
for dex in ("classes2.dex", "classes4.dex"):
    data = z.read(dex)
    print(f"   {dex}: DouqiuVideoWallpaper={'DouqiuVideoWallpaper' in data.decode('latin1')}, "
          f"skipWallpaper={'skipWallpaper' in data.decode('latin1')}")

print("\n3) 设置行")
r = subprocess.run([AAPT2, "dump", "xmltree", "--file", "res/xml/prefs_appdrawer.xml", APK],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
for l in r.stdout.splitlines():
    if re.search(r"douqiu\w+", l) or "EditTextPreference" in l:
        print("   ", l.strip()[:120])

print("\n4) 文案（默认/繁/简）")
r = subprocess.run([AAPT2, "dump", "resources", APK], capture_output=True, text=True,
                   encoding="utf-8", errors="replace")
lines = r.stdout.splitlines()
for key in ("douqiu_video_title", "douqiu_video_path_title"):
    i = next((k for k, l in enumerate(lines) if key in l), None)
    print(f"   {key}:")
    if i is not None:
        for c in lines[i:i + 4]:
            print("      ", c.strip()[:110])
import hashlib
print("\napk sha256:", hashlib.sha256(open(APK, "rb").read()).hexdigest(), os.path.getsize(APK))
