#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# v12 mod-style assembly: original APK as base, replace only
# classes.dex + classes2.dex (4 hooks) + AndroidManifest.xml + 6 resource files.
import hashlib, io, os, sys, zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
W = r"E:\B1807\Documents\DSH\squarehome-mod"
ORIG = os.path.join(W, "squarehome-orig.apk")
BUILT = os.path.join(W, "work3", "built-mod.apk")
OUT = os.path.join(W, "work3", "squarehome-v12-unsigned.apk")

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


def sha(b):
    return hashlib.sha256(b).hexdigest()[:16]


orig = zipfile.ZipFile(ORIG)
built = zipfile.ZipFile(BUILT)
new = {k: open(v, "rb").read() for k, v in DEX.items()}
for r in RES:
    new[r] = built.read(r)
for k, v in new.items():
    print("  %s: %d bytes sha=%s" % (k, len(v), sha(v)))

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
print("\nout: %s (%d bytes, %d entries)" % (OUT, os.path.getsize(OUT), len(z.namelist())))
print("arsc untouched:", z.read("resources.arsc") == o.read("resources.arsc"),
      "| classes4 untouched:", z.read("classes4.dex") == o.read("classes4.dex"))
changed = [n for n in o.namelist() if n not in DROP and n in z.namelist() and o.read(n) != z.read(n)]
print("changed entries (%d): %s" % (len(changed), changed))
print("apk sha256:", hashlib.sha256(open(OUT, "rb").read()).hexdigest())
