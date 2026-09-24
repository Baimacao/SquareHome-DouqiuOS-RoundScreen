#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""外科式重建 APK：只替换 2 个 dex + res/xml/prefs_about.xml（About 页署名），
其余条目（压缩方式/时间戳/属性位）逐字节保留。"""
import sys, io, zipfile, os, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

W = r"E:\B1807\Documents\DSH\squarehome-mod"
ORIG = os.path.join(W, "squarehome-orig.apk")
OUT = os.path.join(W, "work3", "squarehome-round2-unsigned.apk")
BUILT = os.path.join(W, "work3", "built-res.apk")   # apktool 资源重编译产物（只取一个文件）

REPLACEMENTS = {
    "classes.dex": os.path.join(W, "work3", "patched", "classes.dex"),
    "classes2.dex": os.path.join(W, "work3", "patched", "classes2.dex"),
}
# 只取我们「有意修改」的资源文件（apktool 会重编译全部资源，不能整包照搬）
RES_FILES = [
    "res/xml/prefs_about.xml",              # About 页署名
    "res/xml/prefs_appdrawer.xml",          # 圓屏適配 开关
    "res/layout/layout_wizard_content_bg.xml",  # OOBE 卡片安全区
    "res/layout/wizard_advice.xml",         # OOBE 内容安全区
    "res/layout/wizard_tile_effect.xml",    # OOBE 磚塊效果页改为可滚动
    "res/layout/activity_wizard.xml",       # OOBE 外壳：底部按钮移进圆内
]
DROP = {"stamp-cert-sha256"}


def sha(b):
    return hashlib.sha256(b).hexdigest()[:16]


src = zipfile.ZipFile(ORIG)
new_data = {k: open(v, "rb").read() for k, v in REPLACEMENTS.items()}

# 从 apktool 重编译产物里取回我们改动过的资源文件
if os.path.exists(BUILT):
    bz = zipfile.ZipFile(BUILT)
    for name in RES_FILES:
        new_data[name] = bz.read(name)
        print(f"{name} <- apktool build: {len(new_data[name])} bytes sha={sha(new_data[name])}")
    bz.close()
else:
    raise SystemExit("apktool build output missing: " + BUILT)

for k, v in new_data.items():
    if k.endswith(".dex"):
        print(f"{k}: {len(v)} bytes sha={sha(v)}")

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as dst:
    for info in src.infolist():
        name = info.filename
        if name in DROP:
            print("dropped", name)
            continue
        data = new_data[name] if (name in REPLACEMENTS or name in RES_FILES) else src.read(name)
        zi = zipfile.ZipInfo(name, info.date_time)
        zi.compress_type = info.compress_type
        zi.external_attr = info.external_attr
        zi.internal_attr = info.internal_attr
        zi.create_system = info.create_system
        dst.writestr(zi, data, compress_type=info.compress_type)
src.close()

# ---- 核对 ----
a = zipfile.ZipFile(ORIG)
b = zipfile.ZipFile(OUT)
an = {i.filename: i for i in a.infolist()}
bn = {i.filename: i for i in b.infolist()}
print("\nentries: orig=%d new=%d" % (len(an), len(bn)))
changed = []
for n, i in an.items():
    if n in DROP:
        continue
    if n not in bn:
        changed.append((n, "missing"))
    elif a.read(n) != b.read(n):
        changed.append((n, "changed"))
print("changed entries:", changed)
print("resources.arsc method (0=stored):", bn["resources.arsc"].compress_type)
print("out:", OUT, os.path.getsize(OUT), "bytes")
