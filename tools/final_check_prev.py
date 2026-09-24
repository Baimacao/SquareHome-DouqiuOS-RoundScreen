#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3 产物核对。"""
import sys, io, zipfile, hashlib, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

W = r"E:\B1807\Documents\DSH\squarehome-mod"
ORIG = os.path.join(W, "squarehome-orig.apk")
FINAL = os.path.join(W, "SquareHome_3.0.1_round-v3.apk")
DEX = {"classes.dex": os.path.join(W, "work3", "patched", "classes.dex"),
       "classes2.dex": os.path.join(W, "work3", "patched", "classes2.dex")}
RES = ["res/xml/prefs_about.xml", "res/xml/prefs_appdrawer.xml",
       "res/layout/layout_wizard_content_bg.xml", "res/layout/wizard_advice.xml",
       "res/layout/wizard_tile_effect.xml"]


def shaf(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def shab(b):
    return hashlib.sha256(b).hexdigest()


z = zipfile.ZipFile(FINAL)
names = z.namelist()
print("apk   :", FINAL)
print("size  :", os.path.getsize(FINAL))
print("sha256:", shaf(FINAL))
print("entries:", len(names), "| v1 sig:", [n for n in names if n.startswith("META-INF/") and n.split(".")[-1] in ("MF", "SF", "RSA")])
print("stamp-cert-sha256 present:", "stamp-cert-sha256" in names)
print("resources.arsc compress_type:", z.getinfo("resources.arsc").compress_type, "(0=stored)")
for n, p in DEX.items():
    print(f"{n}: {'OK' if shab(z.read(n)) == shaf(p) else 'MISMATCH'} size={z.getinfo(n).file_size}")
for n in RES:
    print(f"{n}: size={z.getinfo(n).file_size} sha={shab(z.read(n))[:16]}")

orig = zipfile.ZipFile(ORIG)
same = {n: orig.read(n) == z.read(n) for n in ("classes3.dex", "classes4.dex", "classes5.dex",
                                               "classes6.dex", "AndroidManifest.xml", "resources.arsc")}
print("untouched entries identical:", same)
diff = []
for i in orig.infolist():
    n = i.filename
    if n == "stamp-cert-sha256" or n in DEX or n in RES:
        continue
    if n.startswith("META-INF/") and n.split(".")[-1] in ("MF", "SF", "RSA"):
        continue
    if n not in names:
        diff.append((n, "missing"))
    elif orig.read(n) != z.read(n):
        diff.append((n, "changed"))
print("unexpected differences:", diff if diff else "none")
print("v2 sha256:", shaf(os.path.join(W, "SquareHome_3.0.1_round-v2.apk")))
