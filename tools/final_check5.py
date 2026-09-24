#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v4 integrity check (ASCII only to survive PowerShell rewriting)."""
import sys, io, zipfile, hashlib, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

W = r"E:\B1807\Documents\DSH\squarehome-mod"
ORIG = os.path.join(W, "squarehome-orig.apk")
FINAL = os.path.join(W, "SquareHome_3.0.1_round-v4.apk")
DEX = {"classes.dex": os.path.join(W, "work3", "patched", "classes.dex"),
       "classes2.dex": os.path.join(W, "work3", "patched", "classes2.dex")}
RES = ["res/xml/prefs_about.xml", "res/xml/prefs_appdrawer.xml",
       "res/layout/layout_wizard_content_bg.xml", "res/layout/wizard_advice.xml",
       "res/layout/wizard_tile_effect.xml", "res/layout/activity_wizard.xml"]


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
print("entries:", len(names), "| sig:", [n for n in names if n.startswith("META-INF/") and n.split(".")[-1] in ("MF", "SF", "RSA")])
print("stamp present:", "stamp-cert-sha256" in names)
print("arsc compress:", z.getinfo("resources.arsc").compress_type, "(0=stored)")
for n, p in DEX.items():
    print(n, "OK" if shab(z.read(n)) == shaf(p) else "MISMATCH", z.getinfo(n).file_size)
for n in RES:
    print(n, z.getinfo(n).file_size, shab(z.read(n))[:16])
orig = zipfile.ZipFile(ORIG)
same = {n: orig.read(n) == z.read(n) for n in ("classes3.dex", "classes4.dex", "classes5.dex",
                                               "classes6.dex", "AndroidManifest.xml", "resources.arsc")}
print("untouched identical:", same)
bad = []
for i in orig.infolist():
    n = i.filename
    if n == "stamp-cert-sha256" or n in DEX or n in RES:
        continue
    if n.startswith("META-INF/") and n.split(".")[-1] in ("MF", "SF", "RSA"):
        continue
    if n not in names:
        bad.append((n, "missing"))
    elif orig.read(n) != z.read(n):
        bad.append((n, "changed"))
print("unexpected differences:", bad if bad else "none")
