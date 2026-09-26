#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v11（mod 式 / 仅圆屏适配）组装：以【原包】为基底，只替换
   classes.dex + classes2.dex（2 处钩子）+ AndroidManifest.xml + 6 个资源文件。"""
import hashlib, io, os, sys, zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
W = r"E:\B1807\Documents\DSH\squarehome-mod"
ORIG = os.path.join(W, "squarehome-orig.apk")
BUILT = os.path.join(W, "work3", "built-mod.apk")
OUT = os.path.join(W, "work3", "squarehome-v11-unsigned.apk")

DEX = {"classes.dex": os.path.join(W, "work3", "patched", "classes.dex"),
       "classes2.dex": os.path.join(W, "work3", "patched", "classes2.dex")}
RES = ["AndroidManifest.xml",
       "res/xml/prefs_appdrawer.xml",
       "res/xml/prefs_about.xml",
       "res/layout/activity_wizard.xml",
       "res/layout/layout_wizard_content_bg.xml",
       "res/layout/wizard_advice.xml",
       "res/layout/wizard_tile_effect.xml"]
DROP = {"stamp-cert-sha256"}
sha = lambda b: hashlib.sha256(b).hexdigest()[:16]

orig = zipfile.ZipFile(ORIG)
built = zipfile.ZipFile(BUILT)
new = {k: open(v, "rb").read() for k, v in DEX.items()}
for r in RES:
    new[r] = built.read(r)
for k, v in new.items():
    print(f"  {k}: {len(v)} bytes sha={sha(v)}")

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as dst:
    for info in orig.infolist():
        n = info.filename
        if n in DROP or (n.startswith("META-INF/") and n.split(".")[-1] in ("MF", "SF", "RSA", "DSA", "EC")):
            continue
        data = new.get(n) or orig.read(n)
        zi = zipfile.ZipInfo(n, info.date_time)
        zi.compress_type = info.compress_type
        zi.external_attr = info.external_attr
        zi.internal_attr = info.internal_attr
        zi.create_system = info.create_system
        dst.writestr(zi, data, compress_type=info.compress_type)
orig.close()

z = zipfile.ZipFile(OUT)
o = zipfile.ZipFile(ORIG)
print(f"\nout: {OUT} ({os.path.getsize(OUT)} bytes, {len(z.namelist())} entries)")
print("arsc untouched:", z.read("resources.arsc") == o.read("resources.arsc"),
      "| classes4 untouched:", z.read("classes4.dex") == o.read("classes4.dex"))
changed = [n for n in o.namelist() if n not in DROP and n in z.namelist() and o.read(n) != z.read(n)]
print("changed entries (%d): %s" % (len(changed), changed))
print("apk sha256:", hashlib.sha256(open(OUT, "rb").read()).hexdigest())
